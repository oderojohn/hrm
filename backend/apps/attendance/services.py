"""Sync logic bridging the ZKTeco device (apps.attendance.zkteco) and Nexas HRM's
Employee / AttendanceRecord models. The device is treated as the source of truth
for enrollment (employee list) and raw punches (attendance logs); HR completes
the rest of an auto-created employee's profile afterwards.
"""
from collections import defaultdict

from django.utils import timezone

from apps.attendance.models import AttendanceRecord, Device, PunchLog
from apps.attendance.utils import evaluate_clock_in, evaluate_clock_out
from apps.attendance.zkteco import ZKTecoClient
from apps.employees.models import Employee

# pyzk's punch/status codes vary by device configuration, so this mapping is
# best-effort metadata for the punch log only — it never drives is_late/overtime.
_IN_PUNCH_CODES = {0, 4}
_OUT_PUNCH_CODES = {1, 5}


def _infer_event_from_status(raw_status):
    if raw_status in _IN_PUNCH_CODES:
        return PunchLog.Event.IN
    if raw_status in _OUT_PUNCH_CODES:
        return PunchLog.Event.OUT
    return PunchLog.Event.UNKNOWN


def _infer_event(log):
    code = getattr(log, "punch", None)
    if code is None:
        code = getattr(log, "status", None)
    return _infer_event_from_status(code)


def format_device_name(employee):
    """Inverse of split_device_name — mirrors the device's own naming convention
    ('FIRST MIDDLE.LAST') so employees pushed from HRM look consistent with
    those enrolled directly on the device."""
    given = f"{employee.first_name} {employee.middle_name}".strip()
    return f"{given}.{employee.last_name}".upper()


def push_employee_to_device(employee, client=None):
    """Creates or updates this employee's enrollment on the ZKTeco device.
    Auto-assigns a device_user_id if the employee doesn't have one yet.
    """
    client = client or ZKTecoClient()

    if not employee.device_user_id:
        existing_ids = set(
            Employee.objects.exclude(device_user_id__isnull=True)
            .exclude(device_user_id="")
            .values_list("device_user_id", flat=True)
        )
        candidate = 1
        while str(candidate) in existing_ids:
            candidate += 1
        employee.device_user_id = str(candidate)
        employee.save(update_fields=["device_user_id"])

    client.push_user(employee.device_user_id, format_device_name(employee))
    return employee.device_user_id


def split_device_name(raw_name):
    """Device names look like 'DICKSON.NTOKOIWUAN' or 'EZEKEIL MANYARA.MWATHI' —
    everything before the last '.' is first/middle name(s), after it is the surname."""
    raw_name = (raw_name or "").strip()
    if "." in raw_name:
        given, _, surname = raw_name.rpartition(".")
    else:
        given, surname = raw_name, ""

    given_parts = given.split()
    first_name = given_parts[0] if given_parts else (surname or "Unknown")
    middle_name = " ".join(given_parts[1:]) if len(given_parts) > 1 else ""
    last_name = surname or (given_parts[0] if len(given_parts) == 1 and not middle_name else "")

    if not last_name and len(given_parts) > 1:
        last_name = given_parts[-1]
        middle_name = " ".join(given_parts[1:-1])

    return first_name, middle_name, last_name or "Unknown"


def sync_employees_from_list(users):
    """Creates/updates Employee rows from an iterable of objects exposing
    `.user_id`/`.name` (pyzk's own User objects satisfy this, and so does a
    plain list of SimpleNamespace built from an agent's HTTP push payload).
    """
    users = list(users)
    created, updated, skipped = 0, 0, 0
    for user in users:
        device_user_id = str(user.user_id).strip()
        if not device_user_id:
            skipped += 1
            continue

        first_name, middle_name, last_name = split_device_name(user.name)
        employee, was_created = Employee.objects.get_or_create(
            device_user_id=device_user_id,
            defaults=dict(
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                employment_date=timezone.now().date(),
                employment_type=Employee.EmploymentType.FULL_TIME,
            ),
        )
        if was_created:
            created += 1
        else:
            changed = False
            if not employee.first_name and first_name:
                employee.first_name = first_name
                changed = True
            if not employee.last_name and last_name:
                employee.last_name = last_name
                changed = True
            if changed:
                employee.save()
            updated += 1

    return {"created": created, "updated": updated, "skipped": skipped, "total_on_device": len(users)}


def sync_employees_from_device(client=None):
    """Pulls the device's enrolled users and creates/updates matching Employee rows."""
    client = client or ZKTecoClient()
    return sync_employees_from_list(client.fetch_users())


