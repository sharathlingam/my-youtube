export interface User {
  id: string;
  email: string;
  name: string | null;
  image: string | null;
  createdAt: string;
}

export interface Video {
  id: string;
  title: string;
  channelId: string;
  channelName: string;
  description: string;
  thumbnailUrl: string;
  publishedAt: string;
  durationSeconds: number;
  viewCount: number;
  tags: string[];
}

export interface FeedItem {
  video: Video;
  score: number;
  reason?: string;
}

export interface WatchEvent {
  videoId: string;
  watchDurationSecs: number;
  completionRate: number;
  sessionId: string;
}

export interface UserInterest {
  topic: string;
  weight: number;
  updatedAt: string;
}
