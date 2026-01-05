import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types/auth";

interface AuthStore {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  clearAuth: () => void;
}

/**
 * Simple auth store with localStorage persistence
 *
 * KISS principle: Keep It Simple
 */
const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,

      setUser: (user) => {
        console.log('🔵 [Store] setUser:', user);
        set({ user, isAuthenticated: !!user });
      },

      clearAuth: () => {
        console.log('🔴 [Store] clearAuth');
        set({ user: null, isAuthenticated: false });
      },
    }),
    {
      name: "auth-storage",
    }
  )
);

export default useAuthStore;