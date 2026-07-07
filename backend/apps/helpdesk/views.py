from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import AuditLogMixin, ExportMixin
from apps.core.models import AuditLog
from apps.core.permissions import IsHRManagerOrAbove
from apps.helpdesk.models import Ticket, TicketAttachment, TicketComment
from apps.helpdesk.serializers import (
    TicketAttachmentSerializer,
    TicketCommentSerializer,
    TicketSerializer,
)


class TicketViewSet(AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    filterset_fields = ["category", "status", "priority", "assigned_to"]
    search_fields = ["subject", "description"]
    ordering_fields = ["created_at", "priority", "status"]
    export_headers = ["Subject", "Category", "Priority", "Status", "Raised By"]

    def get_queryset(self):
        user = self.request.user
        qs = Ticket.objects.select_related("raised_by", "assigned_to")
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        return qs.filter(Q(raised_by=own) | Q(assigned_to=own)) if own else qs.none()

    def export_row(self, obj):
        return [
            obj.subject,
            obj.category,
            obj.priority,
            obj.status,
            obj.raised_by.full_name if obj.raised_by else "",
        ]

    def perform_create(self, serializer):
        employee = getattr(self.request.user, "employee", None)
        instance = serializer.save(raised_by=employee)
        self._log(AuditLog.Action.CREATE, instance)

    @action(detail=True, methods=["post"], permission_classes=[IsHRManagerOrAbove])
    def assign(self, request, pk=None):
        ticket = self.get_object()
        ticket.assigned_to_id = request.data.get("assigned_to")
        ticket.status = Ticket.Status.ASSIGNED
        ticket.save()
        return Response(TicketSerializer(ticket).data)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        ticket = self.get_object()
        own = getattr(request.user, "employee", None)
        is_hr = request.user.role in (request.user.Role.SUPER_ADMIN, request.user.Role.HR_MANAGER)
        if not is_hr and not (own and ticket.assigned_to_id == own.id):
            return Response({"detail": "Not authorized to resolve this ticket."}, status=403)
        ticket.status = Ticket.Status.RESOLVED
        ticket.resolved_at = timezone.now()
        ticket.save()
        return Response(TicketSerializer(ticket).data)


class TicketCommentViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = TicketComment.objects.select_related("ticket", "author").all()
    serializer_class = TicketCommentSerializer
    filterset_fields = ["ticket"]

    def perform_create(self, serializer):
        author = getattr(self.request.user, "employee", None)
        instance = serializer.save(author=author)
        self._log(AuditLog.Action.CREATE, instance)


class TicketAttachmentViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = TicketAttachment.objects.select_related("ticket", "uploaded_by").all()
    serializer_class = TicketAttachmentSerializer
    filterset_fields = ["ticket"]

    def perform_create(self, serializer):
        uploaded_by = getattr(self.request.user, "employee", None)
        instance = serializer.save(uploaded_by=uploaded_by)
        self._log(AuditLog.Action.CREATE, instance)
