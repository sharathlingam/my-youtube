import { auth } from "@/auth";
import { redirect } from "next/navigation";

export default async function HistoryPage() {
  const session = await auth();
  if (!session) redirect("/login");

  return (
    <main className="min-h-screen bg-black px-4 py-6">
      <h1 className="text-xl font-semibold text-white mb-4">Watch History</h1>
      <p className="text-gray-500 text-sm">Your watch history will appear here.</p>
    </main>
  );
}
