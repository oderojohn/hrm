import { apiClient, API_BASE_URL } from "./client";
import { useAuthStore } from "../store/authStore";
import type { PaginatedResponse } from "../types";

export interface ListParams {
  page?: number;
  page_size?: number;
  search?: string;
  ordering?: string;
  [key: string]: string | number | boolean | undefined;
}

export function createResourceApi<T extends { id: number }>(basePath: string) {
  const normalizedBase = basePath.endsWith("/") ? basePath : `${basePath}/`;

  return {
    list: async (params?: ListParams): Promise<PaginatedResponse<T>> => {
      const { data } = await apiClient.get<PaginatedResponse<T>>(normalizedBase, { params });
      return data;
    },
    get: async (id: number): Promise<T> => {
      const { data } = await apiClient.get<T>(`${normalizedBase}${id}/`);
      return data;
    },
    create: async (payload: Partial<T>): Promise<T> => {
      const { data } = await apiClient.post<T>(normalizedBase, payload);
      return data;
    },
    update: async (id: number, payload: Partial<T>): Promise<T> => {
      const { data } = await apiClient.patch<T>(`${normalizedBase}${id}/`, payload);
      return data;
    },
    remove: async (id: number): Promise<void> => {
      await apiClient.delete(`${normalizedBase}${id}/`);
    },
    exportUrl: (format: "csv" | "xlsx" | "pdf", params?: ListParams) => {
      const query = new URLSearchParams({ format, ...toStringRecord(params) });
      return `${API_BASE_URL}${normalizedBase}export/?${query.toString()}`;
    },
  };
}

function toStringRecord(params?: ListParams): Record<string, string> {
  if (!params) return {};
  const entries = Object.entries(params).filter(([, v]) => v !== undefined) as [string, string | number | boolean][];
  return Object.fromEntries(entries.map(([k, v]) => [k, String(v)]));
}

export async function downloadExport(url: string, filename: string) {
  const token = useAuthStore.getState().accessToken;
  const response = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  const blob = await response.blob();
  const objectUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(objectUrl);
}
