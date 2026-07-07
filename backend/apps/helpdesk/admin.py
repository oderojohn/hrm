from django.contrib import admin

from apps.helpdesk.models import Ticket, TicketAttachment, TicketComment


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "category",
        "priority",
        "status",
        "raised_by",
        "assigned_to",
        "created_at",
    )
    list_filter = ("category", "priority", "status")
    search_fields = ("subject", "description")
    inlines = [TicketCommentInline, TicketAttachmentInline]
