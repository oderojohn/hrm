from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.mixins import AuditLogMixin, ExportMixin
from apps.core.models import AuditLog
from apps.core.permissions import IsHRManagerOrAbove
from apps.employees.models import Employee
from apps.leave.audit import log_leave_action
from apps.leave.models import (
    LeaveApprovalStep,
    LeaveBalance,
    LeavePolicy,
    LeaveRequest,
    LeaveType,
    WorkflowStep,
    WorkflowTemplate,
)
from apps.leave.notifications import (
    notify_advanced,
    notify_approved,
    notify_reassigned,
    notify_rejected,
    notify_returned,
    notify_submitted,
)
from apps.leave.serializers import (
    LeaveBalanceSerializer,
    LeavePolicySerializer,
    LeaveRequestSerializer,
    LeaveTypeSerializer,
    WorkflowStepSerializer,
    WorkflowTemplateSerializer,
)
from apps.leave.utils import calculate_working_days, has_overlapping_request, locking_queryset
from apps.leave.workflow import build_dynamic_approval_chain


class LeaveTypeViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = LeaveType.objects.select_related("policy").all()
    serializer_class = LeaveTypeSerializer
    filterset_fields = ["is_active", "is_paid"]
    search_fields = ["name", "code"]

    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [IsHRManagerOrAbove()]
        return [IsAuthenticated()]


class LeavePolicyViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = LeavePolicy.objects.select_related("leave_type").all()
    serializer_class = LeavePolicySerializer
    permission_classes = [IsHRManagerOrAbove]


class LeaveBalanceViewSet(AuditLogMixin, viewsets.ModelViewSet):
    serializer_class = LeaveBalanceSerializer
    filterset_fields = ["employee", "leave_type", "year"]

    def get_queryset(self):
        user = self.request.user
        qs = LeaveBalance.objects.select_related("employee", "leave_type").all()
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own:
            return qs.filter(employee__department_id=own.department_id)
        return qs.filter(employee=own) if own else qs.none()

    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [IsHRManagerOrAbove()]
        return [IsAuthenticated()]


class WorkflowTemplateViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = WorkflowTemplate.objects.prefetch_related("steps", "departments", "branches", "leave_types").all()
    serializer_class = WorkflowTemplateSerializer
    permission_classes = [IsHRManagerOrAbove]
    filterset_fields = ["is_active", "is_default"]
    search_fields = ["name"]


class WorkflowStepViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = WorkflowStep.objects.select_related("template", "specific_employee", "escalate_to_employee").all()
    serializer_class = WorkflowStepSerializer
    permission_classes = [IsHRManagerOrAbove]
    filterset_fields = ["template", "is_active"]


