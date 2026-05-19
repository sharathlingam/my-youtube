export async function registerServiceWorker() {
  if (typeof window === "undefined" || !("serviceWorker" in navigator)) return;
  if (process.env.NODE_ENV === "development") return;

  try {
    const registration = await navigator.serviceWorker.register("/sw.js", {
      scope: "/",
    });
    console.log("SW registered:", registration.scope);
  } catch (err) {
    console.error("SW registration failed:", err);
  }
}
