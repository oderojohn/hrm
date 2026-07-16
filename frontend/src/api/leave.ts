import { apiClient } from "./client";
import { createResourceApi } from "./resource";
import type { PaginatedResponse } from "../types";

export interface LeaveType {
  id: number;
  name: string;
  code: string;
  description: string;
  is_paid: boolean;
  requires_attachment: boolean;
  allow_half_day: boolean;
  is_active: boolean;
}

export interface LeavePolicy {
  id: number;
  leave_type: number;
  leave_type_name: string;
  default_days_per_year: string;
  accrual_rate_per_month: string;
  max_carry_forward_days: string;
  max_consecutive_days: number | null;
  min_service_months: number;
  requires_approval: boolean;
  allow_negative_balance: boolean;
}

export interface LeaveBalance {
  id: number;
  employee: number;
  employee_name: string;
  leave_type: number;
  leave_type_name: string;
  year: number;
  allocated_days: string;
  carried_forward_days: string;
  used_days: string;
  remaining_days: string;
}

export type ResolverType =
  | "REPORTING_MANAGER"
  | "SKIP_LEVEL_MANAGER"
  | "DEPARTMENT_HEAD"
  | "BRANCH_MANAGER"
  | "SPECIFIC_EMPLOYEE"
  | "SYSTEM_ROLE";

export interface LeaveApprovalStep {
  id: number;
  step_order: number;
  name: string;
  resolver_type: ResolverType | "";
  system_role: string;
  approver: number | null;
  approver_name: string | null;
  status: "PENDING" | "APPROVED" | "REJECTED" | "SKIPPED";
  comment: string;
  acted_by_name: string | null;
  acted_at: string | null;
  entered_at: string | null;
  reminder_sent_at: string | null;
  escalated_at: string | null;
}

export interface LeaveRequest {
  id: number;
  employee: number;
  employee_name: string;
  leave_type: number;
  leave_type_name: string;
  start_date: string;
  end_date: string;
  is_half_day: boolean;
  half_day_period: string;
  total_days: string;
  reason: string;
  attachment: string | null;
  status: "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED" | "COMPLETED" | "RETURNED";
  cancelled_reason: string;
  approval_steps: LeaveApprovalStep[];
  created_at: string;
}

export interface WorkflowStep {
  id: number;
  template: number;
  step_order: number;
  name: string;
  resolver_type: ResolverType;
  specific_employee: number | null;
  specific_employee_name: string | null;
  system_role: string;
  skip_levels: number;
  min_days: string | null;
  max_days: string | null;
  reminder_after_hours: number | null;
  escalation_after_hours: number | null;
  escalate_to_employee: number | null;
  escalate_to_employee_name: string | null;
  is_active: boolean;
}

export interface WorkflowTemplate {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  is_default: boolean;
  priority: number;
  require_all_parallel_approvers: boolean;
  departments: number[];
  branches: number[];
  leave_types: number[];
  employment_types: string[];
  steps: WorkflowStep[];
}

export const leaveTypesApi = createResourceApi<LeaveType>("/leave/types");
export const leavePoliciesApi = createResourceApi<LeavePolicy>("/leave/policies");
export const leaveBalancesApi = createResourceApi<LeaveBalance>("/leave/balances");
export const leaveRequestsApi = createResourceApi<LeaveRequest>("/leave/requests");
export const workflowTemplatesApi = createResourceApi<WorkflowTemplate>("/leave/workflow-templates");

export async function fetchLeaveBalances(employeeId?: number): Promise<PaginatedResponse<LeaveBalance>> {
  const { data } = await apiClient.get<PaginatedResponse<LeaveBalance>>("/leave/balances/", {
    params: employeeId ? { employee: employeeId } : undefined,
  });
  return data;
}

export async function approveLeaveRequest(id: number, comment?: string, stepId?: number) {
  const { data } = await apiClient.post<LeaveRequest>(`/leave/requests/${id}/approve/`, {
    comment,
    step_id: stepId,
  });
  return data;
}

export async function rejectLeaveRequest(id: number, comment?: string, stepId?: number) {
  const { data } = await apiClient.post<LeaveRequest>(`/leave/requests/${id}/reject/`, {
    comment,
    step_id: stepId,
  });
  return data;
}

export async function cancelLeaveRequest(id: number, reason?: string) {
  const { data } = await apiClient.post<LeaveRequest>(`/leave/requests/${id}/cancel/`, { reason });
  return data;
}

export async function reassignLeaveStep(id: number, approverId: number, comment?: string, stepId?: number) {
  const { data } = await apiClient.post<LeaveRequest>(`/leave/requests/${id}/reassign/`, {
    approver: approverId,
    comment,
    step_id: stepId,
  });
  return data;
}

export async function returnForCorrection(id: number, comment?: string, stepId?: number) {
  const { data } = await apiClient.post<LeaveRequest>(`/leave/requests/${id}/return_for_correction/`, {
    comment,
    step_id: stepId,
  });
  return data;
}

export async function resubmitLeaveRequest(id: number, payload: Partial<LeaveRequest>) {
  const { data } = await apiClient.post<LeaveRequest>(`/leave/requests/${id}/resubmit/`, payload);
  return data;
}

export async function fetchLeaveCalendar(scope: "personal" | "team") {
  const { data } = await apiClient.get<LeaveRequest[]>("/leave/requests/calendar/", { params: { scope } });
  return data;
}

export interface LeaveRequestPreview {
  total_days: number;
  reporting_date: string;
}

export async function previewLeaveRequest(params: { start_date: string; end_date: string; is_half_day?: boolean }) {
  const { data } = await apiClient.get<LeaveRequestPreview>("/leave/requests/preview/", { params });
  return data;
}
