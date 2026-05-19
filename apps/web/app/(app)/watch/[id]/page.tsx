import { auth } from "@/auth";
import { redirect } from "next/navigation";
import Link from "next/link";
import { WatchTracker } from "@/components/video/WatchTracker";

interface WatchPageProps {
  params: Promise<{ id: string }>;
}

export default async function WatchPage({ params }: WatchPageProps) {
  const session = await auth();
  if (!session) redirect("/login");

  const { id } = await params;

  return (
    <div className="min-h-screen px-5 py-6 max-w-5xl mx-auto">
      <Link
        href="/feed"
        className="inline-flex items-center gap-1.5 text-xs font-medium mb-5 transition-colors hover:text-accent"
        style={{ color: "#5A5A6A" }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M19 12H5M12 5l-7 7 7 7" />
        </svg>
        Back to feed
      </Link>

      <div
        className="w-full overflow-hidden rounded-xl"
        style={{
          border: "1px solid #1E1E28",
          background: "#0F0F14",
          aspectRatio: "16 / 9",
        }}
      >
        <iframe
          id={`yt-player-${id}`}
          src={`https://www.youtube.com/embed/${id}?autoplay=1&rel=0&modestbranding=1&enablejsapi=1`}
          title="Video player"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
          className="w-full h-full"
          style={{ display: "block" }}
        />
      </div>

      <div className="mt-4 flex items-center gap-2">
        <span className="font-mono text-[11px]" style={{ color: "#3A3A4A" }}>{id}</span>
      </div>

      <WatchTracker videoId={id} accessToken={session.sessionToken ?? ""} />
    </div>
  );
}
