"use client";

import { useSession } from "next-auth/react";
import { useEffect, useRef } from "react";
import { apiFetch } from "@/lib/api";

export function useSessionSync() {
  const { data: session, status } = useSession();
  const lastSyncedToken = useRef<string | null>(null);

  useEffect(() => {
    if (status !== "authenticated" || !session) return;
    if (!session.sessionToken || !session.accessToken) return;
    if (lastSyncedToken.current === session.sessionToken) return;

    lastSyncedToken.current = session.sessionToken;

    apiFetch("/api/v1/auth/sync", {
      method: "POST",
      body: JSON.stringify({
        session_token: session.sessionToken,
        access_token: session.accessToken,
        expires_at: null,
        email: session.user?.email ?? "",
        name: session.user?.name ?? null,
        image: session.user?.image ?? null,
        google_id: session.googleId ?? null,
      }),
    }).catch((err) => {
      console.error("Session sync failed:", err);
      lastSyncedToken.current = null;
    });
  }, [session, status]);
}
