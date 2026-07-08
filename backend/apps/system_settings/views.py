from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsSuperAdmin
from apps.system_settings.email import get_configured_connection, get_from_email
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


class EmailSettingsTestView(APIView):
    """Sends a real test email through the currently saved SMTP settings, so
    an admin can confirm Gmail credentials actually work before relying on
    them for real leave/attendance notifications.
    """

    permission_classes = [IsSuperAdmin]

    def post(self, request):
        connection = get_configured_connection()
        if connection is None:
            return Response(
                {"detail": "Set SMTP host, username, and password first."}, status=status.HTTP_400_BAD_REQUEST
            )
        recipient = request.data.get("to") or request.user.email
        if not recipient:
            return Response({"detail": "No recipient email address available."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            send_mail(
                "Nexas HRM — Test Email",
                "This is a test email confirming your SMTP settings are working correctly.",
                get_from_email(),
                [recipient],
                connection=connection,
                fail_silently=False,
            )
        except Exception as exc:
            return Response({"detail": f"Failed to send: {exc}"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": f"Test email sent to {recipient}."})


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
