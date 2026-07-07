from rest_framework import serializers

from apps.disciplinary.models import DisciplinaryAction, DisciplinaryCase, Hearing


class DisciplinaryActionSerializer(serializers.ModelSerializer):
    issued_by_name = serializers.CharField(
        source="issued_by.full_name", read_only=True, default=None
    )

    class Meta:
        model = DisciplinaryAction
        fields = "__all__"


class HearingSerializer(serializers.ModelSerializer):
    panel_members_names = serializers.SerializerMethodField()

    class Meta:
        model = Hearing
        fields = "__all__"

    def get_panel_members_names(self, obj):
        return [member.full_name for member in obj.panel_members.all()]


class DisciplinaryCaseSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    raised_by_name = serializers.CharField(
        source="raised_by.full_name", read_only=True, default=None
    )
    actions = DisciplinaryActionSerializer(many=True, read_only=True)
    hearings = HearingSerializer(many=True, read_only=True)

    class Meta:
        model = DisciplinaryCase
        fields = "__all__"
