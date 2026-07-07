import { useState, type ReactNode } from "react";
import { useParams, Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Fingerprint,
  User as UserIcon,
  Briefcase,
  GraduationCap,
  CalendarDays,
  Clock,
  TrendingUp,
  ShieldAlert,
  Laptop,
  Hash,
  Building2,
  Network,
  type LucideIcon,
} from "lucide-react";
import { fetchEmployeeProfile, pushEmployeeToDevice } from "../api/employees";
import { extractErrorMessage } from "../api/client";
import { FullPageSpinner } from "../components/ui/Spinner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Tabs } from "../components/ui/Tabs";
import { StatusBadge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { AccountPanel } from "../components/employees/AccountPanel";
import { ProfileHeaderBanner } from "../components/ProfileHeaderBanner";
import { useAuthStore, isHRManagerOrAbove } from "../store/authStore";
import { cn, formatDate, formatDateTime } from "../lib/utils";

export function EmployeeProfilePage() {
  const { id } = useParams();
  const employeeId = Number(id);
  const currentUser = useAuthStore((s) => s.user);
  const canManage = isHRManagerOrAbove(currentUser);
  const [pushMessage, setPushMessage] = useState<string | null>(null);

  const { data: employee, isLoading } = useQuery({
    queryKey: ["employee-profile", employeeId],
    queryFn: () => fetchEmployeeProfile(employeeId),
    enabled: !Number.isNaN(employeeId),
  });

  const pushMutation = useMutation({
    mutationFn: () => pushEmployeeToDevice(employeeId),
    onSuccess: (data) => setPushMessage(`Pushed to device as ID ${data.device_user_id}.`),
    onError: (err) => setPushMessage(extractErrorMessage(err)),
  });

  if (isLoading || !employee) return <FullPageSpinner />;

  return (
    <div className="space-y-5">
      <Link
        to="/employees"
        className="inline-flex items-center gap-1 text-sm text-slate-500 transition-colors hover:text-slate-700"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Employees
      </Link>

      <ProfileHeaderBanner
        name={employee.full_name}
        photoUrl={employee.photo}
        metaItems={[
          { icon: Hash, label: employee.employee_number },
          { icon: Briefcase, label: employee.position_title ?? "No position" },
          { icon: Building2, label: employee.department_name ?? "No department" },
        ]}
        badge={<StatusBadge status={employee.employment_status} />}
        actions={
          canManage && (
            <div className="text-right">
              <Button size="sm" variant="outline" onClick={() => pushMutation.mutate()} loading={pushMutation.isPending}>
                <Fingerprint className="h-3.5 w-3.5" />
                {employee.device_user_id ? "Re-push to Device" : "Push to Device"}
              </Button>
              {pushMessage && <p className="mt-1 text-xs text-slate-500">{pushMessage}</p>}
            </div>
          )
        }
      />

      {canManage && <AccountPanel employee={employee} />}

      <Tabs
        tabs={[
          { key: "personal", label: "Personal", content: <PersonalTab employee={employee} /> },
          { key: "employment", label: "Employment", content: <EmploymentTab employee={employee} /> },
          { key: "education", label: "Education & Certifications", content: <EducationTab employee={employee} /> },
          {
            key: "leave",
            label: "Leave History",
            content: (
              <ListTab icon={CalendarDays} items={employee.leave_history} renderItem={renderLeave} empty="No leave history." />
            ),
          },
          {
            key: "attendance",
            label: "Attendance",
            content: (
              <ListTab
                icon={Clock}
                items={employee.attendance_history}
                renderItem={renderAttendance}
                empty="No attendance records."
              />
            ),
          },
          {
            key: "performance",
            label: "Performance",
            content: (
              <ListTab
                icon={TrendingUp}
                items={employee.performance_reviews}
                renderItem={renderPerformance}
                empty="No performance reviews."
              />
            ),
          },
          {
            key: "disciplinary",
            label: "Disciplinary",
            content: (
              <ListTab
                icon={ShieldAlert}
                items={employee.disciplinary_records}
                renderItem={renderDisciplinary}
                empty="No disciplinary records."
              />
            ),
          },
          {
            key: "training",
            label: "Training",
            content: (
              <ListTab
                icon={GraduationCap}
                items={employee.training_records}
                renderItem={renderTraining}
                empty="No training records."
              />
            ),
          },
          {
            key: "assets",
            label: "Assets",
            content: (
              <ListTab icon={Laptop} items={employee.assigned_assets} renderItem={renderAsset} empty="No assets assigned." />
            ),
          },
        ]}
      />
    </div>
  );
}

function InfoGrid({ items }: { items: { label: string; value: string }[] }) {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {items.map(({ label, value }) => (
        <div key={label}>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
          <p className={cn("mt-1 text-sm", value ? "font-medium text-slate-800" : "text-slate-400")}>{value || "Not set"}</p>
        </div>
      ))}
    </div>
  );
}

