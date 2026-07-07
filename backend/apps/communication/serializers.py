from rest_framework import serializers

from apps.communication.models import Announcement, Notification


class AnnouncementSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source="department.name", read_only=True, default=None
    )
    branch_name = serializers.CharField(
        source="branch.name", read_only=True, default=None
    )

    class Meta:
        model = Announcement
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
