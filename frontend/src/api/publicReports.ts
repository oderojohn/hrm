import axios from "axios";
import { API_BASE_URL } from "./client";

// Deliberately its own axios instance (no interceptors) — the public reports
// link carries its own token instead of a user session, and must never pick
// up a stale Authorization header or get redirected to /login on an error.
const publicClient = axios.create({ baseURL: API_BASE_URL });

export interface PublicReportsMonth {
  value: string; // "2026-09"
  label: string; // "September 2026"
}

export interface PublicReportsIndex {
  company: string;
  months: PublicReportsMonth[];
}

export interface PublicAttendanceDay {
  check_in: string;
  check_out: string;
}

export interface PublicAttendanceEmployee {
  employee_number: string;
  name: string;
  department: string;
  days: PublicAttendanceDay[];
}

export interface PublicAttendanceRegister {
  month: string;
  dates: string[];
  employees: PublicAttendanceEmployee[];
}

export async function fetchPublicReportsIndex(token: string): Promise<PublicReportsIndex> {
  const { data } = await publicClient.get<PublicReportsIndex>(`/reports/public/${token}/`);
  return data;
}

export async function fetchPublicAttendanceRegister(token: string, month: string): Promise<PublicAttendanceRegister> {
  const { data } = await publicClient.get<PublicAttendanceRegister>(`/reports/public/${token}/attendance-register/`, {
    params: { month },
  });
  return data;
}

export function publicAttendanceRegisterExportUrl(token: string, month: string) {
  const query = new URLSearchParams({ month, format: "xlsx" });
  return `${API_BASE_URL}/reports/public/${token}/attendance-register/?${query.toString()}`;
}
