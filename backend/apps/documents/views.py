from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.mixins import AuditLogMixin, ExportMixin
from apps.core.permissions import IsHRManagerOrAbove
from apps.documents.models import Document
from apps.documents.serializers import DocumentSerializer


class DocumentViewSet(AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = Document.objects.select_related("employee", "uploaded_by").all()
    serializer_class = DocumentSerializer
    filterset_fields = ["category", "employee", "is_company_document"]
    search_fields = ["title"]
    ordering_fields = ["expiry_date", "created_at"]
    export_headers = ["Title", "Category", "Employee", "Expiry Date"]

    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [IsHRManagerOrAbove()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role in {user.Role.SUPER_ADMIN, user.Role.HR_MANAGER}:
            return qs
        own = getattr(user, "employee", None)
        if own:
            return qs.filter(Q(employee=own) | Q(is_company_document=True))
        return qs.filter(is_company_document=True)

    def export_row(self, obj):
        return [
            obj.title,
            obj.category,
            obj.employee.full_name if obj.employee else "Company-wide",
            obj.expiry_date,
        ]

    @action(detail=False, methods=["get"], permission_classes=[IsHRManagerOrAbove])
    def expiring(self, request):
        days = int(request.query_params.get("days", 30))
        cutoff = timezone.now().date() + timedelta(days=days)
        qs = Document.objects.filter(
            expiry_date__isnull=False,
            expiry_date__lte=cutoff,
            expiry_date__gte=timezone.now().date(),
        )
        return Response(DocumentSerializer(qs, many=True).data)
