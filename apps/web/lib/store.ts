"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AppState {
  interests: string[];
  setInterests: (interests: string[]) => void;
  addInterest: (interest: string) => void;
  removeInterest: (topic: string) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      interests: [],
      setInterests: (interests) => set({ interests }),
      addInterest: (interest) =>
        set((state) => ({
          interests: state.interests.includes(interest)
            ? state.interests
            : [...state.interests, interest],
        })),
      removeInterest: (topic) =>
        set((state) => ({
          interests: state.interests.filter((i) => i !== topic),
        })),
    }),
    { name: "app-store" }
  )
);
