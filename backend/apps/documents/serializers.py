from rest_framework import serializers

from apps.documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source="employee.full_name", read_only=True, default=None
    )

    class Meta:
        model = Document
        fields = "__all__"
