"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

interface Interest {
  topic: string;
  weight: number;
  updated_at: string;
}

const API = process.env.NEXT_PUBLIC_API_URL ?? "";
const BOOST_DELTA = 0.3;
const SUPPRESS_DELTA = 0.3;
const MAX_WEIGHT = 2.0;

function weightPct(w: number): number {
  return Math.min((w / MAX_WEIGHT) * 100, 100);
}

function weightLabel(w: number): string {
  if (w >= 1.5) return "Strong";
  if (w >= 0.8) return "High";
  if (w >= 0.4) return "Medium";
  if (w > 0) return "Low";
  return "Muted";
}

function weightColor(w: number): string {
  if (w >= 1.2) return "#C8FF00";
  if (w >= 0.6) return "#8FBF00";
  if (w > 0) return "#4A7A00";
  return "#2A2A38";
}

export function InterestsClient({ accessToken }: { accessToken: string }) {
  const queryClient = useQueryClient();
  const [newTopic, setNewTopic] = useState("");
  const [addError, setAddError] = useState("");

  const headers = { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" };

  const { data: interests = [], isLoading } = useQuery<Interest[]>({
    queryKey: ["interests", accessToken],
    queryFn: async () => {
      const res = await fetch(`${API}/api/v1/interests`, { headers });
      if (!res.ok) throw new Error("Failed to load interests");
      return res.json();
    },
    enabled: !!accessToken,
  });

  const updateMutation = useMutation({
    mutationFn: async ({ topic, weight }: { topic: string; weight: number }) => {
      const res = await fetch(`${API}/api/v1/interests/${encodeURIComponent(topic)}`, {
        method: "PATCH",
        headers,
        body: JSON.stringify({ weight: Math.max(0, Math.min(weight, 5)) }),
      });
      if (!res.ok) throw new Error("Update failed");
      return res.json();
    },
    onSuccess: (updated: Interest) => {
      queryClient.setQueryData<Interest[]>(["interests", accessToken], (prev = []) =>
        prev.map((i) => (i.topic === updated.topic ? updated : i))
      );
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (topic: string) => {
      await fetch(`${API}/api/v1/interests/${encodeURIComponent(topic)}`, {
        method: "DELETE",
        headers,
      });
    },
    onSuccess: (_: void, topic: string) => {
      queryClient.setQueryData<Interest[]>(["interests", accessToken], (prev = []) =>
        prev.filter((i) => i.topic !== topic)
      );
    },
  });

  const addMutation = useMutation({
    mutationFn: async (topic: string) => {
      const res = await fetch(`${API}/api/v1/interests`, {
        method: "POST",
        headers,
        body: JSON.stringify({ topic, weight: 0.5 }),
      });
      if (!res.ok) throw new Error("Add failed");
      return res.json();
    },
    onSuccess: (added: Interest) => {
      queryClient.setQueryData<Interest[]>(["interests", accessToken], (prev = []) => {
        const exists = prev.some((i) => i.topic === added.topic);
        return exists ? prev : [added, ...prev];
      });
      setNewTopic("");
      setAddError("");
    },
    onError: () => setAddError("Failed to add topic"),
  });

  function handleAdd() {
    const t = newTopic.trim().toLowerCase();
    if (!t) return;
    if (interests.some((i) => i.topic === t)) {
      setAddError("Already in your interests");
      return;
    }
    setAddError("");
    addMutation.mutate(t);
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-16 rounded-xl animate-pulse" style={{ background: "#0F0F14" }} />
        ))}
      </div>
    );
  }

  return (
    <div>
      {/* Add topic */}
      <div className="mb-8">
        <p className="text-xs text-muted mb-3 uppercase tracking-widest" style={{ fontFamily: "var(--font-bebas), sans-serif" }}>
          Add topic
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            value={newTopic}
            onChange={(e) => { setNewTopic(e.target.value); setAddError(""); }}
            onKeyDown={(e) => { if (e.key === "Enter") handleAdd(); }}
            placeholder="e.g. machine learning, jazz, cooking…"
            className="flex-1 px-4 py-2.5 rounded-lg text-sm outline-none transition-all"
            style={{
              background: "#0F0F14",
              border: "1px solid #1E1E28",
              color: "#F0EDE8",
              fontFamily: "var(--font-outfit), sans-serif",
            }}
            onFocus={(e) => { e.currentTarget.style.borderColor = "#C8FF00"; }}
            onBlur={(e) => { e.currentTarget.style.borderColor = "#1E1E28"; }}
          />
          <button
            onClick={handleAdd}
            disabled={!newTopic.trim() || addMutation.isPending}
            className="px-4 py-2.5 rounded-lg text-sm font-semibold transition-all disabled:opacity-40"
            style={{
              background: "#C8FF00",
              color: "#06060A",
              fontFamily: "var(--font-outfit), sans-serif",
            }}
          >
            {addMutation.isPending ? "…" : "Add"}
          </button>
        </div>
        {addError && <p className="text-xs mt-1.5" style={{ color: "#FF3B3B" }}>{addError}</p>}
      </div>

      {/* Interest list */}
      {interests.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-2xl tracking-widest mb-2" style={{ fontFamily: "var(--font-bebas), sans-serif", color: "#1E1E28" }}>
            NO INTERESTS YET
          </p>
          <p className="text-sm text-muted">Watch videos or add topics above — weights build automatically.</p>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-xs text-muted mb-3 uppercase tracking-widest" style={{ fontFamily: "var(--font-bebas), sans-serif" }}>
            {interests.length} topic{interests.length !== 1 ? "s" : ""}
          </p>
          {interests.map((interest) => (
            <div
              key={interest.topic}
              className="group flex items-center gap-4 px-4 py-3 rounded-xl transition-all"
              style={{ background: "#0F0F14", border: "1px solid #1E1E28" }}
            >
              {/* Topic + bar */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-sm font-medium text-text capitalize truncate">
                    {interest.topic}
                  </span>
                  <span
                    className="text-[10px] px-1.5 py-0.5 rounded shrink-0"
                    style={{
                      background: `${weightColor(interest.weight)}20`,
                      color: weightColor(interest.weight),
                      fontFamily: "var(--font-outfit), sans-serif",
                    }}
                  >
                    {weightLabel(interest.weight)}
                  </span>
                </div>
                <div className="h-1 rounded-full overflow-hidden" style={{ background: "#1E1E28" }}>
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${weightPct(interest.weight)}%`,
                      background: weightColor(interest.weight),
                    }}
                  />
                </div>
              </div>

              {/* Controls */}
              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => updateMutation.mutate({ topic: interest.topic, weight: interest.weight + BOOST_DELTA })}
                  disabled={updateMutation.isPending}
                  title="Boost"
                  className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold transition-all disabled:opacity-40 hover:bg-accent/10 hover:text-accent"
                  style={{ color: "#5A5A6A" }}
                >
                  +
                </button>
                <button
                  onClick={() => updateMutation.mutate({ topic: interest.topic, weight: interest.weight - SUPPRESS_DELTA })}
                  disabled={updateMutation.isPending}
                  title="Suppress"
                  className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold transition-all disabled:opacity-40 hover:bg-red-500/10 hover:text-red-400"
                  style={{ color: "#5A5A6A" }}
                >
                  −
                </button>
                <button
                  onClick={() => deleteMutation.mutate(interest.topic)}
                  disabled={deleteMutation.isPending}
                  title="Remove"
                  className="w-7 h-7 rounded-lg flex items-center justify-center transition-all disabled:opacity-40 hover:bg-red-500/10 hover:text-red-400"
                  style={{ color: "#2A2A38" }}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
