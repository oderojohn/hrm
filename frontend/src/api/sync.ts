import { apiClient } from "./client";
import { createResourceApi } from "./resource";

export interface SyncAgent {
  id: number;
  name: string;
  branch: number | null;
  branch_name: string | null;
  key_prefix: string;
  is_active: boolean;
  last_seen_at: string | null;
  created_at: string;
}

export interface SyncAgentCredentials extends SyncAgent {
  detail: string;
  api_key: string;
}

export interface SyncEvent {
  id: number;
  agent: number | null;
  agent_name: string | null;
  event_type: "AUTH_FAILED" | "PUSH" | "ERROR";
  status: "SUCCESS" | "FAILED";
  summary: string;
  payload: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

export const syncAgentsApi = createResourceApi<SyncAgent>("/attendance/sync-agents");
export const syncEventsApi = createResourceApi<SyncEvent>("/attendance/sync-events");

export async function createSyncAgent(payload: { name: string; branch?: number | null }) {
  const { data } = await apiClient.post<SyncAgentCredentials>("/attendance/sync-agents/", payload);
  return data;
}

export async function regenerateSyncAgentKey(id: number) {
  const { data } = await apiClient.post<{ detail: string; api_key: string }>(
    `/attendance/sync-agents/${id}/regenerate-key/`
  );
  return data;
}
