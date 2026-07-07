from rest_framework import serializers

from apps.assets.models import (
    Asset,
    AssetAssignment,
    AssetMaintenanceRecord,
    LostAssetReport,
)


class AssetSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True, default=None)

    class Meta:
        model = Asset
        fields = "__all__"


class AssetAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)

    class Meta:
        model = AssetAssignment
        fields = "__all__"


class AssetMaintenanceRecordSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source="asset.name", read_only=True, default=None)

    class Meta:
        model = AssetMaintenanceRecord
        fields = "__all__"


class LostAssetReportSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source="asset.name", read_only=True, default=None)
    employee_name = serializers.CharField(
        source="employee.full_name", read_only=True, default=None
    )

    class Meta:
        model = LostAssetReport
        fields = "__all__"
