from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
import os

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assets.models import Asset
from apps.attendance.models import AttendanceRecord, PunchLog
from apps.attendance.utils import count_expected_working_days, is_expected_working_day
from apps.communication.models import Announcement
from apps.core.exports import export_attendance_grid_xlsx, export_csv, export_pdf, export_queryset, export_xlsx
from apps.core.models import PublicHoliday
from apps.core.permissions import IsHRManagerOrAbove
from apps.disciplinary.models import DisciplinaryCase
from apps.documents.models import Document
from apps.employees.models import Employee
from apps.leave.models import LeaveRequest
from apps.organization.models import Branch, Department
from apps.performance.models import PerformanceReview
from apps.recruitment.models import Application, JobVacancy
from apps.reports.emails import send_weekly_report_email
from apps.reports.services import SUMMARY_LABELS, build_weekly_summary, resolve_week
from apps.reports.utils import resolve_period
from apps.training.models import TrainingAttendance


def _scoped_employees(user):
    qs = Employee.objects.all()
    if user.role == user.Role.DEPARTMENT_MANAGER:
        own = getattr(user, "employee", None)
        return qs.filter(department_id=own.department_id) if own else qs.none()
    return qs


class DashboardView(APIView):
    def get(self, request):
        user = request.user
        today = timezone.now().date()

        if user.role == user.Role.EMPLOYEE:
            return Response(self._personal_dashboard(user, today))
        return Response(self._management_dashboard(user, today))

    def _personal_dashboard(self, user, today):
        own = getattr(user, "employee", None)
        if not own:
            return {"detail": "No employee profile linked to this account."}

        today_attendance = AttendanceRecord.objects.filter(employee=own, date=today).first()
        upcoming_leave = (
            LeaveRequest.objects.filter(
                employee=own, status=LeaveRequest.Status.APPROVED, start_date__gte=today
            )
            .order_by("start_date")
            .first()
        )
        return {
            "employee_number": own.employee_number,
            "full_name": own.full_name,
            "clocked_in_today": bool(today_attendance and today_attendance.clock_in),
            "clocked_out_today": bool(today_attendance and today_attendance.clock_out),
            "pending_leave_requests": LeaveRequest.objects.filter(
                employee=own, status=LeaveRequest.Status.PENDING
            ).count(),
            "next_approved_leave": upcoming_leave.start_date if upcoming_leave else None,
            "leave_balances": [
                {
                    "leave_type": balance.leave_type.name,
                    "remaining_days": float(balance.remaining_days),
                }
                for balance in own.leave_balances.filter(year=today.year)
            ],
            "recent_announcements": list(
                Announcement.objects.filter(is_published=True)
                .order_by("-published_at")[:5]
                .values("id", "title", "published_at")
            ),
        }

    def _management_dashboard(self, user, today):
        employees = _scoped_employees(user)
        active_employees = employees.filter(employment_status=Employee.EmploymentStatus.ACTIVE)
        active_ids = active_employees.values_list("id", flat=True)

        present_today = AttendanceRecord.objects.filter(
            employee_id__in=active_ids, date=today, clock_in__isnull=False
        ).count()
        on_leave_today = LeaveRequest.objects.filter(
            employee_id__in=active_ids,
            status=LeaveRequest.Status.APPROVED,
            start_date__lte=today,
            end_date__gte=today,
        ).count()
        absent_today = max(active_employees.count() - present_today - on_leave_today, 0)

        thirty_days_ago = today - timedelta(days=30)
        thirty_days_ahead = today + timedelta(days=30)

        data = {
            "total_employees": employees.count(),
            "active_employees": active_employees.count(),
            "present_today": present_today,
            "absent_today": absent_today,
            "on_leave_today": on_leave_today,
            "pending_leave_requests": LeaveRequest.objects.filter(
                employee_id__in=active_ids, status=LeaveRequest.Status.PENDING
            ).count(),
            "birthdays_today": [
                {"id": e.id, "full_name": e.full_name, "employee_number": e.employee_number}
                for e in employees.filter(
                    date_of_birth__month=today.month, date_of_birth__day=today.day
                )
            ],
            "new_employees": [
                {
                    "id": e.id,
                    "full_name": e.full_name,
                    "employee_number": e.employee_number,
                    "employment_date": e.employment_date,
                }
                for e in employees.filter(employment_date__gte=thirty_days_ago)
            ],
            "contract_expiry_alerts": [
                {"id": e.id, "full_name": e.full_name, "contract_end_date": e.contract_end_date}
                for e in employees.filter(
                    contract_end_date__gte=today, contract_end_date__lte=thirty_days_ahead
                )
            ],
            "recent_announcements": list(
                Announcement.objects.filter(is_published=True)
                .order_by("-published_at")[:5]
                .values("id", "title", "published_at")
            ),
            "charts": {
                "employee_growth": self._employee_growth(employees, today),
                "attendance_trends": self._attendance_trends(active_ids, today),
                "leave_trends": self._leave_trends(active_ids, today),
                "department_distribution": self._department_distribution(employees),
                "gender_distribution": self._gender_distribution(employees),
            },
        }

        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            data["document_expiry_alerts"] = list(
                Document.objects.filter(
                    expiry_date__gte=today, expiry_date__lte=thirty_days_ahead
                ).values("id", "title", "expiry_date", "employee_id")
            )
        else:
            data["document_expiry_alerts"] = []

        return data

    @staticmethod
    def _shift_months(d, n):
        """Returns the first of the month that is `n` months before `d`."""
        month_index = d.month - 1 - n
        year = d.year + month_index // 12
        month = month_index % 12 + 1
        return d.replace(year=year, month=month, day=1)

    def _last_12_months(self, today):
        return [self._shift_months(today, i) for i in range(11, -1, -1)]

    def _employee_growth(self, employees, today):
        return [
            {
                "month": month.strftime("%Y-%m"),
                "count": employees.filter(
                    employment_date__year=month.year, employment_date__month=month.month
                ).count(),
            }
            for month in self._last_12_months(today)
        ]

    def _attendance_trends(self, employee_ids, today):
        points = []
        for i in range(29, -1, -1):
            day = today - timedelta(days=i)
            count = AttendanceRecord.objects.filter(
                employee_id__in=employee_ids, date=day, clock_in__isnull=False
            ).count()
            points.append({"date": day.isoformat(), "count": count})
        return points

    def _leave_trends(self, employee_ids, today):
        return [
            {
                "month": month.strftime("%Y-%m"),
                "count": LeaveRequest.objects.filter(
                    employee_id__in=employee_ids,
                    start_date__year=month.year,
                    start_date__month=month.month,
                ).count(),
            }
            for month in self._last_12_months(today)
        ]

    def _department_distribution(self, employees):
        return list(
            employees.exclude(department__isnull=True)
            .values("department__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

    def _gender_distribution(self, employees):
        return list(
            employees.exclude(gender="")
            .values("gender")
            .annotate(count=Count("id"))
            .order_by("gender")
        )


class AttendanceAnalyticsView(APIView):
    """Computes working days/hours from device-synced attendance records —
    the system never accepts manual clock-in/out, only reports on device data.
    """

    export_headers = [
        "Employee",
        "Days Worked",
        "Expected Days",
        "Absent Days",
        "Attendance Rate",
        "Total Hours",
        "Avg Hours/Day",
        "Late Count",
        "Overtime (hrs)",
    ]

    def get(self, request):
        user = request.user
        start, end, period = resolve_period(request)

        employees = _scoped_employees(user)
        employee_param = request.query_params.get("employee")
        branch_param = request.query_params.get("branch")
        department_param = request.query_params.get("department")
        if employee_param:
            employees = employees.filter(id=employee_param)
        elif user.role == user.Role.EMPLOYEE:
            own = getattr(user, "employee", None)
            employees = employees.filter(id=own.id) if own else employees.none()
        if branch_param:
            employees = employees.filter(branch_id=branch_param)
        if department_param:
            employees = employees.filter(department_id=department_param)

        holiday_dates = set(
            PublicHoliday.objects.filter(date__gte=start, date__lte=end).values_list("date", flat=True)
        )

        results = [
            self._employee_summary(employee, start, end, holiday_dates)
            for employee in employees.select_related("work_shift")
        ]

        export_response = export_queryset(request, results, self.export_headers, self._export_row, "attendance_analytics")
        if export_response is not None:
            return export_response

        return Response({"period": period, "start": start.isoformat(), "end": end.isoformat(), "results": results})

    def _export_row(self, summary):
        return [
            summary["employee_name"],
            summary["working_days"],
            summary["expected_working_days"],
            summary["absent_days"],
            summary["attendance_rate"],
            summary["total_hours"],
            summary["average_hours_per_day"],
            summary["late_count"],
            summary["overtime_hours"],
        ]

    def _employee_summary(self, employee, start, end, holiday_dates):
        records = AttendanceRecord.objects.filter(employee=employee, date__gte=start, date__lte=end).order_by("date")

        working_days = 0
        total_seconds = 0
        late_count = 0
        early_count = 0
        overtime_minutes = 0
        daily = []

        for record in records:
            hours = None
            if record.clock_in:
                working_days += 1
            if record.clock_in and record.clock_out:
                seconds = (record.clock_out - record.clock_in).total_seconds()
                total_seconds += seconds
                hours = round(seconds / 3600, 2)
            if record.is_late:
                late_count += 1
            if record.is_early_departure:
                early_count += 1
            overtime_minutes += record.overtime_minutes
            daily.append({"date": record.date.isoformat(), "hours": hours, "is_late": record.is_late})

        expected_days = count_expected_working_days(employee, start, end, holiday_dates)

        total_hours = round(total_seconds / 3600, 1)

        return {
            "employee_id": employee.id,
            "employee_name": employee.full_name,
            "working_days": working_days,
            "expected_working_days": expected_days,
            "absent_days": max(expected_days - working_days, 0),
            "attendance_rate": round((working_days / expected_days) * 100, 1) if expected_days else None,
            "total_hours": total_hours,
            "average_hours_per_day": round(total_hours / working_days, 2) if working_days else 0,
            "late_count": late_count,
            "early_departure_count": early_count,
            "overtime_hours": round(overtime_minutes / 60, 1),
            "daily": daily,
        }


class BaseReportView(APIView):
    permission_classes = [IsHRManagerOrAbove]
    export_headers = []
    base_filename = "report"

    def get_queryset(self, request):
        raise NotImplementedError

    def row(self, obj):
        raise NotImplementedError

    def summarize(self, queryset):
        return {"count": queryset.count()}

    def get(self, request):
        queryset = self.get_queryset(request)
        response = export_queryset(request, queryset, self.export_headers, self.row, self.base_filename)
        if response is not None:
            return response
        return Response(
            {
                "summary": self.summarize(queryset),
                "results": [dict(zip(self.export_headers, self.row(obj))) for obj in queryset[:200]],
            }
        )


class EmployeeReportView(BaseReportView):
    export_headers = ["Employee No.", "Full Name", "Department", "Position", "Status", "Employment Date"]
    base_filename = "employee_report"

    def get_queryset(self, request):
        return Employee.objects.select_related("department", "position").all()

    def row(self, obj):
        return [
            obj.employee_number,
            obj.full_name,
            obj.department.name if obj.department else "",
            obj.position.title if obj.position else "",
            obj.employment_status,
            obj.employment_date,
        ]


class AttendanceReportView(BaseReportView):
    export_headers = ["Employee", "Date", "Clock In", "Clock Out", "Device", "Late", "Overtime (min)"]
    base_filename = "attendance_report"

    def get_queryset(self, request):
        qs = AttendanceRecord.objects.select_related("employee", "device")
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        if start:
            qs = qs.filter(date__gte=start)
        if end:
            qs = qs.filter(date__lte=end)
        return qs

    def row(self, obj):
        return [
            obj.employee.full_name,
            obj.date,
            obj.clock_in,
            obj.clock_out,
            obj.device.name if obj.device else "",
            obj.is_late,
            obj.overtime_minutes,
        ]


class LateArrivalsReportView(BaseReportView):
    export_headers = ["Employee No.", "Employee", "Department", "Date", "Clock In", "Shift", "Minutes Late"]
    base_filename = "late_arrivals_report"

    def get_queryset(self, request):
        start, end, _ = resolve_period(request)
        employees = _scoped_employees(request.user)
        department_param = request.query_params.get("department")
        if department_param:
            employees = employees.filter(department_id=department_param)
        qs = (
            AttendanceRecord.objects.filter(
                employee__in=employees, date__gte=start, date__lte=end, is_late=True
            )
            .select_related("employee", "employee__department", "employee__work_shift")
            .order_by("-date")
        )
        return qs

    def row(self, obj):
        shift = obj.employee.work_shift
        minutes_late = None
        if shift and obj.clock_in:
            shift_start = timezone.make_aware(timezone.datetime.combine(obj.date, shift.start_time))
            minutes_late = max(
                int((obj.clock_in - shift_start).total_seconds() / 60) - shift.grace_period_minutes, 0
            )
        return [
            obj.employee.employee_number,
            obj.employee.full_name,
            obj.employee.department.name if obj.employee.department else "",
            obj.date,
            obj.clock_in,
            shift.name if shift else "",
            minutes_late,
        ]


class AbsenteeismReportView(BaseReportView):
    """Enumerates (employee, date) pairs where an employee had no attendance
    record and no approved leave on a day they were expected to work — the
    same expected-working-day rule AttendanceAnalyticsView uses, just listed
    out per-date instead of summarized into a single absent_days count.
    """

    export_headers = ["Employee No.", "Employee", "Department", "Date"]
    base_filename = "absenteeism_report"

    def get_queryset(self, request):
        start, end, _ = resolve_period(request)
        employees = _scoped_employees(request.user).filter(
            employment_status=Employee.EmploymentStatus.ACTIVE
        )
        department_param = request.query_params.get("department")
        if department_param:
            employees = employees.filter(department_id=department_param)
        employees = employees.select_related("department", "work_shift")

        holiday_dates = set(
            PublicHoliday.objects.filter(date__gte=start, date__lte=end).values_list("date", flat=True)
        )

        rows = []
        for employee in employees:
            present_dates = set(
                AttendanceRecord.objects.filter(
                    employee=employee, date__gte=start, date__lte=end, clock_in__isnull=False
                ).values_list("date", flat=True)
            )
            leave_ranges = list(
                LeaveRequest.objects.filter(
                    employee=employee,
                    status=LeaveRequest.Status.APPROVED,
                    start_date__lte=end,
                    end_date__gte=start,
                ).values_list("start_date", "end_date")
            )
            cursor = start
            while cursor <= end:
                if (
                    cursor not in present_dates
                    and is_expected_working_day(employee, cursor, holiday_dates)
                    and not any(s <= cursor <= e for s, e in leave_ranges)
                ):
                    rows.append((employee, cursor))
                cursor += timedelta(days=1)
        return rows

    def summarize(self, queryset):
        return {"count": len(queryset)}

    def row(self, obj):
        employee, day = obj
        return [
            employee.employee_number,
            employee.full_name,
            employee.department.name if employee.department else "",
            day,
        ]


class AttendanceGridReportView(APIView):
    """Present/Absent register: one row per employee, one column per date in
    the period — the classic printable monthly attendance sheet. Filterable
    down to a single employee, a department, or left open for the whole
    company. CSV/PDF reuse the generic flat-row exporters (headers are just
    the date columns); XLSX uses export_attendance_grid_xlsx for per-cell
    status coloring instead of the plain generic export_xlsx.
    """

    permission_classes = [IsHRManagerOrAbove]

    STATUS_LABELS = {"P": "Present", "L": "Late", "A": "Absent", "LV": "On Leave", "OFF": "Non-working day"}

    def get(self, request):
        start, end, period = resolve_period(request)

        employees = _scoped_employees(request.user).filter(employment_status=Employee.EmploymentStatus.ACTIVE)
        department_param = request.query_params.get("department")
        employee_param = request.query_params.get("employee")
        branch_param = request.query_params.get("branch")
        if department_param:
            employees = employees.filter(department_id=department_param)
        if employee_param:
            employees = employees.filter(id=employee_param)
        if branch_param:
            employees = employees.filter(branch_id=branch_param)
        employees = list(employees.select_related("department", "work_shift").order_by("employee_number"))

        dates = []
        cursor = start
        while cursor <= end:
            dates.append(cursor)
            cursor += timedelta(days=1)

        holiday_dates = set(
            PublicHoliday.objects.filter(date__gte=start, date__lte=end).values_list("date", flat=True)
        )

        records_by_employee = defaultdict(dict)
        for r in AttendanceRecord.objects.filter(employee__in=employees, date__gte=start, date__lte=end):
            records_by_employee[r.employee_id][r.date] = r

        leaves_by_employee = defaultdict(list)
        for employee_id, leave_start, leave_end in LeaveRequest.objects.filter(
            employee__in=employees,
            status=LeaveRequest.Status.APPROVED,
            start_date__lte=end,
            end_date__gte=start,
        ).values_list("employee_id", "start_date", "end_date"):
            leaves_by_employee[employee_id].append((leave_start, leave_end))

        today = timezone.now().date()

        def day_status(employee, day, record):
            if any(s <= day <= e for s, e in leaves_by_employee.get(employee.id, [])):
                return "LV"
            if record and record.clock_in:
                return "L" if record.is_late else "P"
            if day > today:
                # Hasn't happened yet — "Absent" would be a false claim about
                # the future. Blank reads as "not yet known" in both the
                # preview grid and the exported sheet.
                return ""
            if is_expected_working_day(employee, day, holiday_dates):
                return "A"
            return "OFF"

        # The grid always shows one status code per day EXCEPT on days the
        # employee was actually present, where the chosen metric (clock-in
        # time, clock-out time, or hours worked) is shown instead — there's
        # nothing to show a clock-in time for on an absent/leave/off day.
        metric = request.query_params.get("metric", "status")

        def cell_value(employee, day):
            record = records_by_employee.get(employee.id, {}).get(day)
            status = day_status(employee, day, record)
            if metric == "status" or status not in ("P", "L"):
                return status
            if metric == "clock_in":
                return timezone.localtime(record.clock_in).strftime("%H:%M")
            if metric == "clock_out":
                return timezone.localtime(record.clock_out).strftime("%H:%M") if record.clock_out else status
            if metric == "working_hours":
                if record.clock_out:
                    return str(round((record.clock_out - record.clock_in).total_seconds() / 3600, 1))
                return status
            return status

        metric_labels = {
            "status": "Attendance Status",
            "clock_in": "Clock In Times",
            "clock_out": "Clock Out Times",
            "working_hours": "Working Hours",
        }
        date_header_suffix = "" if metric == "status" else f" {metric_labels.get(metric, '')}"
        headers = ["Employee No.", "Employee", "Department"] + [
            f"{d.strftime('%d %b')}{date_header_suffix}" for d in dates
        ]

        def row(employee):
            return [
                employee.employee_number,
                employee.full_name,
                employee.department.name if employee.department else "",
                *[cell_value(employee, d) for d in dates],
            ]

        rows = [row(e) for e in employees]

        fmt = request.query_params.get("format", "").lower()
        base_filename = f"attendance_register_{metric}"
        if fmt == "csv":
            return export_csv(rows, headers, f"{base_filename}.csv")
        if fmt == "xlsx":
            return export_attendance_grid_xlsx(rows, headers, status_col_start=3, filename=f"{base_filename}.xlsx")
        if fmt == "pdf":
            return export_pdf(rows, headers, f"{base_filename}.pdf")

        return Response(
            {
                "period": period,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "dates": [d.isoformat() for d in dates],
                "metric": metric,
                "legend": self.STATUS_LABELS,
                "headers": headers,
                "results": rows[:50],
                "count": len(rows),
            }
        )


@dataclass
class _DaySummary:
    date: date
    record: object = None
    punches: list = field(default_factory=list)


class EmployeeAttendanceDetailView(APIView):
    """Detailed day-by-day attendance for one employee, including every raw
    punch (not just first-in/last-out) — backs both the manager drill-down
    and the employee's own "My Attendance" tab.
    """

    export_headers = ["Date", "Clock In", "Clock Out", "Punch Count", "Punches", "Late", "Early Departure", "Overtime (min)"]

    def get(self, request, employee_id):
        employee = get_object_or_404(
            Employee.objects.select_related("department", "branch", "work_shift"), pk=employee_id
        )
        self._check_access(request.user, employee)

        try:
            start, end, period = resolve_period(request)
        except ValueError:
            return Response({"detail": "Invalid start/end date."}, status=400)

        records = {
            r.date: r
            for r in AttendanceRecord.objects.filter(employee=employee, date__gte=start, date__lte=end).select_related(
                "device"
            )
        }
        punches_qs = (
            PunchLog.objects.filter(employee=employee, timestamp__date__gte=start, timestamp__date__lte=end)
            .select_related("device")
            .order_by("timestamp")
        )
        punches_by_day = defaultdict(list)
        for p in punches_qs:
            punches_by_day[p.timestamp.date()].append(p)

        days = []
        cursor = start
        while cursor <= end:
            days.append(_DaySummary(date=cursor, record=records.get(cursor), punches=punches_by_day.get(cursor, [])))
            cursor += timedelta(days=1)

        response = export_queryset(request, days, self.export_headers, self._row, f"attendance_{employee.employee_number}")
        if response is not None:
            return response

        holiday_dates = set(
            PublicHoliday.objects.filter(date__gte=start, date__lte=end).values_list("date", flat=True)
        )

        return Response(
            {
                "employee": {
                    "id": employee.id,
                    "employee_number": employee.employee_number,
                    "full_name": employee.full_name,
                    "photo": employee.photo.url if employee.photo else None,
                    "department_name": employee.department.name if employee.department else None,
                    "branch_name": employee.branch.name if employee.branch else None,
                    "work_shift_name": employee.work_shift.name if employee.work_shift else None,
                },
                "start": start.isoformat(),
                "end": end.isoformat(),
                "summary": self._summary(days, holiday_dates),
                "days": [self._day_json(d) for d in days],
            }
        )

    def _check_access(self, user, employee):
        if user.role in (user.Role.SUPER_ADMIN, user.Role.HR_MANAGER):
            return
        own = getattr(user, "employee", None)
        if user.role == user.Role.DEPARTMENT_MANAGER and own and employee.department_id == own.department_id:
            return
        if own and own.pk == employee.pk:
            return
        raise PermissionDenied("You do not have access to this employee's attendance.")

    def _row(self, day):
        record = day.record
        punches = day.punches
        punch_summary = ", ".join(f"{p.timestamp.strftime('%H:%M')} {p.event}" for p in punches)
        return [
            day.date,
            record.clock_in if record else None,
            record.clock_out if record else None,
            len(punches),
            punch_summary,
            record.is_late if record else False,
            record.is_early_departure if record else False,
            record.overtime_minutes if record else 0,
        ]

    def _day_json(self, day):
        record = day.record
        return {
            "date": day.date.isoformat(),
            "clock_in": record.clock_in.isoformat() if record and record.clock_in else None,
            "clock_out": record.clock_out.isoformat() if record and record.clock_out else None,
            "is_late": record.is_late if record else False,
            "is_early_departure": record.is_early_departure if record else False,
            "overtime_minutes": record.overtime_minutes if record else 0,
            "punch_count": len(day.punches),
            "punches": [
                {
                    "timestamp": p.timestamp.isoformat(),
                    "event": p.event,
                    "device_name": p.device.name if p.device else None,
                }
                for p in day.punches
            ],
        }

    def _summary(self, days, holiday_dates):
        working_days = sum(1 for d in days if d.record and d.record.clock_in)
        total_seconds = sum(
            (d.record.clock_out - d.record.clock_in).total_seconds()
            for d in days
            if d.record and d.record.clock_in and d.record.clock_out
        )
        late_count = sum(1 for d in days if d.record and d.record.is_late)
        early_count = sum(1 for d in days if d.record and d.record.is_early_departure)
        overtime_minutes = sum(d.record.overtime_minutes for d in days if d.record)
        total_punches = sum(len(d.punches) for d in days)

        expected_days = sum(1 for d in days if d.date not in holiday_dates)
        total_hours = round(total_seconds / 3600, 1)

        return {
            "working_days": working_days,
            "expected_working_days": expected_days,
            "attendance_rate": round((working_days / expected_days) * 100, 1) if expected_days else None,
            "total_hours": total_hours,
            "average_hours_per_day": round(total_hours / working_days, 2) if working_days else 0,
            "late_count": late_count,
            "early_departure_count": early_count,
            "overtime_hours": round(overtime_minutes / 60, 1),
            "total_punches": total_punches,
        }


class LeaveReportView(BaseReportView):
    export_headers = ["Employee", "Leave Type", "Start", "End", "Days", "Status"]
    base_filename = "leave_report"

    def get_queryset(self, request):
        qs = LeaveRequest.objects.select_related("employee", "leave_type")
        status_param = request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    def row(self, obj):
        return [
            obj.employee.full_name,
            obj.leave_type.name,
            obj.start_date,
            obj.end_date,
            obj.total_days,
            obj.status,
        ]


class DepartmentReportView(BaseReportView):
    export_headers = ["Department", "Branch", "Head Count"]
    base_filename = "department_report"

    def get_queryset(self, request):
        return Department.objects.select_related("branch").all()

    def row(self, obj):
        return [obj.name, obj.branch.name, obj.employees.count()]


class BranchReportView(BaseReportView):
    export_headers = ["Branch", "City", "Head Count"]
    base_filename = "branch_report"

    def get_queryset(self, request):
        return Branch.objects.all()

    def row(self, obj):
        return [obj.name, obj.city, obj.employees.count()]


class RecruitmentReportView(BaseReportView):
    export_headers = ["Vacancy", "Department", "Status", "Applications"]
    base_filename = "recruitment_report"

    def get_queryset(self, request):
        return JobVacancy.objects.select_related("department").all()

    def row(self, obj):
        return [obj.title, obj.department.name if obj.department else "", obj.status, obj.applications.count()]

    def summarize(self, queryset):
        return {
            "open_vacancies": queryset.filter(status="OPEN").count(),
            "total_applications": Application.objects.filter(vacancy__in=queryset).count(),
        }


class PerformanceReportView(BaseReportView):
    export_headers = ["Employee", "Review Period", "Type", "Rating", "Status"]
    base_filename = "performance_report"

    def get_queryset(self, request):
        return PerformanceReview.objects.select_related("employee").all()

    def row(self, obj):
        return [
            obj.employee.full_name,
            f"{obj.review_period_start} - {obj.review_period_end}",
            obj.review_type,
            obj.overall_rating,
            obj.status,
        ]


class TrainingReportView(BaseReportView):
    export_headers = ["Employee", "Session", "Status", "Completion Date"]
    base_filename = "training_report"

    def get_queryset(self, request):
        return TrainingAttendance.objects.select_related("employee", "session__program").all()

    def row(self, obj):
        return [obj.employee.full_name, str(obj.session), obj.status, obj.completion_date]


class AssetReportView(BaseReportView):
    export_headers = ["Asset Tag", "Name", "Category", "Status", "Branch"]
    base_filename = "asset_report"

    def get_queryset(self, request):
        return Asset.objects.select_related("branch").all()

    def row(self, obj):
        return [obj.asset_tag, obj.name, obj.category, obj.status, obj.branch.name if obj.branch else ""]


class DisciplinaryReportView(BaseReportView):
    export_headers = ["Employee", "Case Type", "Status", "Incident Date"]
    base_filename = "disciplinary_report"

    def get_queryset(self, request):
        return DisciplinaryCase.objects.select_related("employee").all()

    def row(self, obj):
        return [obj.employee.full_name, obj.case_type, obj.status, obj.incident_date]


class TurnoverReportView(BaseReportView):
    export_headers = ["Employee", "Status", "Employment Date"]
    base_filename = "turnover_report"

    def get_queryset(self, request):
        return Employee.objects.filter(
            employment_status__in=[
                Employee.EmploymentStatus.RESIGNED,
                Employee.EmploymentStatus.TERMINATED,
                Employee.EmploymentStatus.RETIRED,
            ]
        )

    def row(self, obj):
        return [obj.full_name, obj.employment_status, obj.employment_date]

    def summarize(self, queryset):
        total = Employee.objects.count()
        left = queryset.count()
        rate = round((left / total) * 100, 1) if total else 0
        return {"total_employees": total, "employees_who_left": left, "turnover_rate_percent": rate}


class WeeklySummaryReportView(APIView):
    """Company-wide weekly digest — JSON preview, or CSV/XLSX/PDF export via
    ?format=. Same build_weekly_summary() the scheduled/on-demand email uses,
    so the numbers you see match what gets sent.
    """

    permission_classes = [IsHRManagerOrAbove]

    def get(self, request):
        start, end = resolve_week(request)
        summary = build_weekly_summary(start, end)
        rows = [[SUMMARY_LABELS[key], value] for key, value in summary.items() if key in SUMMARY_LABELS]
        headers = ["Metric", "Value"]
        base_filename = f"weekly_report_{start.isoformat()}"

        fmt = request.query_params.get("format", "").lower()
        if fmt == "csv":
            return export_csv(rows, headers, f"{base_filename}.csv")
        if fmt == "xlsx":
            return export_xlsx(rows, headers, f"{base_filename}.xlsx")
        if fmt == "pdf":
            return export_pdf(rows, headers, f"{base_filename}.pdf")

        return Response({"start": start.isoformat(), "end": end.isoformat(), **summary})


class WeeklySummarySendView(APIView):
    """On-demand "send this week's report to an email address" button."""

    permission_classes = [IsHRManagerOrAbove]

    def post(self, request):
        recipient = request.data.get("email")
        if not recipient:
            return Response({"detail": "An email address is required."}, status=400)

        start, end = resolve_week(request)
        summary = build_weekly_summary(start, end)
        try:
            sent = send_weekly_report_email([recipient], start, end, summary)
        except Exception as exc:
            return Response({"detail": f"Failed to send: {exc}"}, status=400)
        if not sent:
            return Response(
                {"detail": "Email isn't configured yet — set it up under Settings -> Email Settings first."},
                status=400,
            )
        return Response({"detail": f"Weekly report sent to {recipient}."})


class WeeklySummaryCronView(APIView):
    """Triggered by Vercel Cron (see vercel.json) every Monday morning —
    emails the just-completed week's report to every HR Manager/Super Admin.
    Vercel attaches `Authorization: Bearer $CRON_SECRET` automatically when
    CRON_SECRET is set as a project env var; any other caller is rejected.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        secret = os.environ.get("CRON_SECRET")
        if secret and request.headers.get("Authorization") != f"Bearer {secret}":
            return Response({"detail": "Unauthorized."}, status=401)

        from apps.accounts.models import User

        today = timezone.now().date()
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        summary = build_weekly_summary(start, end)

        recipients = list(
            User.objects.filter(role__in=[User.Role.HR_MANAGER, User.Role.SUPER_ADMIN], is_active=True)
            .exclude(email="")
            .values_list("email", flat=True)
        )
        if not recipients:
            return Response({"detail": "No HR/Admin recipients with an email address."})

        try:
            sent = send_weekly_report_email(recipients, start, end, summary)
        except Exception as exc:
            return Response({"detail": f"Failed to send: {exc}"}, status=500)
        return Response({"detail": "sent" if sent else "email not configured", "recipients": recipients})
