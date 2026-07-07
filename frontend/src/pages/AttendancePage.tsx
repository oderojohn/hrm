import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Fingerprint, ListChecks, Plus, RefreshCw, TrendingUp } from "lucide-react";
import {
  attendanceRecordsApi,
  attendanceCorrectionsApi,
  fetchAttendanceAnalytics,
  attendanceAnalyticsExportUrl,
  syncZKTeco,
  approveAttendanceCorrection,
  type AttendanceCorrectionRequest,
} from "../api/attendance";
import { downloadExport } from "../api/resource";
import { branchesApi, departmentsApi } from "../api/organization";
import { fetchAllEmployeesForSelect } from "../api/employees";
import { extractErrorMessage } from "../api/client";
import { useAuthStore, isHRManagerOrAbove, isManagerOrAbove } from "../store/authStore";
import { Tabs } from "../components/ui/Tabs";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Dialog } from "../components/ui/Dialog";
import { Select } from "../components/ui/Select";
import { ResourceForm } from "../components/resource/ResourceForm";
import type { FormField } from "../components/resource/types";
import { DataTable } from "../components/resource/DataTable";
import { StatusBadge } from "../components/ui/Badge";
import { ExportButtonGroup } from "../components/ExportButtonGroup";
import { EmployeeAttendanceDetail } from "../components/attendance/EmployeeAttendanceDetail";
import { DateRangeFilter, toAnalyticsParams, toRecordFilterParams, useDateRangeFilter } from "../components/DateRangeFilter";
import { formatDate } from "../lib/utils";

export function AttendancePage() {
  const user = useAuthStore((s) => s.user);
  const canViewAll = isManagerOrAbove(user);

  const tabs = [
    { key: "my-attendance", label: "My Attendance", content: <MyAttendanceTab /> },
    ...(canViewAll ? [{ key: "all-records", label: "All Records & Analytics", content: <AllRecordsTab /> }] : []),
  ];

  return (
    <div className="space-y-5">
      <div className="flex items-start gap-3 rounded-lg border border-brand-100 bg-brand-50/60 px-4 py-3">
        <Fingerprint className="mt-0.5 h-5 w-5 shrink-0 text-brand-600" />
        <div>
          <h1 className="text-lg font-semibold text-slate-900">Attendance</h1>
          <p className="text-sm text-slate-600">
            Clock in/out happens on the biometric device — this system reports on synced data only.
          </p>
        </div>
      </div>
      <Tabs tabs={tabs} />
    </div>
  );
}

function MyAttendanceTab() {
  const user = useAuthStore((s) => s.user);
  const [range, setRange] = useDateRangeFilter("month");
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: corrections } = useQuery({
    queryKey: ["attendance-corrections", "own", user?.employee_id],
    queryFn: () => attendanceCorrectionsApi.list({ employee: user?.employee_id ?? undefined }),
    enabled: !!user?.employee_id,
  });

  const createCorrectionMutation = useMutation({
    mutationFn: (values: Partial<AttendanceCorrectionRequest>) => attendanceCorrectionsApi.create(values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attendance-corrections"] });
      setDialogOpen(false);
      setFormError(null);
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  const correctionFields: FormField[] = [
    { name: "date", label: "Date", type: "date", required: true },
    { name: "requested_clock_in", label: "Correct Clock In", type: "datetime-local" },
    { name: "requested_clock_out", label: "Correct Clock Out", type: "datetime-local" },
    { name: "reason", label: "Reason", type: "textarea", required: true },
  ];

  if (!user?.employee_id) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-slate-500">
          No employee record is linked to this account.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-800">My Attendance Report</h2>
        </div>
        <div className="flex items-center gap-2">
          <DateRangeFilter value={range} onChange={setRange} />
          <Button size="sm" variant="outline" onClick={() => setDialogOpen(true)}>
            <Plus className="h-3.5 w-3.5" /> Request Correction
          </Button>
        </div>
      </div>

      <EmployeeAttendanceDetail employeeId={user.employee_id} range={range} />

      {!!corrections?.results.length && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ListChecks className="h-4 w-4 text-slate-400" /> Correction Requests
            </CardTitle>
          </CardHeader>
          <CardContent className="px-0 pb-0 pt-0">
            <DataTable
              columns={[
                { key: "date", header: "Date", render: (r) => formatDate(r.date) },
                { key: "reason", header: "Reason" },
                { key: "status", header: "Status", render: (r) => <StatusBadge status={r.status} /> },
              ]}
              data={corrections.results}
              canEdit={false}
              canDelete={false}
            />
          </CardContent>
        </Card>
      )}

      <Dialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          setFormError(null);
        }}
        title="Request Attendance Correction"
      >
        <ResourceForm
          fields={correctionFields}
          submitting={createCorrectionMutation.isPending}
          errorMessage={formError}
          onCancel={() => setDialogOpen(false)}
          onSubmit={(values) => createCorrectionMutation.mutate(values as Partial<AttendanceCorrectionRequest>)}
        />
      </Dialog>
    </div>
  );
}

