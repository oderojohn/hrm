import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, CalendarDays, Settings } from "lucide-react";
import {
  leaveRequestsApi,
  leaveTypesApi,
  fetchLeaveBalances,
  fetchLeaveCalendar,
  approveLeaveRequest,
  rejectLeaveRequest,
  cancelLeaveRequest,
  reassignLeaveStep,
  returnForCorrection,
  resubmitLeaveRequest,
  type LeaveRequest,
} from "../api/leave";
import { fetchAllEmployeesForSelect } from "../api/employees";
import { extractErrorMessage } from "../api/client";
import { useAuthStore, isManagerOrAbove, isHRManagerOrAbove } from "../store/authStore";
import { Tabs } from "../components/ui/Tabs";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Dialog } from "../components/ui/Dialog";
import { Select } from "../components/ui/Select";
import { Textarea } from "../components/ui/Textarea";
import { ResourceForm } from "../components/resource/ResourceForm";
import type { FormField } from "../components/resource/types";
import { DataTable } from "../components/resource/DataTable";
import { StatusBadge } from "../components/ui/Badge";
import { StatCard } from "../components/StatCard";
import { ApprovalStepper } from "../components/leave/ApprovalStepper";
import { cn, formatDate } from "../lib/utils";

export function LeavePage() {
  const user = useAuthStore((s) => s.user);
  const canApprove = isManagerOrAbove(user);
  const canManageWorkflows = isHRManagerOrAbove(user);

  const tabs = [
    { key: "my-requests", label: "My Requests", content: <MyRequestsTab /> },
    ...(canApprove ? [{ key: "approvals", label: "Pending Approvals", content: <ApprovalsTab /> }] : []),
    { key: "calendar", label: "Calendar", content: <CalendarTab /> },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-lg font-semibold text-slate-900">Leave Management</h1>
        {canManageWorkflows && (
          <div className="flex flex-wrap gap-2">
            <Link to="/leave/setup">
              <Button size="sm" variant="outline">
                <Settings className="h-3.5 w-3.5" /> Leave Setup
              </Button>
            </Link>
            <Link to="/leave/workflows">
              <Button size="sm" variant="outline">
                <Settings className="h-3.5 w-3.5" /> Manage Workflows
              </Button>
            </Link>
          </div>
        )}
      </div>
      <Tabs tabs={tabs} />
    </div>
  );
}

function MyRequestsTab() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [progressTarget, setProgressTarget] = useState<LeaveRequest | null>(null);

  const { data: balances } = useQuery({
    queryKey: ["leave-balances", user?.employee_id],
    queryFn: () => fetchLeaveBalances(user?.employee_id ?? undefined),
    enabled: !!user?.employee_id,
  });

  const { data: leaveTypes } = useQuery({ queryKey: ["leave-types"], queryFn: () => leaveTypesApi.list({ page_size: 100 }) });

  const { data: requests, isLoading } = useQuery({
    queryKey: ["leave-requests", "own", user?.employee_id],
    queryFn: () => leaveRequestsApi.list({ employee: user?.employee_id ?? undefined, ordering: "-created_at" }),
    enabled: !!user?.employee_id,
  });

  const createMutation = useMutation({
    mutationFn: (values: Partial<LeaveRequest>) => leaveRequestsApi.create(values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leave-requests"] });
      queryClient.invalidateQueries({ queryKey: ["leave-balances"] });
      setDialogOpen(false);
      setFormError(null);
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  const cancelMutation = useMutation({
    mutationFn: (id: number) => cancelLeaveRequest(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["leave-requests"] }),
  });

  const resubmitMutation = useMutation({
    mutationFn: (id: number) => resubmitLeaveRequest(id, {}),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["leave-requests"] }),
  });

  const formFields: FormField[] = [
    {
      name: "leave_type",
      label: "Leave Type",
      type: "select",
      required: true,
      options: leaveTypes?.results.map((lt) => ({ label: lt.name, value: lt.id })) ?? [],
    },
    { name: "start_date", label: "Start Date", type: "date", required: true },
    { name: "end_date", label: "End Date", type: "date", required: true },
    { name: "is_half_day", label: "Half Day", type: "checkbox" },
    { name: "reason", label: "Reason", type: "textarea" },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {balances?.results.map((b) => (
          <StatCard key={b.id} label={b.leave_type_name} value={`${b.remaining_days} days`} icon={CalendarDays} />
        ))}
      </div>

      <div className="flex justify-end">
        <Button size="sm" onClick={() => setDialogOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> Request Leave
        </Button>
      </div>

      <DataTable
        columns={[
          { key: "leave_type_name", header: "Type" },
          { key: "start_date", header: "Start", render: (r) => formatDate(r.start_date) },
          { key: "end_date", header: "End", render: (r) => formatDate(r.end_date) },
          { key: "total_days", header: "Days" },
          { key: "status", header: "Status", render: (r) => <StatusBadge status={r.status} /> },
          {
            key: "actions",
            header: "",
            render: (r) => (
              <div className="flex justify-end gap-2">
                {r.status === "RETURNED" && (
                  <Button size="sm" variant="outline" onClick={() => resubmitMutation.mutate(r.id)}>
                    Resubmit
                  </Button>
                )}
                <Button size="sm" variant="ghost" onClick={() => setProgressTarget(r)}>
                  Progress
                </Button>
              </div>
            ),
          },
        ]}
        data={requests?.results ?? []}
        isLoading={isLoading}
        canEdit={false}
        canDelete
        onDelete={(row) => {
          if ((row.status === "PENDING" || row.status === "APPROVED") && confirm("Cancel this leave request?")) {
            cancelMutation.mutate(row.id);
          }
        }}
      />

      <Dialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          setFormError(null);
        }}
        title="Request Leave"
      >
        <ResourceForm
          fields={formFields}
          submitting={createMutation.isPending}
          errorMessage={formError}
          onCancel={() => setDialogOpen(false)}
          onSubmit={(values) => createMutation.mutate(values as Partial<LeaveRequest>)}
        />
      </Dialog>

      <Dialog open={!!progressTarget} onClose={() => setProgressTarget(null)} title="Approval Progress">
        {progressTarget && (
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-slate-800">{progressTarget.leave_type_name}</p>
              <p className="text-xs text-slate-500">
                {formatDate(progressTarget.start_date)} → {formatDate(progressTarget.end_date)} (
                {progressTarget.total_days} days)
              </p>
            </div>
            <ApprovalStepper steps={progressTarget.approval_steps} />
          </div>
        )}
      </Dialog>
    </div>
  );
}

