import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { FeedClient } from "@/components/video/FeedClient";

export default async function FeedPage() {
  const session = await auth();
  if (!session) redirect("/login");

  return (
    <main className="min-h-screen bg-black px-4 py-6 max-w-7xl mx-auto">
      <h1 className="text-xl font-semibold text-white mb-6">Your Feed</h1>
      <FeedClient accessToken={session.sessionToken ?? ""} />
    </main>
  );
}
