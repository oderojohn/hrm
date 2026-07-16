import { apiClient, API_BASE_URL } from "./client";

export interface ManagementDashboard {
  total_employees: number;
  active_employees: number;
  present_today: number;
  absent_today: number;
  on_leave_today: number;
  pending_leave_requests: number;
  birthdays_today: Array<{ id: number; full_name: string; employee_number: string }>;
  new_employees: Array<{ id: number; full_name: string; employee_number: string; employment_date: string }>;
  contract_expiry_alerts: Array<{ id: number; full_name: string; contract_end_date: string }>;
  document_expiry_alerts: Array<{ id: number; title: string; expiry_date: string; employee_id: number | null }>;
  recent_announcements: Array<{ id: number; title: string; published_at: string | null }>;
  charts: {
    employee_growth: Array<{ month: string; count: number }>;
    attendance_trends: Array<{ date: string; count: number }>;
    leave_trends: Array<{ month: string; count: number }>;
    department_distribution: Array<{ department__name: string; count: number }>;
    gender_distribution: Array<{ gender: string; count: number }>;
  };
}

export interface PersonalDashboard {
  employee_number: string;
  full_name: string;
  clocked_in_today: boolean;
  clocked_out_today: boolean;
  pending_leave_requests: number;
  next_approved_leave: string | null;
  leave_balances: Array<{ leave_type: string; remaining_days: number }>;
  recent_announcements: Array<{ id: number; title: string; published_at: string | null }>;
}

export type DashboardResponse = ManagementDashboard | PersonalDashboard;

export async function fetchDashboard(): Promise<DashboardResponse> {
  const { data } = await apiClient.get<DashboardResponse>("/reports/dashboard/");
  return data;
}

export interface ReportQueryParams {
  period?: "week" | "month";
  start?: string;
  end?: string;
  department?: number;
}

export interface ReportPreview {
  summary: { count: number };
  results: Array<Record<string, string | number | boolean | null>>;
}

function toStringRecord(params?: ReportQueryParams): Record<string, string> {
  if (!params) return {};
  const entries = Object.entries(params).filter(([, v]) => v !== undefined) as [string, string | number][];
  return Object.fromEntries(entries.map(([k, v]) => [k, String(v)]));
}

function reportUrl(path: string, format: "csv" | "xlsx" | "pdf", params?: ReportQueryParams) {
  const query = new URLSearchParams({ format, ...toStringRecord(params) });
  return `${API_BASE_URL}${path}?${query.toString()}`;
}

export async function fetchAttendanceReport(params?: ReportQueryParams) {
  const { data } = await apiClient.get<ReportPreview>("/reports/attendance/", { params });
  return data;
}

export function attendanceReportExportUrl(format: "csv" | "xlsx" | "pdf", params?: ReportQueryParams) {
  return reportUrl("/reports/attendance/", format, params);
}

export async function fetchLateArrivalsReport(params?: ReportQueryParams) {
  const { data } = await apiClient.get<ReportPreview>("/reports/attendance-late-arrivals/", { params });
  return data;
}

export function lateArrivalsReportExportUrl(format: "csv" | "xlsx" | "pdf", params?: ReportQueryParams) {
  return reportUrl("/reports/attendance-late-arrivals/", format, params);
}

export async function fetchAbsenteeismReport(params?: ReportQueryParams) {
  const { data } = await apiClient.get<ReportPreview>("/reports/attendance-absenteeism/", { params });
  return data;
}

export function absenteeismReportExportUrl(format: "csv" | "xlsx" | "pdf", params?: ReportQueryParams) {
  return reportUrl("/reports/attendance-absenteeism/", format, params);
}

export interface AttendanceGridReportParams extends ReportQueryParams {
  employee?: number;
  branch?: number;
  metric?: "status" | "clock_in" | "clock_out" | "working_hours";
}

export interface AttendanceGridReport {
  period: "week" | "month" | "custom";
  start: string;
  end: string;
  dates: string[];
  legend: Record<string, string>;
  headers: string[];
  results: Array<Array<string>>;
  count: number;
}

export async function fetchAttendanceGridReport(params?: AttendanceGridReportParams) {
  const { data } = await apiClient.get<AttendanceGridReport>("/reports/attendance-grid/", { params });
  return data;
}

export function attendanceGridReportExportUrl(format: "csv" | "xlsx" | "pdf", params?: AttendanceGridReportParams) {
  return reportUrl("/reports/attendance-grid/", format, params);
}

export interface WeeklySummary {
  start: string;
  end: string;
  total_employees: number;
  present_days: number;
  absent_days: number;
  on_leave_days: number;
  late_arrivals: number;
  early_departures: number;
  leave_requests_submitted: number;
  leave_requests_approved: number;
  leave_requests_rejected: number;
  leave_requests_pending: number;
}

export interface WeeklySummaryParams {
  start?: string;
}

export async function fetchWeeklySummary(params?: WeeklySummaryParams) {
  const { data } = await apiClient.get<WeeklySummary>("/reports/weekly-summary/", { params });
  return data;
}

export function weeklySummaryExportUrl(format: "csv" | "xlsx" | "pdf", params?: WeeklySummaryParams) {
  return reportUrl("/reports/weekly-summary/", format, params);
}

export async function sendWeeklySummaryEmail(email: string, params?: WeeklySummaryParams) {
  const { data } = await apiClient.post<{ detail: string }>("/reports/weekly-summary/send/", {
    email,
    ...params,
  });
  return data;
}
