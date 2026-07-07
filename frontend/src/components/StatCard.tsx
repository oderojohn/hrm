import { type LucideIcon } from "lucide-react";
import { Card } from "./ui/Card";
import { cn } from "../lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: LucideIcon;
  tone?: "brand" | "green" | "amber" | "red" | "slate" | "blue";
}

const toneClasses: Record<NonNullable<StatCardProps["tone"]>, string> = {
  brand: "bg-brand-50 text-brand-600",
  green: "bg-emerald-50 text-emerald-600",
  amber: "bg-amber-50 text-amber-600",
  red: "bg-red-50 text-red-600",
  slate: "bg-slate-100 text-slate-600",
  blue: "bg-sky-50 text-sky-600",
};

export function StatCard({ label, value, icon: Icon, tone = "brand" }: StatCardProps) {
  return (
    <Card className="flex items-center gap-4 p-4 transition-shadow hover:shadow-md">
      {Icon && (
        <div className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-lg", toneClasses[tone])}>
          <Icon className="h-5 w-5" />
        </div>
      )}
      <div className="min-w-0">
        <p className="truncate text-xs font-medium text-slate-500">{label}</p>
        <p className="text-xl font-semibold tracking-tight text-slate-900">{value}</p>
      </div>
    </Card>
  );
}
