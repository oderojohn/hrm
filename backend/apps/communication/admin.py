from django.contrib import admin

from apps.communication.models import Announcement, Notification


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["title", "audience", "department", "branch", "is_published", "published_at"]
    list_filter = ["audience", "is_published"]
    search_fields = ["title", "body"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "recipient", "channel", "is_read", "created_at"]
    list_filter = ["channel", "is_read"]
    search_fields = ["title", "body"]