class LeaveRequestViewSet(AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    filterset_fields = ["employee", "leave_type", "status"]
    search_fields = ["reason"]
    ordering_fields = ["start_date", "created_at"]
    export_headers = ["Employee", "Leave Type", "Start", "End", "Days", "Status"]

    def get_queryset(self):
        user = self.request.user
        qs = LeaveRequest.objects.select_related("employee", "leave_type").prefetch_related(
            "approval_steps"
        )
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own:
            return qs.filter(employee__department_id=own.department_id)
        return qs.filter(employee=own) if own else qs.none()

    def export_row(self, obj):
        return [
            obj.employee.full_name,
            obj.leave_type.name,
            obj.start_date,
            obj.end_date,
            obj.total_days,
            obj.status,
        ]

    def _resolve_employee(self):
        employee_input = self.request.data.get("employee")
        if employee_input:
            return Employee.objects.filter(id=employee_input).first()
        return getattr(self.request.user, "employee", None)

    def perform_create(self, serializer):
        employee = self._resolve_employee()
        if not employee:
            raise ValidationError({"employee": "No employee could be resolved for this leave request."})

        data = serializer.validated_data
        start_date = data["start_date"]
        end_date = data["end_date"]
        leave_type = data["leave_type"]
        is_half_day = data.get("is_half_day", False)

        if end_date < start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

        if has_overlapping_request(employee, start_date, end_date):
            raise ValidationError(
                {"detail": "This employee already has a pending or approved leave request overlapping these dates."}
            )

        total_days = calculate_working_days(
            start_date, end_date, branch=employee.branch, is_half_day=is_half_day
        )

        policy = getattr(leave_type, "policy", None)
        if not getattr(policy, "allow_negative_balance", False):
            balance = LeaveBalance.objects.filter(
                employee=employee, leave_type=leave_type, year=start_date.year
            ).first()
            remaining = balance.remaining_days if balance else getattr(policy, "default_days_per_year", 0)
            if total_days > remaining:
                raise ValidationError(
                    {"detail": f"This request ({total_days} days) exceeds the remaining balance ({remaining} days)."}
                )

        instance = serializer.save(employee=employee, total_days=total_days)
        build_dynamic_approval_chain(instance)
        self._log(AuditLog.Action.CREATE, instance)
        log_leave_action(self.request, AuditLog.Action.CREATE, instance, {"event": "submitted"})
        notify_submitted(instance)

    def _actionable_step(self, leave_request, step_id=None):
        """Returns (step, parallel_group) for the current user, or (None, group) if
        the request has pending steps but none the current user is authorized to act on."""
        pending = leave_request.approval_steps.filter(status=LeaveApprovalStep.Status.PENDING)
        first = pending.order_by("step_order").first()
        if not first:
            return None, []
        group = list(pending.filter(step_order=first.step_order))

        if step_id:
            match = next((s for s in group if str(s.id) == str(step_id)), None)
            return match, group

        request = self.request
        user_employee = getattr(request.user, "employee", None)
        is_hr = request.user.role in (request.user.Role.SUPER_ADMIN, request.user.Role.HR_MANAGER)

        for step in group:
            if user_employee and step.approver_id == user_employee.id:
                return step, group
            if step.system_role and request.user.role == step.system_role:
                return step, group

        if is_hr:
            return group[0], group

        return None, group

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        leave_request = self.get_object()
        comment = request.data.get("comment", "")
        step, group = self._actionable_step(leave_request, request.data.get("step_id"))

        if not group:
            return Response({"detail": "No pending approval step."}, status=400)
        if not step:
            return Response({"detail": "Not authorized to approve this step."}, status=403)

        user_employee = getattr(request.user, "employee", None)
        step.status = LeaveApprovalStep.Status.APPROVED
        step.comment = comment
        step.acted_by = user_employee
        step.acted_at = timezone.now()
        step.save()
        log_leave_action(request, AuditLog.Action.APPROVE, leave_request, {"step": step.name, "comment": comment})

        template = getattr(step.source_step, "template", None)
        require_all = bool(template and template.require_all_parallel_approvers)

        if len(group) > 1 and not require_all:
            for sibling in group:
                if sibling.id != step.id:
                    sibling.status = LeaveApprovalStep.Status.SKIPPED
                    sibling.save(update_fields=["status"])

        level_cleared = True
        if len(group) > 1 and require_all:
            level_cleared = not leave_request.approval_steps.filter(
                step_order=step.step_order, status=LeaveApprovalStep.Status.PENDING
            ).exists()

        if level_cleared:
            next_step = (
                leave_request.approval_steps.filter(status=LeaveApprovalStep.Status.PENDING)
                .order_by("step_order")
                .first()
            )
            if next_step:
                leave_request.approval_steps.filter(step_order=next_step.step_order).update(
                    entered_at=timezone.now()
                )
                notify_advanced(leave_request)
            else:
                leave_request.status = LeaveRequest.Status.APPROVED
                leave_request.save(update_fields=["status"])
                with transaction.atomic():
                    balance, _ = locking_queryset(LeaveBalance.objects).get_or_create(
                        employee=leave_request.employee,
                        leave_type=leave_request.leave_type,
                        year=leave_request.start_date.year,
                        defaults={
                            "allocated_days": getattr(
                                getattr(leave_request.leave_type, "policy", None),
                                "default_days_per_year",
                                0,
                            )
                        },
                    )
                    balance.used_days += leave_request.total_days
                    balance.save(update_fields=["used_days"])
                notify_approved(leave_request)

        return Response(LeaveRequestSerializer(leave_request).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        leave_request = self.get_object()
        comment = request.data.get("comment", "")
        step, group = self._actionable_step(leave_request, request.data.get("step_id"))

        if group and not step:
            return Response({"detail": "Not authorized to reject this step."}, status=403)

        user_employee = getattr(request.user, "employee", None)
        if step:
            step.status = LeaveApprovalStep.Status.REJECTED
            step.comment = comment
            step.acted_by = user_employee
            step.acted_at = timezone.now()
            step.save()

        leave_request.status = LeaveRequest.Status.REJECTED
        leave_request.save(update_fields=["status"])
        log_leave_action(request, AuditLog.Action.REJECT, leave_request, {"comment": comment})
        notify_rejected(leave_request, comment)
        return Response(LeaveRequestSerializer(leave_request).data)

    @action(detail=True, methods=["post"])
    def reassign(self, request, pk=None):
        """Delegate/forward a pending approval step to a different employee."""
        leave_request = self.get_object()
        new_approver_id = request.data.get("approver")
        comment = request.data.get("comment", "")
        step, group = self._actionable_step(leave_request, request.data.get("step_id"))

        if not group:
            return Response({"detail": "No pending approval step."}, status=400)
        if not step:
            return Response({"detail": "Not authorized to reassign this step."}, status=403)

        new_approver = Employee.objects.filter(id=new_approver_id).first()
        if not new_approver:
            return Response({"detail": "New approver not found."}, status=400)

        step.approver = new_approver
        step.comment = comment
        step.entered_at = timezone.now()
        step.reminder_sent_at = None
        step.escalated_at = None
        step.save()
        log_leave_action(
            request,
            AuditLog.Action.OTHER,
            leave_request,
            {"event": "reassigned", "step": step.name, "new_approver_id": new_approver.id, "comment": comment},
        )
        notify_reassigned(step)
        return Response(LeaveRequestSerializer(leave_request).data)

    @action(detail=True, methods=["post"])
    def return_for_correction(self, request, pk=None):
        leave_request = self.get_object()
        comment = request.data.get("comment", "")
        step, group = self._actionable_step(leave_request, request.data.get("step_id"))

        if group and not step:
            return Response({"detail": "Not authorized to return this request."}, status=403)

        leave_request.status = LeaveRequest.Status.RETURNED
        leave_request.save(update_fields=["status"])
        log_leave_action(request, AuditLog.Action.OTHER, leave_request, {"event": "returned", "comment": comment})
        notify_returned(leave_request, comment)
        return Response(LeaveRequestSerializer(leave_request).data)

    @action(detail=True, methods=["post"])
    def resubmit(self, request, pk=None):
        """Employee edits a RETURNED request and re-enters the workflow from step 1."""
        leave_request = self.get_object()
        own = getattr(request.user, "employee", None)
        is_hr = request.user.role in (request.user.Role.SUPER_ADMIN, request.user.Role.HR_MANAGER)

        if not is_hr and not (own and own.id == leave_request.employee_id):
            return Response({"detail": "Not authorized to resubmit this request."}, status=403)
        if leave_request.status != LeaveRequest.Status.RETURNED:
            return Response({"detail": "Only returned requests can be resubmitted."}, status=400)

        for field in ("start_date", "end_date", "reason", "is_half_day", "half_day_period"):
            if field in request.data:
                setattr(leave_request, field, request.data[field])

        leave_request.total_days = calculate_working_days(
            leave_request.start_date,
            leave_request.end_date,
            branch=leave_request.employee.branch,
            is_half_day=leave_request.is_half_day,
        )
        leave_request.status = LeaveRequest.Status.PENDING
        leave_request.save()

        leave_request.approval_steps.all().delete()
        build_dynamic_approval_chain(leave_request)
        log_leave_action(request, AuditLog.Action.OTHER, leave_request, {"event": "resubmitted"})
        notify_submitted(leave_request)
        return Response(LeaveRequestSerializer(leave_request).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        leave_request = self.get_object()
        user = request.user
        own = getattr(user, "employee", None)
        is_hr = user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER)

        if not is_hr and not (own and own.id == leave_request.employee_id):
            return Response({"detail": "Not authorized to cancel this request."}, status=403)

        if leave_request.status == LeaveRequest.Status.APPROVED:
            with transaction.atomic():
                try:
                    balance = locking_queryset(LeaveBalance.objects).get(
                        employee=leave_request.employee,
                        leave_type=leave_request.leave_type,
                        year=leave_request.start_date.year,
                    )
                    balance.used_days -= leave_request.total_days
                    balance.save(update_fields=["used_days"])
                except LeaveBalance.DoesNotExist:
                    pass

        leave_request.status = LeaveRequest.Status.CANCELLED
        leave_request.cancelled_reason = request.data.get("reason", "")
        leave_request.save(update_fields=["status", "cancelled_reason"])
        log_leave_action(request, AuditLog.Action.CANCEL, leave_request, {"reason": leave_request.cancelled_reason})
        return Response(LeaveRequestSerializer(leave_request).data)

    @action(detail=False, methods=["get"])
    def calendar(self, request):
        scope = request.query_params.get("scope", "personal")
        qs = self.get_queryset().filter(status=LeaveRequest.Status.APPROVED)

        if scope == "team":
            own = getattr(request.user, "employee", None)
            if own and own.department_id:
                qs = qs.filter(employee__department_id=own.department_id)
        else:
            own = getattr(request.user, "employee", None)
            qs = qs.filter(employee=own) if own else qs.none()

        start = request.query_params.get("start")
        end = request.query_params.get("end")
        if start:
            qs = qs.filter(end_date__gte=start)
        if end:
            qs = qs.filter(start_date__lte=end)

        return Response(LeaveRequestSerializer(qs, many=True).data)
