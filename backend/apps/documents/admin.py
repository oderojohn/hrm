from django.contrib import admin

from apps.documents.models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "employee", "expiry_date", "is_company_document"]
    search_fields = ["title"]
    list_filter = ["category", "is_company_document"]
