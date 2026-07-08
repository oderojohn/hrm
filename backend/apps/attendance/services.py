"""Sync logic bridging the ZKTeco device (apps.attendance.zkteco) and Nexas HRM's
Employee / AttendanceRecord models. The device is treated as the source of truth
for enrollment (employee list) and raw punches (attendance logs); HR completes
the rest of an auto-created employee's profile afterwards.
"""
from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from apps.attendance.models import AttendanceRecord, Device, PunchLog
from apps.attendance.utils import evaluate_clock_in, evaluate_clock_out
from apps.attendance.zkteco import ZKTecoClient
from apps.employees.models import Employee

# The real Emboita device tags every punch as either 0 (check-in) or 1
# (check-out) — confirmed against production punch history, no UNKNOWN codes
# in practice. This mapping is authoritative for pairing sessions (see
# ingest_punches); codes 4/5 are kept as a documented alias in case a
# differently-configured device uses the OT-in/OT-out convention instead.
_IN_PUNCH_CODES = {0, 4}
_OUT_PUNCH_CODES = {1, 5}

# Safety bound only, not the primary IN/OUT signal (that comes from the
# device's own event tag) — just how far back to look for a still-open
# session an OUT/UNKNOWN punch might belong to, so we don't match it against
# a session abandoned weeks ago.
_OPEN_SESSION_WINDOW_HOURS = 24


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


def _find_open_session(employee, before_timestamp):
    """The employee's most recent still-open (clock_in set, clock_out not)
    record whose clock_in precedes `before_timestamp` and is recent enough
    to plausibly be the same shift — the record an OUT (or ambiguous) punch
    should close. Bounded so an OUT punch never gets matched to a session
    abandoned weeks earlier."""
    cutoff = before_timestamp - timedelta(hours=_OPEN_SESSION_WINDOW_HOURS)
    return (
        AttendanceRecord.objects.filter(
            employee=employee,
            clock_in__isnull=False,
            clock_out__isnull=True,
            clock_in__gte=cutoff,
            clock_in__lt=before_timestamp,
        )
        .order_by("-clock_in")
        .first()
    )


def _apply_punch(employee, timestamp, event, device):
    """Applies one punch — already known to be the chronologically-next one
    for this employee — to whichever AttendanceRecord it belongs to.

    Trusts the device's own IN/OUT tag as authoritative (confirmed reliable
    against real production data) rather than inferring "first punch of the
    day is clock-in" — that heuristic breaks for night-shift staff, whose
    clock-out lands on the *next* calendar date and would otherwise be
    misread as a brand-new clock-in for that date. Pairing an OUT against
    whatever session is still open (regardless of which date it started on)
    is what correctly attributes an overnight shift's punches to the single
    day it began.

    Returns (record, was_created, was_updated).
    """
    open_session = _find_open_session(employee, timestamp)
    treat_as_close = event == PunchLog.Event.OUT or (event == PunchLog.Event.UNKNOWN and open_session is not None)

    if treat_as_close:
        if open_session:
            record, was_created = open_session, False
        else:
            # Orphan OUT — no matching clock-in in our history (typically
            # the very first punch we ever see for this employee). A
            # pre-noon orphan OUT almost always means "closing a shift that
            # started the day before, which we simply have no record of" —
            # attribute it to the previous date so it can't collide with
            # that same day's own legitimate evening clock-in (which would
            # otherwise merge into this record and corrupt both).
            orphan_date = timestamp.date() - timedelta(days=1) if timestamp.hour < 12 else timestamp.date()
            record, was_created = AttendanceRecord.objects.get_or_create(
                employee=employee, date=orphan_date, defaults={"method": AttendanceRecord.Method.BIOMETRIC}
            )
        record.method = AttendanceRecord.Method.BIOMETRIC
        record.device = device
        if not record.clock_out or timestamp > record.clock_out:
            record.clock_out = timestamp
            evaluate_clock_out(record, employee, timestamp)
            record.save()
            return record, was_created, True
        record.save()
        return record, was_created, False

    # IN (or UNKNOWN with nothing open) starts/continues a session dated to
    # this punch's own day — a plain clock-in is never retroactively
    # attributed to an earlier date.
    record, was_created = AttendanceRecord.objects.get_or_create(
        employee=employee, date=timestamp.date(), defaults={"method": AttendanceRecord.Method.BIOMETRIC}
    )
    record.method = AttendanceRecord.Method.BIOMETRIC
    record.device = device
    if not record.clock_in or timestamp < record.clock_in:
        record.clock_in = timestamp
        evaluate_clock_in(record, employee, timestamp)
        record.save()
        return record, was_created, True
    record.save()
    return record, was_created, False


def ingest_punches(punches, device=None):
    """Writes PunchLog rows verbatim, then applies each punch — in strict
    chronological order per employee — to build/extend AttendanceRecord
    sessions (see _apply_punch). `punches` is any iterable of
    (employee, timestamp, raw_status) tuples — this is the shared core used
    both by the ZK-device pull sync and the local agent's HTTP push, so
    "cloud pulls from device" and "agent pushes to cloud" never duplicate
    this logic.
    """
    by_employee = defaultdict(list)
    punches_created, punches_duplicate = 0, 0

    for employee, timestamp, raw_status in punches:
        if timezone.is_naive(timestamp):
            timestamp = timezone.make_aware(timestamp)
        event = _infer_event_from_status(raw_status)

        _, was_created = PunchLog.objects.get_or_create(
            employee=employee,
            device=device,
            timestamp=timestamp,
            defaults={"event": event, "method": AttendanceRecord.Method.BIOMETRIC, "raw_status": raw_status},
        )
        punches_created += int(was_created)
        punches_duplicate += int(not was_created)
        by_employee[employee.id].append((timestamp, event, employee))

    created, updated = 0, 0
    affected_days = set()
    for employee_id, entries in by_employee.items():
        entries.sort(key=lambda entry: entry[0])
        for timestamp, event, employee in entries:
            record, was_created, was_updated = _apply_punch(employee, timestamp, event, device)
            created += int(was_created)
            updated += int(was_updated and not was_created)
            affected_days.add((employee_id, record.date))

    return {
        "days_synced": len(affected_days),
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
