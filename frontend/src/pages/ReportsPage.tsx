import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { AlarmClockCheck, BarChart3, CalendarDays, History, UserX } from "lucide-react";
import {
  fetchAttendanceReport,
  fetchLateArrivalsReport,
  fetchAbsenteeismReport,
  attendanceReportExportUrl,
  lateArrivalsReportExportUrl,
  absenteeismReportExportUrl,
} from "../api/reports";
import { downloadExport } from "../api/resource";
import { fetchAllEmployeesForSelect } from "../api/employees";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Select } from "../components/ui/Select";
import { Button } from "../components/ui/Button";
import { ExportButtonGroup } from "../components/ExportButtonGroup";

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
  fetcher: (params: { period: "week" | "month" }) => Promise<{ summary: { count: number } }>;
  exportUrl: (format: "csv" | "xlsx" | "pdf", params: { period: "week" | "month" }) => string;
}) {
  const [period, setPeriod] = useState<"week" | "month">("month");
  const { data, isLoading } = useQuery({
    queryKey: [title, period],
    queryFn: () => fetcher({ period }),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-slate-400" /> {title}
        </CardTitle>
        <ExportButtonGroup onExport={(format) => downloadExport(exportUrl(format, { period }), `${title}.${format}`)} />
      </CardHeader>
      <CardContent className="flex items-center justify-between gap-3 px-4 pb-4 pt-0">
        <Select value={period} onChange={(e) => setPeriod(e.target.value as "week" | "month")} className="w-36">
          <option value="week">This Week</option>
          <option value="month">This Month</option>
        </Select>
        <p className="text-sm text-slate-500">{isLoading ? "Loading…" : `${data?.summary.count ?? 0} record(s)`}</p>
      </CardContent>
    </Card>
  );
}