function ApprovalsTab() {
  const queryClient = useQueryClient();
  const [reassignTarget, setReassignTarget] = useState<LeaveRequest | null>(null);
  const [reassignApprover, setReassignApprover] = useState("");
  const [reassignError, setReassignError] = useState<string | null>(null);
  const [commentTarget, setCommentTarget] = useState<{ request: LeaveRequest; action: "reject" | "return" } | null>(null);
  const [comment, setComment] = useState("");

  const { data: requests, isLoading } = useQuery({
    queryKey: ["leave-requests", "pending"],
    queryFn: () => leaveRequestsApi.list({ status: "PENDING", ordering: "created_at" }),
  });
  const { data: employees } = useQuery({ queryKey: ["employees-all"], queryFn: fetchAllEmployeesForSelect });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["leave-requests"] });
  const closeCommentDialog = () => {
    setCommentTarget(null);
    setComment("");
  };

  const approveMutation = useMutation({ mutationFn: (id: number) => approveLeaveRequest(id), onSuccess: invalidate });
  const rejectMutation = useMutation({
    mutationFn: () => rejectLeaveRequest(commentTarget!.request.id, comment),
    onSuccess: () => {
      invalidate();
      closeCommentDialog();
    },
  });
  const returnMutation = useMutation({
    mutationFn: () => returnForCorrection(commentTarget!.request.id, comment),
    onSuccess: () => {
      invalidate();
      closeCommentDialog();
    },
  });
  const reassignMutation = useMutation({
    mutationFn: ({ id, approverId }: { id: number; approverId: number }) => reassignLeaveStep(id, approverId),
    onSuccess: () => {
      invalidate();
      setReassignTarget(null);
      setReassignError(null);
    },
    onError: (err) => setReassignError(extractErrorMessage(err)),
  });

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Pending Leave Approvals</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-slate-400">Loading...</p>
          ) : !requests?.results.length ? (
            <p className="text-sm text-slate-400">No pending approvals.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {requests.results.map((r) => {
                const currentStep = r.approval_steps.find((s) => s.status === "PENDING");
                return (
                  <li key={r.id} className="flex items-center justify-between py-3">
                    <div>
                      <p className="text-sm font-medium text-slate-800">
                        {r.employee_name} — {r.leave_type_name}
                      </p>
                      <p className="text-xs text-slate-500">
                        {formatDate(r.start_date)} → {formatDate(r.end_date)} ({r.total_days} days)
                        {currentStep && <span className="ml-2 text-slate-400">· Awaiting: {currentStep.name}</span>}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="ghost" onClick={() => setReassignTarget(r)}>
                        Reassign
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setCommentTarget({ request: r, action: "return" })}>
                        Return
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setCommentTarget({ request: r, action: "reject" })}>
                        Reject
                      </Button>
                      <Button size="sm" onClick={() => approveMutation.mutate(r.id)}>
                        Approve
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>

      <Dialog
        open={!!reassignTarget}
        onClose={() => {
          setReassignTarget(null);
          setReassignError(null);
        }}
        title="Reassign Approval"
      >
        {reassignTarget && (
          <div className="space-y-4">
            {reassignError && <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{reassignError}</div>}
            <p className="text-sm text-slate-600">
              Delegate {reassignTarget.employee_name}'s pending step to a different approver.
            </p>
            <Select value={reassignApprover} onChange={(e) => setReassignApprover(e.target.value)}>
              <option value="">Select employee...</option>
              {employees?.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.full_name}
                </option>
              ))}
            </Select>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setReassignTarget(null)}>
                Cancel
              </Button>
              <Button
                loading={reassignMutation.isPending}
                disabled={!reassignApprover}
                onClick={() =>
                  reassignTarget && reassignMutation.mutate({ id: reassignTarget.id, approverId: Number(reassignApprover) })
                }
              >
                Reassign
              </Button>
            </div>
          </div>
        )}
      </Dialog>

      <Dialog
        open={!!commentTarget}
        onClose={closeCommentDialog}
        title={commentTarget?.action === "reject" ? "Reject Leave Request" : "Return for Correction"}
      >
        {commentTarget && (
          <div className="space-y-4">
            <p className="text-sm text-slate-600">
              {commentTarget.action === "reject" ? "Rejecting" : "Returning"} {commentTarget.request.employee_name}'s{" "}
              {commentTarget.request.leave_type_name} request ({formatDate(commentTarget.request.start_date)} →{" "}
              {formatDate(commentTarget.request.end_date)}).
            </p>
            <Textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={commentTarget.action === "reject" ? "Reason for rejection (optional)" : "What needs to change (optional)"}
              rows={3}
            />
            <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
              <Button variant="outline" onClick={closeCommentDialog}>
                Cancel
              </Button>
              <Button
                variant={commentTarget.action === "reject" ? "danger" : "primary"}
                loading={commentTarget.action === "reject" ? rejectMutation.isPending : returnMutation.isPending}
                onClick={() => (commentTarget.action === "reject" ? rejectMutation.mutate() : returnMutation.mutate())}
              >
                {commentTarget.action === "reject" ? "Reject" : "Return"}
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </>
  );
}

