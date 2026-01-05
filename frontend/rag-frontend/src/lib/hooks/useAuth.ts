import { useCallback, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import useAuthStore from "@/lib/store/authStore";
import * as authApi from "@/lib/api/auth";
import type { LoginRequest, RegisterRequest } from "@/types/auth";
import { toast } from "sonner";

/**
 * Auth hook with proper loading states
 */
export function useAuth() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, setUser, clearAuth } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Login
   */
  const login = useCallback(
    async (credentials: LoginRequest) => {
      try {
        setIsLoading(true);
        console.log('🟡 [Auth] Login starting...');

        const response = await authApi.login(credentials);
        console.log('🟡 [Auth] API response:', response);

        if (!response.user) {
          throw new Error('No user data in response');
        }

        // Set user in store (Zustand will handle persistence)
        setUser(response.user);

        // Force a small delay to ensure React batches the state update
        await new Promise(resolve => setTimeout(resolve, 100));

        // Verify it was saved
        const store = useAuthStore.getState();
        console.log('🟡 [Auth] Store after setUser:', {
          hasUser: !!store.user,
          isAuthenticated: store.isAuthenticated,
        });

        toast.success("Login successful!");

        // Show redirect message and redirect immediately
        console.log('🟡 [Auth] Redirecting to dashboard...');
        // Use router.push for better navigation handling
        router.push('/dashboard');
      } catch (error: any) {
        console.error('🔴 [Auth] Login error:', error);

        // Check if it's a network error
        if (!error.response) {
          console.error('Network error - backend might not be running');
          toast.error("Cannot connect to server. Is the backend running on localhost:8000?");
          setIsLoading(false);
          throw error; // Re-throw for form to handle
        }

        // Handle specific error statuses
        if (error.response?.status === 401) {
          toast.error("Invalid email or password");
        } else if (error.response?.status === 422) {
          toast.error("Invalid request format");
        } else {
          const errorMessage = error.response?.data?.detail || error.message || "Login failed";
          toast.error(errorMessage);
        }

        setIsLoading(false);
        throw error; // Re-throw for form to handle
      }
    },
    [setUser, router]
  );

  /**
   * Register
   */
  const register = useCallback(
    async (data: RegisterRequest) => {
      try {
        setIsLoading(true);
        console.log('🟡 [Auth] Register starting...');

        const response = await authApi.register(data);
        console.log('🟡 [Auth] API response:', response);

        if (!response.user) {
          throw new Error('No user data in response');
        }

        // Set user in store
        setUser(response.user);

        // Small delay
        await new Promise(resolve => setTimeout(resolve, 100));

        // Verify
        const store = useAuthStore.getState();
        console.log('🟡 [Auth] Store after setUser:', {
          hasUser: !!store.user,
          isAuthenticated: store.isAuthenticated,
        });

        toast.success("Registration successful!");

        // Show redirect message and redirect immediately
        console.log('🟡 [Auth] Redirecting to dashboard...');
        // Use router.push for better navigation handling
        router.push('/dashboard');
      } catch (error: any) {
        console.error('🔴 [Auth] Register error:', error);

        // Check if it's a network error
        if (!error.response) {
          console.error('Network error - backend might not be running');
          toast.error("Cannot connect to server. Is the backend running on localhost:8000?");
          setIsLoading(false);
          throw error; // Re-throw for form to handle
        }

        // Handle specific error statuses
        if (error.response?.status === 400) {
          const detail = error.response?.data?.detail || "";
          if (detail.toLowerCase().includes("username")) {
            toast.error("This username is already taken");
          } else if (detail.toLowerCase().includes("email")) {
            toast.error("This email is already registered");
          } else {
            toast.error(detail || "Registration failed");
          }
        } else if (error.response?.status === 422) {
          toast.error("Invalid request format");
        } else {
          const errorMessage = error.response?.data?.detail || error.message || "Registration failed";
          toast.error(errorMessage);
        }

        setIsLoading(false);
        throw error; // Re-throw for form to handle
      }
    },
    [setUser, router]
  );

  /**
   * Logout
   */
  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearAuth();
      toast.success("Logged out");
      window.location.href = '/login';
    }
  }, [clearAuth]);

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
  };
}