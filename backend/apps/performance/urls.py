from rest_framework.routers import DefaultRouter

from apps.performance.views import (
    GoalViewSet,
    KPIViewSet,
    PerformanceReviewViewSet,
    PromotionRecommendationViewSet,
)

router = DefaultRouter()
router.register("goals", GoalViewSet, basename="goal")
router.register("kpis", KPIViewSet, basename="kpi")
router.register("reviews", PerformanceReviewViewSet, basename="performance-review")
router.register("promotions", PromotionRecommendationViewSet, basename="promotion-recommendation")

urlpatterns = router.urls
