import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Users } from "lucide-react";
import {
  branchesApi,
  departmentsApi,
  positionsApi,
  workShiftsApi,
  assignEmployeesToShift,
  type Branch,
  type Department,
  type Position,
  type WorkShift,
} from "../api/organization";
import { devicesApi, type Device } from "../api/attendance";
import { fetchAllEmployeesForSelect, type EmployeeListItem } from "../api/employees";
import { extractErrorMessage } from "../api/client";
import { useAuthStore, isHRManagerOrAbove } from "../store/authStore";
import { Tabs } from "../components/ui/Tabs";
import { ResourceListPage } from "../components/resource/ResourceListPage";
import type { ResourceConfig } from "../components/resource/types";
import { DataTable } from "../components/resource/DataTable";
import { ResourceForm } from "../components/resource/ResourceForm";
import type { FormField } from "../components/resource/types";
import { Dialog } from "../components/ui/Dialog";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { StatusBadge } from "../components/ui/Badge";
import { FullPageSpinner } from "../components/ui/Spinner";

const WEEKDAYS = [
  { value: 1, label: "Mon" },
  { value: 2, label: "Tue" },
  { value: 3, label: "Wed" },
  { value: 4, label: "Thu" },
  { value: 5, label: "Fri" },
  { value: 6, label: "Sat" },
  { value: 7, label: "Sun" },
];

export function OrganizationPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">Organization</h1>
        <p className="text-sm text-slate-500">Manage branches, departments, positions, and work shifts.</p>
      </div>
      <Tabs
        tabs={[
          { key: "branches", label: "Branches", content: <BranchesTab /> },
          { key: "departments", label: "Departments", content: <DepartmentsTab /> },
          { key: "positions", label: "Positions", content: <PositionsTab /> },
          { key: "shifts", label: "Work Shifts", content: <WorkShiftsTab /> },
          { key: "devices", label: "Devices", content: <DevicesTab /> },
        ]}
      />
    </div>
  );
}

function BranchesTab() {
  const { data: employees, isLoading } = useQuery({ queryKey: ["employees-all"], queryFn: fetchAllEmployeesForSelect });
  if (isLoading) return <FullPageSpinner />;

  const config: ResourceConfig<Branch> = {
    key: "branches",
    title: "Branches",
    api: branchesApi,
    columns: [
      { key: "name", header: "Name" },
      { key: "code", header: "Code" },
      { key: "city", header: "City" },
      { key: "manager_name", header: "Manager", render: (r) => r.manager_name ?? "—" },
      { key: "is_active", header: "Active", render: (r) => (r.is_active ? "Yes" : "No") },
    ],
    formFields: [
      { name: "name", label: "Name", type: "text", required: true },
      { name: "code", label: "Code", type: "text", required: true },
      { name: "address", label: "Address", type: "text" },
      { name: "city", label: "City", type: "text" },
      { name: "county", label: "County", type: "text" },
      { name: "phone", label: "Phone", type: "text" },
      { name: "email", label: "Email", type: "email" },
      {
        name: "manager",
        label: "Branch Manager",
        type: "select",
        options: (employees ?? []).map((e) => ({ label: e.full_name, value: e.id })),
      },
      { name: "is_active", label: "Active", type: "checkbox" },
    ],
  };

  return <ResourceListPage config={config} />;
}

function DepartmentsTab() {
  const { data: branches, isLoading: branchesLoading } = useQuery({
    queryKey: ["branches-all"],
    queryFn: () => branchesApi.list({ page_size: 200 }),
  });
  const { data: employees, isLoading: employeesLoading } = useQuery({
    queryKey: ["employees-all"],
    queryFn: fetchAllEmployeesForSelect,
  });
  const { data: departments, isLoading: departmentsLoading } = useQuery({
    queryKey: ["departments-all"],
    queryFn: () => departmentsApi.list({ page_size: 200 }),
  });

  if (branchesLoading || employeesLoading || departmentsLoading) return <FullPageSpinner />;

  const config: ResourceConfig<Department> = {
    key: "departments",
    title: "Departments",
    api: departmentsApi,
    columns: [
      { key: "name", header: "Name" },
      { key: "code", header: "Code" },
      { key: "branch_name", header: "Branch" },
      { key: "head_name", header: "Head", render: (r) => r.head_name ?? "—" },
      { key: "is_active", header: "Active", render: (r) => (r.is_active ? "Yes" : "No") },
    ],
    formFields: [
      { name: "name", label: "Name", type: "text", required: true },
      { name: "code", label: "Code", type: "text", required: true },
      {
        name: "branch",
        label: "Branch",
        type: "select",
        required: true,
        options: branches?.results.map((b) => ({ label: b.name, value: b.id })) ?? [],
      },
      {
        name: "head",
        label: "Department Head",
        type: "select",
        options: (employees ?? []).map((e) => ({ label: e.full_name, value: e.id })),
      },
      {
        name: "parent_department",
        label: "Parent Department",
        type: "select",
        options: departments?.results.map((d) => ({ label: d.name, value: d.id })) ?? [],
      },
      { name: "is_active", label: "Active", type: "checkbox" },
    ],
  };

  return <ResourceListPage config={config} />;
}

