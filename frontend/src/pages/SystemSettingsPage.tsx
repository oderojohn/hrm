import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarPlus, KeyRound, Plus, Power, Trash2 } from "lucide-react";
import {
  syncAgentsApi,
  syncEventsApi,
  createSyncAgent,
  regenerateSyncAgentKey,
  type SyncAgent,
  type SyncEvent,
} from "../api/sync";
import { fetchAttendanceSettings, updateAttendanceSettings } from "../api/attendance";
import { publicHolidaysApi, type PublicHoliday } from "../api/core";
import { branchesApi } from "../api/organization";
import { extractErrorMessage } from "../api/client";
import { Tabs } from "../components/ui/Tabs";
import { Button } from "../components/ui/Button";
import { Dialog } from "../components/ui/Dialog";
import { Input } from "../components/ui/Input";
import { Label } from "../components/ui/Label";
import { Select } from "../components/ui/Select";
import { ResourceForm } from "../components/resource/ResourceForm";
import type { FormField } from "../components/resource/types";
import { DataTable } from "../components/resource/DataTable";
import { StatusBadge } from "../components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { CredentialRevealDialog } from "../components/CredentialRevealDialog";
import { FullPageSpinner } from "../components/ui/Spinner";
import { formatDate, formatDateTime } from "../lib/utils";

export function SystemSettingsPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">System Settings</h1>
        <p className="text-sm text-slate-500">Manage local sync agent installations and review their activity.</p>
      </div>
      <Tabs
        tabs={[
          { key: "agents", label: "Sync Agents", content: <SyncAgentsTab /> },
          { key: "log", label: "Sync Activity Log", content: <SyncActivityLogTab /> },
          { key: "attendance", label: "Attendance Settings", content: <AttendanceSettingsTab /> },
        ]}
      />
    </div>
  );
}

const WEEKDAY_LABELS = [
  { value: 1, label: "Mon" },
  { value: 2, label: "Tue" },
  { value: 3, label: "Wed" },
  { value: 4, label: "Thu" },
  { value: 5, label: "Fri" },
  { value: 6, label: "Sat" },
  { value: 7, label: "Sun" },
];

