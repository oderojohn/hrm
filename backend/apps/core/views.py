from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import AuditLog, CompanyProfile, LoginHistory, PublicHoliday
from apps.core.permissions import IsHRManagerOrAbove, IsSuperAdmin
from apps.core.serializers import (
    AuditLogSerializer,
    CompanyProfileSerializer,
    LoginHistorySerializer,
    PublicHolidaySerializer,
)


class CompanyProfileView(APIView):
    """Singleton company profile — GET for anyone authenticated, PUT/PATCH for super admins."""

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH"):
            return [IsSuperAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        profile = CompanyProfile.get_solo()
        return Response(CompanyProfileSerializer(profile).data)

    def patch(self, request):
        profile = CompanyProfile.get_solo()
        serializer = CompanyProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PublicHolidayViewSet(viewsets.ModelViewSet):
    queryset = PublicHoliday.objects.all()
    serializer_class = PublicHolidaySerializer
    filterset_fields = ["branch", "is_recurring_annually"]
    search_fields = ["name", "description"]
    ordering_fields = ["date"]

    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [IsHRManagerOrAbove()]
        return [IsAuthenticated()]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("actor").all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ["action", "model_name", "actor"]
    search_fields = ["model_name", "object_repr"]
    ordering_fields = ["timestamp"]


class LoginHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LoginHistory.objects.select_related("user").all()
    serializer_class = LoginHistorySerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ["user", "success"]
    ordering_fields = ["timestamp"]
