import { useQuery } from "@tanstack/react-query";
import { CalendarCheck, Clock3, Fingerprint, History, TrendingUp } from "lucide-react";
import {
  fetchEmployeeAttendanceDetail,
  employeeAttendanceDetailExportUrl,
  type EmployeeAttendanceDay,
} from "../../api/attendance";
import { downloadExport } from "../../api/resource";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { DataTable } from "../resource/DataTable";
import { StatusBadge } from "../ui/Badge";
import { StatCard } from "../StatCard";
import { ExportButtonGroup } from "../ExportButtonGroup";
import { toAnalyticsParams, type DateRangeValue } from "../DateRangeFilter";
import { formatDate } from "../../lib/utils";

interface EmployeeAttendanceDetailProps {
  employeeId: number;
  range: DateRangeValue;
}

export function EmployeeAttendanceDetail({ employeeId, range }: EmployeeAttendanceDetailProps) {
  const params = toAnalyticsParams(range);
  const { data, isLoading } = useQuery({
    queryKey: ["attendance-employee-detail", employeeId, params],
    queryFn: () => fetchEmployeeAttendanceDetail(employeeId, params),
  });

  const handleExport = (format: "csv" | "xlsx" | "pdf") => {
    downloadExport(
      employeeAttendanceDetailExportUrl(employeeId, format, params),
      `attendance-detail.${format}`
    );
  };

  const summary = data?.summary;
  const rows = (data?.days ?? []).map((d, i) => ({ ...d, id: i }));

  return (
    <div className="space-y-5">
      {summary && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard label="Working Days" value={`${summary.working_days} / ${summary.expected_working_days}`} icon={CalendarCheck} />
          <StatCard label="Total Hours" value={summary.total_hours} icon={Clock3} tone="blue" />
          <StatCard label="Avg Hours/Day" value={summary.average_hours_per_day} icon={TrendingUp} tone="green" />
          <StatCard
            label="Attendance Rate"
            value={summary.attendance_rate != null ? `${summary.attendance_rate}%` : "—"}
            icon={CalendarCheck}
            tone={summary.attendance_rate != null && summary.attendance_rate < 80 ? "red" : "green"}
          />
          <StatCard label="Late Count" value={summary.late_count} icon={Clock3} tone="amber" />
          <StatCard label="Early Departures" value={summary.early_departure_count} icon={Clock3} tone="amber" />
          <StatCard label="Overtime (hrs)" value={summary.overtime_hours} icon={TrendingUp} tone="slate" />
          <StatCard label="Total Punches" value={summary.total_punches} icon={Fingerprint} tone="brand" />
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-4 w-4 text-slate-400" /> Daily Breakdown
          </CardTitle>
          <ExportButtonGroup onExport={handleExport} />
        </CardHeader>
        <CardContent className="px-0 pb-0 pt-0">
          <DataTable
            dense
            columns={[
              { key: "date", header: "Date", render: (r: EmployeeAttendanceDay & { id: number }) => formatDate(r.date) },
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
              { key: "punch_count", header: "Punches", align: "center" },
              {
                key: "punches",
                header: "Punch Detail",
                render: (r) =>
                  r.punches.length
                    ? r.punches
                        .map(
                          (p) =>
                            `${new Date(p.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} ${p.event}${p.device_name ? ` (${p.device_name})` : ""}`
                        )
                        .join(", ")
                    : "—",
              },
              { key: "is_late", header: "Late", render: (r) => (r.is_late ? <StatusBadge status="PENDING" /> : "—") },
              {
                key: "is_early_departure",
                header: "Early Departure",
                render: (r) => (r.is_early_departure ? <StatusBadge status="REJECTED" /> : "—"),
              },
              { key: "overtime_minutes", header: "Overtime (min)", align: "right" },
            ]}
            data={rows}
            isLoading={isLoading}
            canEdit={false}
            canDelete={false}
          />
        </CardContent>
      </Card>
    </div>
  );
}
