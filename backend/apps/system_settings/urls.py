from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.system_settings.views import (
    BackupRecordViewSet,
    EmailSettingsView,
    SMSGatewaySettingsView,
    SystemSettingViewSet,
)

router = DefaultRouter()
router.register("settings", SystemSettingViewSet, basename="system-setting")
router.register("backups", BackupRecordViewSet, basename="backup-record")

urlpatterns = [
    path("email-settings/", EmailSettingsView.as_view(), name="email-settings"),
    path("sms-settings/", SMSGatewaySettingsView.as_view(), name="sms-settings"),
] + router.urls
