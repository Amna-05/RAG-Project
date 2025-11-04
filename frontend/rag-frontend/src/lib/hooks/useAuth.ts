import { useCallback, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/lib/store/authStore";
import * as authApi from "@/lib/api/auth";
import type { LoginRequest, RegisterRequest } from "@/types/auth";
import { toast } from "sonner";

/**
 * Custom hook for authentication
 * 
 * Usage:
 *   const { user, login, logout, isLoading } = useAuth()
 */
export function useAuth() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, setUser, setLoading, logout: clearAuth } = useAuthStore();

  /**
   * Login user
   */
  const login = useCallback(
    async (credentials: LoginRequest) => {
      try {
        setLoading(true);
        const response = await authApi.login(credentials);
        
        setUser(response.user);
        toast.success("Login successful!");
        router.push("/dashboard");
      } catch (error: any) {
        toast.error(error.response?.data?.detail || "Login failed");
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [router, setUser, setLoading]
  );

  /**
   * Register new user
   */
  const register = useCallback(
    async (data: RegisterRequest) => {
      try {
        setLoading(true);
        const response = await authApi.register(data);
        
        setUser(response.user);
        toast.success("Registration successful!");
        router.push("/dashboard");
      } catch (error: any) {
        toast.error(error.response?.data?.detail || "Registration failed");
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [router, setUser, setLoading]
  );

  /**
   * Logout user
   */
  const logout = useCallback(async () => {
    try {
      await authApi.logout();
      clearAuth();
      toast.success("Logged out successfully");
      router.push("/login");
    } catch (error) {
      clearAuth();
      router.push("/login");
    }
  }, [router, clearAuth]);

  /**
   * Check if user is authenticated
   * 
   * FIXED: Only runs on protected routes, not auth pages
   */
  const refreshAuth = useCallback(async () => {
    // Skip auth check on login/register pages
    const isAuthPage = pathname === "/login" || pathname === "/register";
    if (isAuthPage) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const userData = await authApi.getCurrentUser();
      setUser(userData);
    } catch (error) {
      // Not authenticated, clear state
      clearAuth();
      
      // Only redirect if on protected route
      const isProtectedRoute = pathname?.startsWith("/dashboard") || 
                               pathname?.startsWith("/documents") || 
                               pathname?.startsWith("/chat");
      
      if (isProtectedRoute) {
        router.push("/login");
      }
    } finally {
      setLoading(false);
    }
  }, [pathname, setUser, setLoading, clearAuth, router]);

  /**
   * Auto-refresh auth on mount
   * 
   * FIXED: Proper dependency array to prevent infinite loops
   */
  useEffect(() => {
    // Only check auth if:
    // 1. We don't have user data yet
    // 2. We're not on auth pages
    const isAuthPage = pathname === "/login" || pathname === "/register";
    
    if (!user && !isAuthPage) {
      refreshAuth();
    } else {
      setLoading(false);
    }
  }, [pathname]); // Only re-run when pathname changes

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshAuth,
  };
}