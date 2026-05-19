"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { type Session } from "next-auth";
import { SessionProvider } from "next-auth/react";
import { useEffect, useState } from "react";
import { registerServiceWorker } from "@/lib/sw-register";
import { useSessionSync } from "@/lib/use-session-sync";

function SessionSync() {
  useSessionSync();
  return null;
}

export function Providers({
  children,
  session,
}: {
  children: React.ReactNode;
  session: Session | null;
}) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            gcTime: 5 * 60 * 1000,
          },
        },
      })
  );

  useEffect(() => {
    registerServiceWorker();
  }, []);

  return (
    <SessionProvider session={session}>
      <SessionSync />
      <QueryClientProvider client={queryClient}>
        {children}
        {process.env.NODE_ENV === "development" && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </SessionProvider>
  );
}
