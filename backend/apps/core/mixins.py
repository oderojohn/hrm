from apps.core.exports import export_queryset
from apps.core.models import AuditLog
from rest_framework.decorators import action
from rest_framework.response import Response


class AuditLogMixin:
    """Writes an AuditLog row for every create/update/delete through this viewset."""

    audit_model_name = None

    def _log(self, action_name, instance, changes=None):
        user = self.request.user if self.request.user.is_authenticated else None
        AuditLog.objects.create(
            actor=user,
            action=action_name,
            model_name=self.audit_model_name or instance.__class__.__name__,
            object_id=str(instance.pk),
            object_repr=str(instance)[:255],
            changes=changes or {},
            ip_address=self.request.META.get("REMOTE_ADDR"),
            user_agent=self.request.META.get("HTTP_USER_AGENT", "")[:255],
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        self._log(AuditLog.Action.CREATE, instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._log(AuditLog.Action.UPDATE, instance)

    def perform_destroy(self, instance):
        self._log(AuditLog.Action.DELETE, instance)
        instance.delete()


class ExportMixin:
    """Adds a GET /<resource>/export/?format=csv|xlsx|pdf action to a viewset.

    Subclasses set `export_headers` and implement `export_row(obj)`.
    """

    export_headers = []

    def export_row(self, obj):
        raise NotImplementedError

    @action(detail=False, methods=["get"])
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        base_name = queryset.model._meta.verbose_name_plural.replace(" ", "_")
        response = export_queryset(
            request, queryset, self.export_headers, self.export_row, base_name
        )
        if response is None:
            return Response(
                {"detail": "Unsupported format. Use ?format=csv, xlsx, or pdf."}, status=400
            )
        return response
