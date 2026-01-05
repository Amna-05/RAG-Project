import { apiClient } from "./client";
import type {
  LoginRequest,
  RegisterRequest,
  User
} from "@/types/auth";

/**
 * Auth API endpoints
 *
 * All functions use apiClient which:
 * - Automatically includes cookies (HttpOnly tokens)
 * - Handles token refresh via interceptors
 * - Throws errors for failed requests
 *
 * Note: Backend sets auth cookies directly, so we only receive User data
 */

/**
 * Login user
 *
 * @param credentials - Email and password
 * @returns User data (tokens in httpOnly cookies)
 *
 * Backend sets HttpOnly cookie automatically
 */
export async function login(credentials: LoginRequest): Promise<{ user: User }> {
  const user = await apiClient.post<User>("/auth/login", credentials);
  return { user: user.data };
}

/**
 * Register new user
 *
 * @param data - User registration data
 * @returns User data (tokens in httpOnly cookies)
 */
export async function register(data: RegisterRequest): Promise<{ user: User }> {
  const user = await apiClient.post<User>("/auth/register", data);
  return { user: user.data };
}

/**
 * Logout user
 * 
 * Clears HttpOnly cookie on backend
 */
export async function logout(): Promise<void> {
  await apiClient.post("/auth/logout");
}

/**
 * Refresh access token
 * 
 * Uses refresh token from HttpOnly cookie
 * Backend returns new access token in cookie
 */
export async function refreshToken(): Promise<void> {
  await apiClient.post("/auth/refresh");
}

/**
 * Get current user data
 * 
 * Used to check if user is authenticated
 * and get fresh user data
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me");
  return response.data;
}

/**
 * Check authentication status
 * 
 * Returns basic auth check without full user data
 */
export async function checkAuth(): Promise<{ authenticated: boolean }> {
  const response = await apiClient.get<{ authenticated: boolean }>("/auth/check");
  return response.data;
}