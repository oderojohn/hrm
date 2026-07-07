from rest_framework.routers import DefaultRouter

from apps.disciplinary.views import (
    DisciplinaryActionViewSet,
    DisciplinaryCaseViewSet,
    HearingViewSet,
)

router = DefaultRouter()
router.register("cases", DisciplinaryCaseViewSet, basename="disciplinary-case")
router.register("actions", DisciplinaryActionViewSet, basename="disciplinary-action")
router.register("hearings", HearingViewSet, basename="disciplinary-hearing")

urlpatterns = router.urls
