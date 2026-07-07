import { ArrowDown, ArrowUp, ArrowUpDown, Inbox } from "lucide-react";
import type { ColumnDef } from "./types";
import { Spinner } from "../ui/Spinner";
import { cn } from "../../lib/utils";

export interface SortState {
  key: string;
  direction: "asc" | "desc";
}

interface DataTableProps<T extends { id: number }> {
  columns: ColumnDef<T>[];
  data: T[];
  isLoading?: boolean;
  onEdit?: (row: T) => void;
  onDelete?: (row: T) => void;
  canEdit?: boolean;
  canDelete?: boolean;
  /** Spreadsheet styling: full cell grid lines, zebra rows, row numbers, sticky header. */
  dense?: boolean;
  rowNumberStart?: number;
  sort?: SortState | null;
  onSortChange?: (key: string) => void;
}

export function DataTable<T extends { id: number }>({
  columns,
  data,
  isLoading,
  onEdit,
  onDelete,
  canEdit,
  canDelete,
  dense,
  rowNumberStart = 1,
  sort,
  onSortChange,
}: DataTableProps<T>) {
  const showActions = canEdit || canDelete;
  const totalCols = columns.length + (dense ? 1 : 0) + (showActions ? 1 : 0);

  const alignClass = (align?: ColumnDef<T>["align"]) =>
    align === "right" ? "text-right" : align === "center" ? "text-center" : "text-left";

  return (
    <div
      className={cn(
        "overflow-x-auto rounded-lg border border-slate-200 bg-white",
        dense && "max-h-[70vh] overflow-y-auto"
      )}
    >
      <table className={cn("w-full min-w-max text-left text-sm", dense && "border-collapse text-[13px]")}>
        <thead
          className={cn(
            "border-b border-slate-200 bg-slate-50/80 text-xs font-semibold uppercase tracking-wide text-slate-500",
            dense && "sticky top-0 z-10 bg-slate-100"
          )}
        >
          <tr>
            {dense && (
              <th className={cn("w-10 whitespace-nowrap px-2 py-2 text-right text-slate-400", dense && "border border-slate-200")}>
                #
              </th>
            )}
            {columns.map((col) => {
              const isSorted = sort?.key === col.key;
              return (
                <th
                  key={col.key}
                  className={cn(
                    "whitespace-nowrap px-4 py-3",
                    dense && "border border-slate-200 px-3 py-2",
                    alignClass(col.align),
                    col.sortable && "cursor-pointer select-none hover:bg-slate-200/60"
                  )}
                  onClick={() => col.sortable && onSortChange?.(col.key)}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.header}
                    {col.sortable &&
                      (isSorted ? (
                        sort?.direction === "asc" ? (
                          <ArrowUp className="h-3 w-3" />
                        ) : (
                          <ArrowDown className="h-3 w-3" />
                        )
                      ) : (
                        <ArrowUpDown className="h-3 w-3 text-slate-300" />
                      ))}
                  </span>
                </th>
              );
            })}
            {showActions && (
              <th className={cn("px-4 py-3 text-right", dense && "border border-slate-200 px-3 py-2")}>Actions</th>
            )}
          </tr>
        </thead>
        <tbody className={cn(!dense && "divide-y divide-slate-100")}>
          {isLoading ? (
            <tr>
              <td colSpan={totalCols} className="px-4 py-14 text-center">
                <div className="flex justify-center">
                  <Spinner />
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={totalCols} className="px-4 py-14 text-center">
                <div className="flex flex-col items-center gap-2 text-slate-400">
                  <Inbox className="h-8 w-8" />
                  <span className="text-sm">No records found.</span>
                </div>
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr
                key={row.id}
                className={cn(
                  "transition-colors hover:bg-brand-50/50",
                  dense && rowIndex % 2 === 1 && "bg-slate-50/60"
                )}
              >
                {dense && (
                  <td className="border border-slate-200 px-2 py-1.5 text-right text-xs text-slate-400">
                    {rowNumberStart + rowIndex}
                  </td>
                )}
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={cn(
                      "whitespace-nowrap px-4 py-3 text-slate-700",
                      dense && "border border-slate-200 px-3 py-1.5",
                      alignClass(col.align)
                    )}
                  >
                    {col.render ? col.render(row) : String((row as Record<string, unknown>)[col.key] ?? "—")}
                  </td>
                ))}
                {showActions && (
                  <td className={cn("whitespace-nowrap px-4 py-3 text-right", dense && "border border-slate-200 px-3 py-1.5")}>
                    <div className="flex justify-end gap-2">
                      {canEdit && (
                        <button
                          onClick={() => onEdit?.(row)}
                          className="rounded px-2 py-1 text-xs font-medium text-brand-600 transition-colors hover:bg-brand-50"
                        >
                          Edit
                        </button>
                      )}
                      {canDelete && (
                        <button
                          onClick={() => onDelete?.(row)}
                          className="rounded px-2 py-1 text-xs font-medium text-red-600 transition-colors hover:bg-red-50"
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </td>
                )}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
