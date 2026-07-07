from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.attendance.views import (
    AttendanceCorrectionRequestViewSet,
    AttendanceDeviceWebhookView,
    AttendanceRecordViewSet,
    DeviceViewSet,
    PunchLogViewSet,
    QRTokenViewSet,
    SyncAgentViewSet,
    SyncEventViewSet,
    SyncPushView,
    ZKTecoSyncView,
)

router = DefaultRouter()
router.register("records", AttendanceRecordViewSet, basename="attendance-record")
router.register("corrections", AttendanceCorrectionRequestViewSet, basename="attendance-correction")
router.register("qr-tokens", QRTokenViewSet, basename="qr-token")
router.register("devices", DeviceViewSet, basename="device")
router.register("punch-logs", PunchLogViewSet, basename="punch-log")
router.register("sync-agents", SyncAgentViewSet, basename="sync-agent")
router.register("sync-events", SyncEventViewSet, basename="sync-event")

urlpatterns = [
    path("device-webhook/", AttendanceDeviceWebhookView.as_view(), name="attendance-device-webhook"),
    path("zkteco/sync/", ZKTecoSyncView.as_view(), name="zkteco-sync"),
    path("sync/push/", SyncPushView.as_view(), name="sync-push"),
] + router.urls
