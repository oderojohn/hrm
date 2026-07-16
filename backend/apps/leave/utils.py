from datetime import timedelta
from decimal import Decimal

from django.db import connection
from django.db.models import Q

from apps.core.models import PublicHoliday


def locking_queryset(manager_or_queryset):
    """Applies select_for_update() only on backends that support it (Postgres/MySQL).

    SQLite raises NotSupportedError for select_for_update, so this is a no-op there —
    the calling code becomes real row-level locking automatically once DATABASE_URL
    points at Postgres, with no code changes needed.
    """
    if connection.features.has_select_for_update:
        return manager_or_queryset.select_for_update()
    return manager_or_queryset.all() if hasattr(manager_or_queryset, "all") else manager_or_queryset


def calculate_working_days(start_date, end_date, branch=None, is_half_day=False):
    """Counts weekdays between two dates inclusive, excluding public holidays."""
    if is_half_day:
        return Decimal("0.5")

    holiday_dates = set(
        PublicHoliday.objects.filter(date__gte=start_date, date__lte=end_date)
        .filter(Q(branch=branch) | Q(branch__isnull=True))
        .values_list("date", flat=True)
    )

    total = Decimal("0")
    current = start_date
    while current <= end_date:
        if current.weekday() < 5 and current not in holiday_dates:
            total += 1
        current += timedelta(days=1)
    return total


def next_reporting_date(end_date, branch=None):
    """The next working day after end_date — when the employee is expected
    back at work. Mirrors calculate_working_days' own weekday/holiday rules
    so the two always agree."""
    holiday_dates = set(
        PublicHoliday.objects.filter(date__gt=end_date, date__lte=end_date + timedelta(days=14))
        .filter(Q(branch=branch) | Q(branch__isnull=True))
        .values_list("date", flat=True)
    )
    cursor = end_date + timedelta(days=1)
    while cursor.weekday() >= 5 or cursor in holiday_dates:
        cursor += timedelta(days=1)
    return cursor


def has_overlapping_request(employee, start_date, end_date, exclude_id=None):
    """True if the employee already has a PENDING/APPROVED request overlapping this range."""
    from apps.leave.models import LeaveRequest

    qs = LeaveRequest.objects.filter(
        employee=employee,
        status__in=[LeaveRequest.Status.PENDING, LeaveRequest.Status.APPROVED],
        start_date__lte=end_date,
        end_date__gte=start_date,
    )
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    return qs.exists()
