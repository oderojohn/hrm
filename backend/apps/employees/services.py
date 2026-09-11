from django.db import transaction

from apps.attendance.models import AttendanceRecord, PunchLog
from apps.attendance.services import ingest_punches
from apps.employees.models import Employee

# Found 2026-09: these employee numbers are the same person enrolled twice on
# the Bahati device under two different device_user_ids (confirmed by exact
# full-name match + non-overlapping punch history) — each copy's attendance
# looked artificially sparse because their real history was split across two
# Employee rows. Hardcoded rather than name-matched generically so a genuine
# coincidence (two different people sharing a name) can never be merged by
# mistake.
KNOWN_DUPLICATE_EMPLOYEE_NUMBER_PAIRS = [
    ("EMBO066", "EMBO075"),
    ("EMBO067", "EMBO076"),
    ("EMBO069", "EMBO077"),
    ("EMBO070", "EMBO078"),
    ("EMBO071", "EMBO079"),
    ("EMBO072", "EMBO080"),
    ("EMBO073", "EMBO081"),
    ("EMBO074", "EMBO082"),
]


def merge_employee(canonical, duplicate):
    """Consolidates `duplicate` into `canonical` — the same person enrolled
    twice on the device under two different IDs. Reassigns the duplicate's
    punch history onto the canonical employee, then rebuilds AttendanceRecord
    from the merged punches via the same session-pairing logic the sync
    pipeline itself uses (ingest_punches/_apply_punch), so overlapping days
    merge correctly instead of one side's data just being discarded.

    Clears the duplicate's device_user_id before soft-deleting it: the
    ActiveManager behind Employee.objects filters out soft-deleted rows, so
    leaving device_user_id set would let a future device sync's
    get_or_create try to INSERT a new row with that same value and crash on
    the unique constraint instead of just no-op'ing.
    """
    with transaction.atomic():
        PunchLog.objects.filter(employee=duplicate).update(employee=canonical)
        AttendanceRecord.objects.filter(employee__in=[canonical, duplicate]).delete()

        canonical_punches = list(PunchLog.objects.filter(employee=canonical).order_by("timestamp"))
        device = next((p.device for p in reversed(canonical_punches) if p.device_id), None)
        punches = [(canonical, p.timestamp, p.raw_status) for p in canonical_punches]
        result = ingest_punches(punches, device=device)

        duplicate.device_user_id = None
        duplicate.is_deleted = True
        duplicate.save(update_fields=["device_user_id", "is_deleted", "updated_at"])

    return result


def merge_duplicate_employees(pairs=None, dry_run=True):
    """Runs merge_employee over a list of (employee_number_a, employee_number_b)
    pairs, picking whichever side has more punch history as the canonical
    record. dry_run=True (the default) only reports what it *would* do.
    """
    pairs = pairs if pairs is not None else KNOWN_DUPLICATE_EMPLOYEE_NUMBER_PAIRS
    report = []
    for num_a, num_b in pairs:
        entry = {"pair": [num_a, num_b]}
        try:
            emp_a = Employee.all_objects.get(employee_number=num_a)
            emp_b = Employee.all_objects.get(employee_number=num_b)
        except Employee.DoesNotExist:
            entry["error"] = "one or both employee numbers not found"
            report.append(entry)
            continue

        count_a = PunchLog.objects.filter(employee=emp_a).count()
        count_b = PunchLog.objects.filter(employee=emp_b).count()
        canonical, duplicate = (emp_a, emp_b) if count_a >= count_b else (emp_b, emp_a)
        canonical_count, duplicate_count = max(count_a, count_b), min(count_a, count_b)

        entry.update(
            {
                "name": canonical.full_name,
                "canonical": canonical.employee_number,
                "duplicate": duplicate.employee_number,
                "canonical_punches": canonical_count,
                "duplicate_punches": duplicate_count,
            }
        )
        if not dry_run:
            try:
                entry["result"] = merge_employee(canonical, duplicate)
            except Exception as exc:
                entry["error"] = str(exc)
        report.append(entry)
    return report
