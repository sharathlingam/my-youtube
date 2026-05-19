"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { VideoCard } from "./VideoCard";

interface VideoOut {
  id: string;
  title: string;
  channel_id: string;
  channel_name: string;
  thumbnail_url: string | null;
  published_at: string | null;
  duration_secs: number | null;
  view_count: number | null;
}

interface FeedResponse {
  items: VideoOut[];
  next_cursor: string | null;
}

interface FeedClientProps {
  accessToken: string;
}

export function FeedClient({ accessToken }: FeedClientProps) {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, status } =
    useInfiniteQuery<FeedResponse>({
      queryKey: ["feed"],
      queryFn: ({ pageParam }) => {
        const cursor = pageParam ? `&cursor=${encodeURIComponent(pageParam as string)}` : "";
        return apiFetch<FeedResponse>(`/api/v1/feed?limit=20${cursor}`, {
          accessToken,
        });
      },
      initialPageParam: null,
      getNextPageParam: (last) => last.next_cursor ?? undefined,
    });

  if (status === "pending") {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex flex-col gap-2">
            <div className="aspect-video w-full rounded-lg bg-gray-800 animate-pulse" />
            <div className="h-4 w-3/4 rounded bg-gray-800 animate-pulse" />
            <div className="h-3 w-1/2 rounded bg-gray-800 animate-pulse" />
          </div>
        ))}
      </div>
    );
  }

  if (status === "error") {
    return <p className="text-red-500 text-sm">Failed to load feed.</p>;
  }

  const videos = data.pages.flatMap((p) => p.items);

  if (videos.length === 0) {
    return (
      <p className="text-gray-500 text-sm">
        No videos yet. Subscriptions will sync in the background.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {videos.map((v) => (
          <VideoCard
            key={v.id}
            id={v.id}
            title={v.title}
            channelName={v.channel_name}
            thumbnailUrl={v.thumbnail_url}
            publishedAt={v.published_at}
            durationSecs={v.duration_secs}
            viewCount={v.view_count}
          />
        ))}
      </div>
      {hasNextPage && (
        <button
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
          className="mx-auto px-6 py-2 rounded-full bg-gray-800 text-white text-sm hover:bg-gray-700 disabled:opacity-50"
        >
          {isFetchingNextPage ? "Loading…" : "Load more"}
        </button>
      )}
    </div>
  );
}
