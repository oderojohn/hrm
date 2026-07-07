from django.contrib import admin

from apps.assets.models import (
    Asset,
    AssetAssignment,
    AssetMaintenanceRecord,
    LostAssetReport,
)


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("asset_tag", "name", "category", "condition", "status", "branch")
    list_filter = ("category", "status", "condition", "branch")
    search_fields = ("asset_tag", "name", "serial_number")


@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = ("asset", "employee", "assigned_date", "returned_at")
    list_filter = ("assigned_date", "returned_at")
    search_fields = ("asset__asset_tag", "employee__first_name", "employee__last_name")


@admin.register(AssetMaintenanceRecord)
class AssetMaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ("asset", "reported_date", "status", "resolved_date")
    list_filter = ("status",)
    search_fields = ("asset__asset_tag", "description")


@admin.register(LostAssetReport)
class LostAssetReportAdmin(admin.ModelAdmin):
    list_display = ("asset", "employee", "reported_date", "status")
    list_filter = ("status",)
    search_fields = ("asset__asset_tag", "circumstances")
