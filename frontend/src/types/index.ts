export type Role = "SUPER_ADMIN" | "HR_MANAGER" | "DEPARTMENT_MANAGER" | "EMPLOYEE";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  phone_number: string;
  is_active: boolean;
  is_2fa_enabled: boolean;
  must_change_password: boolean;
  date_joined: string;
  employee_id: number | null;
}

export interface PaginatedResponse<T> {
  count: number;
  num_pages: number;
  current_page: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiErrorShape {
  success: false;
  errors: Record<string, unknown> | string;
  status_code: number;
}
