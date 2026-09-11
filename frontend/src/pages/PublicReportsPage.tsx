import { Fragment, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Download, CalendarDays } from "lucide-react";
import {
  fetchPublicReportsIndex,
  fetchPublicAttendanceRegister,
  publicAttendanceRegisterExportUrl,
} from "../api/publicReports";
import { Spinner } from "../components/ui/Spinner";

async function downloadPublicReport(url: string, filename: string) {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Download failed (HTTP ${response.status}).`);
    const blob = await response.blob();
    const objectUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(objectUrl);
  } catch (err) {
    window.alert(err instanceof Error ? err.message : "Download failed.");
  }
}

function CellValue({ value }: { value: string }) {
  if (value === "Absent") return <span className="font-medium text-red-600">Absent</span>;
  if (value === "On Leave") return <span className="font-medium text-sky-600">On Leave</span>;
  if (value === "Off") return <span className="text-slate-400">Off</span>;
  if (!value) return <span className="text-slate-300">—</span>;
  return <span>{value}</span>;
}

export function PublicReportsPage() {
  const { token = "" } = useParams<{ token: string }>();

  const indexQuery = useQuery({
    queryKey: ["public-reports-index", token],
    queryFn: () => fetchPublicReportsIndex(token),
    retry: false,
  });

  const [month, setMonth] = useState<string | null>(null);
  const activeMonth = month ?? indexQuery.data?.months.at(-1)?.value ?? null;

  const registerQuery = useQuery({
    queryKey: ["public-attendance-register", token, activeMonth],
    queryFn: () => fetchPublicAttendanceRegister(token, activeMonth as string),
    enabled: !!activeMonth,
  });

  if (indexQuery.isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Spinner />
      </div>
    );
  }

  if (indexQuery.isError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
        <div className="max-w-sm rounded-lg border border-slate-200 bg-white p-6 text-center shadow-sm">
          <h1 className="text-base font-semibold text-slate-900">Link not found</h1>
          <p className="mt-2 text-sm text-slate-500">
            This report link is invalid or has been disabled. Ask HR for a current link.
          </p>
        </div>
      </div>
    );
  }

  const { company, months } = indexQuery.data!;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-5 sm:px-6">
          <h1 className="text-lg font-semibold text-slate-900">{company}</h1>
          <p className="text-sm text-slate-500">Attendance Reports</p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          {months.map((m) => (
            <button
              key={m.value}
              onClick={() => setMonth(m.value)}
              className={`rounded-md border px-3 py-1.5 text-sm font-medium transition-colors ${
                activeMonth === m.value
                  ? "border-amber-500 bg-amber-50 text-amber-700"
                  : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              <CalendarDays className="mr-1.5 inline h-3.5 w-3.5" />
              {m.label}
            </button>
          ))}
        </div>

        <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
            <h2 className="text-sm font-semibold text-slate-900">
              {registerQuery.data ? `Attendance Report — ${registerQuery.data.month}` : "Loading…"}
            </h2>
            {activeMonth && (
              <button
                onClick={() =>
                  downloadPublicReport(
                    publicAttendanceRegisterExportUrl(token, activeMonth),
                    `Attendance_Report_${activeMonth}.xlsx`
                  )
                }
                className="inline-flex items-center gap-1.5 rounded-md bg-amber-500 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-600"
              >
                <Download className="h-3.5 w-3.5" /> Download Excel
              </button>
            )}
          </div>

          <div className="overflow-auto p-2">
            {registerQuery.isLoading || !registerQuery.data ? (
              <p className="p-4 text-sm text-slate-400">Loading…</p>
            ) : (
              <table className="w-full min-w-max border-collapse text-xs">
                <thead className="sticky top-0 bg-slate-50">
                  <tr>
                    <th rowSpan={2} className="whitespace-nowrap border border-slate-200 px-2 py-1.5 text-left font-semibold text-slate-600">
                      Employee
                    </th>
                    <th rowSpan={2} className="whitespace-nowrap border border-slate-200 px-2 py-1.5 text-left font-semibold text-slate-600">
                      Department
                    </th>
                    {registerQuery.data.dates.map((d) => (
                      <th
                        key={d}
                        colSpan={2}
                        className="whitespace-nowrap border border-slate-200 px-2 py-1.5 text-center font-semibold text-slate-600"
                      >
                        {new Date(d).toLocaleDateString(undefined, { day: "2-digit", month: "short" })}
                      </th>
                    ))}
                  </tr>
                  <tr>
                    {registerQuery.data.dates.map((d) => (
                      <Fragment key={d}>
                        <th className="whitespace-nowrap border border-slate-200 px-2 py-1 text-center font-medium text-slate-500">
                          Check In
                        </th>
                        <th className="whitespace-nowrap border border-slate-200 px-2 py-1 text-center font-medium text-slate-500">
                          Check Out
                        </th>
                      </Fragment>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {registerQuery.data.employees.map((emp) => (
                    <tr key={emp.employee_number}>
                      <td className="whitespace-nowrap border border-slate-200 px-2 py-1 text-slate-700">{emp.name}</td>
                      <td className="whitespace-nowrap border border-slate-200 px-2 py-1 text-slate-700">{emp.department}</td>
                      {emp.days.map((day, i) => (
                        <Fragment key={i}>
                          <td className="whitespace-nowrap border border-slate-200 px-2 py-1 text-center">
                            <CellValue value={day.check_in} />
                          </td>
                          <td className="whitespace-nowrap border border-slate-200 px-2 py-1 text-center">
                            <CellValue value={day.check_out} />
                          </td>
                        </Fragment>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
