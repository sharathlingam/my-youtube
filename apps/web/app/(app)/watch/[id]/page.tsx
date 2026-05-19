import { auth } from "@/auth";
import { redirect } from "next/navigation";
import Link from "next/link";

interface WatchPageProps {
  params: Promise<{ id: string }>;
}

export default async function WatchPage({ params }: WatchPageProps) {
  const session = await auth();
  if (!session) redirect("/login");

  const { id } = await params;

  return (
    <main className="min-h-screen bg-black px-4 py-6 max-w-5xl mx-auto">
      <Link href="/feed" className="text-sm text-gray-400 hover:text-white mb-4 inline-block">
        ← Back to feed
      </Link>
      <div className="aspect-video w-full rounded-lg overflow-hidden bg-gray-900">
        <iframe
          src={`https://www.youtube.com/embed/${id}?autoplay=1&rel=0`}
          title="YouTube video player"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
          className="w-full h-full"
        />
      </div>
    </main>
  );
}
