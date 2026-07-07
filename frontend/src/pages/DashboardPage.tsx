import { useQuery } from "@tanstack/react-query";
import { Users, UserCheck, UserX, CalendarClock, CalendarDays, Clock3, Cake } from "lucide-react";
import { fetchDashboard, type ManagementDashboard, type PersonalDashboard } from "../api/reports";
import { useAuthStore } from "../store/authStore";
import { StatCard } from "../components/StatCard";
import { TrendChart } from "../components/charts/TrendChart";
import { DistributionChart } from "../components/charts/DistributionChart";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { FullPageSpinner } from "../components/ui/Spinner";
import { formatDate } from "../lib/utils";

function isManagementDashboard(data: ManagementDashboard | PersonalDashboard): data is ManagementDashboard {
  return "total_employees" in data;
}

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboard });

  if (isLoading || !data) return <FullPageSpinner />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">
          Welcome back, {user?.first_name || user?.email}
        </h1>
        <p className="text-sm text-slate-500">Here's what's happening today.</p>
      </div>

      {isManagementDashboard(data) ? (
        <ManagementView data={data} />
      ) : (
        <PersonalView data={data} />
      )}
    </div>
  );
}

function ManagementView({ data }: { data: ManagementDashboard }) {
  return (
    <>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        <StatCard label="Total Employees" value={data.total_employees} icon={Users} />
        <StatCard label="Active" value={data.active_employees} icon={UserCheck} tone="green" />
        <StatCard label="Present Today" value={data.present_today} icon={UserCheck} tone="blue" />
        <StatCard label="Absent Today" value={data.absent_today} icon={UserX} tone="red" />
        <StatCard label="On Leave" value={data.on_leave_today} icon={CalendarClock} tone="amber" />
        <StatCard label="Pending Leave" value={data.pending_leave_requests} icon={Clock3} tone="amber" />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <TrendChart title="Employee Growth (12 months)" data={data.charts.employee_growth} xKey="month" yKey="count" />
        <TrendChart
          title="Attendance Trend (30 days)"
          data={data.charts.attendance_trends}
          xKey="date"
          yKey="count"
          color="#10b981"
        />
        <TrendChart
          title="Leave Trend (12 months)"
          data={data.charts.leave_trends}
          xKey="month"
          yKey="count"
          color="#f59e0b"
        />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:contents">
          <DistributionChart
            title="Department Distribution"
            data={data.charts.department_distribution}
            nameKey="department__name"
            valueKey="count"
          />
          <DistributionChart
            title="Gender Distribution"
            data={data.charts.gender_distribution}
            nameKey="gender"
            valueKey="count"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <ListCard
          title="Birthdays Today"
          icon={Cake}
          items={data.birthdays_today.map((e) => ({ id: e.id, primary: e.full_name, secondary: e.employee_number }))}
          empty="No birthdays today"
        />
        <ListCard
          title="New Employees (30 days)"
          icon={Users}
          items={data.new_employees.map((e) => ({
            id: e.id,
            primary: e.full_name,
            secondary: formatDate(e.employment_date),
          }))}
          empty="No new employees"
        />
        <ListCard
          title="Contract Expiry Alerts"
          icon={CalendarClock}
          items={data.contract_expiry_alerts.map((e) => ({
            id: e.id,
            primary: e.full_name,
            secondary: formatDate(e.contract_end_date),
          }))}
          empty="No upcoming contract expiries"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Announcements</CardTitle>
        </CardHeader>
        <CardContent>
          {data.recent_announcements.length === 0 ? (
            <p className="text-sm text-slate-400">No announcements yet.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {data.recent_announcements.map((a) => (
                <li key={a.id} className="flex items-center justify-between py-2 text-sm">
                  <span className="text-slate-700">{a.title}</span>
                  <span className="text-slate-400">{formatDate(a.published_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </>
  );
}

function PersonalView({ data }: { data: PersonalDashboard }) {
  return (
    <>
      {data.leave_balances.length > 0 && (
        <div>
          <h2 className="mb-2 text-sm font-semibold text-slate-700">My Leave Balance</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
            {data.leave_balances.map((b) => (
              <StatCard
                key={b.leave_type}
                label={b.leave_type}
                value={`${b.remaining_days} ${b.remaining_days === 1 ? "day" : "days"}`}
                icon={CalendarDays}
                tone={b.remaining_days <= 0 ? "red" : "green"}
              />
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Clocked In" value={data.clocked_in_today ? "Yes" : "No"} icon={Clock3} tone={data.clocked_in_today ? "green" : "slate"} />
        <StatCard label="Clocked Out" value={data.clocked_out_today ? "Yes" : "No"} icon={Clock3} />
        <StatCard label="Pending Leave" value={data.pending_leave_requests} icon={CalendarClock} tone="amber" />
        <StatCard label="Next Leave" value={data.next_approved_leave ? formatDate(data.next_approved_leave) : "—"} icon={CalendarClock} />
      </div>

      {data.leave_balances.length === 0 && (
        <Card>
          <CardContent className="text-sm text-slate-400">
            No leave balances recorded yet. Contact HR if you believe this is a mistake.
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Recent Announcements</CardTitle>
        </CardHeader>
        <CardContent>
          {data.recent_announcements.length === 0 ? (
            <p className="text-sm text-slate-400">No announcements yet.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {data.recent_announcements.map((a) => (
                <li key={a.id} className="py-2 text-sm text-slate-700">
                  {a.title}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </>
  );
}

function ListCard({
  title,
  icon: Icon,
  items,
  empty,
}: {
  title: string;
  icon: typeof Cake;
  items: Array<{ id: number; primary: string; secondary: string }>;
  empty: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-slate-400" /> {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-slate-400">{empty}</p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {items.map((item) => (
              <li key={item.id} className="flex items-center justify-between py-2 text-sm">
                <span className="text-slate-700">{item.primary}</span>
                <span className="text-slate-400">{item.secondary}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
