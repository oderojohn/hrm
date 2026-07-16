import { apiClient } from "./client";

export interface EmailSettings {
  id: number;
  smtp_host: string;
  smtp_port: number | null;
  smtp_username: string;
  use_tls: boolean;
  from_email: string;
  is_configured: boolean;
}

export async function fetchEmailSettings() {
  const { data } = await apiClient.get<EmailSettings>("/system-settings/email-settings/");
  return data;
}

export async function updateEmailSettings(payload: Partial<EmailSettings> & { smtp_password?: string }) {
  const { data } = await apiClient.patch<EmailSettings>("/system-settings/email-settings/", payload);
  return data;
}

export async function sendTestEmail(to?: string) {
  const { data } = await apiClient.post<{ detail: string }>("/system-settings/email-settings/test/", { to });
  return data;
}

export interface WeeklyReportSettings {
  id: number;
  is_enabled: boolean;
  extra_recipients: string[];
}

export async function fetchWeeklyReportSettings() {
  const { data } = await apiClient.get<WeeklyReportSettings>("/system-settings/weekly-report-settings/");
  return data;
}

export async function updateWeeklyReportSettings(payload: Partial<WeeklyReportSettings>) {
  const { data } = await apiClient.patch<WeeklyReportSettings>("/system-settings/weekly-report-settings/", payload);
  return data;
}
