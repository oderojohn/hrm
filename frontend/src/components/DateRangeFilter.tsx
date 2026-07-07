import { useState } from "react";
import { Select } from "./ui/Select";
import { Input } from "./ui/Input";

export type RangeMode = "week" | "month" | "custom";

export interface DateRangeValue {
  mode: RangeMode;
  start?: string;
  end?: string;
}

interface DateRangeFilterProps {
  value: DateRangeValue;
  onChange: (value: DateRangeValue) => void;
}

export function useDateRangeFilter(initial: RangeMode = "month") {
  return useState<DateRangeValue>({ mode: initial });
}

export function DateRangeFilter({ value, onChange }: DateRangeFilterProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Select
        value={value.mode}
        onChange={(e) => onChange({ mode: e.target.value as RangeMode, start: value.start, end: value.end })}
        className="w-36"
      >
        <option value="week">This Week</option>
        <option value="month">This Month</option>
        <option value="custom">Custom Range</option>
      </Select>
      {value.mode === "custom" && (
        <>
          <Input
            type="date"
            value={value.start ?? ""}
            onChange={(e) => onChange({ ...value, start: e.target.value })}
            className="w-40"
          />
          <span className="text-sm text-slate-400">to</span>
          <Input
            type="date"
            value={value.end ?? ""}
            onChange={(e) => onChange({ ...value, end: e.target.value })}
            className="w-40"
          />
        </>
      )}
    </div>
  );
}

/** Converts a DateRangeValue into query params for the analytics endpoint. */
export function toAnalyticsParams(value: DateRangeValue) {
  if (value.mode === "custom" && value.start && value.end) {
    return { start: value.start, end: value.end };
  }
  return { period: value.mode === "custom" ? "month" : value.mode } as { period: "week" | "month" };
}

/** Converts a DateRangeValue into date_from/date_to params for record list endpoints. */
export function toRecordFilterParams(value: DateRangeValue) {
  if (value.mode === "custom" && value.start && value.end) {
    return { date_from: value.start, date_to: value.end };
  }
  const today = new Date();
  if (value.mode === "week") {
    const start = new Date(today);
    start.setDate(today.getDate() - today.getDay());
    return { date_from: start.toISOString().slice(0, 10), date_to: today.toISOString().slice(0, 10) };
  }
  const start = new Date(today.getFullYear(), today.getMonth(), 1);
  return { date_from: start.toISOString().slice(0, 10), date_to: today.toISOString().slice(0, 10) };
}
