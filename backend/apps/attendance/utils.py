from datetime import timedelta

from django.utils import timezone


def get_working_day_numbers(employee):
    """ISO weekday numbers (1=Mon..7=Sun) this employee is expected to work —
    per their shift if assigned, else the company-wide AttendanceSettings
    weekend_days fallback (previously employees with no shift were silently
    treated as working every day of the week)."""
    if employee.work_shift:
        return employee.work_shift.working_days
    from apps.attendance.models import AttendanceSettings

    weekend_days = AttendanceSettings.get_solo().weekend_days
    return [d for d in range(1, 8) if d not in weekend_days]


def is_expected_working_day(employee, day, holiday_dates):
    return day.isoweekday() in get_working_day_numbers(employee) and day not in holiday_dates


def count_expected_working_days(employee, start, end, holiday_dates):
    numbers = get_working_day_numbers(employee)
    count = 0
    cursor = start
    while cursor <= end:
        if cursor.isoweekday() in numbers and cursor not in holiday_dates:
            count += 1
        cursor += timedelta(days=1)
    return count


def evaluate_clock_in(record, employee, when):
    shift = employee.work_shift
    if shift:
        shift_start = timezone.make_aware(
            timezone.datetime.combine(record.date, shift.start_time)
        )
        grace = timedelta(minutes=shift.grace_period_minutes)
        record.is_late = when > shift_start + grace


def evaluate_clock_out(record, employee, when):
    shift = employee.work_shift
    if shift:
        shift_end = timezone.make_aware(timezone.datetime.combine(record.date, shift.end_time))
        record.is_early_departure = when < shift_end
        if when > shift_end:
            record.overtime_minutes = int((when - shift_end).total_seconds() // 60)
