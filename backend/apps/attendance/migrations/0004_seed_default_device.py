from django.conf import settings
from django.db import migrations


def seed_default_device(apps, schema_editor):
    Device = apps.get_model("attendance", "Device")
    if Device.objects.exists():
        return
    Device.objects.create(
        name="Main Biometric Device",
        device_type="ZKTECO",
        ip_address=getattr(settings, "ZKTECO_DEVICE_IP", None),
        port=getattr(settings, "ZKTECO_DEVICE_PORT", 4370),
        is_active=True,
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("attendance", "0003_device_attendancerecord_device_punchlog"),
    ]

    operations = [
        migrations.RunPython(seed_default_device, noop),
    ]
