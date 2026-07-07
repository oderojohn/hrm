from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.mixins import AuditLogMixin, ExportMixin
from apps.core.permissions import IsHRManagerOrAbove
from apps.communication.models import Announcement, Notification
from apps.communication.serializers import AnnouncementSerializer, NotificationSerializer


class AnnouncementViewSet(AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    filterset_fields = ["audience", "is_published"]
    search_fields = ["title", "body"]
    export_headers = ["Title", "Audience", "Published"]

    def get_queryset(self):
        user = self.request.user
        qs = Announcement.objects.all()
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        qs = qs.filter(is_published=True)
        if own:
            return qs.filter(
                Q(audience=Announcement.Audience.ALL)
                | Q(
                    audience=Announcement.Audience.DEPARTMENT,
                    department_id=own.department_id,
                )
                | Q(audience=Announcement.Audience.BRANCH, branch_id=own.branch_id)
            )
        return qs.filter(audience=Announcement.Audience.ALL)

    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [IsHRManagerOrAbove()]
        return [IsAuthenticated()]

    def export_row(self, obj):
        return [obj.title, obj.audience, obj.is_published]


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    filterset_fields = ["is_read", "channel"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)
