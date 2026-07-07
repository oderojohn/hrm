from rest_framework.routers import DefaultRouter

from apps.exit_management.views import (
    ClearanceItemViewSet,
    ExitInterviewViewSet,
    ExitProcessViewSet,
)

router = DefaultRouter()
router.register("processes", ExitProcessViewSet, basename="exit-process")
router.register("clearance-items", ClearanceItemViewSet, basename="clearance-item")
router.register("interviews", ExitInterviewViewSet, basename="exit-interview")

urlpatterns = router.urls