function CalendarTab() {
  const user = useAuthStore((s) => s.user);
  const canViewTeam = isManagerOrAbove(user);
  const [scope, setScope] = useState<"personal" | "team">("personal");
  const [monthOffset, setMonthOffset] = useState(0);

  const { data: entries } = useQuery({
    queryKey: ["leave-calendar", scope],
    queryFn: () => fetchLeaveCalendar(scope),
  });

  const monthDate = useMemo(() => {
    const d = new Date();
    d.setDate(1);
    d.setMonth(d.getMonth() + monthOffset);
    return d;
  }, [monthOffset]);

  const days = useMemo(() => buildMonthGrid(monthDate), [monthDate]);

  const entriesByDay = useMemo(() => {
    const map = new Map<string, LeaveRequest[]>();
    for (const entry of entries ?? []) {
      let cursor = new Date(entry.start_date);
      const end = new Date(entry.end_date);
      while (cursor <= end) {
        const key = cursor.toISOString().slice(0, 10);
        if (!map.has(key)) map.set(key, []);
        map.get(key)!.push(entry);
        cursor = new Date(cursor.getTime() + 86400000);
      }
    }
    return map;
  }, [entries]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => setMonthOffset((o) => o - 1)}>
            ← Prev
          </Button>
          <span className="text-sm font-medium text-slate-800">
            {monthDate.toLocaleDateString(undefined, { month: "long", year: "numeric" })}
          </span>
          <Button size="sm" variant="outline" onClick={() => setMonthOffset((o) => o + 1)}>
            Next →
          </Button>
        </div>
        {canViewTeam && (
          <Select value={scope} onChange={(e) => setScope(e.target.value as "personal" | "team")} className="w-full sm:w-40">
            <option value="personal">My Calendar</option>
            <option value="team">Team Calendar</option>
          </Select>
        )}
      </div>

      <div className="grid grid-cols-7 gap-px overflow-hidden rounded-lg border border-slate-200 bg-slate-200">
        {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
          <div key={d} className="bg-slate-50 px-2 py-1 text-center text-xs font-medium text-slate-500">
            {d}
          </div>
        ))}
        {days.map((day, i) => {
          const key = day ? day.toISOString().slice(0, 10) : `blank-${i}`;
          const dayEntries = day ? entriesByDay.get(key) ?? [] : [];
          return (
            <div
              key={key}
              className={cn("min-h-20 bg-white p-1.5 text-xs", !day && "bg-slate-50")}
            >
              {day && (
                <>
                  <div className="mb-1 text-right text-slate-400">{day.getDate()}</div>
                  {dayEntries.slice(0, 2).map((entry) => (
                    <div key={entry.id} className="mb-0.5 truncate rounded bg-brand-50 px-1 py-0.5 text-[10px] text-brand-700">
                      {entry.employee_name}
                    </div>
                  ))}
                  {dayEntries.length > 2 && (
                    <div className="text-[10px] text-slate-400">+{dayEntries.length - 2} more</div>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function buildMonthGrid(monthDate: Date): (Date | null)[] {
  const year = monthDate.getFullYear();
  const month = monthDate.getMonth();
  const firstDay = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const leadingBlanks = firstDay.getDay();

  const cells: (Date | null)[] = Array(leadingBlanks).fill(null);
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push(new Date(year, month, d));
  }
  while (cells.length % 7 !== 0) {
    cells.push(null);
  }
  return cells;
}
