from rest_framework.routers import DefaultRouter

from apps.leave.views import (
    LeaveBalanceViewSet,
    LeavePolicyViewSet,
    LeaveRequestViewSet,
    LeaveTypeViewSet,
    WorkflowStepViewSet,
    WorkflowTemplateViewSet,
)

router = DefaultRouter()
router.register("types", LeaveTypeViewSet, basename="leave-type")
router.register("policies", LeavePolicyViewSet, basename="leave-policy")
router.register("balances", LeaveBalanceViewSet, basename="leave-balance")
router.register("requests", LeaveRequestViewSet, basename="leave-request")
router.register("workflow-templates", WorkflowTemplateViewSet, basename="workflow-template")
router.register("workflow-steps", WorkflowStepViewSet, basename="workflow-step")

urlpatterns = router.urls
