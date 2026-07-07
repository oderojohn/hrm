import { NavLink } from "react-router-dom";
import { X } from "lucide-react";
import { NAV_ITEMS } from "./navConfig";
import { useAuthStore } from "../../store/authStore";
import { cn } from "../../lib/utils";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const user = useAuthStore((s) => s.user);

  const items = NAV_ITEMS.filter((item) => !item.roles || (user && item.roles.includes(user.role)));

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/40 backdrop-blur-[1px] transition-opacity md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 shrink-0 transform flex-col border-r border-slate-800 bg-slate-900 shadow-xl transition-transform duration-200 ease-in-out",
          "md:static md:z-auto md:w-60 md:translate-x-0 md:shadow-none",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-14 items-center justify-between gap-2 border-b border-slate-800 px-5">
          <div className="rounded-md bg-white px-2 py-1">
            <img src="/emboita-logo.png" alt="Emboita Hotel" className="h-6 w-auto" />
          </div>
          <span className="sr-only">Emboita Hotel HRM</span>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-800 hover:text-white md:hidden"
            aria-label="Close menu"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
          {items.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-md border-l-2 px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "border-brand-500 bg-slate-800 text-brand-300"
                    : "border-transparent text-slate-400 hover:bg-slate-800 hover:text-white"
                )
              }
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
}
