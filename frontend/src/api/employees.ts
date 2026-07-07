import { createResourceApi } from "./resource";
import { apiClient } from "./client";

export interface EmployeeListItem {
  id: number;
  employee_number: string;
  photo: string | null;
  full_name: string;
  first_name: string;
  last_name: string;
  email: string;
  phone_number: string;
  department_name: string | null;
  position_title: string | null;
  branch_name: string | null;
  employment_type: string;
  employment_status: string;
  employment_date: string;
  reporting_manager: number | null;
}

export interface Employee extends EmployeeListItem {
  middle_name: string;
  gender: string;
  date_of_birth: string | null;
  national_id: string | null;
  passport_number: string;
  kra_pin: string;
  nssf_number: string;
  shif_number: string;
  alternative_phone: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  emergency_contact_relationship: string;
  nationality: string;
  marital_status: string;
  address: string;
  county: string;
  sub_county: string;
  postal_address: string;
  department: number | null;
  position: number | null;
  branch: number | null;
  reporting_manager: number | null;
  reporting_manager_name: string | null;
  probation_end_date: string | null;
  contract_end_date: string | null;
  work_shift: number | null;
  device_user_id: string | null;
  user: number | null;
  education: Array<Record<string, unknown>>;
  certifications: Array<Record<string, unknown>>;
  employment_history: Array<Record<string, unknown>>;
}

export interface EmployeeProfile extends Employee {
  leave_history: Array<Record<string, unknown>>;
  attendance_history: Array<Record<string, unknown>>;
  performance_reviews: Array<Record<string, unknown>>;
  disciplinary_records: Array<Record<string, unknown>>;
  training_records: Array<Record<string, unknown>>;
  assigned_assets: Array<Record<string, unknown>>;
}

export const employeesApi = createResourceApi<EmployeeListItem>("/employees/employees");

export async function fetchEmployeeProfile(id: number): Promise<EmployeeProfile> {
  const { data } = await apiClient.get<EmployeeProfile>(`/employees/employees/${id}/profile/`);
  return data;
}

export async function fetchAllEmployeesForSelect(): Promise<EmployeeListItem[]> {
  const { data } = await apiClient.get("/employees/employees/", { params: { page_size: 500 } });
  return data.results;
}

export interface MyEmployeeProfile {
  id: number;
  employee_number: string;
  full_name: string;
  photo: string | null;
  email: string;
  phone_number: string;
  alternative_phone: string;
  address: string;
  county: string;
  sub_county: string;
  postal_address: string;
  marital_status: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  emergency_contact_relationship: string;
  department_name: string | null;
  position_title: string | null;
  branch_name: string | null;
  employment_status: string;
}

export async function fetchMyEmployeeProfile(): Promise<MyEmployeeProfile> {
  const { data } = await apiClient.get<MyEmployeeProfile>("/employees/employees/me/");
  return data;
}

export async function updateMyEmployeeProfile(payload: Partial<MyEmployeeProfile>): Promise<MyEmployeeProfile> {
  const { data } = await apiClient.patch<MyEmployeeProfile>("/employees/employees/me/", payload);
  return data;
}

export async function pushEmployeeToDevice(id: number): Promise<{ detail: string; device_user_id: string }> {
  const { data } = await apiClient.post(`/employees/employees/${id}/push-to-device/`);
  return data;
}

export interface AccountCredentials {
  detail: string;
  email: string;
  password: string;
  user_id?: number;
}

export async function createEmployeeAccount(
  id: number,
  payload: { email?: string; password?: string; role?: string }
): Promise<AccountCredentials> {
  const { data } = await apiClient.post(`/employees/employees/${id}/create-account/`, payload);
  return data;
}

export async function resetEmployeePassword(id: number, password?: string): Promise<AccountCredentials> {
  const { data } = await apiClient.post(`/employees/employees/${id}/reset-password/`, { password });
  return data;
}
