import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { API_URL } from "../constants";

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Rate limit error interface
interface RateLimitError {
  detail: string;
  retry_after?: number;
  error_code?: string;
}

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Handle rate limiting (429 Too Many Requests)
    if (error.response?.status === 429) {
      const rateLimitError = error.response.data as RateLimitError;
      const retryAfter = rateLimitError.retry_after ||
                         parseInt(error.response.headers['retry-after'] || '60', 10);

      // Create a user-friendly error with retry information
      const rateLimitMessage = `Rate limit exceeded. Please try again in ${retryAfter} seconds.`;

      // Dispatch custom event for UI components to handle
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('rate-limit-exceeded', {
          detail: {
            retryAfter,
            message: rateLimitMessage,
            endpoint: originalRequest.url
          }
        }));
      }

      // Enhance error with rate limit info
      const enhancedError = new Error(rateLimitMessage) as Error & {
        retryAfter: number;
        isRateLimitError: boolean;
      };
      enhancedError.retryAfter = retryAfter;
      enhancedError.isRateLimitError = true;

      return Promise.reject(enhancedError);
    }

    // If 401 and not already retried, try refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Don't try to refresh if we're already on auth endpoints
      const isAuthEndpoint = originalRequest.url?.includes("/auth/login") ||
                            originalRequest.url?.includes("/auth/register") ||
                            originalRequest.url?.includes("/auth/refresh");

      if (isAuthEndpoint) {
        return Promise.reject(error);
      }

      try {
        // Try to refresh token
        await axios.post(
          `${API_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        );

        // Retry original request
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed - let the useAuth hook handle redirect
        // Don't redirect here to avoid infinite loops
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Helper function to handle API errors
export function getErrorMessage(error: unknown): string {
  // Check for rate limit errors first
  if (error && typeof error === 'object' && 'isRateLimitError' in error) {
    const rateLimitError = error as { isRateLimitError: unknown; message?: string };
    return rateLimitError.message || 'Rate limit exceeded. Please try again later.';
  }

  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail: string }>;

    // Handle rate limit response
    if (axiosError.response?.status === 429) {
      const retryAfter = axiosError.response.headers['retry-after'] || '60';
      return `Rate limit exceeded. Please try again in ${retryAfter} seconds.`;
    }

    return axiosError.response?.data?.detail || error.message;
  }
  return "An unexpected error occurred";
}

// Helper to check if error is a rate limit error
export function isRateLimitError(error: unknown): boolean {
  if (error && typeof error === 'object' && 'isRateLimitError' in error) {
    return true;
  }
  if (axios.isAxiosError(error) && error.response?.status === 429) {
    return true;
  }
  return false;
}

// Get retry-after time from rate limit error
export function getRetryAfter(error: unknown): number {
  if (error && typeof error === 'object' && 'retryAfter' in error) {
    return (error as { retryAfter: number }).retryAfter;
  }
  if (axios.isAxiosError(error) && error.response?.status === 429) {
    return parseInt(error.response.headers['retry-after'] || '60', 10);
  }
  return 60; // Default 60 seconds
}