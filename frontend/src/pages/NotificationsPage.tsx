import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, BellOff, Check, CheckCheck, Mail, MessageSquare } from "lucide-react";
import { fetchNotifications, markNotificationRead, type Notification } from "../api/communication";
import { Card, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Select } from "../components/ui/Select";
import { StatCard } from "../components/StatCard";
import { FullPageSpinner } from "../components/ui/Spinner";
import { cn, formatDateTime } from "../lib/utils";

const CHANNEL_META: Record<Notification["channel"], { icon: typeof Bell; label: string; classes: string }> = {
  IN_APP: { icon: Bell, label: "In-App", classes: "bg-brand-100 text-brand-600" },
  EMAIL: { icon: Mail, label: "Email", classes: "bg-purple-100 text-purple-600" },
  SMS: { icon: MessageSquare, label: "SMS", classes: "bg-emerald-100 text-emerald-600" },
};

function groupLabel(dateStr: string): string {
  const date = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);

  const isSameDay = (a: Date, b: Date) =>
    a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();

  if (isSameDay(date, today)) return "Today";
  if (isSameDay(date, yesterday)) return "Yesterday";
  return date.toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" });
}

export function NotificationsPage() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<"all" | "unread">("all");

  const { data, isLoading } = useQuery({
    queryKey: ["notifications", "all", filter],
    queryFn: () => fetchNotifications(filter === "unread" ? { is_read: false, page_size: 100 } : { page_size: 100 }),
  });

  const markReadMutation = useMutation({
    mutationFn: (id: number) => markNotificationRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAllMutation = useMutation({
    mutationFn: async (ids: number[]) => Promise.all(ids.map((id) => markNotificationRead(id))),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const groups = useMemo(() => {
    const map = new Map<string, Notification[]>();
    for (const n of data?.results ?? []) {
      const key = groupLabel(n.created_at);
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(n);
    }
    return Array.from(map.entries());
  }, [data]);

  const unreadCount = data?.results.filter((n) => !n.is_read).length ?? 0;
  const unreadIds = data?.results.filter((n) => !n.is_read).map((n) => n.id) ?? [];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">Notifications</h1>
          <p className="text-sm text-slate-500">Approvals, reminders, and system alerts addressed to you.</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={filter} onChange={(e) => setFilter(e.target.value as "all" | "unread")} className="w-36">
            <option value="all">All</option>
            <option value="unread">Unread</option>
          </Select>
          {unreadCount > 0 && (
            <Button size="sm" variant="outline" onClick={() => markAllMutation.mutate(unreadIds)} loading={markAllMutation.isPending}>
              <CheckCheck className="h-3.5 w-3.5" /> Mark all read
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
        <StatCard label="Unread" value={unreadCount} icon={Bell} tone={unreadCount > 0 ? "amber" : "green"} />
        <StatCard label="Total" value={data?.count ?? 0} icon={CheckCheck} />
      </div>

      {isLoading ? (
        <FullPageSpinner />
      ) : !data?.results.length ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-14 text-slate-400">
            <BellOff className="h-8 w-8" />
            <span className="text-sm">No notifications.</span>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-5">
          {groups.map(([label, items]) => (
            <div key={label}>
              <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</h2>
              <Card>
                <CardContent className="p-0">
                  <ul className="divide-y divide-slate-100">
                    {items.map((n) => (
                      <NotificationRow key={n.id} notification={n} onMarkRead={() => markReadMutation.mutate(n.id)} />
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function NotificationRow({ notification, onMarkRead }: { notification: Notification; onMarkRead: () => void }) {
  const { icon: Icon, label, classes } = CHANNEL_META[notification.channel] ?? CHANNEL_META.IN_APP;

  return (
    <li className={cn("flex items-start gap-3 px-4 py-3 transition-colors", !notification.is_read && "bg-brand-50/40")}>
      <div className={cn("mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full", classes)}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1">
          <div className="flex items-center gap-2">
            <p className={cn("text-sm", notification.is_read ? "text-slate-600" : "font-semibold text-slate-900")}>
              {notification.title}
            </p>
            <span className={cn("rounded-full px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide", classes)}>
              {label}
            </span>
          </div>
          <span className="shrink-0 text-xs text-slate-400">{formatDateTime(notification.created_at)}</span>
        </div>
        <p className="mt-0.5 text-sm text-slate-500">{notification.body}</p>
      </div>
      {!notification.is_read && (
        <Button size="sm" variant="ghost" onClick={onMarkRead} title="Mark as read">
          <Check className="h-3.5 w-3.5" />
        </Button>
      )}
    </li>
  );
}
