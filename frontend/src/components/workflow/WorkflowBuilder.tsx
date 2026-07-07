import { useState } from "react";
import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";
import type { ResolverType, WorkflowTemplate } from "../../api/leave";
import { Input } from "../ui/Input";
import { Label } from "../ui/Label";
import { Select } from "../ui/Select";
import { Textarea } from "../ui/Textarea";
import { Button } from "../ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

const RESOLVER_OPTIONS: { value: ResolverType; label: string }[] = [
  { value: "REPORTING_MANAGER", label: "Reporting Manager" },
  { value: "SKIP_LEVEL_MANAGER", label: "Manager's Manager (N levels up)" },
  { value: "DEPARTMENT_HEAD", label: "Department Head" },
  { value: "BRANCH_MANAGER", label: "Branch Manager" },
  { value: "SPECIFIC_EMPLOYEE", label: "Specific Employee" },
  { value: "SYSTEM_ROLE", label: "Anyone with a System Role" },
];

const SYSTEM_ROLE_OPTIONS = [
  { value: "SUPER_ADMIN", label: "Super Administrator" },
  { value: "HR_MANAGER", label: "HR Manager" },
  { value: "DEPARTMENT_MANAGER", label: "Department Manager" },
  { value: "EMPLOYEE", label: "Employee" },
];

const EMPLOYMENT_TYPE_OPTIONS = ["FULL_TIME", "PART_TIME", "CONTRACT", "INTERNSHIP", "CASUAL"];

interface StepDraft {
  id?: number;
  name: string;
  resolver_type: ResolverType;
  specific_employee: string;
  system_role: string;
  skip_levels: number;
  min_days: string;
  max_days: string;
  reminder_after_hours: string;
  escalation_after_hours: string;
  escalate_to_employee: string;
  is_active: boolean;
}

interface TemplateDraft {
  name: string;
  description: string;
  is_active: boolean;
  is_default: boolean;
  priority: number;
  require_all_parallel_approvers: boolean;
  departments: number[];
  branches: number[];
  leave_types: number[];
  employment_types: string[];
  steps: StepDraft[];
}

function toDraft(template?: WorkflowTemplate): TemplateDraft {
  if (!template) {
    return {
      name: "",
      description: "",
      is_active: true,
      is_default: false,
      priority: 0,
      require_all_parallel_approvers: false,
      departments: [],
      branches: [],
      leave_types: [],
      employment_types: [],
      steps: [],
    };
  }
  return {
    name: template.name,
    description: template.description,
    is_active: template.is_active,
    is_default: template.is_default,
    priority: template.priority,
    require_all_parallel_approvers: template.require_all_parallel_approvers,
    departments: template.departments,
    branches: template.branches,
    leave_types: template.leave_types,
    employment_types: template.employment_types,
    steps: template.steps.map((s) => ({
      id: s.id,
      name: s.name,
      resolver_type: s.resolver_type,
      specific_employee: s.specific_employee ? String(s.specific_employee) : "",
      system_role: s.system_role,
      skip_levels: s.skip_levels,
      min_days: s.min_days ?? "",
      max_days: s.max_days ?? "",
      reminder_after_hours: s.reminder_after_hours != null ? String(s.reminder_after_hours) : "",
      escalation_after_hours: s.escalation_after_hours != null ? String(s.escalation_after_hours) : "",
      escalate_to_employee: s.escalate_to_employee ? String(s.escalate_to_employee) : "",
      is_active: s.is_active,
    })),
  };
}

function newStep(): StepDraft {
  return {
    name: "",
    resolver_type: "REPORTING_MANAGER",
    specific_employee: "",
    system_role: "",
    skip_levels: 1,
    min_days: "",
    max_days: "",
    reminder_after_hours: "",
    escalation_after_hours: "",
    escalate_to_employee: "",
    is_active: true,
  };
}

interface Option {
  id: number;
  label: string;
}

interface WorkflowBuilderProps {
  template?: WorkflowTemplate;
  departments: Option[];
  branches: Option[];
  leaveTypes: Option[];
  employees: Option[];
  submitting?: boolean;
  errorMessage?: string | null;
  onCancel: () => void;
  onSubmit: (payload: Record<string, unknown>) => void;
}

