from rest_framework import serializers

from apps.leave.models import (
    LeaveApprovalStep,
    LeaveBalance,
    LeavePolicy,
    LeaveRequest,
    LeaveType,
    WorkflowStep,
    WorkflowTemplate,
)


class LeavePolicySerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)

    class Meta:
        model = LeavePolicy
        fields = "__all__"


class LeaveTypeSerializer(serializers.ModelSerializer):
    policy = LeavePolicySerializer(read_only=True)

    class Meta:
        model = LeaveType
        fields = "__all__"


class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)
    remaining_days = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)

    class Meta:
        model = LeaveBalance
        fields = "__all__"


class LeaveApprovalStepSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(source="approver.full_name", read_only=True, default=None)
    acted_by_name = serializers.CharField(source="acted_by.full_name", read_only=True, default=None)

    class Meta:
        model = LeaveApprovalStep
        fields = "__all__"


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)
    approval_steps = LeaveApprovalStepSerializer(many=True, read_only=True)

    class Meta:
        model = LeaveRequest
        fields = "__all__"
        read_only_fields = ["total_days", "status", "employee"]


class WorkflowStepSerializer(serializers.ModelSerializer):
    specific_employee_name = serializers.CharField(
        source="specific_employee.full_name", read_only=True, default=None
    )
    escalate_to_employee_name = serializers.CharField(
        source="escalate_to_employee.full_name", read_only=True, default=None
    )

    class Meta:
        model = WorkflowStep
        fields = "__all__"
        extra_kwargs = {"template": {"required": False}}


class WorkflowTemplateSerializer(serializers.ModelSerializer):
    steps = WorkflowStepSerializer(many=True, required=False)

    class Meta:
        model = WorkflowTemplate
        fields = "__all__"

    def create(self, validated_data):
        steps_data = validated_data.pop("steps", [])
        departments = validated_data.pop("departments", [])
        branches = validated_data.pop("branches", [])
        leave_types = validated_data.pop("leave_types", [])

        template = WorkflowTemplate.objects.create(**validated_data)
        template.departments.set(departments)
        template.branches.set(branches)
        template.leave_types.set(leave_types)

        for step_data in steps_data:
            WorkflowStep.objects.create(template=template, **step_data)
        return template

    def update(self, instance, validated_data):
        steps_data = validated_data.pop("steps", None)
        departments = validated_data.pop("departments", None)
        branches = validated_data.pop("branches", None)
        leave_types = validated_data.pop("leave_types", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if departments is not None:
            instance.departments.set(departments)
        if branches is not None:
            instance.branches.set(branches)
        if leave_types is not None:
            instance.leave_types.set(leave_types)

        if steps_data is not None:
            instance.steps.all().delete()
            for step_data in steps_data:
                WorkflowStep.objects.create(template=instance, **step_data)

        return instance
