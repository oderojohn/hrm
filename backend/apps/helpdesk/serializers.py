from rest_framework import serializers

from apps.helpdesk.models import Ticket, TicketAttachment, TicketComment


class TicketSerializer(serializers.ModelSerializer):
    raised_by_name = serializers.CharField(source="raised_by.full_name", read_only=True, default=None)
    assigned_to_name = serializers.CharField(
        source="assigned_to.full_name", read_only=True, default=None
    )
    response_time_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = ["raised_by", "status", "resolved_at"]


class TicketCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True, default=None)

    class Meta:
        model = TicketComment
        fields = "__all__"
        read_only_fields = ["author"]


class TicketAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(
        source="uploaded_by.full_name", read_only=True, default=None
    )

    class Meta:
        model = TicketAttachment
        fields = "__all__"
        read_only_fields = ["uploaded_by"]
