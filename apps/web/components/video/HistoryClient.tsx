"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import Link from "next/link";
import Image from "next/image";

interface HistoryItem {
  event_id: string;
  video_id: string;
  title: string;
  channel_name: string;
  thumbnail_url: string | null;
  duration_secs: number | null;
  completion_rate: number;
  watched_at: string;
}

interface HistoryResponse {
  items: HistoryItem[];
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return `${Math.floor(days / 7)}w ago`;
}

export function HistoryClient({ accessToken }: { accessToken: string }) {
  const { data, status } = useQuery<HistoryResponse>({
    queryKey: ["history"],
    queryFn: () => apiFetch<HistoryResponse>("/api/v1/history?limit=50", { accessToken }),
  });

  if (status === "pending") {
    return (
      <div className="flex flex-col gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex gap-3 items-center">
            <div className="w-32 shrink-0 aspect-video rounded-lg skeleton" />
            <div className="flex flex-col gap-2 flex-1">
              <div className="h-4 w-3/4 rounded skeleton" />
              <div className="h-3 w-1/3 rounded skeleton" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (status === "error") {
    return <p className="text-sm" style={{ color: "#FF3B3B" }}>Failed to load history.</p>;
  }

  const items = data.items;

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3" style={{ border: "1px dashed #1E1E28", borderRadius: "12px" }}>
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#2E2E3A" strokeWidth="1.2" strokeLinecap="round">
          <circle cx="12" cy="12" r="9" /><polyline points="12 7 12 12 15 15" />
        </svg>
        <p className="text-3xl tracking-widest" style={{ fontFamily: "var(--font-bebas), sans-serif", color: "#2E2E3A" }}>NOTHING YET</p>
        <p className="text-sm" style={{ color: "#5A5A6A" }}>Watch videos to build your history.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      {items.map((item) => (
        <Link
          key={item.event_id}
          href={`/watch/${item.video_id}`}
          className="group flex gap-4 items-center px-3 py-3 rounded-xl transition-colors"
          style={{ background: "transparent" }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "#0F0F14")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
        >
          {/* Thumbnail */}
          <div className="relative w-32 shrink-0 aspect-video rounded-lg overflow-hidden" style={{ background: "#161620" }}>
            {item.thumbnail_url ? (
              <Image src={item.thumbnail_url} alt={item.title} fill className="object-cover" sizes="128px" />
            ) : (
              <div className="w-full h-full" style={{ background: "#161620" }} />
            )}
            {/* Completion bar */}
            <div className="absolute bottom-0 left-0 right-0 h-0.5" style={{ background: "#1E1E28" }}>
              <div
                className="h-full bg-accent"
                style={{ width: `${Math.round(item.completion_rate * 100)}%` }}
              />
            </div>
          </div>

          {/* Meta */}
          <div className="flex flex-col gap-1 min-w-0 flex-1">
            <p className="text-sm font-medium line-clamp-2 group-hover:text-accent transition-colors" style={{ color: "#F0EDE8" }}>
              {item.title}
            </p>
            <p className="text-[11px] uppercase tracking-wider" style={{ color: "#5A5A6A" }}>{item.channel_name}</p>
            <p className="text-[11px]" style={{ color: "#3A3A4A" }}>
              {Math.round(item.completion_rate * 100)}% watched · {timeAgo(item.watched_at)}
            </p>
          </div>
        </Link>
      ))}
    </div>
  );
}
