import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlarmClockCheck,
  CalendarDays,
  CheckCircle2,
  Fingerprint,
  ListChecks,
  Plus,
  RefreshCw,
  TrendingUp,
  Users,
  Wifi,
  WifiOff,
  XCircle,
} from "lucide-react";
import {
  attendanceRecordsApi,
  attendanceCorrectionsApi,
  fetchAttendanceAnalytics,
  attendanceAnalyticsExportUrl,
  fetchAttendanceDashboard,
  fetchDailyAttendance,
  dailyAttendanceExportUrl,
  syncZKTeco,
  devicesApi,
  approveAttendanceCorrection,
  rejectAttendanceCorrection,
  supervisorApproveCorrection,
  supervisorRejectCorrection,
  type AttendanceCorrectionRequest,
  type ZKTecoSyncResult,
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
import { Input } from "../components/ui/Input";
import { Textarea } from "../components/ui/Textarea";
import { ResourceForm } from "../components/resource/ResourceForm";
import type { FormField } from "../components/resource/types";
import { DataTable } from "../components/resource/DataTable";
import { StatusBadge } from "../components/ui/Badge";
import { StatCard } from "../components/StatCard";
import { ExportButtonGroup } from "../components/ExportButtonGroup";
import { EmployeeAttendanceDetail } from "../components/attendance/EmployeeAttendanceDetail";
import { DateRangeFilter, toAnalyticsParams, toRecordFilterParams, useDateRangeFilter } from "../components/DateRangeFilter";
import { formatDate, formatDateTime } from "../lib/utils";

export function AttendancePage() {
  const user = useAuthStore((s) => s.user);
  const canViewAll = isManagerOrAbove(user);
  const canSync = isHRManagerOrAbove(user);

  const tabs = [
    ...(canViewAll ? [{ key: "dashboard", label: "Dashboard", content: <AttendanceDashboardTab /> }] : []),
    { key: "my-attendance", label: "My Attendance", content: <MyAttendanceTab /> },
    ...(canViewAll ? [{ key: "daily", label: "Daily Attendance", content: <DailyAttendanceTab /> }] : []),
    ...(canViewAll ? [{ key: "all-records", label: "All Records & Analytics", content: <AllRecordsTab /> }] : []),
    ...(canSync ? [{ key: "biometric-sync", label: "Biometric Sync", content: <BiometricSyncTab /> }] : []),
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

function AttendanceDashboardTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["attendance-dashboard"],
    queryFn: fetchAttendanceDashboard,
    refetchInterval: 60_000,
  });

  if (isLoading || !data) {
    return <Card className="p-10 text-center text-sm text-slate-400">Loading dashboard…</Card>;
  }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard label="Total Employees" value={data.total_employees} icon={Users} tone="slate" />
        <StatCard label="Present Today" value={data.present_today} icon={CheckCircle2} tone="green" />
        <StatCard label="Absent Today" value={data.absent_today} icon={XCircle} tone="red" />
        <StatCard label="On Leave" value={data.on_leave_today} icon={CalendarDays} tone="blue" />
        <StatCard label="Late Arrivals" value={data.late_arrivals_today} icon={AlarmClockCheck} tone="amber" />
        <StatCard label="Early Departures" value={data.early_departures_today} icon={AlarmClockCheck} tone="amber" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Fingerprint className="h-4 w-4 text-slate-400" /> Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent className="px-0 pb-0 pt-0">
          {data.recent_activity.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-slate-400">No punches recorded yet.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {data.recent_activity.map((activity, i) => (
                <li key={i} className="flex items-center justify-between gap-3 px-4 py-2.5 text-sm">
                  <div className="flex items-center gap-2">
                    <StatusBadge status={activity.event === "IN" ? "PRESENT" : activity.event === "OUT" ? "LATE" : "OFF"} />
                    <span className="font-medium text-slate-800">{activity.employee_name}</span>
                    <span className="text-xs text-slate-400">{activity.device_name ?? "—"}</span>
                  </div>
                  <span className="text-xs text-slate-500">{formatDateTime(activity.timestamp)}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DailyAttendanceTab() {
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today);
  const [departmentId, setDepartmentId] = useState("");
  const [employeeId, setEmployeeId] = useState("");

  const { data: departments } = useQuery({
    queryKey: ["departments-all"],
    queryFn: () => departmentsApi.list({ page_size: 200 }),
  });
  const { data: employees } = useQuery({ queryKey: ["employees-all"], queryFn: fetchAllEmployeesForSelect });

  const params = {
    date,
    department: departmentId ? Number(departmentId) : undefined,
    employee: employeeId ? Number(employeeId) : undefined,
  };

  const { data, isLoading } = useQuery({
    queryKey: ["attendance-daily", params],
    queryFn: () => fetchDailyAttendance(params),
  });

  const handleExport = (format: "csv" | "xlsx" | "pdf") => {
    downloadExport(dailyAttendanceExportUrl(format, params), `daily-attendance-${date}.${format}`);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="w-full sm:w-44" />
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
            <CalendarDays className="h-4 w-4 text-slate-400" /> Daily Attendance — {formatDate(date)}
          </CardTitle>
          <ExportButtonGroup onExport={handleExport} />
        </CardHeader>
        <CardContent className="px-0 pb-0 pt-0">
          <DataTable
            dense
            columns={[
              { key: "employee_number", header: "Employee ID" },
              { key: "employee_name", header: "Employee Name" },
              { key: "department_name", header: "Department", render: (r) => r.department_name ?? "—" },
              { key: "shift_name", header: "Shift", render: (r) => r.shift_name ?? "—" },
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
              { key: "working_hours", header: "Working Hours", render: (r) => (r.working_hours != null ? `${r.working_hours}h` : "—") },
              { key: "status", header: "Status", render: (r) => <StatusBadge status={r.status} /> },
            ]}
            data={(data?.results ?? []).map((r) => ({ ...r, id: r.employee_id }))}
            isLoading={isLoading}
            canEdit={false}
            canDelete={false}
          />
        </CardContent>
      </Card>
    </div>
  );
}

function BiometricSyncTab() {
  const queryClient = useQueryClient();
  const [syncing, setSyncing] = useState(false);
  const [lastResult, setLastResult] = useState<{ results: ZKTecoSyncResult[]; syncedAt: string } | null>(null);

  const { data: devices, isLoading } = useQuery({
    queryKey: ["devices-all"],
    queryFn: () => devicesApi.list({ page_size: 100 }),
  });

  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await syncZKTeco();
      setLastResult({ results: result.results, syncedAt: new Date().toISOString() });
      queryClient.invalidateQueries({ queryKey: ["devices-all"] });
      queryClient.invalidateQueries({ queryKey: ["attendance-all"] });
      queryClient.invalidateQueries({ queryKey: ["attendance-daily"] });
      queryClient.invalidateQueries({ queryKey: ["attendance-dashboard"] });
    } catch (err) {
      setLastResult({
        results: [{ device_id: 0, device_name: "Sync", employees: null, attendance: null, error: extractErrorMessage(err) }],
        syncedAt: new Date().toISOString(),
      });
    } finally {
      setSyncing(false);
    }
  };

  const recordsImported = lastResult?.results.reduce(
    (sum, r) => sum + (r.attendance?.records_created ?? 0) + (r.attendance?.records_updated ?? 0),
    0
  );

  // No configurable auto-sync interval on the cloud side (the local desktop
  // agent controls its own polling interval) — this is just a fixed,
  // reasonable staleness threshold for the health badge below.
  const STALE_AFTER_MINUTES = 15;
  const isConnected = (lastSyncedAt: string | null) => {
    if (!lastSyncedAt) return false;
    return (Date.now() - new Date(lastSyncedAt).getTime()) / 60000 < STALE_AFTER_MINUTES;
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-4 p-4">
          <div>
            <p className="text-sm font-medium text-slate-800">Sync Attendance</p>
            <p className="text-xs text-slate-500">
              {lastResult
                ? `Last sync: ${formatDateTime(lastResult.syncedAt)} — ${recordsImported ?? 0} record(s) imported`
                : "Pull the latest enrolled users and punches from every active device."}
            </p>
          </div>
          <Button onClick={handleSync} loading={syncing}>
            <RefreshCw className="h-3.5 w-3.5" /> Sync Now
          </Button>
        </CardContent>
      </Card>

      {lastResult && (
        <Card>
          <CardHeader>
            <CardTitle>Last Sync Result</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 px-4 pb-4 pt-0 text-sm">
            {lastResult.results.map((r, i) => (
              <div key={i} className="flex items-center justify-between rounded-md border border-slate-100 px-3 py-2">
                <span className="font-medium text-slate-700">{r.device_name}</span>
                {r.error ? (
                  <span className="text-red-600">{r.error}</span>
                ) : (
                  <span className="text-slate-500">
                    {r.employees?.created ?? 0} new employee(s), {r.attendance?.records_created ?? 0} new /{" "}
                    {r.attendance?.records_updated ?? 0} updated record(s)
                  </span>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Devices</CardTitle>
        </CardHeader>
        <CardContent className="px-0 pb-0 pt-0">
          <DataTable
            columns={[
              { key: "name", header: "Name" },
              { key: "branch_name", header: "Branch", render: (r) => r.branch_name ?? "—" },
              { key: "ip_address", header: "IP Address", render: (r) => r.ip_address ?? "—" },
              {
                key: "last_synced_at",
                header: "Last Synced",
                render: (r) => (r.last_synced_at ? formatDateTime(r.last_synced_at) : "Never"),
              },
              {
                key: "connected",
                header: "Status",
                render: (r) =>
                  isConnected(r.last_synced_at) ? (
                    <span className="inline-flex items-center gap-1 text-emerald-600">
                      <Wifi className="h-3.5 w-3.5" /> Connected
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-slate-400">
                      <WifiOff className="h-3.5 w-3.5" /> Disconnected
                    </span>
                  ),
              },
            ]}
            data={devices?.results ?? []}
            isLoading={isLoading}
            canEdit={false}
            canDelete={false}
          />
        </CardContent>
      </Card>
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
                {
                  key: "stage",
                  header: "Stage",
                  render: (r) => (r.current_stage === "DONE" ? <StatusBadge status={r.status} /> : <StatusBadge status={r.current_stage} />),
                },
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
  const [range, setRange] = useDateRangeFilter("month");
  const [branchId, setBranchId] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [employeeId, setEmployeeId] = useState("");

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
    queryKey: ["attendance-corrections", "pending-hr"],
    queryFn: () => attendanceCorrectionsApi.list({ status: "PENDING" }),
  });

  const { data: pendingSupervisorCorrections } = useQuery({
    queryKey: ["attendance-corrections", "pending-supervisor"],
    queryFn: () => attendanceCorrectionsApi.list({ pending_supervisor_approval: true }),
  });

  const handleExportAnalytics = (format: "csv" | "xlsx" | "pdf") => {
    downloadExport(attendanceAnalyticsExportUrl(format, analyticsParams), `attendance-analytics.${format}`);
  };

  const handleExportRecords = (format: "csv" | "xlsx" | "pdf") => {
    downloadExport(attendanceRecordsApi.exportUrl(format, recordParams), `attendance-records.${format}`);
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
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

      {!!pendingSupervisorCorrections?.results.length && (
        <PendingCorrectionsCard
          title="Awaiting Your Approval (as Supervisor)"
          corrections={pendingSupervisorCorrections.results}
          stage="supervisor"
        />
      )}
      {!!pendingCorrections?.results.filter((c) => c.current_stage === "HR").length && (
        <PendingCorrectionsCard
          title="Awaiting HR Approval"
          corrections={pendingCorrections.results.filter((c) => c.current_stage === "HR")}
          stage="hr"
        />
      )}
    </div>
  );
}

function PendingCorrectionsCard({
  title,
  corrections,
  stage,
}: {
  title: string;
  corrections: AttendanceCorrectionRequest[];
  stage: "supervisor" | "hr";
}) {
  const queryClient = useQueryClient();
  const [rejecting, setRejecting] = useState<AttendanceCorrectionRequest | null>(null);
  const [comment, setComment] = useState("");

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["attendance-corrections"] });

  const approve = useMutation({
    mutationFn: (id: number) => (stage === "supervisor" ? supervisorApproveCorrection(id) : approveAttendanceCorrection(id)),
    onSuccess: invalidate,
  });

  const reject = useMutation({
    mutationFn: () =>
      stage === "supervisor" ? supervisorRejectCorrection(rejecting!.id, comment) : rejectAttendanceCorrection(rejecting!.id, comment),
    onSuccess: () => {
      invalidate();
      setRejecting(null);
      setComment("");
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="divide-y divide-slate-100">
          {corrections.map((c) => (
            <li key={c.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
              <div>
                <p className="font-medium text-slate-800">
                  {c.employee_name} — {formatDate(c.date)}
                </p>
                <p className="text-xs text-slate-500">{c.reason}</p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={() => approve.mutate(c.id)} loading={approve.isPending}>
                  Approve
                </Button>
                <Button size="sm" variant="outline" onClick={() => setRejecting(c)}>
                  Reject
                </Button>
              </div>
            </li>
          ))}
        </ul>
      </CardContent>

      <Dialog open={!!rejecting} onClose={() => setRejecting(null)} title="Reject Correction Request">
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            Rejecting {rejecting?.employee_name}'s correction for {rejecting ? formatDate(rejecting.date) : ""}.
          </p>
          <Textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Reason for rejection (optional)"
            rows={3}
          />
          <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
            <Button variant="outline" onClick={() => setRejecting(null)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={() => reject.mutate()} loading={reject.isPending}>
              Reject
            </Button>
          </div>
        </div>
      </Dialog>
    </Card>
  );
}
