from django.contrib import admin

from apps.core.models import AuditLog, CompanyProfile, LoginHistory, PublicHoliday


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "country")


@admin.register(PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "branch", "is_recurring_annually")
    list_filter = ("branch", "is_recurring_annually")
    search_fields = ("name",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "actor", "action", "model_name", "object_id")
    list_filter = ("action", "model_name")
    search_fields = ("object_repr", "model_name")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "timestamp", "ip_address", "success")
    list_filter = ("success",)

    def has_add_permission(self, request):
        return False
