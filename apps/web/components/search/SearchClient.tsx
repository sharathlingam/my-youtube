"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { useSearchParams, useRouter } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import Link from "next/link";

interface VideoResult {
  id: string;
  title: string;
  channel_id: string;
  channel_name: string;
  thumbnail_url: string | null;
  published_at: string | null;
  duration_secs: number | null;
  view_count: number | null;
}

interface SearchResponse {
  items: VideoResult[];
  query: string;
  has_more: boolean;
}

function formatViews(n: number | null): string {
  if (!n) return "";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${Math.round(n / 1_000)}K`;
  return String(n);
}

function formatDuration(secs: number | null): string {
  if (!secs) return "";
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

const API = process.env.NEXT_PUBLIC_API_URL ?? "";
const PAGE_SIZE = 20;

export function SearchClient({ accessToken }: { accessToken: string }) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialQ = searchParams.get("q") ?? "";
  const [inputVal, setInputVal] = useState(initialQ);
  const [query, setQuery] = useState(initialQ);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setInputVal(initialQ);
    setQuery(initialQ);
  }, [initialQ]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const {
    data,
    isLoading,
    isFetchingNextPage,
    fetchNextPage,
    hasNextPage,
  } = useInfiniteQuery<SearchResponse>({
    queryKey: ["search", query, accessToken],
    initialPageParam: 0,
    queryFn: async ({ pageParam }) => {
      if (!query.trim()) return { items: [], query, has_more: false };
      const offset = typeof pageParam === "number" ? pageParam : 0;
      const res = await fetch(
        `${API}/api/v1/search?q=${encodeURIComponent(query)}&limit=${PAGE_SIZE}&offset=${offset}`,
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      if (!res.ok) throw new Error("Search failed");
      return res.json();
    },
    getNextPageParam: (lastPage, allPages) =>
      lastPage.has_more ? allPages.length * PAGE_SIZE : undefined,
    enabled: !!accessToken,
    staleTime: 10_000,
  });

  function submit(q: string) {
    const trimmed = q.trim();
    setQuery(trimmed);
    router.replace(`/search?q=${encodeURIComponent(trimmed)}`, { scroll: false });
  }

  const allItems = data?.pages.flatMap((p) => p.items) ?? [];
  const totalCount = allItems.length;

  return (
    <div>
      {/* Search bar */}
      <form
        onSubmit={(e) => { e.preventDefault(); submit(inputVal); }}
        className="relative mb-6"
      >
        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-muted pointer-events-none">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </span>
        <input
          ref={inputRef}
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          placeholder="Search any video or channel…"
          className="w-full pl-11 pr-12 py-3 rounded-xl text-sm outline-none transition-all"
          style={{
            background: "#0F0F14",
            border: "1px solid #1E1E28",
            color: "#F0EDE8",
            fontFamily: "var(--font-outfit), sans-serif",
          }}
          onFocus={(e) => { e.currentTarget.style.borderColor = "#C8FF00"; }}
          onBlur={(e) => { e.currentTarget.style.borderColor = "#1E1E28"; }}
        />
        {inputVal && (
          <button
            type="button"
            onClick={() => { setInputVal(""); submit(""); inputRef.current?.focus(); }}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-muted hover:text-text transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}
      </form>

      {/* Empty prompt */}
      {!query.trim() && (
        <div className="text-center py-20">
          <p className="text-muted text-sm">Search any video, channel, or topic on YouTube</p>
        </div>
      )}

      {/* Loading — includes YouTube API fetch time */}
      {query.trim() && isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="rounded-xl overflow-hidden" style={{ background: "#0F0F14" }}>
              <div className="aspect-video animate-pulse" style={{ background: "#1E1E28" }} />
              <div className="p-3 space-y-2">
                <div className="h-3.5 rounded animate-pulse" style={{ background: "#1E1E28", width: "85%" }} />
                <div className="h-3 rounded animate-pulse" style={{ background: "#1E1E28", width: "50%" }} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* No results */}
      {query.trim() && !isLoading && allItems.length === 0 && (
        <div className="text-center py-20">
          <p
            className="text-2xl tracking-widest mb-2"
            style={{ fontFamily: "var(--font-bebas), sans-serif", color: "#F0EDE8" }}
          >
            NO RESULTS
          </p>
          <p className="text-muted text-sm">Nothing found for &ldquo;{query}&rdquo;</p>
        </div>
      )}

      {/* Results grid */}
      {!isLoading && allItems.length > 0 && (
        <>
          <p className="text-xs text-muted mb-4">
            {totalCount} result{totalCount !== 1 ? "s" : ""} for &ldquo;{query}&rdquo;
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {allItems.map((v, i) => (
              <Link
                key={v.id}
                href={`/watch/${v.id}`}
                className="group rounded-xl overflow-hidden transition-all duration-200 hover:ring-1 hover:ring-accent/30"
                style={{
                  background: "#0F0F14",
                  border: "1px solid #1E1E28",
                  animationDelay: `${i * 30}ms`,
                  animation: "fadeUp 0.4s ease both",
                }}
              >
                <div className="relative aspect-video overflow-hidden">
                  {v.thumbnail_url ? (
                    <img
                      src={v.thumbnail_url}
                      alt={v.title}
                      className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    />
                  ) : (
                    <div className="w-full h-full" style={{ background: "#1E1E28" }} />
                  )}
                  {v.duration_secs && (
                    <span
                      className="absolute bottom-2 right-2 text-[10px] font-semibold px-1.5 py-0.5 rounded"
                      style={{ background: "rgba(6,6,10,0.85)", color: "#F0EDE8", fontFamily: "var(--font-outfit), sans-serif" }}
                    >
                      {formatDuration(v.duration_secs)}
                    </span>
                  )}
                  <div
                    className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                    style={{ background: "rgba(6,6,10,0.5)" }}
                  >
                    <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: "#C8FF00" }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="#06060A"><polygon points="5 3 19 12 5 21 5 3" /></svg>
                    </div>
                  </div>
                </div>
                <div className="p-3">
                  <p className="text-text text-sm font-medium leading-snug line-clamp-2 group-hover:text-accent transition-colors mb-1">
                    {v.title}
                  </p>
                  <p className="text-muted text-xs">{v.channel_name}</p>
                  {v.view_count && (
                    <p className="text-muted text-xs mt-0.5">{formatViews(v.view_count)} views</p>
                  )}
                </div>
              </Link>
            ))}
          </div>

          {/* Load More */}
          {(hasNextPage || isFetchingNextPage) && (
            <div className="flex justify-center mt-8">
              <button
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
                className="flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-medium transition-all"
                style={{
                  background: isFetchingNextPage ? "#1A1A24" : "transparent",
                  border: "1px solid #2A2A38",
                  color: isFetchingNextPage ? "#5A5A6A" : "#F0EDE8",
                  fontFamily: "var(--font-outfit), sans-serif",
                  cursor: isFetchingNextPage ? "not-allowed" : "pointer",
                }}
                onMouseEnter={(e) => { if (!isFetchingNextPage) e.currentTarget.style.borderColor = "#C8FF00"; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = "#2A2A38"; }}
              >
                {isFetchingNextPage ? (
                  <>
                    <span className="w-3 h-3 rounded-full border border-muted border-t-transparent animate-spin" />
                    Loading…
                  </>
                ) : (
                  "Load more"
                )}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
