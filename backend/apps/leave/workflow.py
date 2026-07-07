"""Resolves which WorkflowTemplate applies to a leave request and expands its
steps into concrete LeaveApprovalStep rows for that request.
"""
from django.utils import timezone


def resolve_template(leave_request):
    from apps.leave.models import WorkflowTemplate

    candidates = WorkflowTemplate.objects.filter(is_active=True).prefetch_related(
        "departments", "branches", "leave_types"
    )
    matches = [t for t in candidates if t.matches(leave_request)]
    if matches:
        return max(matches, key=lambda t: t.priority)
    return WorkflowTemplate.objects.filter(is_active=True, is_default=True).first()


def resolve_approver(step_def, employee):
    from apps.leave.models import WorkflowStep

    resolver = step_def.resolver_type
    if resolver == WorkflowStep.ResolverType.REPORTING_MANAGER:
        return employee.reporting_manager
    if resolver == WorkflowStep.ResolverType.SKIP_LEVEL_MANAGER:
        current = employee
        for _ in range(max(step_def.skip_levels, 1)):
            current = current.reporting_manager if current else None
            if not current:
                return None
        return current
    if resolver == WorkflowStep.ResolverType.DEPARTMENT_HEAD:
        return employee.department.head if employee.department_id else None
    if resolver == WorkflowStep.ResolverType.BRANCH_MANAGER:
        return employee.branch.manager if employee.branch_id else None
    if resolver == WorkflowStep.ResolverType.SPECIFIC_EMPLOYEE:
        return step_def.specific_employee
    if resolver == WorkflowStep.ResolverType.SYSTEM_ROLE:
        return None  # authorized by role at approval time, not a single resolved person
    return None


def _build_default_chain(leave_request):
    """Fallback used when no WorkflowTemplate is configured at all."""
    from apps.leave.models import LeaveApprovalStep, WorkflowStep

    steps = []
    order = 1
    supervisor = leave_request.employee.reporting_manager
    if supervisor is not None:
        steps.append(
            LeaveApprovalStep(
                leave_request=leave_request,
                step_order=order,
                name="Supervisor",
                resolver_type=WorkflowStep.ResolverType.REPORTING_MANAGER,
                approver=supervisor,
            )
        )
        order += 1
    steps.append(
        LeaveApprovalStep(
            leave_request=leave_request,
            step_order=order,
            name="HR",
            resolver_type=WorkflowStep.ResolverType.SYSTEM_ROLE,
            system_role="HR_MANAGER",
        )
    )
    return steps


def build_dynamic_approval_chain(leave_request):
    from apps.leave.models import LeaveApprovalStep, WorkflowStep

    template = resolve_template(leave_request)
    steps = []

    if template is None:
        steps = _build_default_chain(leave_request)
    else:
        for step_def in template.steps.filter(is_active=True).order_by("step_order"):
            if step_def.min_days is not None and leave_request.total_days < step_def.min_days:
                continue
            if step_def.max_days is not None and leave_request.total_days > step_def.max_days:
                continue

            approver = resolve_approver(step_def, leave_request.employee)
            needs_specific_person = step_def.resolver_type != WorkflowStep.ResolverType.SYSTEM_ROLE
            if needs_specific_person and approver is None:
                continue  # nobody resolvable at this level (e.g. no manager set) — auto-skip

            steps.append(
                LeaveApprovalStep(
                    leave_request=leave_request,
                    source_step=step_def,
                    step_order=step_def.step_order,
                    name=step_def.name,
                    resolver_type=step_def.resolver_type,
                    system_role=step_def.system_role,
                    approver=approver,
                )
            )

    if not steps:
        # Nothing resolvable at all (e.g. templates configured but every step skipped) —
        # fall back to a straight-to-HR step so the request is never stuck unroutable.
        steps = [
            LeaveApprovalStep(
                leave_request=leave_request,
                step_order=1,
                name="HR",
                resolver_type=WorkflowStep.ResolverType.SYSTEM_ROLE,
                system_role="HR_MANAGER",
            )
        ]

    LeaveApprovalStep.objects.bulk_create(steps)

    first_order = min(s.step_order for s in steps)
    LeaveApprovalStep.objects.filter(leave_request=leave_request, step_order=first_order).update(
        entered_at=timezone.now()
    )