export function WorkflowBuilder({
  template,
  departments,
  branches,
  leaveTypes,
  employees,
  submitting,
  errorMessage,
  onCancel,
  onSubmit,
}: WorkflowBuilderProps) {
  const [draft, setDraft] = useState<TemplateDraft>(() => toDraft(template));

  const updateStep = (index: number, patch: Partial<StepDraft>) => {
    setDraft((d) => ({
      ...d,
      steps: d.steps.map((s, i) => (i === index ? { ...s, ...patch } : s)),
    }));
  };

  const moveStep = (index: number, direction: -1 | 1) => {
    setDraft((d) => {
      const steps = [...d.steps];
      const target = index + direction;
      if (target < 0 || target >= steps.length) return d;
      [steps[index], steps[target]] = [steps[target], steps[index]];
      return { ...d, steps };
    });
  };

  const removeStep = (index: number) => {
    setDraft((d) => ({ ...d, steps: d.steps.filter((_, i) => i !== index) }));
  };

  const toggleMultiSelect = (field: "departments" | "branches" | "leave_types", id: number) => {
    setDraft((d) => {
      const current = d[field];
      const next = current.includes(id) ? current.filter((v) => v !== id) : [...current, id];
      return { ...d, [field]: next };
    });
  };

  const toggleEmploymentType = (value: string) => {
    setDraft((d) => ({
      ...d,
      employment_types: d.employment_types.includes(value)
        ? d.employment_types.filter((v) => v !== value)
        : [...d.employment_types, value],
    }));
  };

  const handleSubmit = () => {
    const payload = {
      name: draft.name,
      description: draft.description,
      is_active: draft.is_active,
      is_default: draft.is_default,
      priority: draft.priority,
      require_all_parallel_approvers: draft.require_all_parallel_approvers,
      departments: draft.departments,
      branches: draft.branches,
      leave_types: draft.leave_types,
      employment_types: draft.employment_types,
      steps: draft.steps.map((s, index) => ({
        step_order: index + 1,
        name: s.name,
        resolver_type: s.resolver_type,
        specific_employee: s.resolver_type === "SPECIFIC_EMPLOYEE" && s.specific_employee ? Number(s.specific_employee) : null,
        system_role: s.resolver_type === "SYSTEM_ROLE" ? s.system_role : "",
        skip_levels: s.resolver_type === "SKIP_LEVEL_MANAGER" ? s.skip_levels : 1,
        min_days: s.min_days || null,
        max_days: s.max_days || null,
        reminder_after_hours: s.reminder_after_hours ? Number(s.reminder_after_hours) : null,
        escalation_after_hours: s.escalation_after_hours ? Number(s.escalation_after_hours) : null,
        escalate_to_employee: s.escalate_to_employee ? Number(s.escalate_to_employee) : null,
        is_active: s.is_active,
      })),
    };
    onSubmit(payload);
  };

  return (
    <div className="space-y-5">
      {errorMessage && <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{errorMessage}</div>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <Label>Template Name</Label>
          <Input value={draft.name} onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))} required />
        </div>
        <div>
          <Label>Priority (higher wins on multiple matches)</Label>
          <Input
            type="number"
            value={draft.priority}
            onChange={(e) => setDraft((d) => ({ ...d, priority: Number(e.target.value) }))}
          />
        </div>
        <div className="sm:col-span-2">
          <Label>Description</Label>
          <Textarea value={draft.description} onChange={(e) => setDraft((d) => ({ ...d, description: e.target.value }))} />
        </div>
      </div>

      <div className="flex flex-wrap gap-5">
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={draft.is_active}
            onChange={(e) => setDraft((d) => ({ ...d, is_active: e.target.checked }))}
          />
          Active
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={draft.is_default}
            onChange={(e) => setDraft((d) => ({ ...d, is_default: e.target.checked }))}
          />
          Default fallback template
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={draft.require_all_parallel_approvers}
            onChange={(e) => setDraft((d) => ({ ...d, require_all_parallel_approvers: e.target.checked }))}
          />
          Require all approvers at a parallel step
        </label>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Applies To (leave blank for "any")</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <MultiCheckList
            label="Departments"
            options={departments}
            selected={draft.departments}
            onToggle={(id) => toggleMultiSelect("departments", id)}
          />
          <MultiCheckList
            label="Branches"
            options={branches}
            selected={draft.branches}
            onToggle={(id) => toggleMultiSelect("branches", id)}
          />
          <MultiCheckList
            label="Leave Types"
            options={leaveTypes}
            selected={draft.leave_types}
            onToggle={(id) => toggleMultiSelect("leave_types", id)}
          />
          <div>
            <Label>Employment Types</Label>
            <div className="space-y-1">
              {EMPLOYMENT_TYPE_OPTIONS.map((opt) => (
                <label key={opt} className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={draft.employment_types.includes(opt)}
                    onChange={() => toggleEmploymentType(opt)}
                  />
                  {opt.replaceAll("_", " ")}
                </label>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Approval Levels</CardTitle>
          <Button size="sm" variant="outline" onClick={() => setDraft((d) => ({ ...d, steps: [...d.steps, newStep()] }))}>
            <Plus className="h-3.5 w-3.5" /> Add Step
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {draft.steps.length === 0 && <p className="text-sm text-slate-400">No steps yet — add at least one.</p>}
          {draft.steps.map((step, index) => (
            <div key={index} className="rounded-md border border-slate-200 p-3">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500">LEVEL {index + 1}</span>
                <div className="flex gap-1">
                  <button
                    type="button"
                    onClick={() => moveStep(index, -1)}
                    disabled={index === 0}
                    className="rounded p-1 text-slate-400 hover:bg-slate-100 disabled:opacity-30"
                  >
                    <ArrowUp className="h-3.5 w-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => moveStep(index, 1)}
                    disabled={index === draft.steps.length - 1}
                    className="rounded p-1 text-slate-400 hover:bg-slate-100 disabled:opacity-30"
                  >
                    <ArrowDown className="h-3.5 w-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => removeStep(index)}
                    className="rounded p-1 text-red-400 hover:bg-red-50"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <Label>Label (e.g. "Head of Department")</Label>
                  <Input value={step.name} onChange={(e) => updateStep(index, { name: e.target.value })} required />
                </div>
                <div>
                  <Label>Resolves To</Label>
                  <Select
                    value={step.resolver_type}
                    onChange={(e) => updateStep(index, { resolver_type: e.target.value as ResolverType })}
                  >
                    {RESOLVER_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </Select>
                </div>

                {step.resolver_type === "SPECIFIC_EMPLOYEE" && (
                  <div>
                    <Label>Employee</Label>
                    <Select
                      value={step.specific_employee}
                      onChange={(e) => updateStep(index, { specific_employee: e.target.value })}
                    >
                      <option value="">Select...</option>
                      {employees.map((e) => (
                        <option key={e.id} value={e.id}>
                          {e.label}
                        </option>
                      ))}
                    </Select>
                  </div>
                )}
                {step.resolver_type === "SYSTEM_ROLE" && (
                  <div>
                    <Label>Role</Label>
                    <Select value={step.system_role} onChange={(e) => updateStep(index, { system_role: e.target.value })}>
                      <option value="">Select...</option>
                      {SYSTEM_ROLE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </Select>
                  </div>
                )}
                {step.resolver_type === "SKIP_LEVEL_MANAGER" && (
                  <div>
                    <Label>Levels Up</Label>
                    <Input
                      type="number"
                      min={1}
                      value={step.skip_levels}
                      onChange={(e) => updateStep(index, { skip_levels: Number(e.target.value) })}
                    />
                  </div>
                )}

                <div>
                  <Label>Only if total days ≥</Label>
                  <Input value={step.min_days} onChange={(e) => updateStep(index, { min_days: e.target.value })} />
                </div>
                <div>
                  <Label>Only if total days ≤</Label>
                  <Input value={step.max_days} onChange={(e) => updateStep(index, { max_days: e.target.value })} />
                </div>
                <div>
                  <Label>Remind after (hours)</Label>
                  <Input
                    value={step.reminder_after_hours}
                    onChange={(e) => updateStep(index, { reminder_after_hours: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Escalate after (hours)</Label>
                  <Input
                    value={step.escalation_after_hours}
                    onChange={(e) => updateStep(index, { escalation_after_hours: e.target.value })}
                  />
                </div>
                {step.escalation_after_hours && (
                  <div>
                    <Label>Escalate To</Label>
                    <Select
                      value={step.escalate_to_employee}
                      onChange={(e) => updateStep(index, { escalate_to_employee: e.target.value })}
                    >
                      <option value="">Select...</option>
                      {employees.map((e) => (
                        <option key={e.id} value={e.id}>
                          {e.label}
                        </option>
                      ))}
                    </Select>
                  </div>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={handleSubmit} loading={submitting}>
          Save Workflow
        </Button>
      </div>
    </div>
  );
}

function MultiCheckList({
  label,
  options,
  selected,
  onToggle,
}: {
  label: string;
  options: Option[];
  selected: number[];
  onToggle: (id: number) => void;
}) {
  return (
    <div>
      <Label>{label}</Label>
      <div className="max-h-32 space-y-1 overflow-y-auto rounded-md border border-slate-200 p-2">
        {options.length === 0 && <p className="text-xs text-slate-400">None available</p>}
        {options.map((opt) => (
          <label key={opt.id} className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={selected.includes(opt.id)} onChange={() => onToggle(opt.id)} />
            {opt.label}
          </label>
        ))}
      </div>
    </div>
  );
}
