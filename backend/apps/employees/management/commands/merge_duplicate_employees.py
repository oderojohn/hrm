from django.core.management.base import BaseCommand

from apps.employees.services import merge_duplicate_employees


class Command(BaseCommand):
    help = (
        "Merges the known duplicate employee enrollments (same person, two "
        "device_user_ids) — see KNOWN_DUPLICATE_EMPLOYEE_NUMBER_PAIRS in "
        "apps.employees.services. Reports what it would do unless --apply "
        "is passed."
    )

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Actually perform the merge (default: dry-run).")

    def handle(self, *args, **options):
        report = merge_duplicate_employees(dry_run=not options["apply"])
        for entry in report:
            if "error" in entry:
                self.stderr.write(self.style.ERROR(f"{entry['pair']}: {entry['error']}"))
                continue
            self.stdout.write(
                self.style.SUCCESS(
                    f"{entry['name']}: keep {entry['canonical']} ({entry['canonical_punches']} punches), "
                    f"merge {entry['duplicate']} ({entry['duplicate_punches']} punches)"
                    + (f" -> {entry['result']}" if "result" in entry else "")
                )
            )
        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Dry run only — pass --apply to actually merge."))
