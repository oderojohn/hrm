import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "../store/authStore";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refresh = useAuthStore.getState().refreshToken;
  if (!refresh) throw new Error("No refresh token available");

  const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, { refresh });
  const newAccess = response.data.access as string;
  useAuthStore.getState().setAccessToken(newAccess);
  return newAccess;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken().finally(() => {
            refreshPromise = null;
          });
        }
        const newToken = await refreshPromise;
        originalRequest.headers = originalRequest.headers ?? {};
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch {
        useAuthStore.getState().clearAuth();
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { errors?: unknown; detail?: string } | undefined;
    if (data?.errors) {
      if (typeof data.errors === "string") return data.errors;
      if (typeof data.errors === "object") {
        const first = Object.values(data.errors as Record<string, unknown>)[0];
        if (Array.isArray(first)) return String(first[0]);
        if (typeof first === "string") return first;
      }
    }
    if (data?.detail) return data.detail;
    return error.message;
  }
  return "Something went wrong. Please try again.";
}
