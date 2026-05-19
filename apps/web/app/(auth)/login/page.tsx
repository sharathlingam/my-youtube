import { signIn } from "@/auth";

export default function LoginPage() {
  return (
    <main
      className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{ background: "#06060A" }}
    >
      {/* Background grid lines */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(30,30,40,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(30,30,40,0.5) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage: "radial-gradient(ellipse 70% 60% at 50% 50%, black 30%, transparent 100%)",
          WebkitMaskImage: "radial-gradient(ellipse 70% 60% at 50% 50%, black 30%, transparent 100%)",
        }}
      />

      {/* Glow */}
      <div
        className="absolute pointer-events-none"
        style={{
          width: "600px",
          height: "600px",
          background: "radial-gradient(circle, rgba(200,255,0,0.04) 0%, transparent 70%)",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
        }}
      />

      {/* Card */}
      <div
        className="relative z-10 flex flex-col items-center px-10 py-12 w-full max-w-sm"
        style={{
          background: "#0F0F14",
          border: "1px solid #1E1E28",
          borderRadius: "16px",
        }}
      >
        {/* Logo */}
        <div className="flex items-center gap-2 mb-2">
          <span
            className="text-5xl tracking-widest leading-none"
            style={{ fontFamily: "var(--font-bebas), sans-serif", color: "#F0EDE8" }}
          >
            SIGNAL
          </span>
          <span
            className="w-2.5 h-2.5 rounded-full bg-accent mt-2 shrink-0"
            aria-hidden="true"
          />
        </div>

        <p className="text-sm mb-10 text-center" style={{ color: "#5A5A6A" }}>
          Your personalized feed, tuned to your taste
        </p>

        {/* Divider */}
        <div className="w-full h-px mb-8" style={{ background: "#1E1E28" }} />

        {/* Sign in button */}
        <form
          action={async () => {
            "use server";
            await signIn("google", { redirectTo: "/feed" });
          }}
          className="w-full"
        >
          <button
            type="submit"
            className="w-full flex items-center justify-center gap-3 py-3 px-5 rounded-lg text-sm font-medium transition-colors duration-150 hover:bg-white"
            style={{
              background: "#F0EDE8",
              color: "#06060A",
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Continue with Google
          </button>
        </form>

        <p className="mt-6 text-[11px] text-center" style={{ color: "#3A3A4A" }}>
          Your watch history stays private and local
        </p>
      </div>
    </main>
  );
}
