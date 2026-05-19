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

function SkeletonCard() {
  return (
    <div className="flex flex-col gap-2.5">
      <div className="aspect-video w-full rounded-lg skeleton" />
      <div className="px-0.5 flex flex-col gap-2">
        <div className="h-3 w-1/3 rounded skeleton" />
        <div className="h-4 w-full rounded skeleton" />
        <div className="h-4 w-3/4 rounded skeleton" />
        <div className="h-3 w-1/4 rounded skeleton" />
      </div>
    </div>
  );
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
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {Array.from({ length: 9 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (status === "error") {
    return (
      <div
        className="flex flex-col items-center justify-center py-24 gap-3"
      >
        <span className="text-4xl" style={{ fontFamily: "var(--font-bebas), sans-serif", color: "#FF3B3B", letterSpacing: "0.1em" }}>
          ERROR
        </span>
        <p className="text-sm" style={{ color: "#5A5A6A" }}>
          Failed to load feed. Check API connection.
        </p>
      </div>
    );
  }

  const videos = data.pages.flatMap((p) => p.items);

  if (videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3">
        <span
          className="text-5xl"
          style={{ fontFamily: "var(--font-bebas), sans-serif", color: "#1E1E28", letterSpacing: "0.1em" }}
        >
          NO SIGNAL
        </span>
        <p className="text-sm text-center max-w-xs" style={{ color: "#5A5A6A" }}>
          Subscriptions are syncing in the background. Check back soon.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {videos.map((v, i) => (
          <VideoCard
            key={v.id}
            id={v.id}
            title={v.title}
            channelName={v.channel_name}
            thumbnailUrl={v.thumbnail_url}
            publishedAt={v.published_at}
            durationSecs={v.duration_secs}
            viewCount={v.view_count}
            index={i}
          />
        ))}
      </div>

      {hasNextPage && (
        <div className="flex justify-center">
          <button
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
            className="group flex items-center gap-2 px-6 py-2.5 text-sm font-medium transition-all duration-150 rounded-full disabled:opacity-40"
            style={{
              border: "1px solid #1E1E28",
              color: "#5A5A6A",
              background: "transparent",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = "#C8FF00";
              (e.currentTarget as HTMLButtonElement).style.color = "#C8FF00";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = "#1E1E28";
              (e.currentTarget as HTMLButtonElement).style.color = "#5A5A6A";
            }}
          >
            {isFetchingNextPage ? (
              <>
                <span className="w-3.5 h-3.5 rounded-full border-2 border-current border-t-transparent animate-spin" />
                Loading
              </>
            ) : (
              "Load more →"
            )}
          </button>
        </div>
      )}
    </div>
  );
}
