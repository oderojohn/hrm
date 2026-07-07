import sys

from django.core.management.base import BaseCommand

from apps.attendance.models import Device
from apps.attendance.services import sync_all_devices


class Command(BaseCommand):
    help = (
        "Pulls enrolled employees and attendance logs from every active Device. "
        "Intended to run on a schedule (e.g. every 5-15 minutes via Windows Task Scheduler / cron)."
    )

    def handle(self, *args, **options):
        if not Device.objects.filter(is_active=True).exists():
            self.stdout.write(self.style.WARNING("No active devices configured — nothing to sync."))
            return

        results = sync_all_devices()
        for result in results:
            if result["error"]:
                self.stderr.write(self.style.ERROR(f"{result['device_name']}: sync failed — {result['error']}"))
                continue
            self.stdout.write(self.style.SUCCESS(f"{result['device_name']}: employees={result['employees']}"))
            self.stdout.write(self.style.SUCCESS(f"{result['device_name']}: attendance={result['attendance']}"))
            if result["attendance"]["unmatched_device_user_ids"]:
                self.stdout.write(
                    self.style.WARNING(
                        f"{result['device_name']}: unmatched device user IDs "
                        "(no Employee.device_user_id match): "
                        + ", ".join(result["attendance"]["unmatched_device_user_ids"])
                    )
                )

        if results and all(r["error"] for r in results):
            sys.exit(1)
