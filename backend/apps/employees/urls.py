from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.employees.temp_admin_views import TempEmployeeDiagnosticsView, TempMergeDuplicateEmployeesView
from apps.employees.views import (
    CertificationViewSet,
    EducationViewSet,
    EmployeeViewSet,
    EmploymentHistoryViewSet,
)

router = DefaultRouter()
router.register("employees", EmployeeViewSet, basename="employee")
router.register("education", EducationViewSet, basename="education")
router.register("certifications", CertificationViewSet, basename="certification")
router.register("employment-history", EmploymentHistoryViewSet, basename="employment-history")

urlpatterns = router.urls + [
    path("temp-merge-duplicates/", TempMergeDuplicateEmployeesView.as_view(), name="temp-merge-duplicates"),
    path("temp-employee-diagnostics/", TempEmployeeDiagnosticsView.as_view(), name="temp-employee-diagnostics"),
]
