import { type HTMLAttributes } from "react";
import { cn } from "../../lib/utils";

type Tone = "slate" | "green" | "amber" | "red" | "blue";

const toneClasses: Record<Tone, string> = {
  slate: "bg-slate-100 text-slate-700",
  green: "bg-emerald-100 text-emerald-700",
  amber: "bg-amber-100 text-amber-700",
  red: "bg-red-100 text-red-700",
  blue: "bg-blue-100 text-blue-700",
};

export function Badge({
  className,
  tone = "slate",
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        toneClasses[tone],
        className
      )}
      {...props}
    />
  );
}

const STATUS_TONE: Record<string, Tone> = {
  ACTIVE: "green",
  APPROVED: "green",
  COMPLETED: "green",
  RESOLVED: "green",
  SUCCESS: "green",
  PRESENT: "green",
  CLOSED: "slate",
  PENDING: "amber",
  IN_PROGRESS: "amber",
  OPEN: "amber",
  LATE: "amber",
  ASSIGNED: "blue",
  SCHEDULED: "blue",
  ON_LEAVE: "blue",
  SUPERVISOR: "amber",
  HR: "amber",
  DONE: "slate",
  SKIPPED: "slate",
  OFF: "slate",
  REJECTED: "red",
  CANCELLED: "red",
  TERMINATED: "red",
  SUSPENDED: "red",
  FAILED: "red",
  ABSENT: "red",
};

export function StatusBadge({ status }: { status: string }) {
  const tone = STATUS_TONE[status] ?? "slate";
  return <Badge tone={tone}>{status.replaceAll("_", " ")}</Badge>;
}
