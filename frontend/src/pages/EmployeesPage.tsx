import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, Plus, Search } from "lucide-react";
import { employeesApi, fetchAllEmployeesForSelect, type EmployeeListItem } from "../api/employees";
import { branchesApi, departmentsApi, positionsApi } from "../api/organization";
import { downloadExport } from "../api/resource";
import { extractErrorMessage } from "../api/client";
import { DataTable, type SortState } from "../components/resource/DataTable";
import { ResourceForm } from "../components/resource/ResourceForm";
import type { FormField } from "../components/resource/types";
import { Dialog } from "../components/ui/Dialog";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { StatusBadge } from "../components/ui/Badge";
import { useAuthStore, isHRManagerOrAbove } from "../store/authStore";
import { formatDate } from "../lib/utils";

const EMPLOYMENT_TYPE_OPTIONS = [
  { label: "Full-Time", value: "FULL_TIME" },
  { label: "Part-Time", value: "PART_TIME" },
  { label: "Contract", value: "CONTRACT" },
  { label: "Internship", value: "INTERNSHIP" },
  { label: "Casual", value: "CASUAL" },
];

const GENDER_OPTIONS = [
  { label: "Male", value: "MALE" },
  { label: "Female", value: "FEMALE" },
  { label: "Other", value: "OTHER" },
];