function AttendanceSettingsTab() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["attendance-settings"], queryFn: fetchAttendanceSettings });
  const [weekendDays, setWeekendDays] = useState<number[]>([]);
  const [holidayDialogOpen, setHolidayDialogOpen] = useState(false);
  const [editingHoliday, setEditingHoliday] = useState<PublicHoliday | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (data) setWeekendDays(data.weekend_days);
  }, [data]);

  const saveWeekendDays = useMutation({
    mutationFn: (days: number[]) => updateAttendanceSettings({ weekend_days: days }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["attendance-settings"] }),
  });

  const toggleDay = (day: number) => {
    const next = weekendDays.includes(day) ? weekendDays.filter((d) => d !== day) : [...weekendDays, day];
    setWeekendDays(next);
    saveWeekendDays.mutate(next);
  };

  const { data: holidays, isLoading: holidaysLoading } = useQuery({
    queryKey: ["public-holidays"],
    queryFn: () => publicHolidaysApi.list({ page_size: 100, ordering: "date" }),
  });

  const { data: branches } = useQuery({ queryKey: ["branches-all"], queryFn: () => branchesApi.list({ page_size: 200 }) });

  const invalidateHolidays = () => queryClient.invalidateQueries({ queryKey: ["public-holidays"] });

  const saveHoliday = useMutation({
    mutationFn: (values: Partial<PublicHoliday>) =>
      editingHoliday ? publicHolidaysApi.update(editingHoliday.id, values) : publicHolidaysApi.create(values),
    onSuccess: () => {
      invalidateHolidays();
      setHolidayDialogOpen(false);
      setEditingHoliday(null);
      setFormError(null);
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  const deleteHoliday = useMutation({
    mutationFn: (id: number) => publicHolidaysApi.remove(id),
    onSuccess: invalidateHolidays,
  });

  const holidayFields: FormField[] = [
    { name: "name", label: "Holiday Name", type: "text", required: true },
    { name: "date", label: "Date", type: "date", required: true },
    {
      name: "branch",
      label: "Branch (leave blank for company-wide)",
      type: "select",
      options: branches?.results.map((b) => ({ value: b.id, label: b.name })) ?? [],
    },
    { name: "is_recurring_annually", label: "Repeats every year", type: "checkbox" },
    { name: "description", label: "Description", type: "textarea" },
  ];

  if (isLoading) return <FullPageSpinner />;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Weekend Days</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 px-4 pb-4 pt-0">
          <p className="text-xs text-slate-500">
            Fallback non-working days for employees with no work shift assigned. Employees with a shift use its own
            working-days setting instead (Organization → Shifts).
          </p>
          <div className="flex flex-wrap gap-2">
            {WEEKDAY_LABELS.map((d) => (
              <button
                key={d.value}
                onClick={() => toggleDay(d.value)}
                className={
                  weekendDays.includes(d.value)
                    ? "rounded-md border border-brand-500 bg-brand-50 px-3 py-1.5 text-sm font-medium text-brand-700"
                    : "rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
                }
              >
                {d.label}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Public Holidays</CardTitle>
          <Button
            size="sm"
            onClick={() => {
              setEditingHoliday(null);
              setHolidayDialogOpen(true);
            }}
          >
            <CalendarPlus className="h-3.5 w-3.5" /> Add Holiday
          </Button>
        </CardHeader>
        <CardContent className="px-0 pb-0 pt-0">
          <DataTable
            columns={[
              { key: "name", header: "Name" },
              { key: "date", header: "Date", render: (r) => formatDate(r.date) },
              { key: "is_recurring_annually", header: "Recurring", render: (r) => (r.is_recurring_annually ? "Yes" : "No") },
              {
                key: "actions",
                header: "",
                render: (r) => (
                  <div className="flex justify-end gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEditingHoliday(r);
                        setHolidayDialogOpen(true);
                      }}
                    >
                      Edit
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => deleteHoliday.mutate(r.id)}>
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                ),
              },
            ]}
            data={holidays?.results ?? []}
            isLoading={holidaysLoading}
            canEdit={false}
            canDelete={false}
          />
        </CardContent>
      </Card>

      <Dialog
        open={holidayDialogOpen}
        onClose={() => {
          setHolidayDialogOpen(false);
          setEditingHoliday(null);
          setFormError(null);
        }}
        title={editingHoliday ? "Edit Holiday" : "Add Holiday"}
      >
        <ResourceForm
          fields={holidayFields}
          defaultValues={editingHoliday ? { ...editingHoliday } : undefined}
          submitting={saveHoliday.isPending}
          errorMessage={formError}
          onCancel={() => setHolidayDialogOpen(false)}
          onSubmit={(values) => saveHoliday.mutate(values as Partial<PublicHoliday>)}
        />
      </Dialog>
    </div>
  );
}

function SyncAgentsTab() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState("");
  const [branch, setBranch] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [credentialFields, setCredentialFields] = useState<{ label: string; value: string }[] | null>(null);

  const { data: branches } = useQuery({ queryKey: ["branches-all"], queryFn: () => branchesApi.list({ page_size: 200 }) });
  const { data, isLoading } = useQuery({ queryKey: ["sync-agents"], queryFn: () => syncAgentsApi.list({ page_size: 100 }) });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["sync-agents"] });

  const createMutation = useMutation({
    mutationFn: () => createSyncAgent({ name, branch: branch ? Number(branch) : null }),
    onSuccess: (result) => {
      setCreateOpen(false);
      setName("");
      setBranch("");
      setFormError(null);
      invalidate();
      setCredentialFields([
        { label: "Agent Name", value: result.name },
        { label: "API Key", value: result.api_key },
      ]);
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  const regenerateMutation = useMutation({
    mutationFn: (agent: SyncAgent) => regenerateSyncAgentKey(agent.id).then((r) => ({ ...r, agentName: agent.name })),
    onSuccess: (result) => {
      setCredentialFields([
        { label: "Agent Name", value: result.agentName },
        { label: "API Key", value: result.api_key },
      ]);
    },
  });

  const toggleActiveMutation = useMutation({
    mutationFn: (agent: SyncAgent) => syncAgentsApi.update(agent.id, { is_active: !agent.is_active }),
    onSuccess: invalidate,
  });

  if (isLoading) return <FullPageSpinner />;

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> New Agent
        </Button>
      </div>

      <DataTable
        columns={[
          { key: "name", header: "Name" },
          { key: "branch_name", header: "Branch", render: (r) => r.branch_name ?? "—" },
          { key: "key_prefix", header: "Key", render: (r) => <span className="font-mono text-xs">{r.key_prefix}…</span> },
          { key: "is_active", header: "Status", render: (r) => <StatusBadge status={r.is_active ? "ACTIVE" : "SUSPENDED"} /> },
          {
            key: "last_seen_at",
            header: "Last Seen",
            render: (r) => (r.last_seen_at ? formatDateTime(r.last_seen_at) : "Never"),
          },
          {
            key: "actions",
            header: "",
            render: (r) => (
              <div className="flex justify-end gap-2">
                <Button size="sm" variant="outline" onClick={() => regenerateMutation.mutate(r)} loading={regenerateMutation.isPending}>
                  <KeyRound className="h-3.5 w-3.5" /> Regenerate Key
                </Button>
                <Button size="sm" variant="outline" onClick={() => toggleActiveMutation.mutate(r)} loading={toggleActiveMutation.isPending}>
                  <Power className="h-3.5 w-3.5" /> {r.is_active ? "Deactivate" : "Activate"}
                </Button>
              </div>
            ),
          },
        ]}
        data={data?.results ?? []}
        canEdit={false}
        canDelete={false}
      />

      <Dialog
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          setFormError(null);
        }}
        title="New Sync Agent"
      >
        <div className="space-y-4">
          {formError && <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>}
          <div>
            <Label>Name</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Front Desk PC" />
          </div>
          <div>
            <Label>Branch</Label>
            <Select value={branch} onChange={(e) => setBranch(e.target.value)}>
              <option value="">Select...</option>
              {branches?.results.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => createMutation.mutate()} loading={createMutation.isPending} disabled={!name}>
              Create Agent
            </Button>
          </div>
        </div>
      </Dialog>

      <CredentialRevealDialog
        open={!!credentialFields}
        onClose={() => setCredentialFields(null)}
        title="Sync Agent API Key"
        warning="Paste this key into the local agent's Settings screen now — it will not be shown again."
        fields={credentialFields ?? []}
      />
    </div>
  );
}

