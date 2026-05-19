"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut } from "next-auth/react";
import { useSession } from "next-auth/react";

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
  const { data: session } = useSession();

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
        <div className="px-6 py-7 border-b border-[#1E1E28]">
          <Link href="/feed" className="flex items-center gap-2 group">
            <span
              className="text-3xl tracking-widest leading-none text-[#F0EDE8] group-hover:text-[#C8FF00] transition-colors"
              style={{ fontFamily: "var(--font-bebas), sans-serif" }}
            >
              SIGNAL
            </span>
            <span
              className="w-2 h-2 rounded-full bg-[#C8FF00] mt-1 shrink-0"
              aria-hidden="true"
            />
          </Link>
        </div>

        {/* Nav links */}
        <nav className="flex flex-col gap-1 px-3 py-5 flex-1">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
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
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full bg-[#C8FF00]"
                    aria-hidden="true"
                  />
                )}
              </Link>
            );
          })}
        </nav>

        {/* User */}
        <div className="px-4 py-5 border-t border-[#1E1E28]">
          <div className="flex items-center gap-3 mb-3">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold shrink-0"
              style={{ background: "#1E1E28", color: "#C8FF00" }}
            >
              {initials}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-[#F0EDE8] truncate">
                {session?.user?.name ?? "—"}
              </p>
              <p className="text-[11px] text-[#5A5A6A] truncate">
                {session?.user?.email ?? ""}
              </p>
            </div>
          </div>
          <button
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="w-full text-left text-xs text-[#5A5A6A] hover:text-[#F0EDE8] transition-colors py-1 px-1"
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
        <div
          className="md:ml-[220px] min-h-screen"
        >
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
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-all"
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
