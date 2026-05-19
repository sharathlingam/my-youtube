import type { Metadata, Viewport } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { auth } from "@/auth";
import { Providers } from "@/components/providers";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist" });

export const metadata: Metadata = {
  title: "My YouTube",
  description: "Personalized YouTube feed",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "MyYT",
  },
};

export const viewport: Viewport = {
  themeColor: "#ff0000",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();

  return (
    <html lang="en" className={`${geist.variable} h-full antialiased`}>
      <body className="min-h-full bg-black text-white" suppressHydrationWarning>
        <Providers session={session}>{children}</Providers>
      </body>
    </html>
  );
}