function PositionsTab() {
  const { data: departments, isLoading } = useQuery({
    queryKey: ["departments-all"],
    queryFn: () => departmentsApi.list({ page_size: 200 }),
  });
  if (isLoading) return <FullPageSpinner />;

  const config: ResourceConfig<Position> = {
    key: "positions",
    title: "Positions",
    api: positionsApi,
    columns: [
      { key: "title", header: "Title" },
      { key: "code", header: "Code" },
      { key: "department_name", header: "Department", render: (r) => r.department_name ?? "—" },
      { key: "is_active", header: "Active", render: (r) => (r.is_active ? "Yes" : "No") },
    ],
    formFields: [
      { name: "title", label: "Title", type: "text", required: true },
      { name: "code", label: "Code", type: "text", required: true },
      {
        name: "department",
        label: "Department",
        type: "select",
        options: departments?.results.map((d) => ({ label: d.name, value: d.id })) ?? [],
      },
      { name: "description", label: "Description", type: "textarea" },
      { name: "is_active", label: "Active", type: "checkbox" },
    ],
  };

  return <ResourceListPage config={config} />;
}

/** Bespoke (not the generic ResourceListPage) because working_days is a JSON
 * array on the backend, rendered as day-of-week checkboxes in the form, and
 * because it needs a bulk "assign employees" action per row. */
function WorkShiftsTab() {
  const queryClient = useQueryClient();
  const [dialogState, setDialogState] = useState<{ mode: "create" | "edit"; row?: WorkShift } | null>(null);
  const [assignTarget, setAssignTarget] = useState<WorkShift | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({ queryKey: ["work-shifts"], queryFn: () => workShiftsApi.list({ page_size: 100 }) });
  const { data: employees } = useQuery({ queryKey: ["employees-all"], queryFn: fetchAllEmployeesForSelect });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["work-shifts"] });

  const createMutation = useMutation({
    mutationFn: (values: Record<string, unknown>) => workShiftsApi.create(transformPayload(values)),
    onSuccess: () => {
      invalidate();
      setDialogState(null);
      setFormError(null);
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: Record<string, unknown> }) =>
      workShiftsApi.update(id, transformPayload(values)),
    onSuccess: () => {
      invalidate();
      setDialogState(null);
      setFormError(null);
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  const formFields: FormField[] = [
    { name: "name", label: "Name", type: "text", required: true },
    { name: "start_time", label: "Start Time", type: "time" },
    { name: "end_time", label: "End Time", type: "time" },
    { name: "break_duration_minutes", label: "Break Duration (minutes)", type: "number" },
    { name: "grace_period_minutes", label: "Grace Period (minutes)", type: "number" },
    {
      name: "working_days",
      label: "Working Days",
      type: "checkbox-group",
      options: WEEKDAYS.map((w) => ({ label: w.label, value: w.value })),
    },
    {
      name: "is_flexible",
      label: "Flexible hours — never mark late or early departure (e.g. 00:00–23:59 open shifts)",
      type: "checkbox",
    },
    { name: "is_active", label: "Active", type: "checkbox" },
  ];

  const defaultValues = dialogState?.row
    ? { ...dialogState.row, working_days: dialogState.row.working_days.map(String) }
    : undefined;

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button size="sm" onClick={() => setDialogState({ mode: "create" })}>
          <Plus className="h-3.5 w-3.5" /> New Work Shift
        </Button>
      </div>

      <DataTable
        columns={[
          { key: "name", header: "Name" },
          { key: "start_time", header: "Start" },
          { key: "end_time", header: "End" },
          {
            key: "working_days",
            header: "Working Days",
            render: (r) => r.working_days.map((d) => WEEKDAYS.find((w) => w.value === d)?.label ?? d).join(", "),
          },
          { key: "is_flexible", header: "Flexible", render: (r) => (r.is_flexible ? <StatusBadge status="ACTIVE" /> : "—") },
          { key: "is_active", header: "Active", render: (r) => <StatusBadge status={r.is_active ? "ACTIVE" : "SUSPENDED"} /> },
          {
            key: "assign",
            header: "",
            render: (r) => (
              <Button size="sm" variant="outline" onClick={() => setAssignTarget(r)}>
                <Users className="h-3.5 w-3.5" /> Assign Employees
              </Button>
            ),
          },
        ]}
        data={data?.results ?? []}
        isLoading={isLoading}
        canEdit
        canDelete
        onEdit={(row) => setDialogState({ mode: "edit", row })}
        onDelete={(row) => confirm("Delete this work shift?") && workShiftsApi.remove(row.id).then(invalidate)}
      />

      <Dialog
        open={!!dialogState}
        onClose={() => {
          setDialogState(null);
          setFormError(null);
        }}
        title={dialogState?.mode === "edit" ? "Edit Work Shift" : "New Work Shift"}
      >
        {dialogState && (
          <ResourceForm
            fields={formFields}
            defaultValues={defaultValues}
            submitting={createMutation.isPending || updateMutation.isPending}
            errorMessage={formError}
            onCancel={() => setDialogState(null)}
            onSubmit={(values) => {
              if (dialogState.mode === "edit" && dialogState.row) {
                updateMutation.mutate({ id: dialogState.row.id, values });
              } else {
                createMutation.mutate(values);
              }
            }}
          />
        )}
      </Dialog>

      {assignTarget && (
        <AssignShiftDialog shift={assignTarget} employees={employees ?? []} onClose={() => setAssignTarget(null)} />
      )}
    </div>
  );
}

