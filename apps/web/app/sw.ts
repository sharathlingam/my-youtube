/// <reference lib="webworker" />
import { defaultCache } from "@serwist/next/worker";
import type { PrecacheEntry, SerwistGlobalConfig } from "serwist";
import { CacheFirst, ExpirationPlugin, NetworkFirst, Serwist, StaleWhileRevalidate } from "serwist";

declare global {
  interface ServiceWorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (PrecacheEntry | string)[] | undefined;
  }
}

declare const self: ServiceWorkerGlobalScope;

const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  disableDevLogs: true,
  runtimeCaching: [
    {
      matcher: /^https:\/\/i\.ytimg\.com\/.*/i,
      handler: new CacheFirst({
        cacheName: "yt-thumbnails",
        plugins: [
          new ExpirationPlugin({ maxEntries: 300, maxAgeSeconds: 60 * 60 * 24 * 7 }),
        ],
      }),
    },
    {
      matcher: /^https:\/\/yt3\.ggpht\.com\/.*/i,
      handler: new CacheFirst({
        cacheName: "yt-avatars",
        plugins: [
          new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 60 * 60 * 24 * 7 }),
        ],
      }),
    },
    {
      matcher: ({ url }: { url: URL }) => url.pathname.startsWith("/api/v1/feed"),
      handler: new StaleWhileRevalidate({
        cacheName: "api-feed",
        plugins: [
          new ExpirationPlugin({ maxEntries: 1, maxAgeSeconds: 60 * 5 }),
        ],
      }),
    },
    {
      matcher: ({ url }: { url: URL }) => url.pathname.startsWith("/api/v1/videos"),
      handler: new CacheFirst({
        cacheName: "api-videos",
        plugins: [
          new ExpirationPlugin({ maxEntries: 500, maxAgeSeconds: 60 * 60 * 24 }),
        ],
      }),
    },
    {
      matcher: /^https:\/\/www\.youtube\.com\/embed\/.*/i,
      handler: new CacheFirst({
        cacheName: "yt-embeds",
        plugins: [
          new ExpirationPlugin({ maxEntries: 50, maxAgeSeconds: 60 * 60 * 24 * 7 }),
        ],
      }),
    },
    ...defaultCache,
  ],
});

serwist.addEventListeners();
