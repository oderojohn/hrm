from rest_framework.routers import DefaultRouter

from apps.assets.views import (
    AssetAssignmentViewSet,
    AssetMaintenanceRecordViewSet,
    AssetViewSet,
    LostAssetReportViewSet,
)

router = DefaultRouter()
router.register("assets", AssetViewSet, basename="asset")
router.register("assignments", AssetAssignmentViewSet, basename="asset-assignment")
router.register("maintenance", AssetMaintenanceRecordViewSet, basename="asset-maintenance")
router.register("lost-reports", LostAssetReportViewSet, basename="lost-asset-report")

urlpatterns = router.urls
