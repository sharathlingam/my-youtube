"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { signOut } from "next-auth/react";
import { useSession } from "next-auth/react";
import { useState, useRef } from "react";

const NAV_ITEMS = [
  {
    href: "/feed",
    label: "Feed",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    ),
  },
  {
    href: "/search",
    label: "Search",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
    ),
  },
  {
    href: "/history",
    label: "History",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9" />
        <polyline points="12 7 12 12 15 15" />
      </svg>
    ),
  },
  {
    href: "/interests",
    label: "Interests",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
      </svg>
    ),
  },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { data: session } = useSession();
  const [searchVal, setSearchVal] = useState("");
  const searchRef = useRef<HTMLInputElement>(null);

  function submitSearch() {
    const q = searchVal.trim();
    router.push(`/search${q ? `?q=${encodeURIComponent(q)}` : ""}`);
  }

  const initials = session?.user?.name
    ? session.user.name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : "??";

  return (
    <div className="min-h-screen flex">
      {/* ── Desktop sidebar ── */}
      <aside
        className="hidden md:flex flex-col fixed left-0 top-0 h-full z-40"
        style={{
          width: "220px",
          background: "#0F0F14",
          borderRight: "1px solid #1E1E28",
        }}
      >
        {/* Logo */}
        <div className="px-6 py-7 border-b border-border">
          <Link href="/feed" className="flex items-center gap-2 group">
            <span
              className="text-3xl tracking-widest leading-none text-text group-hover:text-accent transition-colors"
              style={{ fontFamily: "var(--font-bebas), sans-serif" }}
            >
              SIGNAL
            </span>
            <span
              className="w-2 h-2 rounded-full bg-accent mt-1 shrink-0"
              aria-hidden="true"
            />
          </Link>
        </div>

        {/* Search */}
        <div className="px-3 pt-4 pb-2">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-muted">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </span>
            <input
              ref={searchRef}
              type="text"
              value={searchVal}
              onChange={(e) => setSearchVal(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") submitSearch(); }}
              placeholder="Search…"
              className="w-full pl-8 pr-3 py-2 rounded-lg text-xs outline-none transition-all"
              style={{
                background: "#1A1A24",
                border: "1px solid #2A2A38",
                color: "#F0EDE8",
                fontFamily: "var(--font-outfit), sans-serif",
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = "#C8FF00"; }}
              onBlur={(e) => { e.currentTarget.style.borderColor = "#2A2A38"; }}
            />
          </div>
        </div>

        {/* Nav links */}
        <nav className="flex flex-col gap-1 px-3 py-3 flex-1">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || (item.href !== "/feed" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 relative group"
                style={{
                  color: active ? "#C8FF00" : "#5A5A6A",
                  background: active ? "rgba(200,255,0,0.06)" : "transparent",
                }}
              >
                <span
                  className="transition-colors"
                  style={{ color: active ? "#C8FF00" : "#5A5A6A" }}
                >
                  {item.icon}
                </span>
                <span
                  className="transition-colors"
                  style={{ color: active ? "#F0EDE8" : "#5A5A6A" }}
                >
                  {item.label}
                </span>
                {active && (
                  <span
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full bg-accent"
                    aria-hidden="true"
                  />
                )}
              </Link>
            );
          })}
        </nav>

        {/* User */}
        <div className="px-4 py-5 border-t border-border">
          <div className="flex items-center gap-3 mb-3">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold shrink-0"
              style={{ background: "#1E1E28", color: "#C8FF00" }}
            >
              {initials}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-text truncate">
                {session?.user?.name ?? "—"}
              </p>
              <p className="text-[11px] text-muted truncate">
                {session?.user?.email ?? ""}
              </p>
            </div>
          </div>
          <button
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="w-full text-left text-xs text-muted hover:text-text transition-colors py-1 px-1"
          >
            Sign out →
          </button>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main
        className="flex-1 min-h-screen pb-20 md:pb-0"
        style={{ marginLeft: "0", paddingLeft: "0" }}
      >
        <div className="md:ml-55 min-h-screen">
          {children}
        </div>
      </main>

      {/* ── Mobile bottom tab bar ── */}
      <nav
        className="md:hidden fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around px-2 safe-area-inset-bottom"
        style={{
          background: "#0F0F14",
          borderTop: "1px solid #1E1E28",
          height: "64px",
        }}
      >
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || (item.href !== "/feed" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-all"
              style={{ color: active ? "#C8FF00" : "#5A5A6A" }}
            >
              {item.icon}
              <span
                className="text-[10px] font-medium tracking-wide"
                style={{ fontFamily: "var(--font-bebas), sans-serif", letterSpacing: "0.08em" }}
              >
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
