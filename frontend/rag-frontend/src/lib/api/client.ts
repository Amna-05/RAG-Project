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

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

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
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail: string }>;
    return axiosError.response?.data?.detail || error.message;
  }
  return "An unexpected error occurred";
}