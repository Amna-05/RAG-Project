import { useCallback, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/lib/store/authStore";
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
        setIsLoading(false);
        
        // Redirect using window.location for guaranteed navigation
        console.log('🟡 [Auth] Redirecting...');
        window.location.href = '/dashboard';
      } catch (error: any) {
        console.error('🔴 [Auth] Login error:', error);
        toast.error(error.response?.data?.detail || "Login failed");
        setIsLoading(false);
      }
    },
    [setUser]
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
        setIsLoading(false);
        
        // Redirect using window.location
        console.log('🟡 [Auth] Redirecting...');
        window.location.href = '/dashboard';
      } catch (error: any) {
        console.error('🔴 [Auth] Register error:', error);
        toast.error(error.response?.data?.detail || "Registration failed");
        setIsLoading(false);
      }
    },
    [setUser]
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