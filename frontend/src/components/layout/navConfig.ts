import {
  LayoutDashboard,
  Users,
  CalendarDays,
  Clock,
  Building2,
  Settings,
  BarChart3,
  UserCog,
  Network,
  Bell,
  type LucideIcon,
} from "lucide-react";
import type { Role } from "../../types";

export interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  roles?: Role[];
}

// Modules not built yet (Recruitment, Performance, Training, Assets,
// Documents, Announcements, Helpdesk, Disciplinary, Exit Management) are
// deliberately left out of the sidebar rather than shown as "coming soon"
// placeholders. Their routes still exist in App.tsx (redirecting to
// NotFoundPage) as a graceful fallback for any old bookmarked links — add
// the nav entry back here once a module is actually built.
export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard },
  { label: "Notifications", path: "/notifications", icon: Bell },
  { label: "Employees", path: "/employees", icon: Users },
  { label: "Org Chart", path: "/org-chart", icon: Network },
  { label: "Leave", path: "/leave", icon: CalendarDays },
  { label: "Attendance", path: "/attendance", icon: Clock },
  {
    label: "Organization",
    path: "/organization",
    icon: Building2,
    roles: ["SUPER_ADMIN", "HR_MANAGER", "DEPARTMENT_MANAGER"],
  },
  { label: "Reports", path: "/reports", icon: BarChart3, roles: ["SUPER_ADMIN", "HR_MANAGER", "DEPARTMENT_MANAGER"] },
  { label: "Users", path: "/users", icon: UserCog, roles: ["SUPER_ADMIN"] },
  { label: "System Settings", path: "/settings", icon: Settings, roles: ["SUPER_ADMIN"] },
];
