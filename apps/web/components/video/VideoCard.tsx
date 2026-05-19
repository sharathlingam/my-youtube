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
}

function formatDuration(secs: number): string {
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function formatViews(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M views`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K views`;
  return `${n} views`;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diff / 86_400_000);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days} days ago`;
  if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
  if (days < 365) return `${Math.floor(days / 30)} months ago`;
  return `${Math.floor(days / 365)} years ago`;
}

export function VideoCard({
  id,
  title,
  channelName,
  thumbnailUrl,
  publishedAt,
  durationSecs,
  viewCount,
}: VideoCardProps) {
  return (
    <Link href={`/watch/${id}`} className="group flex flex-col gap-2">
      <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-gray-800">
        {thumbnailUrl ? (
          <Image
            src={thumbnailUrl}
            alt={title}
            fill
            className="object-cover transition-transform group-hover:scale-105"
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          />
        ) : (
          <div className="w-full h-full bg-gray-800" />
        )}
        {durationSecs != null && (
          <span className="absolute bottom-1 right-1 rounded bg-black/80 px-1 py-0.5 text-xs text-white">
            {formatDuration(durationSecs)}
          </span>
        )}
      </div>
      <div className="flex flex-col gap-1 px-0.5">
        <p className="line-clamp-2 text-sm font-medium text-white leading-snug">{title}</p>
        <p className="text-xs text-gray-400">{channelName}</p>
        <p className="text-xs text-gray-500">
          {viewCount != null ? `${formatViews(viewCount)} · ` : ""}
          {publishedAt ? timeAgo(publishedAt) : ""}
        </p>
      </div>
    </Link>
  );
}
