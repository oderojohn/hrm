from rest_framework.routers import DefaultRouter

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

urlpatterns = router.urls
