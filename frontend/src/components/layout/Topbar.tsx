import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, ChevronDown, LogOut, Menu, User as UserIcon } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../../store/authStore";
import { fetchNotifications } from "../../api/communication";
import { logout as logoutApi } from "../../api/auth";

interface TopbarProps {
  onMenuClick: () => void;
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const { user, refreshToken, clearAuth } = useAuthStore();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const { data } = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => fetchNotifications({ is_read: false, page: 1 }),
    refetchInterval: 60_000,
  });

  const handleLogout = async () => {
    try {
      if (refreshToken) await logoutApi(refreshToken);
    } catch {
      // ignore — clearing local auth regardless
    }
    clearAuth();
    navigate("/login");
  };

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white/80 px-4 backdrop-blur-sm sm:px-5">
      <button
        onClick={onMenuClick}
        className="rounded-md p-2 text-slate-500 transition-colors hover:bg-slate-100 md:hidden"
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </button>
      <div className="hidden md:block" />
      <div className="flex items-center gap-2 sm:gap-4">
        <button
          onClick={() => navigate("/notifications")}
          className="relative rounded-md p-2 text-slate-500 transition-colors hover:bg-slate-100"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          {!!data?.count && (
            <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-medium text-white ring-2 ring-white">
              {data.count > 9 ? "9+" : data.count}
            </span>
          )}
        </button>

        <div className="relative">
          <button
            onClick={() => setMenuOpen((o) => !o)}
            className="flex items-center gap-2 rounded-md px-1.5 py-1.5 text-sm transition-colors hover:bg-slate-50 sm:px-2"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-slate-200 to-slate-300 text-slate-600">
              <UserIcon className="h-4 w-4" />
            </div>
            <div className="hidden text-left sm:block">
              <p className="text-xs font-medium text-slate-900">
                {user?.first_name || user?.email} {user?.last_name}
              </p>
              <p className="text-[11px] text-slate-500">{user?.role.replaceAll("_", " ")}</p>
            </div>
            <ChevronDown className="hidden h-3.5 w-3.5 text-slate-400 sm:block" />
          </button>

          {menuOpen && (
            <div
              className="absolute right-0 z-10 mt-1 w-48 overflow-hidden rounded-lg border border-slate-200 bg-white py-1 shadow-lg"
              onMouseLeave={() => setMenuOpen(false)}
            >
              <button
                onClick={() => {
                  setMenuOpen(false);
                  navigate("/profile");
                }}
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-slate-700 transition-colors hover:bg-slate-50"
              >
                <UserIcon className="h-4 w-4" /> My Profile
              </button>
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-600 transition-colors hover:bg-red-50"
              >
                <LogOut className="h-4 w-4" /> Log out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
