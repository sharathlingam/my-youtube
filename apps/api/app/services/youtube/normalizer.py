from __future__ import annotations

import re
from datetime import UTC, datetime


def _parse_duration(iso: str) -> int | None:
    """ISO 8601 duration (PT4M13S) → seconds."""
    if not iso:
        return None
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return None
    h, mn, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mn * 60 + s


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def normalize_video(item: dict) -> dict:
    snippet = item.get("snippet", {})
    content = item.get("contentDetails", {})
    stats = item.get("statistics", {})
    thumbnails = snippet.get("thumbnails", {})
    thumb = (
        thumbnails.get("maxres")
        or thumbnails.get("standard")
        or thumbnails.get("high")
        or thumbnails.get("medium")
        or thumbnails.get("default")
        or {}
    )
    return {
        "id": item["id"],
        "title": snippet.get("title", ""),
        "channel_id": snippet.get("channelId", ""),
        "channel_name": snippet.get("channelTitle", ""),
        "description": snippet.get("description", ""),
        "thumbnail_url": thumb.get("url"),
        "duration_secs": _parse_duration(content.get("duration", "")),
        "published_at": _parse_dt(snippet.get("publishedAt")),
        "category_id": snippet.get("categoryId"),
        "tags": snippet.get("tags", []),
        "view_count": int(stats["viewCount"]) if stats.get("viewCount") else None,
        "fetched_at": datetime.now(UTC),
    }


def normalize_channel(item: dict) -> dict:
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    thumbnails = snippet.get("thumbnails", {})
    thumb = (thumbnails.get("high") or thumbnails.get("medium") or thumbnails.get("default") or {})
    return {
        "id": item["id"],
        "name": snippet.get("title", ""),
        "thumbnail_url": thumb.get("url"),
        "subscriber_count": int(stats["subscriberCount"]) if stats.get("subscriberCount") else None,
        "fetched_at": datetime.now(UTC),
    }
