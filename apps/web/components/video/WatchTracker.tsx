"use client";

import { useEffect, useRef } from "react";
import { apiFetch } from "@/lib/api";

declare global {
  interface Window {
    YT: any;
    onYouTubeIframeAPIReady: () => void;
  }
}

interface WatchTrackerProps {
  videoId: string;
  accessToken: string;
}

function loadYTScript(): Promise<void> {
  return new Promise((resolve) => {
    if (window.YT && window.YT.Player) {
      resolve();
      return;
    }
    const existing = document.getElementById("yt-iframe-api");
    if (!existing) {
      const tag = document.createElement("script");
      tag.id = "yt-iframe-api";
      tag.src = "https://www.youtube.com/iframe_api";
      document.head.appendChild(tag);
    }
    window.onYouTubeIframeAPIReady = () => resolve();
  });
}

export function WatchTracker({ videoId, accessToken }: WatchTrackerProps) {
  const playerRef = useRef<any>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sessionId = useRef(crypto.randomUUID());
  const maxWatched = useRef(0);

  async function flush() {
    const player = playerRef.current;
    if (!player) return;
    try {
      const current = player.getCurrentTime?.() ?? 0;
      const duration = player.getDuration?.() ?? 0;
      if (duration <= 0 || current <= 0) return;

      const watched = Math.max(maxWatched.current, current);
      const completionRate = Math.min(watched / duration, 1);

      await apiFetch("/api/v1/history", {
        method: "POST",
        accessToken,
        body: JSON.stringify({
          video_id: videoId,
          watch_duration_secs: Math.round(watched),
          completion_rate: completionRate,
          session_id: sessionId.current,
        }),
      });
    } catch {
      // Non-blocking — don't surface tracking errors to user
    }
  }

  useEffect(() => {
    let destroyed = false;

    async function init() {
      await loadYTScript();
      if (destroyed) return;

      playerRef.current = new window.YT.Player(`yt-player-${videoId}`, {
        events: {
          onStateChange: (event: any) => {
            if (event.data === window.YT.PlayerState.PAUSED || event.data === window.YT.PlayerState.ENDED) {
              flush();
            }
          },
        },
      });
    }

    init();

    // Poll current time every 10s to track max watched position
    intervalRef.current = setInterval(() => {
      const player = playerRef.current;
      if (!player) return;
      try {
        const t = player.getCurrentTime?.() ?? 0;
        if (t > maxWatched.current) maxWatched.current = t;
      } catch {
        // Player not ready yet
      }
    }, 10_000);

    return () => {
      destroyed = true;
      if (intervalRef.current) clearInterval(intervalRef.current);
      flush();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [videoId]);

  return null;
}
