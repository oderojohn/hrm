import {
  LayoutDashboard,
  Users,
  CalendarDays,
  Clock,
  Building2,
  Briefcase,
  TrendingUp,
  GraduationCap,
  Laptop,
  FileText,
  Megaphone,
  LifeBuoy,
  ShieldAlert,
  LogOut as LogOutIcon,
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
  { label: "Recruitment", path: "/recruitment", icon: Briefcase, roles: ["SUPER_ADMIN", "HR_MANAGER"] },
  { label: "Performance", path: "/performance", icon: TrendingUp },
  { label: "Training", path: "/training", icon: GraduationCap },
  { label: "Assets", path: "/assets", icon: Laptop, roles: ["SUPER_ADMIN", "HR_MANAGER"] },
  { label: "Documents", path: "/documents", icon: FileText },
  { label: "Announcements", path: "/announcements", icon: Megaphone },
  { label: "Helpdesk", path: "/helpdesk", icon: LifeBuoy },
  { label: "Disciplinary", path: "/disciplinary", icon: ShieldAlert },
  { label: "Exit Management", path: "/exit-management", icon: LogOutIcon, roles: ["SUPER_ADMIN", "HR_MANAGER"] },
  { label: "Reports", path: "/reports", icon: BarChart3, roles: ["SUPER_ADMIN", "HR_MANAGER", "DEPARTMENT_MANAGER"] },
  { label: "Users", path: "/users", icon: UserCog, roles: ["SUPER_ADMIN"] },
  { label: "System Settings", path: "/settings", icon: Settings, roles: ["SUPER_ADMIN"] },
];
