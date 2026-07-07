import { apiClient, API_BASE_URL } from "./client";
import { createResourceApi, type ListParams } from "./resource";

export interface AttendanceRecord {
  id: number;
  employee: number;
  employee_name: string;
  device: number | null;
  device_name: string | null;
  date: string;
  clock_in: string | null;
  clock_out: string | null;
  method: string;
  is_late: boolean;
  is_early_departure: boolean;
  overtime_minutes: number;
  notes: string;
}

export interface Device {
  id: number;
  name: string;
  device_type: string;
  branch: number | null;
  branch_name: string | null;
  ip_address: string | null;
  port: number;
  is_active: boolean;
  last_synced_at: string | null;
  notes: string;
}

export interface PunchLog {
  id: number;
  employee: number;
  employee_name: string;
  device: number | null;
  device_name: string | null;
  timestamp: string;
  event: "IN" | "OUT" | "UNKNOWN";
  method: string;
  raw_status: number | null;
}

export interface AttendanceCorrectionRequest {
  id: number;
  employee: number;
  employee_name: string;
  attendance: number | null;
  date: string;
  requested_clock_in: string | null;
  requested_clock_out: string | null;
  reason: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
  reviewed_by_name: string | null;
  review_comment: string;
}

export interface AttendanceAnalyticsEntry {
  employee_id: number;
  employee_name: string;
  working_days: number;
  expected_working_days: number;
  absent_days: number;
  attendance_rate: number | null;
  total_hours: number;
  average_hours_per_day: number;
  late_count: number;
  early_departure_count: number;
  overtime_hours: number;
  daily: Array<{ date: string; hours: number | null; is_late: boolean }>;
}

export interface AttendanceAnalyticsResponse {
  period: "week" | "month" | "custom";
  start: string;
  end: string;
  results: AttendanceAnalyticsEntry[];
}

export interface EmployeeAttendancePunch {
  timestamp: string;
  event: "IN" | "OUT" | "UNKNOWN";
  device_name: string | null;
}

export interface EmployeeAttendanceDay {
  date: string;
  clock_in: string | null;
  clock_out: string | null;
  is_late: boolean;
  is_early_departure: boolean;
  overtime_minutes: number;
  punch_count: number;
  punches: EmployeeAttendancePunch[];
}

export interface EmployeeAttendanceDetailResponse {
  employee: {
    id: number;
    employee_number: string;
    full_name: string;
    photo: string | null;
    department_name: string | null;
    branch_name: string | null;
    work_shift_name: string | null;
  };
  start: string;
  end: string;
  summary: {
    working_days: number;
    expected_working_days: number;
    attendance_rate: number | null;
    total_hours: number;
    average_hours_per_day: number;
    late_count: number;
    early_departure_count: number;
    overtime_hours: number;
    total_punches: number;
  };
  days: EmployeeAttendanceDay[];
}

export interface ZKTecoSyncResult {
  device_id: number;
  device_name: string;
  employees: { created: number; updated: number; skipped: number; total_on_device: number } | null;
  attendance: {
    days_synced: number;
    records_created: number;
    records_updated: number;
    unmatched_device_user_ids: string[];
    total_logs_on_device: number;
  } | null;
  error: string | null;
}

export const attendanceRecordsApi = createResourceApi<AttendanceRecord>("/attendance/records");
export const attendanceCorrectionsApi = createResourceApi<AttendanceCorrectionRequest>("/attendance/corrections");
export const devicesApi = createResourceApi<Device>("/attendance/devices");
export const punchLogsApi = createResourceApi<PunchLog>("/attendance/punch-logs");

export async function fetchAttendanceAnalytics(params: {
  period?: "week" | "month";
  date?: string;
  employee?: number;
  branch?: number;
  department?: number;
  start?: string;
  end?: string;
}) {
  const { data } = await apiClient.get<AttendanceAnalyticsResponse>("/reports/attendance-analytics/", { params });
  return data;
}

export async function fetchEmployeeAttendanceDetail(
  employeeId: number,
  params: { period?: "week" | "month"; start?: string; end?: string }
) {
  const { data } = await apiClient.get<EmployeeAttendanceDetailResponse>(
    `/reports/attendance/employee/${employeeId}/`,
    { params }
  );
  return data;
}

export function employeeAttendanceDetailExportUrl(
  employeeId: number,
  format: "csv" | "xlsx" | "pdf",
  params?: ListParams
) {
  const query = new URLSearchParams({ format, ...toStringRecord(params) });
  return `${API_BASE_URL}/reports/attendance/employee/${employeeId}/?${query.toString()}`;
}

export function attendanceAnalyticsExportUrl(format: "csv" | "xlsx" | "pdf", params?: ListParams) {
  const query = new URLSearchParams({ format, ...toStringRecord(params) });
  return `${API_BASE_URL}/reports/attendance-analytics/?${query.toString()}`;
}

function toStringRecord(params?: ListParams): Record<string, string> {
  if (!params) return {};
  const entries = Object.entries(params).filter(([, v]) => v !== undefined) as [string, string | number | boolean][];
  return Object.fromEntries(entries.map(([k, v]) => [k, String(v)]));
}

export async function syncZKTeco() {
  const { data } = await apiClient.post<{ devices_synced: number; results: ZKTecoSyncResult[] }>(
    "/attendance/zkteco/sync/"
  );
  return data;
}

export async function approveAttendanceCorrection(id: number, comment?: string) {
  const { data } = await apiClient.post<AttendanceCorrectionRequest>(
    `/attendance/corrections/${id}/approve/`,
    { comment }
  );
  return data;
}

export async function rejectAttendanceCorrection(id: number, comment?: string) {
  const { data } = await apiClient.post<AttendanceCorrectionRequest>(
    `/attendance/corrections/${id}/reject/`,
    { comment }
  );
  return data;
}
