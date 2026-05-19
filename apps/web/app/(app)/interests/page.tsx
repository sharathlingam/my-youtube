import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { InterestsClient } from "@/components/interests/InterestsClient";

export default async function InterestsPage() {
  const session = await auth();
  if (!session) redirect("/login");

  return (
    <div className="px-5 py-8 max-w-3xl mx-auto">
      <div className="flex items-baseline gap-3 mb-2">
        <h1
          className="text-4xl tracking-widest"
          style={{ fontFamily: "var(--font-bebas), sans-serif", color: "#F0EDE8" }}
        >
          INTERESTS
        </h1>
        <span className="w-1.5 h-1.5 rounded-full bg-accent mb-1" aria-hidden="true" />
      </div>
      <p className="text-sm mb-8 text-muted">
        Topics shape your feed ranking. Weights build automatically from watch history — boost or suppress manually.
      </p>
      <InterestsClient accessToken={session.sessionToken ?? ""} />
    </div>
  );
}
