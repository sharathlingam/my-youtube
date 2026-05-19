from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx
from redis.asyncio import Redis

from app.core.config import get_settings
from app.services.youtube.normalizer import normalize_channel, normalize_video
from app.services.youtube.quota import QuotaTracker

YT_BASE = "https://www.googleapis.com/youtube/v3"
_VIDEO_PARTS = "snippet,contentDetails,statistics"
_CHANNEL_PARTS = "snippet,statistics"
_SUB_PARTS = "snippet"


class YouTubeClient:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis
        self._quota = QuotaTracker(redis)
        self._settings = get_settings()
        self._http = httpx.AsyncClient(timeout=30.0)

    async def aclose(self) -> None:
        await self._http.aclose()

    # ------------------------------------------------------------------
    # Subscriptions
    # ------------------------------------------------------------------

    async def get_subscriptions(
        self, access_token: str, user_id: str
    ) -> list[dict]:
        cache_key = f"yt:subs:{user_id}"
        cached = await self._redis.get(cache_key)
        if cached:
            return json.loads(cached)

        channels: list[dict] = []
        page_token: str | None = None

        while True:
            await self._quota.check_and_increment("subscriptions.list")
            params: dict = {
                "part": _SUB_PARTS,
                "mine": "true",
                "maxResults": 50,
            }
            if page_token:
                params["pageToken"] = page_token

            resp = await self._http.get(
                f"{YT_BASE}/subscriptions",
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                resource = snippet.get("resourceId", {})
                channels.append(
                    {
                        "channel_id": resource.get("channelId", ""),
                        "channel_name": snippet.get("title", ""),
                        "thumbnail_url": (
                            snippet.get("thumbnails", {})
                            .get("high", {})
                            .get("url")
                        ),
                        "subscribed_since": snippet.get("publishedAt"),
                    }
                )

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        await self._redis.setex(cache_key, 3600, json.dumps(channels))
        return channels

    # ------------------------------------------------------------------
    # Channel details
    # ------------------------------------------------------------------

    async def get_channels(self, channel_ids: list[str]) -> list[dict]:
        results: list[dict] = []
        for i in range(0, len(channel_ids), 50):
            batch = channel_ids[i : i + 50]
            await self._quota.check_and_increment("subscriptions.list")
            resp = await self._http.get(
                f"{YT_BASE}/channels",
                params={
                    "part": _CHANNEL_PARTS,
                    "id": ",".join(batch),
                    "key": self._settings.youtube_api_key,
                    "maxResults": 50,
                },
            )
            resp.raise_for_status()
            for item in resp.json().get("items", []):
                results.append(normalize_channel(item))
        return results

    # ------------------------------------------------------------------
    # Playlist items (uploads playlist)
    # ------------------------------------------------------------------

    async def iter_playlist_videos(
        self, playlist_id: str, max_pages: int = 5
    ) -> AsyncIterator[str]:
        page_token: str | None = None
        for _ in range(max_pages):
            await self._quota.check_and_increment("playlistItems.list")
            params: dict = {
                "part": "contentDetails",
                "playlistId": playlist_id,
                "maxResults": 50,
                "key": self._settings.youtube_api_key,
            }
            if page_token:
                params["pageToken"] = page_token

            resp = await self._http.get(f"{YT_BASE}/playlistItems", params=params)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("items", []):
                vid_id = item.get("contentDetails", {}).get("videoId")
                if vid_id:
                    yield vid_id

            page_token = data.get("nextPageToken")
            if not page_token:
                break

    # ------------------------------------------------------------------
    # Video details (batched 50)
    # ------------------------------------------------------------------

    async def get_videos(self, video_ids: list[str]) -> list[dict]:
        results: list[dict] = []
        uncached: list[str] = []

        for vid_id in video_ids:
            cached = await self._redis.get(f"yt:video:{vid_id}")
            if cached:
                results.append(json.loads(cached))
            else:
                uncached.append(vid_id)

        for i in range(0, len(uncached), 50):
            batch = uncached[i : i + 50]
            await self._quota.check_and_increment("videos.list", len(batch))
            resp = await self._http.get(
                f"{YT_BASE}/videos",
                params={
                    "part": _VIDEO_PARTS,
                    "id": ",".join(batch),
                    "key": self._settings.youtube_api_key,
                    "maxResults": 50,
                },
            )
            resp.raise_for_status()
            for item in resp.json().get("items", []):
                normalized = normalize_video(item)
                await self._redis.setex(
                    f"yt:video:{normalized['id']}", 86400, json.dumps(normalized, default=str)
                )
                results.append(normalized)

        return results
