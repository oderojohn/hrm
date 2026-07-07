from rest_framework.routers import DefaultRouter

from apps.training.views import (
    TrainingAttendanceViewSet,
    TrainingProgramViewSet,
    TrainingSessionViewSet,
)

router = DefaultRouter()
router.register("programs", TrainingProgramViewSet, basename="training-program")
router.register("sessions", TrainingSessionViewSet, basename="training-session")
router.register("attendance", TrainingAttendanceViewSet, basename="training-attendance")

urlpatterns = router.urls
