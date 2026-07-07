from datetime import timedelta

from django.utils import timezone


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