function transformPayload(values: Record<string, unknown>): Partial<WorkShift> {
  const workingDaysRaw = values.working_days;
  const working_days = Array.isArray(workingDaysRaw) ? workingDaysRaw.map((v) => Number(v)) : [];
  return { ...values, working_days } as Partial<WorkShift>;
}

function AssignShiftDialog({
  shift,
  employees,
  onClose,
}: {
  shift: WorkShift;
  employees: EmployeeListItem[];
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const filtered = useMemo(
    () => employees.filter((e) => e.full_name.toLowerCase().includes(search.toLowerCase())),
    [employees, search]
  );

  const assignMutation = useMutation({
    mutationFn: () => assignEmployeesToShift(shift.id, [...selected]),
    onSuccess: (data) => {
      setMessage(data.detail);
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["employees-all"] });
      queryClient.invalidateQueries({ queryKey: ["employees"] });
    },
    onError: (err) => setError(extractErrorMessage(err)),
  });

  const toggle = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAllFiltered = () => {
    setSelected((prev) => {
      const next = new Set(prev);
      filtered.forEach((e) => next.add(e.id));
      return next;
    });
  };

  return (
    <Dialog open onClose={onClose} title={`Assign Employees — ${shift.name}`}>
      <div className="space-y-3">
        {message && <div className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div>}
        {error && <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}

        <div className="flex items-center justify-between gap-2">
          <Input placeholder="Search employees..." value={search} onChange={(e) => setSearch(e.target.value)} />
          <Button size="sm" variant="outline" onClick={selectAllFiltered}>
            Select all
          </Button>
        </div>

        <div className="max-h-72 overflow-y-auto rounded-md border border-slate-200">
          <ul className="divide-y divide-slate-100">
            {filtered.map((e) => (
              <li key={e.id} className="flex items-center gap-2 px-3 py-2 text-sm">
                <input
                  type="checkbox"
                  checked={selected.has(e.id)}
                  onChange={() => toggle(e.id)}
                  className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                />
                <span className="text-slate-700">{e.full_name}</span>
                <span className="ml-auto text-xs text-slate-400">{e.department_name ?? "—"}</span>
              </li>
            ))}
            {!filtered.length && <li className="px-3 py-6 text-center text-sm text-slate-400">No employees found.</li>}
          </ul>
        </div>

        <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          <Button onClick={() => assignMutation.mutate()} loading={assignMutation.isPending} disabled={!selected.size}>
            Assign {selected.size > 0 ? `(${selected.size})` : ""}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}

function DevicesTab() {
  const user = useAuthStore((s) => s.user);
  const canManage = isHRManagerOrAbove(user);
  const { data: branches, isLoading } = useQuery({
    queryKey: ["branches-all"],
    queryFn: () => branchesApi.list({ page_size: 200 }),
  });
  if (isLoading) return <FullPageSpinner />;

  const config: ResourceConfig<Device> = {
    key: "devices",
    title: "Devices",
    api: devicesApi,
    canCreate: canManage,
    canEdit: canManage,
    canDelete: canManage,
    columns: [
      { key: "name", header: "Name" },
      { key: "device_type", header: "Type" },
      { key: "branch_name", header: "Branch", render: (r) => r.branch_name ?? "—" },
      { key: "ip_address", header: "IP Address", render: (r) => r.ip_address ?? "—" },
      { key: "port", header: "Port" },
      { key: "is_active", header: "Active", render: (r) => <StatusBadge status={r.is_active ? "ACTIVE" : "SUSPENDED"} /> },
      {
        key: "last_synced_at",
        header: "Last Synced",
        render: (r) => (r.last_synced_at ? new Date(r.last_synced_at).toLocaleString() : "Never"),
      },
    ],
    formFields: [
      { name: "name", label: "Name", type: "text", required: true },
      {
        name: "branch",
        label: "Branch",
        type: "select",
        options: branches?.results.map((b) => ({ label: b.name, value: b.id })) ?? [],
      },
      { name: "ip_address", label: "IP Address", type: "text", placeholder: "192.168.5.200" },
      { name: "port", label: "Port", type: "number" },
      { name: "notes", label: "Notes", type: "textarea" },
      { name: "is_active", label: "Active", type: "checkbox" },
    ],
  };

  return <ResourceListPage config={config} />;
}
