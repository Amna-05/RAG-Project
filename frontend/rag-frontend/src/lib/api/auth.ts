import { apiClient } from "./client";
import type { 
  LoginRequest, 
  RegisterRequest, 
  AuthResponse, 
  User 
} from "@/types/auth";

/**
 * Auth API endpoints
 * 
 * All functions use apiClient which:
 * - Automatically includes cookies (HttpOnly tokens)
 * - Handles token refresh via interceptors
 * - Throws errors for failed requests
 */

/**
 * Login user
 * 
 * @param credentials - Email and password
 * @returns User data and access token
 * 
 * Backend sets HttpOnly cookie automatically
 */
export async function login(credentials: LoginRequest): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>("/auth/login", credentials);
  return response.data;
}

/**
 * Register new user
 * 
 * @param data - User registration data
 * @returns User data and access token
 */
export async function register(data: RegisterRequest): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>("/auth/register", data);
  return response.data;
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