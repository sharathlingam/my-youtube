import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { Suspense } from "react";
import { SearchClient } from "@/components/search/SearchClient";

export default async function SearchPage() {
  const session = await auth();
  if (!session) redirect("/login");

  return (
    <div className="px-5 py-8 max-w-7xl mx-auto">
      <div className="flex items-baseline gap-3 mb-8">
        <h1
          className="text-4xl tracking-widest"
          style={{ fontFamily: "var(--font-bebas), sans-serif", color: "#F0EDE8" }}
        >
          SEARCH
        </h1>
        <span className="w-1.5 h-1.5 rounded-full bg-accent mb-1" aria-hidden="true" />
      </div>
      <Suspense>
        <SearchClient accessToken={session.sessionToken ?? ""} />
      </Suspense>
    </div>
  );
}
