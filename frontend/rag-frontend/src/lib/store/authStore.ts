import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, AuthState } from "@/types/auth";

interface AuthStore extends AuthState {
  // Actions
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

/**
 * Zustand store for authentication state
 * 
 * Features:
 * - Persists user data to localStorage
 * - Provides global auth state
 * - Handles login/logout actions
 * 
 * Usage:
 *   const { user, isAuthenticated, setUser } = useAuthStore()
 */
export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: true,

      // Actions
      setUser: (user) =>
        set({
          user,
          isAuthenticated: !!user,
          isLoading: false,
        }),

      setLoading: (loading) =>
        set({ isLoading: loading }),

      logout: () =>
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        }),
    }),
    {
      name: "auth-storage", // localStorage key
      partialize: (state) => ({
        // Only persist user data, not loading state
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
