from rest_framework import serializers

from apps.training.models import TrainingAttendance, TrainingProgram, TrainingSession


class TrainingProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingProgram
        fields = "__all__"


class TrainingSessionSerializer(serializers.ModelSerializer):
    program_title = serializers.CharField(source="program.title", read_only=True)

    class Meta:
        model = TrainingSession
        fields = "__all__"


class TrainingAttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)

    class Meta:
        model = TrainingAttendance
        fields = "__all__"
