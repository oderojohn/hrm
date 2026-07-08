import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { AlarmClockCheck, BarChart3, CalendarDays, CheckSquare, History, UserX } from "lucide-react";
import {
  fetchAttendanceReport,
  fetchLateArrivalsReport,
  fetchAbsenteeismReport,
  fetchAttendanceGridReport,
  attendanceReportExportUrl,
  lateArrivalsReportExportUrl,
  absenteeismReportExportUrl,
  attendanceGridReportExportUrl,
} from "../api/reports";
import { downloadExport } from "../api/resource";
import { fetchAllEmployeesForSelect } from "../api/employees";
import { branchesApi, departmentsApi } from "../api/organization";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Select } from "../components/ui/Select";
import { Button } from "../components/ui/Button";
import { ExportButtonGroup } from "../components/ExportButtonGroup";
import { DateRangeFilter, toAnalyticsParams, useDateRangeFilter } from "../components/DateRangeFilter";

function monthRange() {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10);
  const end = now.toISOString().slice(0, 10);
  return { start, end };
}

function todayRange() {
  const today = new Date().toISOString().slice(0, 10);
  return { start: today, end: today };
}

export function ReportsPage() {
  const navigate = useNavigate();
  const { data: employees } = useQuery({ queryKey: ["employees-all"], queryFn: fetchAllEmployeesForSelect });
  const [historyEmployeeId, setHistoryEmployeeId] = useState("");

  return (
    <div className="space-y-5">
      <div className="flex items-start gap-3 rounded-lg border border-brand-100 bg-brand-50/60 px-4 py-3">
        <BarChart3 className="mt-0.5 h-5 w-5 shrink-0 text-brand-600" />
        <div>
          <h1 className="text-lg font-semibold text-slate-900">Reports</h1>
          <p className="text-sm text-slate-600">Generate and export attendance reports for any period.</p>
        </div>
      </div>

      <AttendanceRegisterCard />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <AttendanceReportCard title="Daily Attendance Report" icon={CalendarDays} range={todayRange()} />
        <AttendanceReportCard title="Monthly Attendance Report" icon={CalendarDays} range={monthRange()} />
        <PeriodReportCard
          title="Late Arrivals Report"
          icon={AlarmClockCheck}
          fetcher={fetchLateArrivalsReport}
          exportUrl={lateArrivalsReportExportUrl}
        />
        <PeriodReportCard
          title="Absenteeism Report"
          icon={UserX}
          fetcher={fetchAbsenteeismReport}
          exportUrl={absenteeismReportExportUrl}
        />

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History className="h-4 w-4 text-slate-400" /> Employee Attendance History
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap items-center gap-2 px-4 pb-4 pt-0">
            <Select value={historyEmployeeId} onChange={(e) => setHistoryEmployeeId(e.target.value)} className="flex-1">
              <option value="">Select an employee...</option>
              {employees?.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.full_name}
                </option>
              ))}
            </Select>
            <Button
              disabled={!historyEmployeeId}
              onClick={() => navigate(`/attendance/employee/${historyEmployeeId}`)}
            >
              View History
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

const STATUS_CELL_CLASS: Record<string, string> = {
  P: "bg-emerald-50 text-emerald-700",
  L: "bg-amber-50 text-amber-700",
  A: "bg-red-50 text-red-700",
  LV: "bg-sky-50 text-sky-700",
  OFF: "bg-slate-100 text-slate-500",
};

const METRIC_OPTIONS: { value: "status" | "clock_in" | "clock_out" | "working_hours"; label: string }[] = [
  { value: "status", label: "Attendance Status (Present/Late/Absent/Leave)" },
  { value: "clock_in", label: "Clock In Times" },
  { value: "clock_out", label: "Clock Out Times" },
  { value: "working_hours", label: "Working Hours" },
];

