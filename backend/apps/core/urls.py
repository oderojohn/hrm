from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.core.views import (
    AuditLogViewSet,
    CompanyProfileView,
    LoginHistoryViewSet,
    PublicHolidayViewSet,
)

router = DefaultRouter()
router.register("public-holidays", PublicHolidayViewSet, basename="public-holiday")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")
router.register("login-history", LoginHistoryViewSet, basename="login-history")

urlpatterns = [
    path("company-profile/", CompanyProfileView.as_view(), name="company-profile"),
] + router.urls
