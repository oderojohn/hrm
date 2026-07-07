import { apiClient } from "./client";
import type { PaginatedResponse } from "../types";

export interface Notification {
  id: number;
  channel: "EMAIL" | "SMS" | "IN_APP";
  title: string;
  body: string;
  is_read: boolean;
  related_url: string;
  created_at: string;
}

export async function fetchNotifications(params?: { is_read?: boolean; page?: number; page_size?: number }) {
  const { data } = await apiClient.get<PaginatedResponse<Notification>>("/communication/notifications/", { params });
  return data;
}

export async function markNotificationRead(id: number) {
  const { data } = await apiClient.post<Notification>(`/communication/notifications/${id}/mark_read/`);
  return data;
}
