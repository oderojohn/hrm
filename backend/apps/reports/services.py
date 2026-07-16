"""Company-wide weekly summary — the numbers behind the scheduled/on-demand
weekly report email and its Excel/PDF export.
"""
from collections import defaultdict
from datetime import date, timedelta

from django.utils import timezone

from apps.attendance.models import AttendanceRecord
from apps.attendance.utils import is_expected_working_day
from apps.core.models import PublicHoliday
from apps.employees.models import Employee
from apps.leave.models import LeaveRequest


def resolve_week(request):
    """?start=YYYY-MM-DD picks that Monday-Sunday week; otherwise defaults to
    the most recently completed Monday-Sunday week."""
    start_param = request.query_params.get("start")
    if start_param:
        start = date.fromisoformat(start_param)
        start -= timedelta(days=start.weekday())  # snap to that week's Monday
    else:
        today = timezone.now().date()
        start = today - timedelta(days=today.weekday() + 7)
    end = start + timedelta(days=6)
    return start, end


def build_weekly_summary(start, end):
    employees = list(
        Employee.objects.filter(employment_status=Employee.EmploymentStatus.ACTIVE).select_related("work_shift")
    )
    total_employees = len(employees)

    records_qs = AttendanceRecord.objects.filter(date__gte=start, date__lte=end)
    present_days = records_qs.filter(clock_in__isnull=False).count()
    late_arrivals = records_qs.filter(is_late=True).count()
    early_departures = records_qs.filter(is_early_departure=True).count()

    present_by_employee = defaultdict(set)
    for employee_id, day in records_qs.filter(clock_in__isnull=False).values_list("employee_id", "date"):
        present_by_employee[employee_id].add(day)

    leaves_by_employee = defaultdict(list)
    for employee_id, leave_start, leave_end in LeaveRequest.objects.filter(
        status=LeaveRequest.Status.APPROVED, start_date__lte=end, end_date__gte=start
    ).values_list("employee_id", "start_date", "end_date"):
        leaves_by_employee[employee_id].append((leave_start, leave_end))

    holiday_dates = set(
        PublicHoliday.objects.filter(date__gte=start, date__lte=end).values_list("date", flat=True)
    )

    absent_days = 0
    on_leave_days = 0
    for employee in employees:
        cursor = start
        while cursor <= end:
            on_leave = any(s <= cursor <= e for s, e in leaves_by_employee.get(employee.id, []))
            if on_leave:
                on_leave_days += 1
            elif cursor not in present_by_employee.get(employee.id, set()) and is_expected_working_day(
                employee, cursor, holiday_dates
            ):
                absent_days += 1
            cursor += timedelta(days=1)

    submitted = LeaveRequest.objects.filter(created_at__date__gte=start, created_at__date__lte=end).count()
    approved = LeaveRequest.objects.filter(
        status=LeaveRequest.Status.APPROVED, updated_at__date__gte=start, updated_at__date__lte=end
    ).count()
    rejected = LeaveRequest.objects.filter(
        status=LeaveRequest.Status.REJECTED, updated_at__date__gte=start, updated_at__date__lte=end
    ).count()
    pending = LeaveRequest.objects.filter(status=LeaveRequest.Status.PENDING).count()

    return {
        "total_employees": total_employees,
        "present_days": present_days,
        "absent_days": absent_days,
        "on_leave_days": on_leave_days,
        "late_arrivals": late_arrivals,
        "early_departures": early_departures,
        "leave_requests_submitted": submitted,
        "leave_requests_approved": approved,
        "leave_requests_rejected": rejected,
        "leave_requests_pending": pending,
    }


SUMMARY_LABELS = {
    "total_employees": "Total Employees",
    "present_days": "Present (employee-days)",
    "absent_days": "Absent (employee-days)",
    "on_leave_days": "On Leave (employee-days)",
    "late_arrivals": "Late Arrivals",
    "early_departures": "Early Departures",
    "leave_requests_submitted": "Leave Requests Submitted",
    "leave_requests_approved": "Leave Requests Approved",
    "leave_requests_rejected": "Leave Requests Rejected",
    "leave_requests_pending": "Leave Requests Pending (all-time)",
}
