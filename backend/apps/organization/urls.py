from rest_framework.routers import DefaultRouter

from apps.organization.views import (
    BranchViewSet,
    DepartmentViewSet,
    PositionViewSet,
    WorkShiftViewSet,
)

router = DefaultRouter()
router.register("branches", BranchViewSet, basename="branch")
router.register("departments", DepartmentViewSet, basename="department")
router.register("positions", PositionViewSet, basename="position")
router.register("work-shifts", WorkShiftViewSet, basename="work-shift")

urlpatterns = router.urls
