from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/organization/", include("apps.organization.urls")),
    path("api/employees/", include("apps.employees.urls")),
    path("api/leave/", include("apps.leave.urls")),
    path("api/attendance/", include("apps.attendance.urls")),
    path("api/recruitment/", include("apps.recruitment.urls")),
    path("api/performance/", include("apps.performance.urls")),
    path("api/training/", include("apps.training.urls")),
    path("api/assets/", include("apps.assets.urls")),
    path("api/documents/", include("apps.documents.urls")),
    path("api/communication/", include("apps.communication.urls")),
    path("api/helpdesk/", include("apps.helpdesk.urls")),
    path("api/disciplinary/", include("apps.disciplinary.urls")),
    path("api/exit-management/", include("apps.exit_management.urls")),
    path("api/system-settings/", include("apps.system_settings.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/core/", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