function SectionCard({
  icon: Icon,
  title,
  children,
}: {
  icon: LucideIcon;
  title: string;
  children: ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-slate-400" /> {title}
        </CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function PersonalTab({ employee }: { employee: Awaited<ReturnType<typeof fetchEmployeeProfile>> }) {
  return (
    <div className="space-y-4">
      <SectionCard icon={UserIcon} title="Personal Information">
        <InfoGrid
          items={[
            { label: "Gender", value: employee.gender },
            { label: "Date of Birth", value: formatDate(employee.date_of_birth) },
            { label: "National ID", value: employee.national_id ?? "" },
            { label: "Passport Number", value: employee.passport_number },
            { label: "Nationality", value: employee.nationality },
            { label: "Marital Status", value: employee.marital_status },
            { label: "Email", value: employee.email },
            { label: "Phone", value: employee.phone_number },
            { label: "Alternative Phone", value: employee.alternative_phone },
            { label: "Address", value: employee.address },
            { label: "County", value: employee.county },
            { label: "Sub County", value: employee.sub_county },
          ]}
        />
      </SectionCard>
      <SectionCard icon={ShieldAlert} title="Emergency Contact">
        <InfoGrid
          items={[
            { label: "Name", value: employee.emergency_contact_name },
            { label: "Phone", value: employee.emergency_contact_phone },
            { label: "Relationship", value: employee.emergency_contact_relationship },
          ]}
        />
      </SectionCard>
    </div>
  );
}

function EmploymentTab({ employee }: { employee: Awaited<ReturnType<typeof fetchEmployeeProfile>> }) {
  return (
    <div className="space-y-4">
      <SectionCard icon={Briefcase} title="Employment Information">
        <InfoGrid
          items={[
            { label: "Employee Number", value: employee.employee_number },
            { label: "Department", value: employee.department_name ?? "" },
            { label: "Position", value: employee.position_title ?? "" },
            { label: "Branch", value: employee.branch_name ?? "" },
            { label: "Employment Type", value: employee.employment_type },
            { label: "Employment Date", value: formatDate(employee.employment_date) },
            { label: "Probation End Date", value: formatDate(employee.probation_end_date) },
            { label: "Contract End Date", value: formatDate(employee.contract_end_date) },
          ]}
        />
      </SectionCard>
      <SectionCard icon={Network} title="Reporting & Statutory">
        <InfoGrid
          items={[
            { label: "Reporting Manager", value: employee.reporting_manager_name ?? "" },
            { label: "KRA PIN", value: employee.kra_pin },
            { label: "NSSF Number", value: employee.nssf_number },
            { label: "SHIF/NHIF Number", value: employee.shif_number },
          ]}
        />
      </SectionCard>
    </div>
  );
}

function EducationTab({ employee }: { employee: Awaited<ReturnType<typeof fetchEmployeeProfile>> }) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <SectionCard icon={GraduationCap} title="Education">
        {employee.education.length === 0 ? (
          <EmptyState label="No education records." />
        ) : (
          <ul className="space-y-3">
            {employee.education.map((e, i) => (
              <li key={i} className="rounded-lg border border-slate-100 bg-slate-50/60 px-3 py-2 text-sm">
                <p className="font-medium text-slate-800">{String(e.qualification)}</p>
                <p className="text-slate-500">{String(e.institution)}</p>
              </li>
            ))}
          </ul>
        )}
      </SectionCard>
      <SectionCard icon={Fingerprint} title="Certifications">
        {employee.certifications.length === 0 ? (
          <EmptyState label="No certifications." />
        ) : (
          <ul className="space-y-3">
            {employee.certifications.map((c, i) => (
              <li key={i} className="rounded-lg border border-slate-100 bg-slate-50/60 px-3 py-2 text-sm">
                <p className="font-medium text-slate-800">{String(c.name)}</p>
                <p className="text-slate-500">{String(c.issuing_body)}</p>
              </li>
            ))}
          </ul>
        )}
      </SectionCard>
    </div>
  );
}

function EmptyState({ label }: { label: string }) {
  return <p className="py-2 text-sm text-slate-400">{label}</p>;
}

const KNOWN_STATUSES = new Set([
  "PENDING",
  "APPROVED",
  "REJECTED",
  "CANCELLED",
  "COMPLETED",
  "RETURNED",
  "OPEN",
  "UNDER_REVIEW",
  "RESOLVED",
  "CLOSED",
  "ENROLLED",
  "ATTENDED",
  "ABSENT",
  "DRAFT",
  "SUBMITTED",
  "ACKNOWLEDGED",
]);

function ListTab({
  icon: Icon,
  items,
  renderItem,
  empty,
}: {
  icon: LucideIcon;
  items: Array<Record<string, unknown>>;
  renderItem: (item: Record<string, unknown>) => { primary: string; secondary: string };
  empty: string;
}) {
  return (
    <Card>
      <CardContent className={items.length ? "p-0" : undefined}>
        {items.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-10 text-slate-400">
            <Icon className="h-7 w-7" />
            <span className="text-sm">{empty}</span>
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {items.map((item, i) => {
              const { primary, secondary } = renderItem(item);
              return (
                <li key={i} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                  <span className="flex items-center gap-2.5 text-slate-700">
                    <Icon className="h-4 w-4 shrink-0 text-slate-400" />
                    {primary}
                  </span>
                  {KNOWN_STATUSES.has(secondary) ? (
                    <StatusBadge status={secondary} />
                  ) : (
                    <span className="shrink-0 text-slate-400">{secondary}</span>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function renderLeave(item: Record<string, unknown>) {
  return {
    primary: `${item.leave_type_name} (${item.start_date} → ${item.end_date})`,
    secondary: String(item.status),
  };
}

function renderAttendance(item: Record<string, unknown>) {
  return {
    primary: String(item.date),
    secondary: `${item.clock_in ? formatDateTime(String(item.clock_in)) : "—"} → ${item.clock_out ? formatDateTime(String(item.clock_out)) : "—"}`,
  };
}

function renderPerformance(item: Record<string, unknown>) {
  return {
    primary: `${item.review_type} review (${item.review_period_start} → ${item.review_period_end})`,
    secondary: String(item.status),
  };
}

function renderDisciplinary(item: Record<string, unknown>) {
  return { primary: String(item.title), secondary: String(item.status) };
}

function renderTraining(item: Record<string, unknown>) {
  return { primary: `Session #${item.session}`, secondary: String(item.status) };
}

function renderAsset(item: Record<string, unknown>) {
  return { primary: String(item.asset_name ?? item.asset), secondary: formatDate(String(item.assigned_date)) };
}
