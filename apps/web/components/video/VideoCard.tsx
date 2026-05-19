"use client";

import Image from "next/image";
import Link from "next/link";

interface VideoCardProps {
  id: string;
  title: string;
  channelName: string;
  thumbnailUrl: string | null;
  publishedAt: string | null;
  durationSecs: number | null;
  viewCount: number | null;
  index?: number;
}

function formatDuration(secs: number): string {
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function formatViews(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${Math.round(n / 1_000)}K`;
  return `${n}`;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diff / 86_400_000);
  if (days === 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  if (days < 365) return `${Math.floor(days / 30)}mo ago`;
  return `${Math.floor(days / 365)}y ago`;
}

export function VideoCard({
  id,
  title,
  channelName,
  thumbnailUrl,
  publishedAt,
  durationSecs,
  viewCount,
  index = 0,
}: VideoCardProps) {
  const delay = Math.min(index * 40, 400);

  return (
    <Link
      href={`/watch/${id}`}
      className="group block animate-fade-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      {/* Thumbnail */}
      <div
        className="relative aspect-video w-full overflow-hidden rounded-lg"
        style={{ background: "#0F0F14", border: "1px solid #1E1E28" }}
      >
        {thumbnailUrl ? (
          <Image
            src={thumbnailUrl}
            alt={title}
            fill
            className="object-cover transition-transform duration-500 group-hover:scale-[1.04]"
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center"
            style={{ background: "#161620" }}
          >
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2E2E3A" strokeWidth="1.5">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
          </div>
        )}

        {/* Duration badge */}
        {durationSecs != null && (
          <span
            className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded text-[11px] font-mono font-medium"
            style={{
              background: "rgba(6,6,10,0.85)",
              color: "#F0EDE8",
              backdropFilter: "blur(4px)",
              letterSpacing: "0.02em",
            }}
          >
            {formatDuration(durationSecs)}
          </span>
        )}

        {/* Hover overlay */}
        <div
          className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200"
          style={{ background: "rgba(6,6,10,0.4)" }}
        >
          <div
            className="w-11 h-11 rounded-full flex items-center justify-center"
            style={{ background: "#C8FF00" }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="#06060A">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
          </div>
        </div>
      </div>

      {/* Meta */}
      <div className="mt-2.5 px-0.5">
        {/* Channel + time row */}
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[11px] font-medium uppercase tracking-wider truncate" style={{ color: "#5A5A6A", maxWidth: "70%" }}>
            {channelName}
          </span>
          {publishedAt && (
            <span className="text-[11px] shrink-0 ml-2" style={{ color: "#3A3A4A" }}>
              {timeAgo(publishedAt)}
            </span>
          )}
        </div>

        {/* Title */}
        <h3
          className="text-sm font-medium leading-snug line-clamp-2 group-hover:text-accent transition-colors duration-200"
          style={{ color: "#F0EDE8" }}
        >
          {title}
        </h3>

        {/* Views */}
        {viewCount != null && (
          <p className="mt-1 text-[11px]" style={{ color: "#3A3A4A" }}>
            {formatViews(viewCount)} views
          </p>
        )}
      </div>
    </Link>
  );
}
