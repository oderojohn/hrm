"""Thin notification hooks for the leave approval lifecycle, built on the
existing apps.communication.Notification model + Django's configured email backend.
"""
from django.conf import settings
from django.core.mail import send_mail


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
            send_mail(title, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        except Exception:
            pass


def notify_employee(employee, title, body, related_url=""):
    if employee and employee.user_id:
        _notify_user(employee.user, title, body, related_url)


def notify_step(step):
    """Notifies whoever can act on a pending approval step — either the
    resolved approver, or everyone holding the step's system role."""
    if step.approver:
        notify_employee(
            step.approver,
            f"Leave approval needed: {step.name}",
            f"A leave request is awaiting your approval as {step.name}.",
        )
    elif step.system_role:
        from apps.accounts.models import User

        for user in User.objects.filter(role=step.system_role, is_active=True):
            _notify_user(
                user,
                f"Leave approval needed: {step.name}",
                f"A leave request is awaiting {step.name} approval.",
            )


def _notify_current_step(leave_request):
    step = leave_request.approval_steps.filter(status="PENDING").order_by("step_order").first()
    if step:
        notify_step(step)


def notify_submitted(leave_request):
    _notify_current_step(leave_request)


def notify_advanced(leave_request):
    _notify_current_step(leave_request)


def notify_approved(leave_request):
    notify_employee(
        leave_request.employee,
        "Leave request approved",
        f"Your {leave_request.leave_type.name} request ({leave_request.start_date} to "
        f"{leave_request.end_date}) has been approved.",
    )


def notify_rejected(leave_request, comment=""):
    notify_employee(
        leave_request.employee,
        "Leave request rejected",
        f"Your {leave_request.leave_type.name} request has been rejected. {comment}".strip(),
    )


def notify_returned(leave_request, comment=""):
    notify_employee(
        leave_request.employee,
        "Leave request returned for correction",
        f"Your leave request needs corrections: {comment}".strip(),
    )


def notify_reassigned(step):
    notify_step(step)
