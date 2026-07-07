import { useQuery } from "@tanstack/react-query";
import { leaveTypesApi, leavePoliciesApi, leaveBalancesApi } from "../api/leave";
import { fetchAllEmployeesForSelect } from "../api/employees";
import { Tabs } from "../components/ui/Tabs";
import { ResourceListPage } from "../components/resource/ResourceListPage";
import type { ResourceConfig } from "../components/resource/types";
import { FullPageSpinner } from "../components/ui/Spinner";
import type { LeaveType, LeavePolicy, LeaveBalance } from "../api/leave";

const leaveTypeConfig: ResourceConfig<LeaveType> = {
  key: "leave-types",
  title: "Leave Types",
  api: leaveTypesApi,
  columns: [
    { key: "name", header: "Name" },
    { key: "code", header: "Code" },
    { key: "is_paid", header: "Paid", render: (r) => (r.is_paid ? "Yes" : "No") },
    { key: "allow_half_day", header: "Half Day", render: (r) => (r.allow_half_day ? "Yes" : "No") },
    { key: "requires_attachment", header: "Attachment Required", render: (r) => (r.requires_attachment ? "Yes" : "No") },
    { key: "is_active", header: "Active", render: (r) => (r.is_active ? "Yes" : "No") },
  ],
  formFields: [
    { name: "name", label: "Name", type: "text", required: true },
    { name: "code", label: "Code", type: "text", required: true },
    { name: "description", label: "Description", type: "textarea" },
    { name: "is_paid", label: "Paid Leave", type: "checkbox" },
    { name: "allow_half_day", label: "Allow Half Day", type: "checkbox" },
    { name: "requires_attachment", label: "Requires Attachment", type: "checkbox" },
    { name: "is_active", label: "Active", type: "checkbox" },
  ],
};

function LeaveTypesTab() {
  return <ResourceListPage config={leaveTypeConfig} />;
}

function PoliciesTab() {
  const { data: leaveTypes, isLoading } = useQuery({
    queryKey: ["leave-types-all"],
    queryFn: () => leaveTypesApi.list({ page_size: 100 }),
  });

  if (isLoading) return <FullPageSpinner />;

  const config: ResourceConfig<LeavePolicy> = {
    key: "leave-policies",
    title: "Leave Policies",
    api: leavePoliciesApi,
    columns: [
      { key: "leave_type_name", header: "Leave Type" },
      { key: "default_days_per_year", header: "Days / Year" },
      { key: "accrual_rate_per_month", header: "Accrual / Month" },
      { key: "max_carry_forward_days", header: "Max Carry Forward" },
      { key: "min_service_months", header: "Min Service (months)" },
      { key: "requires_approval", header: "Needs Approval", render: (r) => (r.requires_approval ? "Yes" : "No") },
      { key: "allow_negative_balance", header: "Allow Overdraft", render: (r) => (r.allow_negative_balance ? "Yes" : "No") },
    ],
    formFields: [
      {
        name: "leave_type",
        label: "Leave Type",
        type: "select",
        required: true,
        options: leaveTypes?.results.map((lt) => ({ label: lt.name, value: lt.id })) ?? [],
      },
      { name: "default_days_per_year", label: "Default Days / Year", type: "number", step: "0.5" },
      { name: "accrual_rate_per_month", label: "Accrual Rate / Month", type: "number", step: "0.01" },
      { name: "max_carry_forward_days", label: "Max Carry Forward Days", type: "number", step: "0.5" },
      { name: "max_consecutive_days", label: "Max Consecutive Days", type: "number" },
      { name: "min_service_months", label: "Min Service (months)", type: "number" },
      { name: "requires_approval", label: "Requires Approval", type: "checkbox" },
      { name: "allow_negative_balance", label: "Allow Balance Overdraft", type: "checkbox" },
    ],
  };

  return <ResourceListPage config={config} />;
}

function BalancesTab() {
  const { data: employees, isLoading: employeesLoading } = useQuery({
    queryKey: ["employees-all"],
    queryFn: fetchAllEmployeesForSelect,
  });
  const { data: leaveTypes, isLoading: typesLoading } = useQuery({
    queryKey: ["leave-types-all"],
    queryFn: () => leaveTypesApi.list({ page_size: 100 }),
  });

  if (employeesLoading || typesLoading) return <FullPageSpinner />;

  const config: ResourceConfig<LeaveBalance> = {
    key: "leave-balances",
    title: "Employee Leave Balances",
    api: leaveBalancesApi,
    columns: [
      { key: "employee_name", header: "Employee" },
      { key: "leave_type_name", header: "Leave Type" },
      { key: "year", header: "Year" },
      { key: "allocated_days", header: "Allocated" },
      { key: "carried_forward_days", header: "Carried Forward" },
      { key: "used_days", header: "Used" },
      { key: "remaining_days", header: "Remaining" },
    ],
    filters: [{ name: "employee", label: "All Employees", options: (employees ?? []).map((e) => ({ label: e.full_name, value: e.id })) }],
    formFields: [
      {
        name: "employee",
        label: "Employee",
        type: "select",
        required: true,
        options: (employees ?? []).map((e) => ({ label: e.full_name, value: e.id })),
      },
      {
        name: "leave_type",
        label: "Leave Type",
        type: "select",
        required: true,
        options: leaveTypes?.results.map((lt) => ({ label: lt.name, value: lt.id })) ?? [],
      },
      { name: "year", label: "Year", type: "number", required: true },
      { name: "allocated_days", label: "Allocated Days", type: "number", step: "0.5", required: true },
      { name: "carried_forward_days", label: "Carried Forward Days", type: "number", step: "0.5" },
      { name: "used_days", label: "Used Days", type: "number", step: "0.5" },
    ],
  };

  return <ResourceListPage config={config} />;
}

export function LeaveSetupPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">Leave Setup</h1>
        <p className="text-sm text-slate-500">Create leave types, configure their policies, and assign balances to employees.</p>
      </div>
      <Tabs
        tabs={[
          { key: "types", label: "Leave Types", content: <LeaveTypesTab /> },
          { key: "policies", label: "Policies", content: <PoliciesTab /> },
          { key: "balances", label: "Assign Balances", content: <BalancesTab /> },
        ]}
      />
    </div>
  );
}
