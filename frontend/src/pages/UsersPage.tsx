import { usersApi } from "../api/users";
import { ResourceListPage } from "../components/resource/ResourceListPage";
import type { ResourceConfig } from "../components/resource/types";
import { StatusBadge } from "../components/ui/Badge";
import type { User } from "../types";

const ROLE_OPTIONS = [
  { label: "Employee", value: "EMPLOYEE" },
  { label: "Department Manager", value: "DEPARTMENT_MANAGER" },
  { label: "HR Manager", value: "HR_MANAGER" },
  { label: "Super Administrator", value: "SUPER_ADMIN" },
];

const usersConfig: ResourceConfig<User> = {
  key: "users",
  title: "Users",
  api: usersApi,
  filters: [{ name: "role", label: "All Roles", options: ROLE_OPTIONS }],
  columns: [
    { key: "email", header: "Email" },
    { key: "first_name", header: "First Name" },
    { key: "last_name", header: "Last Name" },
    { key: "role", header: "Role", render: (r) => r.role.replaceAll("_", " ") },
    { key: "is_active", header: "Status", render: (r) => <StatusBadge status={r.is_active ? "ACTIVE" : "SUSPENDED"} /> },
    { key: "employee_id", header: "Linked Employee", render: (r) => (r.employee_id ? `#${r.employee_id}` : "—") },
  ],
  formFields: [
    { name: "email", label: "Email", type: "email", required: true },
    { name: "first_name", label: "First Name", type: "text" },
    { name: "last_name", label: "Last Name", type: "text" },
    { name: "phone_number", label: "Phone Number", type: "text" },
    { name: "role", label: "Role", type: "select", required: true, options: ROLE_OPTIONS },
    { name: "password", label: "Password (leave blank to auto-generate)", type: "text" },
    { name: "is_active", label: "Active", type: "checkbox" },
  ],
};

export function UsersPage() {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">
        Manage login accounts, roles, and permissions. To link a new user to an existing employee record, use
        the "Create Account" button on that employee's profile instead — this page is for standalone accounts
        and role changes.
      </p>
      <ResourceListPage config={usersConfig} />
    </div>
  );
}
