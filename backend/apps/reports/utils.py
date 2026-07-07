from datetime import date, timedelta

from django.utils import timezone


def resolve_period(request):
    """Parses period/start/end/date query params into a concrete (start, end, period) range.

    Shared by AttendanceAnalyticsView and EmployeeAttendanceDetailView so both
    honor the same ?period=week|month / ?start=&end= / ?date= conventions.
    """
    period = request.query_params.get("period", "month")
    start_param = request.query_params.get("start")
    end_param = request.query_params.get("end")

    if start_param and end_param:
        start = date.fromisoformat(start_param)
        end = date.fromisoformat(end_param)
        period = "custom"
    else:
        date_param = request.query_params.get("date")
        anchor = date.fromisoformat(date_param) if date_param else timezone.now().date()
        if period == "week":
            start = anchor - timedelta(days=anchor.weekday())
            end = start + timedelta(days=6)
        else:
            start = anchor.replace(day=1)
            end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

    return start, end, period