function AttendanceRegisterCard() {
  const [range, setRange] = useDateRangeFilter("month");
  const [branchId, setBranchId] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [metric, setMetric] = useState<"status" | "clock_in" | "clock_out" | "working_hours">("status");

  const { data: branches } = useQuery({ queryKey: ["branches-all"], queryFn: () => branchesApi.list({ page_size: 200 }) });
  const { data: departments } = useQuery({
    queryKey: ["departments-all"],
    queryFn: () => departmentsApi.list({ page_size: 200 }),
  });
  const { data: employees } = useQuery({ queryKey: ["employees-all"], queryFn: fetchAllEmployeesForSelect });

  const params = {
    ...toAnalyticsParams(range),
    metric,
    branch: branchId ? Number(branchId) : undefined,
    department: departmentId ? Number(departmentId) : undefined,
    employee: employeeId ? Number(employeeId) : undefined,
  };

  const { data, isLoading } = useQuery({
    queryKey: ["report-attendance-grid", params],
    queryFn: () => fetchAttendanceGridReport(params),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckSquare className="h-4 w-4 text-slate-400" /> Attendance Register
        </CardTitle>
        <ExportButtonGroup
          onExport={(format) => downloadExport(attendanceGridReportExportUrl(format, params), `attendance-register-${metric}.${format}`)}
        />
      </CardHeader>
      <CardContent className="space-y-3 px-4 pb-4 pt-0">
        <p className="text-xs text-slate-500">
          Employees down the left, dates across the top. Scope it to a branch, a department, a single employee, or
          leave all blank for the whole company — then choose what each date column should show before exporting.
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <DateRangeFilter value={range} onChange={setRange} />
          <Select value={branchId} onChange={(e) => setBranchId(e.target.value)} className="w-full sm:w-40">
            <option value="">All Branches</option>
            {branches?.results.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </Select>
          <Select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} className="w-full sm:w-48">
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

        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Report shows, per date:</label>
          <Select value={metric} onChange={(e) => setMetric(e.target.value as typeof metric)} className="w-full sm:w-72">
            {METRIC_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>
        </div>

        {isLoading || !data ? (
          <p className="text-sm text-slate-400">Loading…</p>
        ) : (
          <>
            <div className="max-h-80 overflow-auto rounded-md border border-slate-200">
              <table className="w-full min-w-max border-collapse text-xs">
                <thead className="sticky top-0 bg-slate-50">
                  <tr>
                    {data.headers.map((h, i) => (
                      <th key={i} className="whitespace-nowrap border border-slate-200 px-2 py-1.5 text-left font-semibold text-slate-600">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((row, rIdx) => (
                    <tr key={rIdx}>
                      {row.map((cell, cIdx) => (
                        <td
                          key={cIdx}
                          className={
                            cIdx >= 3
                              ? `whitespace-nowrap border border-slate-200 px-2 py-1 text-center font-medium ${STATUS_CELL_CLASS[cell] ?? ""}`
                              : "whitespace-nowrap border border-slate-200 px-2 py-1 text-slate-700"
                          }
                        >
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-slate-400">
              Showing {data.results.length} of {data.count} employee(s). Export for the full register.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function AttendanceReportCard({
  title,
  icon: Icon,
  range,
}: {
  title: string;
  icon: typeof CalendarDays;
  range: { start: string; end: string };
}) {
  const { data, isLoading } = useQuery({
    queryKey: ["report-attendance", range],
    queryFn: () => fetchAttendanceReport(range),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-slate-400" /> {title}
        </CardTitle>
        <ExportButtonGroup onExport={(format) => downloadExport(attendanceReportExportUrl(format, range), `${title}.${format}`)} />
      </CardHeader>
      <CardContent className="px-4 pb-4 pt-0 text-sm text-slate-500">
        {isLoading ? "Loading…" : `${data?.summary.count ?? 0} record(s) in this period.`}
      </CardContent>
    </Card>
  );
}

function PeriodReportCard({
  title,
  icon: Icon,
  fetcher,
  exportUrl,
}: {
  title: string;
  icon: typeof CalendarDays;
  fetcher: (params: { period?: "week" | "month"; start?: string; end?: string }) => Promise<{ summary: { count: number } }>;
  exportUrl: (format: "csv" | "xlsx" | "pdf", params: { period?: "week" | "month"; start?: string; end?: string }) => string;
}) {
  const [range, setRange] = useDateRangeFilter("month");
  const params = toAnalyticsParams(range);
  const { data, isLoading } = useQuery({
    queryKey: [title, params],
    queryFn: () => fetcher(params),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-slate-400" /> {title}
        </CardTitle>
        <ExportButtonGroup onExport={(format) => downloadExport(exportUrl(format, params), `${title}.${format}`)} />
      </CardHeader>
      <CardContent className="flex flex-wrap items-center justify-between gap-3 px-4 pb-4 pt-0">
        <DateRangeFilter value={range} onChange={setRange} />
        <p className="text-sm text-slate-500">{isLoading ? "Loading…" : `${data?.summary.count ?? 0} record(s)`}</p>
      </CardContent>
    </Card>
  );
}