def ingest_punches(punches, device=None):
    """Writes PunchLog rows and collapses them per employee/day into first-in/last-out
    AttendanceRecord rows. Punch semantics vary by device configuration, so instead
    of trusting individual IN/OUT codes, the earliest punch of the day is treated
    as clock-in and the latest as clock-out. Every individual punch is also kept
    verbatim in PunchLog, since the collapse above discards everything except the
    first and last punch of the day.

    `punches` is any iterable of (employee, timestamp, raw_status) tuples — this is
    the shared core used both by the ZK-device pull sync and the local agent's HTTP
    push, so "cloud pulls from device" and "agent pushes to cloud" never duplicate
    this logic.
    """
    by_employee_day = defaultdict(list)
    employees_by_day = {}
    punches_created, punches_duplicate = 0, 0

    for employee, timestamp, raw_status in punches:
        if timezone.is_naive(timestamp):
            timestamp = timezone.make_aware(timestamp)
        key = (employee.id, timestamp.date())
        by_employee_day[key].append(timestamp)
        employees_by_day[key] = employee

        _, was_created = PunchLog.objects.get_or_create(
            employee=employee,
            device=device,
            timestamp=timestamp,
            defaults={
                "event": _infer_event_from_status(raw_status),
                "method": AttendanceRecord.Method.BIOMETRIC,
                "raw_status": raw_status,
            },
        )
        punches_created += int(was_created)
        punches_duplicate += int(not was_created)

    created, updated = 0, 0
    for (employee_id, day), timestamps in by_employee_day.items():
        employee = employees_by_day[(employee_id, day)]
        batch_first = min(timestamps)
        batch_last = max(timestamps)

        record, was_created = AttendanceRecord.objects.get_or_create(
            employee=employee, date=day, defaults={"method": AttendanceRecord.Method.BIOMETRIC}
        )
        record.method = AttendanceRecord.Method.BIOMETRIC
        record.device = device
        if not record.clock_in or batch_first < record.clock_in:
            record.clock_in = batch_first
            evaluate_clock_in(record, employee, batch_first)
        # A punch later than the established clock-in is a clock-out candidate.
        # This can't be gated on "more than one punch in *this* batch" — the
        # local agent pushes incrementally, often one punch at a time, so a
        # day's clock-out punch frequently arrives alone in its own batch,
        # long after the clock-in punch was already synced and saved.
        if batch_last != record.clock_in and (not record.clock_out or batch_last > record.clock_out):
            record.clock_out = batch_last
            evaluate_clock_out(record, employee, batch_last)
        record.save()

        created += int(was_created)
        updated += int(not was_created)

    return {
        "days_synced": len(by_employee_day),
        "records_created": created,
        "records_updated": updated,
        "punches_created": punches_created,
        "punches_duplicate": punches_duplicate,
    }


def sync_attendance_from_device(client=None, device=None):
    """Pulls raw punches from a live ZK device and delegates to ingest_punches."""
    client = client or ZKTecoClient()
    logs = client.fetch_attendance_logs()

    device_id_to_employee = {
        e.device_user_id: e
        for e in Employee.objects.exclude(device_user_id__isnull=True).exclude(device_user_id="")
    }

    punches = []
    unmatched_device_ids = set()
    for log in logs:
        device_user_id = str(log.user_id).strip()
        employee = device_id_to_employee.get(device_user_id)
        if not employee:
            unmatched_device_ids.add(device_user_id)
            continue
        raw_status = getattr(log, "punch", None)
        if raw_status is None:
            raw_status = getattr(log, "status", None)
        punches.append((employee, log.timestamp, raw_status))

    result = ingest_punches(punches, device=device)
    result["unmatched_device_user_ids"] = sorted(unmatched_device_ids)
    result["total_logs_on_device"] = len(logs)
    return result


def sync_all_devices():
    """Runs enrollment + attendance sync against every active Device, isolating
    failures so one offline device doesn't abort the sync for the rest.
    """
    results = []
    for device in Device.objects.filter(is_active=True):
        client = ZKTecoClient(ip=device.ip_address, port=device.port)
        try:
            employee_summary = sync_employees_from_device(client)
            attendance_summary = sync_attendance_from_device(client, device=device)
            device.last_synced_at = timezone.now()
            device.save(update_fields=["last_synced_at"])
            results.append(
                {
                    "device_id": device.id,
                    "device_name": device.name,
                    "employees": employee_summary,
                    "attendance": attendance_summary,
                    "error": None,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "device_id": device.id,
                    "device_name": device.name,
                    "employees": None,
                    "attendance": None,
                    "error": str(exc),
                }
            )
    return results
