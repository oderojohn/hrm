import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Building2,
  Car,
  ChefHat,
  ChevronDown,
  ChevronRight,
  DoorOpen,
  Laptop,
  Package,
  ShieldCheck,
  Sparkles,
  TreeDeciduous,
  UserCog,
  Users,
  UtensilsCrossed,
  Wallet,
  type LucideIcon,
} from "lucide-react";
import { Link } from "react-router-dom";
import { fetchAllEmployeesForSelect, type EmployeeListItem } from "../api/employees";
import { departmentsApi, type Department } from "../api/organization";
import { FullPageSpinner } from "../components/ui/Spinner";
import { cn } from "../lib/utils";

const DEPARTMENT_ICONS: Record<string, LucideIcon> = {
  "Executive Management": ShieldCheck,
  Kitchen: ChefHat,
  "Food & Beverage": UtensilsCrossed,
  "Front Office": DoorOpen,
  Housekeeping: Sparkles,
  Stores: Package,
  Finance: Wallet,
  IT: Laptop,
  "Grounds & Maintenance": TreeDeciduous,
  Transport: Car,
};

interface DivisionNode {
  department: Department | null; // null = "Unassigned" bucket
  employees: EmployeeListItem[];
}

export function OrgChartPage() {
  const { data: employees, isLoading: employeesLoading } = useQuery({
    queryKey: ["employees-org-chart"],
    queryFn: fetchAllEmployeesForSelect,
  });
  const { data: departmentsPage, isLoading: departmentsLoading } = useQuery({
    queryKey: ["departments-org-chart"],
    queryFn: () => departmentsApi.list({ page_size: 200 }),
  });

  const gm = useMemo(() => employees?.find((e) => e.position_title === "General Manager"), [employees]);
  const hr = useMemo(() => employees?.find((e) => e.position_title === "HR Manager"), [employees]);

  const divisions = useMemo<DivisionNode[]>(() => {
    if (!employees || !departmentsPage) return [];
    const excludedIds = new Set([gm?.id, hr?.id].filter((id): id is number => id != null));

    const byDeptName = new Map<string, EmployeeListItem[]>();
    const unassigned: EmployeeListItem[] = [];
    for (const e of employees) {
      if (excludedIds.has(e.id)) continue;
      if (!e.department_name) {
        unassigned.push(e);
        continue;
      }
      if (!byDeptName.has(e.department_name)) byDeptName.set(e.department_name, []);
      byDeptName.get(e.department_name)!.push(e);
    }

    const nodes: DivisionNode[] = departmentsPage.results
      .filter((d) => d.is_active && d.name !== "Human Resources")
      .map((d) => ({ department: d, employees: byDeptName.get(d.name) ?? [] }))
      .sort((a, b) => b.employees.length - a.employees.length);

    if (unassigned.length) nodes.push({ department: null, employees: unassigned });
    return nodes;
  }, [employees, departmentsPage, gm, hr]);

  const branchName = employees?.find((e) => e.branch_name)?.branch_name ?? "Organization";

  if (employeesLoading || departmentsLoading) return <FullPageSpinner />;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">Organizational Chart</h1>
        <p className="text-sm text-slate-500">
          Emboita Hotel → General Manager → HR Manager → Divisions. Tap a division to see its team.
        </p>
      </div>

      <div className="space-y-1.5 rounded-lg border border-slate-200 bg-white p-3 sm:p-4">
        <HierarchyRow icon={Building2} label={branchName} sublabel={`${employees?.length ?? 0} employees`} depth={0} />
        {gm ? (
          <HierarchyRow icon={UserCog} label={gm.full_name} sublabel="General Manager" depth={1} href={`/employees/${gm.id}`} />
        ) : (
          <HierarchyRow icon={UserCog} label="Not assigned" sublabel="General Manager" depth={1} muted />
        )}
        {hr ? (
          <HierarchyRow icon={UserCog} label={hr.full_name} sublabel="HR Manager" depth={2} href={`/employees/${hr.id}`} />
        ) : (
          <HierarchyRow icon={UserCog} label="Not assigned" sublabel="HR Manager" depth={2} muted />
        )}

        {divisions.map((node) => (
          <DivisionGroup key={node.department?.id ?? "unassigned"} node={node} />
        ))}
      </div>
    </div>
  );
}

const INDENT_PX = 22;

function HierarchyRow({
  icon: Icon,
  label,
  sublabel,
  depth,
  href,
  muted,
  badge,
  onClick,
  expandState,
}: {
  icon: LucideIcon;
  label: string;
  sublabel?: string;
  depth: number;
  href?: string;
  muted?: boolean;
  badge?: number;
  onClick?: () => void;
  expandState?: "expanded" | "collapsed" | "none";
}) {
  const content = (
    <div
      className={cn(
        "flex items-center gap-2.5 rounded-lg px-3 py-2.5 transition-colors",
        muted ? "bg-slate-800/60" : "bg-slate-900 hover:bg-slate-800",
        onClick && "cursor-pointer"
      )}
      style={{ marginLeft: depth * INDENT_PX }}
    >
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-500/15 text-brand-300">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className={cn("truncate text-sm font-semibold", muted ? "text-slate-400" : "text-white")}>{label}</p>
        {sublabel && <p className="truncate text-xs text-brand-300/90">{sublabel}</p>}
      </div>
      {badge != null && (
        <span className="shrink-0 rounded-full bg-brand-500 px-2 py-0.5 text-[11px] font-semibold text-slate-900">{badge}</span>
      )}
      {expandState && expandState !== "none" && (
        <span className="shrink-0 text-slate-400">
          {expandState === "expanded" ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </span>
      )}
    </div>
  );

  if (href) {
    return (
      <Link to={href} style={{ display: "block" }}>
        {content}
      </Link>
    );
  }
  if (onClick) {
    return (
      <button onClick={onClick} className="block w-full text-left">
        {content}
      </button>
    );
  }
  return content;
}

function DivisionGroup({ node }: { node: DivisionNode }) {
  const [expanded, setExpanded] = useState(false);
  const name = node.department?.name ?? "Unassigned";
  const headName = node.department?.head_name;
  const hasEmployees = node.employees.length > 0;
  const Icon = DEPARTMENT_ICONS[name] ?? Users;

  return (
    <>
      <HierarchyRow
        icon={Icon}
        label={name}
        sublabel={headName ? `Head: ${headName}` : "No head assigned"}
        depth={3}
        badge={node.employees.length}
        expandState={hasEmployees ? (expanded ? "expanded" : "collapsed") : "none"}
        onClick={hasEmployees ? () => setExpanded((v) => !v) : undefined}
      />
      {expanded &&
        hasEmployees &&
        node.employees.map((emp) => (
          <HierarchyRow
            key={emp.id}
            icon={Users}
            label={emp.full_name}
            sublabel={emp.position_title ?? "—"}
            depth={4}
            href={`/employees/${emp.id}`}
          />
        ))}
    </>
  );
}
