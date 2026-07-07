from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsSuperAdmin
from apps.system_settings.models import (
    BackupRecord,
    EmailSettings,
    SMSGatewaySettings,
    SystemSetting,
)
from apps.system_settings.serializers import (
    BackupRecordSerializer,
    EmailSettingsSerializer,
    SMSGatewaySettingsSerializer,
    SystemSettingSerializer,
)


class SystemSettingViewSet(viewsets.ModelViewSet):
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [IsSuperAdmin]
    search_fields = ["key"]


class EmailSettingsView(APIView):
    """Singleton email/SMTP settings — documented here for admin review only."""

    permission_classes = [IsSuperAdmin]

    def get(self, request):
        settings_obj = EmailSettings.get_solo()
        return Response(EmailSettingsSerializer(settings_obj).data)

    def patch(self, request):
        settings_obj = EmailSettings.get_solo()
        serializer = EmailSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class SMSGatewaySettingsView(APIView):
    """Singleton SMS gateway settings — documented here for admin review only."""

    permission_classes = [IsSuperAdmin]

    def get(self, request):
        settings_obj = SMSGatewaySettings.get_solo()
        return Response(SMSGatewaySettingsSerializer(settings_obj).data)

    def patch(self, request):
        settings_obj = SMSGatewaySettings.get_solo()
        serializer = SMSGatewaySettingsSerializer(
            settings_obj, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BackupRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BackupRecord.objects.select_related("triggered_by").all()
    serializer_class = BackupRecordSerializer
    permission_classes = [IsSuperAdmin]

    @action(detail=False, methods=["post"])
    def trigger(self, request):
        record = BackupRecord.objects.create(
            triggered_by=getattr(request.user, "employee", None),
            file_name=f"backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.sqlite3",
            status=BackupRecord.Status.COMPLETED,
            notes="Placeholder backup record — wire up real backup automation at the infrastructure layer.",
        )
        return Response(BackupRecordSerializer(record).data, status=201)
