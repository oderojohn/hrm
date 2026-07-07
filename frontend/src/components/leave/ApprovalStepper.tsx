import { Check, Clock, Minus, X } from "lucide-react";
import type { LeaveApprovalStep } from "../../api/leave";
import { cn, formatDateTime } from "../../lib/utils";

const STATUS_STYLE: Record<LeaveApprovalStep["status"], { icon: typeof Check; classes: string }> = {
  APPROVED: { icon: Check, classes: "bg-emerald-100 text-emerald-600" },
  REJECTED: { icon: X, classes: "bg-red-100 text-red-600" },
  SKIPPED: { icon: Minus, classes: "bg-slate-100 text-slate-400" },
  PENDING: { icon: Clock, classes: "bg-amber-100 text-amber-600" },
};

export function ApprovalStepper({ steps }: { steps: LeaveApprovalStep[] }) {
  const ordered = [...steps].sort((a, b) => a.step_order - b.step_order);

  return (
    <ol className="space-y-4">
      {ordered.map((step, index) => {
        const { icon: Icon, classes } = STATUS_STYLE[step.status];
        const isLast = index === ordered.length - 1;
        return (
          <li key={step.id} className="relative flex gap-3 pb-1">
            {!isLast && <span className="absolute left-4 top-8 h-full w-px bg-slate-200" />}
            <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-full", classes)}>
              <Icon className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1 pt-1">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-slate-800">{step.name || step.resolver_type}</p>
                <span className="text-xs font-medium text-slate-400">{step.status}</span>
              </div>
              {step.approver_name && <p className="text-xs text-slate-500">Approver: {step.approver_name}</p>}
              {step.comment && <p className="mt-0.5 text-xs text-slate-500 italic">"{step.comment}"</p>}
              {step.acted_at && (
                <p className="mt-0.5 text-xs text-slate-400">
                  {step.acted_by_name ? `${step.acted_by_name} · ` : ""}
                  {formatDateTime(step.acted_at)}
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
