import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Briefcase, Building2, Hash } from "lucide-react";
import { fetchEmployeeAttendanceDetail } from "../api/attendance";
import { toAnalyticsParams, DateRangeFilter, useDateRangeFilter } from "../components/DateRangeFilter";
import { ProfileHeaderBanner } from "../components/ProfileHeaderBanner";
import { EmployeeAttendanceDetail } from "../components/attendance/EmployeeAttendanceDetail";
import { FullPageSpinner } from "../components/ui/Spinner";

export function EmployeeAttendanceDetailPage() {
  const { id } = useParams();
  const employeeId = Number(id);
  const [range, setRange] = useDateRangeFilter("month");

  const { data, isLoading } = useQuery({
    queryKey: ["attendance-employee-detail-header", employeeId, toAnalyticsParams(range)],
    queryFn: () => fetchEmployeeAttendanceDetail(employeeId, toAnalyticsParams(range)),
    enabled: !Number.isNaN(employeeId),
  });

  if (isLoading || !data) return <FullPageSpinner />;

  return (
    <div className="space-y-5">
      <Link
        to="/attendance"
        className="inline-flex items-center gap-1 text-sm text-slate-500 transition-colors hover:text-slate-700"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Attendance
      </Link>

      <ProfileHeaderBanner
        name={data.employee.full_name}
        photoUrl={data.employee.photo}
        metaItems={[
          { icon: Hash, label: data.employee.employee_number },
          { icon: Briefcase, label: data.employee.work_shift_name ?? "No shift assigned" },
          { icon: Building2, label: data.employee.department_name ?? "No department" },
        ]}
      />

      <div className="flex justify-end">
        <DateRangeFilter value={range} onChange={setRange} />
      </div>

      <EmployeeAttendanceDetail employeeId={employeeId} range={range} />
    </div>
  );
}
