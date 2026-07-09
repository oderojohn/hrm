import { apiClient } from "./client";
import { createResourceApi } from "./resource";

export interface Branch {
  id: number;
  name: string;
  code: string;
  city: string;
  county: string;
  phone: string;
  email: string;
  manager: number | null;
  manager_name: string | null;
  is_active: boolean;
}

export interface Department {
  id: number;
  name: string;
  code: string;
  branch: number;
  branch_name: string;
  head: number | null;
  head_name: string | null;
  parent_department: number | null;
  is_active: boolean;
}

export interface Position {
  id: number;
  title: string;
  code: string;
  department: number | null;
  department_name: string | null;
  description: string;
  is_active: boolean;
}

export interface WorkShift {
  id: number;
  name: string;
  start_time: string;
  end_time: string;
  break_duration_minutes: number;
  grace_period_minutes: number;
  working_days: number[];
  is_flexible: boolean;
  is_active: boolean;
}

export const branchesApi = createResourceApi<Branch>("/organization/branches");
export const departmentsApi = createResourceApi<Department>("/organization/departments");
export const positionsApi = createResourceApi<Position>("/organization/positions");
export const workShiftsApi = createResourceApi<WorkShift>("/organization/work-shifts");

export async function assignEmployeesToShift(shiftId: number, employeeIds: number[]) {
  const { data } = await apiClient.post<{ detail: string; updated_count: number }>(
    `/organization/work-shifts/${shiftId}/assign-employees/`,
    { employee_ids: employeeIds }
  );
  return data;
}
