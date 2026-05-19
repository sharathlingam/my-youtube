import { auth } from "@/auth";
import { redirect } from "next/navigation";

const SAMPLE_TOPICS = [
  "Programming", "Machine Learning", "Science", "Design",
  "Music", "Gaming", "Finance", "Philosophy",
];

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
      <p className="text-sm mb-8" style={{ color: "#5A5A6A" }}>
        Topics you care about shape your feed ranking.
      </p>

      {/* Topic pills — static preview, will be interactive in Phase 3 */}
      <div className="flex flex-wrap gap-2 mb-10">
        {SAMPLE_TOPICS.map((topic) => (
          <span
            key={topic}
            className="px-3 py-1.5 rounded-full text-sm font-medium cursor-default"
            style={{
              background: "#161620",
              border: "1px solid #1E1E28",
              color: "#5A5A6A",
            }}
          >
            {topic}
          </span>
        ))}
      </div>

      <div
        className="rounded-xl px-6 py-5 flex items-start gap-3"
        style={{ background: "#0F0F14", border: "1px solid #1E1E28" }}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 shrink-0" />
        <p className="text-sm leading-relaxed" style={{ color: "#5A5A6A" }}>
          Interest management will be fully interactive in Phase 3 — weights, auto-detected tags from your watch history, and manual boosts/suppression will appear here.
        </p>
      </div>
    </div>
  );
}
