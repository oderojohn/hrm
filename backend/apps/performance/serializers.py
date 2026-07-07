from rest_framework import serializers

from apps.performance.models import (
    Goal,
    KPI,
    PerformanceReview,
    PromotionRecommendation,
)


class GoalSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True, default=None)

    class Meta:
        model = Goal
        fields = "__all__"


class KPISerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True, default=None)
    goal_title = serializers.CharField(source="goal.title", read_only=True, default=None)

    class Meta:
        model = KPI
        fields = "__all__"


class PerformanceReviewSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True, default=None)
    reviewer_name = serializers.CharField(source="reviewer.full_name", read_only=True, default=None)

    class Meta:
        model = PerformanceReview
        fields = "__all__"


class PromotionRecommendationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True, default=None)
    recommended_by_name = serializers.CharField(
        source="recommended_by.full_name", read_only=True, default=None
    )
    current_position_title = serializers.CharField(
        source="current_position.title", read_only=True, default=None
    )
    recommended_position_title = serializers.CharField(
        source="recommended_position.title", read_only=True, default=None
    )

    class Meta:
        model = PromotionRecommendation
        fields = "__all__"