function AllRecordsTab() {
  const user = useAuthStore((s) => s.user);
  const canSync = isHRManagerOrAbove(user);
  const [range, setRange] = useDateRangeFilter("month");
  const [branchId, setBranchId] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const queryClient = useQueryClient();
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const { data: branches } = useQuery({ queryKey: ["branches-all"], queryFn: () => branchesApi.list({ page_size: 200 }) });
  const { data: departments } = useQuery({
    queryKey: ["departments-all"],
    queryFn: () => departmentsApi.list({ page_size: 200 }),
  });
  const { data: employees } = useQuery({ queryKey: ["employees-all"], queryFn: fetchAllEmployeesForSelect });

  const filterParams = useMemo(
    () => ({
      branch: branchId ? Number(branchId) : undefined,
      department: departmentId ? Number(departmentId) : undefined,
      employee: employeeId ? Number(employeeId) : undefined,
    }),
    [branchId, departmentId, employeeId]
  );

  const analyticsParams = { ...toAnalyticsParams(range), ...filterParams };
  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ["attendance-analytics", "all", analyticsParams],
    queryFn: () => fetchAttendanceAnalytics(analyticsParams),
  });

  const recordParams = { ...toRecordFilterParams(range), ...filterParams };
  const { data, isLoading } = useQuery({
    queryKey: ["attendance-all", recordParams],
    queryFn: () => attendanceRecordsApi.list({ ordering: "-date", page_size: 100, ...recordParams }),
  });

  const { data: pendingCorrections } = useQuery({
    queryKey: ["attendance-corrections", "pending"],
    queryFn: () => attendanceCorrectionsApi.list({ status: "PENDING" }),
  });

  const handleSync = async () => {
    setSyncing(true);
    setSyncMessage(null);
    try {
      const result = await syncZKTeco();
      const ok = result.results.filter((r) => !r.error);
      const failed = result.results.filter((r) => r.error);
      const employeesCreated = ok.reduce((sum, r) => sum + (r.employees?.created ?? 0), 0);
      const recordsCreated = ok.reduce((sum, r) => sum + (r.attendance?.records_created ?? 0), 0);
      const recordsUpdated = ok.reduce((sum, r) => sum + (r.attendance?.records_updated ?? 0), 0);
      let message = `Synced ${ok.length} device(s): ${employeesCreated} new employees, ${recordsCreated} new / ${recordsUpdated} updated attendance records.`;
      if (failed.length) {
        message += ` ${failed.length} device(s) failed: ${failed.map((f) => `${f.device_name} (${f.error})`).join("; ")}`;
      }
      setSyncMessage(message);
      queryClient.invalidateQueries({ queryKey: ["attendance-all"] });
      queryClient.invalidateQueries({ queryKey: ["attendance-analytics"] });
    } catch (err) {
      setSyncMessage(extractErrorMessage(err));
    } finally {
      setSyncing(false);
    }
  };

  const handleExportAnalytics = (format: "csv" | "xlsx" | "pdf") => {
    downloadExport(attendanceAnalyticsExportUrl(format, analyticsParams), `attendance-analytics.${format}`);
  };

  const handleExportRecords = (format: "csv" | "xlsx" | "pdf") => {
    downloadExport(attendanceRecordsApi.exportUrl(format, recordParams), `attendance-records.${format}`);
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        {canSync && (
          <div className="flex w-full flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3 sm:flex-1">
            <div>
              <p className="text-sm font-medium text-slate-800">Biometric Devices</p>
              {syncMessage && <p className="text-xs text-slate-500">{syncMessage}</p>}
            </div>
            <Button size="sm" variant="outline" onClick={handleSync} loading={syncing}>
              <RefreshCw className="h-3.5 w-3.5" /> Sync Now
            </Button>
          </div>
        )}
        <DateRangeFilter value={range} onChange={setRange} />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Select value={branchId} onChange={(e) => setBranchId(e.target.value)} className="w-full sm:w-44">
          <option value="">All Branches</option>
          {branches?.results.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </Select>
        <Select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className="w-full sm:w-44">
          <option value="">All Departments</option>
          {departments?.results.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </Select>
        <Select value={employeeId} onChange={(e) => setEmployeeId(e.target.value)} className="w-full sm:w-56">
          <option value="">All Employees</option>
          {employees?.map((e) => (
            <option key={e.id} value={e.id}>
              {e.full_name}
            </option>
          ))}
        </Select>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-slate-400" /> Working Hours &amp; Days — Intelligent Report
          </CardTitle>
          <ExportButtonGroup onExport={handleExportAnalytics} />
        </CardHeader>
        <CardContent className="px-0 pb-0 pt-0">
          <DataTable
            dense
            columns={[
              {
                key: "employee_name",
                header: "Employee",
                render: (r) => (
                  <Link to={`/attendance/employee/${r.employee_id}`} className="font-medium text-brand-600 hover:underline">
                    {r.employee_name}
                  </Link>
                ),
              },
              { key: "working_days", header: "Days Worked", render: (r) => `${r.working_days} / ${r.expected_working_days}` },
              { key: "absent_days", header: "Absent Days", align: "center" },
              {
                key: "attendance_rate",
                header: "Attendance Rate",
                render: (r) => (r.attendance_rate != null ? `${r.attendance_rate}%` : "—"),
              },
              { key: "total_hours", header: "Total Hours", align: "right" },
              { key: "average_hours_per_day", header: "Avg Hrs/Day", align: "right" },
              { key: "late_count", header: "Late Count", align: "center" },
              { key: "overtime_hours", header: "Overtime (hrs)", align: "right" },
            ]}
            data={(analytics?.results ?? []).map((r) => ({ ...r, id: r.employee_id }))}
            isLoading={analyticsLoading}
            canEdit={false}
            canDelete={false}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Fingerprint className="h-4 w-4 text-slate-400" /> Raw Records (from device)
          </CardTitle>
          <ExportButtonGroup onExport={handleExportRecords} />
        </CardHeader>
        <CardContent className="px-0 pb-0 pt-0">
          <DataTable
            dense
            columns={[
              {
                key: "employee_name",
                header: "Employee",
                render: (r) => (
                  <Link to={`/attendance/employee/${r.employee}`} className="font-medium text-brand-600 hover:underline">
                    {r.employee_name}
                  </Link>
                ),
              },
              { key: "date", header: "Date", render: (r) => formatDate(r.date) },
              {
                key: "clock_in",
                header: "Clock In",
                render: (r) => (r.clock_in ? new Date(r.clock_in).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—"),
              },
              {
                key: "clock_out",
                header: "Clock Out",
                render: (r) => (r.clock_out ? new Date(r.clock_out).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—"),
              },
              { key: "device_name", header: "Device", render: (r) => r.device_name ?? "—" },
              { key: "method", header: "Method" },
            ]}
            data={data?.results ?? []}
            isLoading={isLoading}
            canEdit={false}
            canDelete={false}
          />
        </CardContent>
      </Card>

      {!!pendingCorrections?.results.length && <PendingCorrectionsCard corrections={pendingCorrections.results} />}
    </div>
  );
}

function PendingCorrectionsCard({ corrections }: { corrections: AttendanceCorrectionRequest[] }) {
  const queryClient = useQueryClient();

  const approve = useMutation({
    mutationFn: (id: number) => approveAttendanceCorrection(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["attendance-corrections"] }),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pending Correction Requests</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="divide-y divide-slate-100">
          {corrections.map((c) => (
            <li key={c.id} className="flex items-center justify-between py-2.5 text-sm">
              <div>
                <p className="font-medium text-slate-800">
                  {c.employee_name} — {formatDate(c.date)}
                </p>
                <p className="text-xs text-slate-500">{c.reason}</p>
              </div>
              <Button size="sm" onClick={() => approve.mutate(c.id)}>
                Approve
              </Button>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
