from django.utils.crypto import get_random_string
from rest_framework import serializers

from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, style={"input_type": "password"}
    )
    employee_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone_number",
            "is_active",
            "is_2fa_enabled",
            "must_change_password",
            "date_joined",
            "password",
            "employee_id",
        ]
        read_only_fields = ["id", "date_joined", "is_2fa_enabled"]

    def get_employee_id(self, obj):
        employee = getattr(obj, "employee", None)
        return employee.id if employee else None

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        user.set_password(password or get_random_string(12))
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