function SyncActivityLogTab() {
  const [agentId, setAgentId] = useState("");
  const [status, setStatus] = useState("");
  const [eventType, setEventType] = useState("");
  const [selected, setSelected] = useState<SyncEvent | null>(null);

  const { data: agents } = useQuery({ queryKey: ["sync-agents"], queryFn: () => syncAgentsApi.list({ page_size: 100 }) });
  const { data, isLoading } = useQuery({
    queryKey: ["sync-events", agentId, status, eventType],
    queryFn: () =>
      syncEventsApi.list({
        page_size: 100,
        ordering: "-created_at",
        agent: agentId || undefined,
        status: status || undefined,
        event_type: eventType || undefined,
      }),
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Select value={agentId} onChange={(e) => setAgentId(e.target.value)} className="w-full sm:w-48">
          <option value="">All Agents</option>
          {agents?.results.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </Select>
        <Select value={eventType} onChange={(e) => setEventType(e.target.value)} className="w-full sm:w-44">
          <option value="">All Event Types</option>
          <option value="PUSH">Data Push</option>
          <option value="AUTH_FAILED">Auth Failed</option>
          <option value="ERROR">Error</option>
        </Select>
        <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-full sm:w-36">
          <option value="">All Statuses</option>
          <option value="SUCCESS">Success</option>
          <option value="FAILED">Failed</option>
        </Select>
      </div>

      <DataTable
        dense
        columns={[
          { key: "created_at", header: "Time", render: (r) => formatDateTime(r.created_at) },
          { key: "agent_name", header: "Agent", render: (r) => r.agent_name ?? "Unknown" },
          { key: "event_type", header: "Type" },
          { key: "status", header: "Status", render: (r) => <StatusBadge status={r.status} /> },
          {
            key: "summary",
            header: "Summary",
            render: (r) => (
              <button onClick={() => setSelected(r)} className="text-left text-brand-700 hover:underline">
                {r.summary}
              </button>
            ),
          },
        ]}
        data={data?.results ?? []}
        isLoading={isLoading}
        canEdit={false}
        canDelete={false}
      />

      <Dialog open={!!selected} onClose={() => setSelected(null)} title="Sync Event Detail" className="max-w-2xl">
        {selected && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-xs font-medium uppercase text-slate-400">Agent</p>
                <p>{selected.agent_name ?? "Unknown"}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase text-slate-400">Time</p>
                <p>{formatDateTime(selected.created_at)}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase text-slate-400">IP Address</p>
                <p>{selected.ip_address ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase text-slate-400">Status</p>
                <StatusBadge status={selected.status} />
              </div>
            </div>
            <div>
              <p className="mb-1 text-xs font-medium uppercase text-slate-400">Payload</p>
              <pre className="max-h-80 overflow-auto rounded-md bg-slate-900 p-3 text-xs text-slate-100">
                {JSON.stringify(selected.payload, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
