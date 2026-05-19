import { openDB, type DBSchema, type IDBPDatabase } from "idb";

interface YouTubeDB extends DBSchema {
  videos: {
    key: string;
    value: {
      id: string;
      title: string;
      channelName: string;
      thumbnailUrl: string;
      publishedAt: string;
      durationSeconds: number;
      cachedAt: number;
    };
    indexes: { "by-cached": number };
  };
  watchEvents: {
    key: string;
    value: {
      videoId: string;
      watchDurationSecs: number;
      completionRate: number;
      sessionId: string;
      createdAt: number;
      synced: boolean;
    };
    indexes: { "by-synced": number };
  };
  feed: {
    key: string;
    value: {
      id: string;
      data: unknown[];
      cachedAt: number;
    };
  };
}

let dbPromise: Promise<IDBPDatabase<YouTubeDB>> | null = null;

export function getDB() {
  if (!dbPromise) {
    dbPromise = openDB<YouTubeDB>("yt-pwa-db", 1, {
      upgrade(db) {
        const videoStore = db.createObjectStore("videos", { keyPath: "id" });
        videoStore.createIndex("by-cached", "cachedAt");

        const eventStore = db.createObjectStore("watchEvents", {
          keyPath: "videoId",
        });
        eventStore.createIndex("by-synced", "synced");

        db.createObjectStore("feed", { keyPath: "id" });
      },
    });
  }
  return dbPromise;
}

export async function queueWatchEvent(
  event: Omit<YouTubeDB["watchEvents"]["value"], "createdAt" | "synced">
) {
  const db = await getDB();
  await db.put("watchEvents", {
    ...event,
    createdAt: Date.now(),
    synced: false,
  });
}

export async function getUnsyncedEvents() {
  const db = await getDB();
  const all = await db.getAll("watchEvents");
  return all.filter((e) => !e.synced);
}

export async function markEventSynced(videoId: string) {
  const db = await getDB();
  const event = await db.get("watchEvents", videoId);
  if (event) {
    await db.put("watchEvents", { ...event, synced: true });
  }
}

export async function cacheFeed(data: unknown[]) {
  const db = await getDB();
  await db.put("feed", { id: "main", data, cachedAt: Date.now() });
}

export async function getCachedFeed() {
  const db = await getDB();
  return db.get("feed", "main");
}
