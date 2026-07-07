from django.contrib import admin

from apps.performance.models import (
    Goal,
    KPI,
    PerformanceReview,
    PromotionRecommendation,
)


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("title", "employee", "status", "target_date", "weight_percentage")
    list_filter = ("status",)
    search_fields = ("title", "employee__first_name", "employee__last_name")


@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ("name", "employee", "goal", "target_value", "actual_value")
    search_fields = ("name", "employee__first_name", "employee__last_name")


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "reviewer",
        "review_type",
        "review_period_start",
        "review_period_end",
        "overall_rating",
        "status",
    )
    list_filter = ("review_type", "status")
    search_fields = ("employee__first_name", "employee__last_name")


@admin.register(PromotionRecommendation)
class PromotionRecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "current_position",
        "recommended_position",
        "status",
        "decided_at",
    )
    list_filter = ("status",)
    search_fields = ("employee__first_name", "employee__last_name", "justification")
