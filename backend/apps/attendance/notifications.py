"""Thin notification hooks for the attendance-correction approval lifecycle,
mirroring apps.leave.notifications — same Notification model + the
admin-configured SMTP connection, just for the Employee -> Supervisor -> HR
correction chain.
"""
from django.core.mail import send_mail

from apps.system_settings.email import get_configured_connection, get_from_email


def _notify_user(user, title, body, related_url=""):
    if not user:
        return
    from apps.communication.models import Notification

    Notification.objects.create(
        recipient=user,
        channel=Notification.Channel.IN_APP,
        title=title,
        body=body,
        related_url=related_url,
    )
    if user.email:
        try:
            send_mail(title, body, get_from_email(), [user.email], connection=get_configured_connection(), fail_silently=True)
        except Exception:
            pass


def notify_employee(employee, title, body, related_url=""):
    if employee and employee.user_id:
        _notify_user(employee.user, title, body, related_url)


def notify_hr(title, body, related_url=""):
    from apps.accounts.models import User

    for user in User.objects.filter(
        role__in=[User.Role.HR_MANAGER, User.Role.SUPER_ADMIN], is_active=True
    ):
        _notify_user(user, title, body, related_url)


def notify_submitted(correction):
    if correction.supervisor_status == correction.SupervisorStatus.PENDING:
        notify_employee(
            correction.supervisor,
            "Attendance correction needs your approval",
            f"{correction.employee.full_name} submitted a correction request for {correction.date}.",
        )
    else:
        notify_hr(
            "Attendance correction awaiting approval",
            f"{correction.employee.full_name} submitted a correction request for {correction.date}.",
        )


def notify_supervisor_approved(correction):
    notify_hr(
        "Attendance correction awaiting HR approval",
        f"{correction.employee.full_name}'s correction for {correction.date} was approved by "
        f"their supervisor and now awaits HR approval.",
    )


def notify_approved(correction):
    notify_employee(
        correction.employee,
        "Attendance correction approved",
        f"Your correction request for {correction.date} has been approved.",
    )


def notify_rejected(correction, stage=""):
    by = " by your supervisor" if stage == "supervisor" else ""
    notify_employee(
        correction.employee,
        "Attendance correction rejected",
        f"Your correction request for {correction.date} was rejected{by}.",
    )