export function EmployeesPage() {
  const user = useAuthStore((s) => s.user);
  const canManage = isHRManagerOrAbove(user);
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<SortState | null>(null);
  const [dialogState, setDialogState] = useState<{ mode: "create" | "edit"; row?: EmployeeListItem } | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const ordering = sort ? (sort.direction === "desc" ? `-${sort.key}` : sort.key) : undefined;

  const handleSortChange = (key: string) => {
    setSort((prev) => {
      if (!prev || prev.key !== key) return { key, direction: "asc" };
      if (prev.direction === "asc") return { key, direction: "desc" };
      return null;
    });
  };

  const { data, isLoading } = useQuery({
    queryKey: ["employees", page, search, ordering],
    queryFn: () => employeesApi.list({ page, search: search || undefined, ordering }),
  });

  const { data: departments } = useQuery({ queryKey: ["departments-all"], queryFn: () => departmentsApi.list({ page_size: 200 }) });
  const { data: branches } = useQuery({ queryKey: ["branches-all"], queryFn: () => branchesApi.list({ page_size: 200 }) });
  const { data: positions } = useQuery({ queryKey: ["positions-all"], queryFn: () => positionsApi.list({ page_size: 200 }) });
  const { data: allEmployees } = useQuery({ queryKey: ["employees-all"], queryFn: fetchAllEmployeesForSelect });

  const formFields: FormField[] = [
    { name: "first_name", label: "First Name", type: "text", required: true },
    { name: "middle_name", label: "Middle Name", type: "text" },
    { name: "last_name", label: "Last Name", type: "text", required: true },
    { name: "gender", label: "Gender", type: "select", options: GENDER_OPTIONS },
    { name: "date_of_birth", label: "Date of Birth", type: "date" },
    { name: "national_id", label: "National ID", type: "text" },
    { name: "email", label: "Email", type: "email" },
    { name: "phone_number", label: "Phone Number", type: "text" },
    { name: "employment_date", label: "Employment Date", type: "date", required: true },
    { name: "employment_type", label: "Employment Type", type: "select", options: EMPLOYMENT_TYPE_OPTIONS, required: true },
    {
      name: "department",
      label: "Department",
      type: "select",
      options: departments?.results.map((d) => ({ label: d.name, value: d.id })) ?? [],
    },
    {
      name: "position",
      label: "Position",
      type: "select",
      options: positions?.results.map((p) => ({ label: p.title, value: p.id })) ?? [],
    },
    {
      name: "branch",
      label: "Branch",
      type: "select",
      options: branches?.results.map((b) => ({ label: b.name, value: b.id })) ?? [],
    },
    {
      name: "reporting_manager",
      label: "Reporting Manager (Supervisor)",
      type: "select",
      options: (allEmployees ?? [])
        .filter((e) => e.id !== dialogState?.row?.id)
        .map((e) => ({ label: e.full_name, value: e.id })),
    },
    { name: "kra_pin", label: "KRA PIN", type: "text" },
    { name: "nssf_number", label: "NSSF Number", type: "text" },
    { name: "shif_number", label: "SHIF/NHIF Number", type: "text" },
    { name: "emergency_contact_name", label: "Emergency Contact Name", type: "text" },
    { name: "emergency_contact_phone", label: "Emergency Contact Phone", type: "text" },
    {
      name: "device_user_id",
      label: "Biometric Device ID",
      type: "text",
      placeholder: "Auto-assigned if left blank",
    },
  ];

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["employees"] });

  const createMutation = useMutation({
    mutationFn: (values: Partial<EmployeeListItem>) => employeesApi.create(values),
    onSuccess: () => {
      invalidate();
      setDialogState(null);
      setFormError(null);
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: Partial<EmployeeListItem> }) => employeesApi.update(id, values),
    onSuccess: () => {
      invalidate();
      setDialogState(null);
      setFormError(null);
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        <h1 className="text-lg font-semibold text-slate-900">Employees</h1>
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex-1 sm:flex-none">
            <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search employees..."
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
              className="w-full pl-8 sm:w-56"
            />
          </div>
          <Button variant="outline" size="sm" onClick={() => downloadExport(employeesApi.exportUrl("csv"), "employees.csv")}>
            <Download className="h-3.5 w-3.5" /> CSV
          </Button>
          {canManage && (
            <Button size="sm" onClick={() => setDialogState({ mode: "create" })}>
              <Plus className="h-3.5 w-3.5" /> New Employee
            </Button>
          )}
        </div>
      </div>

      <DataTable
        dense
        rowNumberStart={(data?.current_page ? data.current_page - 1 : 0) * 20 + 1}
        sort={sort}
        onSortChange={handleSortChange}
        columns={[
          {
            key: "last_name",
            header: "Name",
            sortable: true,
            render: (row) => (
              <Link to={`/employees/${row.id}`} className="font-medium text-brand-700 hover:underline">
                {row.full_name}
              </Link>
            ),
          },
          { key: "employee_number", header: "Employee No.", sortable: true },
          { key: "department_name", header: "Department", render: (row) => row.department_name ?? "—" },
          { key: "position_title", header: "Position", render: (row) => row.position_title ?? "—" },
          { key: "branch_name", header: "Branch", render: (row) => row.branch_name ?? "—" },
          { key: "email", header: "Email", render: (row) => row.email || "—" },
          { key: "phone_number", header: "Phone", render: (row) => row.phone_number || "—" },
          { key: "employment_type", header: "Type" },
          {
            key: "employment_status",
            header: "Status",
            render: (row) => <StatusBadge status={row.employment_status} />,
          },
          { key: "employment_date", header: "Joined", sortable: true, render: (row) => formatDate(row.employment_date) },
        ]}
        data={data?.results ?? []}
        isLoading={isLoading}
        canEdit={canManage}
        canDelete={false}
        onEdit={(row) => setDialogState({ mode: "edit", row })}
      />

      {data && data.num_pages > 1 && (
        <div className="flex items-center justify-between text-sm text-slate-500">
          <span>
            Page {data.current_page} of {data.num_pages} ({data.count} total)
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={!data.previous} onClick={() => setPage((p) => p - 1)}>
              Previous
            </Button>
            <Button variant="outline" size="sm" disabled={!data.next} onClick={() => setPage((p) => p + 1)}>
              Next
            </Button>
          </div>
        </div>
      )}

      <Dialog
        open={!!dialogState}
        onClose={() => {
          setDialogState(null);
          setFormError(null);
        }}
        title={dialogState?.mode === "edit" ? "Edit Employee" : "New Employee"}
        className="max-w-2xl"
      >
        {dialogState && (
          <ResourceForm
            fields={formFields}
            defaultValues={dialogState.row as unknown as Record<string, unknown>}
            submitting={createMutation.isPending || updateMutation.isPending}
            errorMessage={formError}
            onCancel={() => {
              setDialogState(null);
              setFormError(null);
            }}
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
    </div>
  );
}
