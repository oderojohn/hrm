from rest_framework import serializers

from apps.organization.models import Branch, Department, Position, WorkShift


class BranchSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source="manager.full_name", read_only=True, default=None)

    class Meta:
        model = Branch
        fields = "__all__"


class DepartmentSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    head_name = serializers.CharField(source="head.full_name", read_only=True, default=None)

    class Meta:
        model = Department
        fields = "__all__"


class PositionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)

    class Meta:
        model = Position
        fields = "__all__"


class WorkShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkShift
        fields = "__all__"
