from rest_framework import serializers

from apps.exit_management.models import ClearanceItem, ExitInterview, ExitProcess


class ClearanceItemSerializer(serializers.ModelSerializer):
    cleared_by_name = serializers.CharField(source="cleared_by.full_name", read_only=True)

    class Meta:
        model = ClearanceItem
        fields = "__all__"


class ExitInterviewSerializer(serializers.ModelSerializer):
    conducted_by_name = serializers.CharField(source="conducted_by.full_name", read_only=True)

    class Meta:
        model = ExitInterview
        fields = "__all__"


class ExitProcessSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    clearance_items = ClearanceItemSerializer(many=True, read_only=True)

    class Meta:
        model = ExitProcess
        fields = "__all__"
