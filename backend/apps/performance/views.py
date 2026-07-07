from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.mixins import AuditLogMixin, ExportMixin
from apps.core.permissions import IsHRManagerOrAbove
from apps.performance.models import (
    Goal,
    KPI,
    PerformanceReview,
    PromotionRecommendation,
)
from apps.performance.serializers import (
    GoalSerializer,
    KPISerializer,
    PerformanceReviewSerializer,
    PromotionRecommendationSerializer,
)


class WriteRestrictedMixin:
    """Read access for any authenticated user; writes restricted to HR managers or above."""

    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [IsHRManagerOrAbove()]
        return [IsAuthenticated()]


class GoalViewSet(WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    filterset_fields = ["employee", "status"]
    search_fields = ["title", "description"]
    ordering_fields = ["target_date", "created_at"]
    export_headers = ["Employee", "Title", "Status", "Target Date", "Weight %"]

    def get_queryset(self):
        user = self.request.user
        qs = Goal.objects.select_related("employee")
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own:
            return qs.filter(employee__department_id=own.department_id)
        return qs.filter(employee=own) if own else qs.none()

    def export_row(self, obj):
        return [
            obj.employee.full_name,
            obj.title,
            obj.status,
            obj.target_date,
            obj.weight_percentage,
        ]


class KPIViewSet(WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    serializer_class = KPISerializer
    filterset_fields = ["employee", "goal"]
    search_fields = ["name"]
    ordering_fields = ["created_at"]
    export_headers = ["Employee", "Name", "Target", "Actual", "Unit"]

    def get_queryset(self):
        user = self.request.user
        qs = KPI.objects.select_related("employee", "goal")
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own:
            return qs.filter(employee__department_id=own.department_id)
        return qs.filter(employee=own) if own else qs.none()

    def export_row(self, obj):
        return [
            obj.employee.full_name,
            obj.name,
            obj.target_value,
            obj.actual_value,
            obj.measurement_unit,
        ]


class PerformanceReviewViewSet(AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    serializer_class = PerformanceReviewSerializer
    filterset_fields = ["employee", "reviewer", "review_type", "status"]
    search_fields = ["manager_comments", "employee_feedback"]
    ordering_fields = ["review_period_start", "review_period_end", "created_at"]
    export_headers = ["Employee", "Reviewer", "Period Start", "Period End", "Type", "Rating", "Status"]

    def get_permissions(self):
        if self.action == "acknowledge":
            return [IsAuthenticated()]
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [IsHRManagerOrAbove()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = PerformanceReview.objects.select_related("employee", "reviewer")
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own:
            return qs.filter(employee__department_id=own.department_id)
        return qs.filter(employee=own) if own else qs.none()

    def export_row(self, obj):
        return [
            obj.employee.full_name,
            obj.reviewer.full_name if obj.reviewer else "",
            obj.review_period_start,
            obj.review_period_end,
            obj.review_type,
            obj.overall_rating,
            obj.status,
        ]

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        review = self.get_object()
        own = getattr(request.user, "employee", None)
        if not own or own.id != review.employee_id:
            return Response({"detail": "Only the reviewed employee can acknowledge this."}, status=403)
        review.employee_feedback = request.data.get("employee_feedback", review.employee_feedback)
        review.status = PerformanceReview.Status.ACKNOWLEDGED
        review.save()
        return Response(PerformanceReviewSerializer(review).data)


class PromotionRecommendationViewSet(
    WriteRestrictedMixin, AuditLogMixin, ExportMixin, viewsets.ModelViewSet
):
    serializer_class = PromotionRecommendationSerializer
    filterset_fields = ["employee", "status", "current_position", "recommended_position"]
    search_fields = ["justification"]
    ordering_fields = ["created_at", "decided_at"]
    export_headers = ["Employee", "Current Position", "Recommended Position", "Status"]

    def get_queryset(self):
        user = self.request.user
        qs = PromotionRecommendation.objects.select_related(
            "employee", "recommended_by", "current_position", "recommended_position"
        )
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return qs
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own:
            return qs.filter(employee__department_id=own.department_id)
        return qs.filter(employee=own) if own else qs.none()

    def export_row(self, obj):
        return [
            obj.employee.full_name,
            obj.current_position.title if obj.current_position else "",
            obj.recommended_position.title if obj.recommended_position else "",
            obj.status,
        ]
