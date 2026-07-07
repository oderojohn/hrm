import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Star } from "lucide-react";
import { workflowTemplatesApi, leaveTypesApi, type WorkflowTemplate } from "../api/leave";
import { departmentsApi, branchesApi } from "../api/organization";
import { fetchAllEmployeesForSelect } from "../api/employees";
import { extractErrorMessage } from "../api/client";
import { WorkflowBuilder } from "../components/workflow/WorkflowBuilder";
import { Dialog } from "../components/ui/Dialog";
import { Button } from "../components/ui/Button";
import { Card, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { FullPageSpinner } from "../components/ui/Spinner";

export function LeaveWorkflowsPage() {
  const queryClient = useQueryClient();
  const [dialogState, setDialogState] = useState<{ mode: "create" | "edit"; template?: WorkflowTemplate } | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: templates, isLoading } = useQuery({
    queryKey: ["workflow-templates"],
    queryFn: () => workflowTemplatesApi.list({ page_size: 100 }),
  });
  const { data: departments } = useQuery({ queryKey: ["departments-all"], queryFn: () => departmentsApi.list({ page_size: 200 }) });
  const { data: branches } = useQuery({ queryKey: ["branches-all"], queryFn: () => branchesApi.list({ page_size: 200 }) });
  const { data: leaveTypes } = useQuery({ queryKey: ["leave-types"], queryFn: () => leaveTypesApi.list({ page_size: 100 }) });
  const { data: employees } = useQuery({ queryKey: ["employees-all"], queryFn: fetchAllEmployeesForSelect });

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => workflowTemplatesApi.create(payload as Partial<WorkflowTemplate>),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-templates"] });
      setDialogState(null);
      setFormError(null);
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Record<string, unknown> }) =>
      workflowTemplatesApi.update(id, payload as Partial<WorkflowTemplate>),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-templates"] });
      setDialogState(null);
      setFormError(null);
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => workflowTemplatesApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workflow-templates"] }),
  });

  if (isLoading) return <FullPageSpinner />;

  const departmentOptions = departments?.results.map((d) => ({ id: d.id, label: d.name })) ?? [];
  const branchOptions = branches?.results.map((b) => ({ id: b.id, label: b.name })) ?? [];
  const leaveTypeOptions = leaveTypes?.results.map((lt) => ({ id: lt.id, label: lt.name })) ?? [];
  const employeeOptions = employees?.map((e) => ({ id: e.id, label: e.full_name })) ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">Leave Approval Workflows</h1>
          <p className="text-sm text-slate-500">
            Design unlimited-level approval chains — assign them to departments, branches, leave types, or employment types.
          </p>
        </div>
        <Button size="sm" onClick={() => setDialogState({ mode: "create" })}>
          <Plus className="h-3.5 w-3.5" /> New Workflow
        </Button>
      </div>

      <div className="space-y-3">
        {!templates?.results.length && (
          <Card>
            <CardContent className="py-8 text-center text-sm text-slate-400">
              No workflows configured yet. New leave requests fall back to a default Supervisor → HR chain until you create one.
            </CardContent>
          </Card>
        )}
        {templates?.results.map((template) => (
          <Card key={template.id}>
            <CardContent className="flex items-center justify-between py-4">
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-medium text-slate-900">{template.name}</p>
                  {template.is_default && <Badge tone="blue">Default</Badge>}
                  {!template.is_active && <Badge tone="red">Inactive</Badge>}
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {template.steps.length} level{template.steps.length === 1 ? "" : "s"}:{" "}
                  {template.steps.map((s) => s.name).join(" → ")}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1 text-xs text-slate-400">
                  <Star className="h-3 w-3" /> Priority {template.priority}
                </span>
                <Button size="sm" variant="outline" onClick={() => setDialogState({ mode: "edit", template })}>
                  Edit
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => confirm("Delete this workflow template?") && deleteMutation.mutate(template.id)}
                >
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog
        open={!!dialogState}
        onClose={() => {
          setDialogState(null);
          setFormError(null);
        }}
        title={dialogState?.mode === "edit" ? "Edit Workflow" : "New Workflow"}
        className="max-w-3xl"
      >
        {dialogState && (
          <WorkflowBuilder
            template={dialogState.template}
            departments={departmentOptions}
            branches={branchOptions}
            leaveTypes={leaveTypeOptions}
            employees={employeeOptions}
            submitting={createMutation.isPending || updateMutation.isPending}
            errorMessage={formError}
            onCancel={() => setDialogState(null)}
            onSubmit={(payload) => {
              if (dialogState.mode === "edit" && dialogState.template) {
                updateMutation.mutate({ id: dialogState.template.id, payload });
              } else {
                createMutation.mutate(payload);
              }
            }}
          />
        )}
      </Dialog>
    </div>
  );
}
