from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import AuditLog
from apps.leave.models import LeaveApprovalStep
from apps.leave.notifications import notify_step


class Command(BaseCommand):
    help = (
        "Sends reminders and escalates overdue pending leave approval steps. "
        "Intended to run on a schedule (e.g. hourly via Windows Task Scheduler / cron)."
    )

    def handle(self, *args, **options):
        now = timezone.now()
        reminders_sent = 0
        escalations = 0

        pending_steps = LeaveApprovalStep.objects.filter(
            status=LeaveApprovalStep.Status.PENDING,
            entered_at__isnull=False,
            source_step__isnull=False,
        ).select_related("source_step", "source_step__escalate_to_employee", "leave_request")

        for step in pending_steps:
            source = step.source_step
            elapsed = now - step.entered_at

            if (
                source.reminder_after_hours is not None
                and not step.reminder_sent_at
                and elapsed >= timedelta(hours=source.reminder_after_hours)
            ):
                notify_step(step)
                step.reminder_sent_at = now
                step.save(update_fields=["reminder_sent_at"])
                reminders_sent += 1

            if (
                source.escalation_after_hours is not None
                and not step.escalated_at
                and elapsed >= timedelta(hours=source.escalation_after_hours)
            ):
                AuditLog.objects.create(
                    action=AuditLog.Action.OTHER,
                    model_name="LeaveRequest",
                    object_id=str(step.leave_request_id),
                    object_repr=str(step.leave_request)[:255],
                    changes={
                        "event": "escalated",
                        "step": step.name,
                        "escalate_to_employee_id": getattr(source.escalate_to_employee, "id", None),
                    },
                )
                if source.escalate_to_employee:
                    step.approver = source.escalate_to_employee
                    step.entered_at = now
                    step.reminder_sent_at = None
                step.escalated_at = now
                step.save()
                notify_step(step)
                escalations += 1

        self.stdout.write(
            self.style.SUCCESS(f"Reminders sent: {reminders_sent}. Escalations processed: {escalations}.")
        )
