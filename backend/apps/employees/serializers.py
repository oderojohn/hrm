from rest_framework import serializers

from apps.employees.models import (
    Certification,
    Education,
    Employee,
    EmploymentHistoryRecord,
)


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = "__all__"


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = "__all__"


class EmploymentHistoryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmploymentHistoryRecord
        fields = "__all__"


class EmployeeListSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    position_title = serializers.CharField(source="position.title", read_only=True, default=None)
    branch_name = serializers.CharField(source="branch.name", read_only=True, default=None)

    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_number",
            "photo",
            "full_name",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "department_name",
            "position_title",
            "branch_name",
            "employment_type",
            "employment_status",
            "employment_date",
            "reporting_manager",
        ]


class EmployeeSelfServiceSerializer(serializers.ModelSerializer):
    """Fields an employee may edit on their own record. Deliberately excludes
    employment/department/legal-identifier fields, which stay HR-controlled
    through the main EmployeeDetailSerializer."""

    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    position_title = serializers.CharField(source="position.title", read_only=True, default=None)
    branch_name = serializers.CharField(source="branch.name", read_only=True, default=None)

    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_number",
            "full_name",
            "photo",
            "email",
            "phone_number",
            "alternative_phone",
            "address",
            "county",
            "sub_county",
            "postal_address",
            "marital_status",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
            "department_name",
            "position_title",
            "branch_name",
            "employment_status",
        ]
        read_only_fields = [
            "id",
            "employee_number",
            "full_name",
            "department_name",
            "position_title",
            "branch_name",
            "employment_status",
        ]


class EmployeeDetailSerializer(serializers.ModelSerializer):
    # full_name is a model @property, not a DB field — fields="__all__" below
    # only auto-includes concrete model fields, so it must be declared explicitly
    # (unlike EmployeeListSerializer/EmployeeSelfServiceSerializer, which list
    # their fields explicitly and get it auto-detected).
    full_name = serializers.CharField(read_only=True)
    education = EducationSerializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    employment_history = EmploymentHistoryRecordSerializer(many=True, read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    position_title = serializers.CharField(source="position.title", read_only=True, default=None)
    branch_name = serializers.CharField(source="branch.name", read_only=True, default=None)
    reporting_manager_name = serializers.CharField(
        source="reporting_manager.full_name", read_only=True, default=None
    )

    class Meta:
        model = Employee
        fields = "__all__"
        read_only_fields = ["employee_number"]
