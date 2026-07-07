from apps.core.models import AuditLog


def log_leave_action(request, action, leave_request, changes=None):
    """Writes an immutable AuditLog row for a leave approval action. Approval
    history is never edited or deleted — the timeline for a request is just
    AuditLog.objects.filter(model_name="LeaveRequest", object_id=<id>).
    """
    user = request.user if request.user.is_authenticated else None
    AuditLog.objects.create(
        actor=user,
        action=action,
        model_name="LeaveRequest",
        object_id=str(leave_request.pk),
        object_repr=str(leave_request)[:255],
        changes=changes or {},
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
    )
