"""TEMPORARY — one-off endpoints for production diagnostics/fixes that need
the ORM but have no other way to run against the Vercel deployment (no
shell/DB access). Delete this file and its url entries once done.
"""
import hmac
import os

from django.http import Http404, JsonResponse
from django.views import View

from apps.attendance.models import PunchLog
from apps.employees.models import Employee
from apps.employees.services import merge_duplicate_employees


def _check_token(request):
    expected = os.environ.get("ADMIN_TASK_TOKEN", "")
    token = request.GET.get("token", "")
    if not expected or not hmac.compare_digest(token, expected):
        raise Http404


class TempMergeDuplicateEmployeesView(View):
    def get(self, request):
        _check_token(request)
        dry_run = request.GET.get("apply") != "1"
        report = merge_duplicate_employees(dry_run=dry_run)
        return JsonResponse({"dry_run": dry_run, "report": report})


class TempEmployeeDiagnosticsView(View):
    """Every Employee row that has a device_user_id (i.e. is or was enrolled
    on a device), regardless of branch/employment_status — so a device
    enrollment that's missing from the (branch- and status-filtered) public
    report can be traced to exactly why: wrong/no branch, inactive status,
    or genuinely absent from HRM.
    """

    def get(self, request):
        _check_token(request)
        employees = (
            Employee.all_objects.exclude(device_user_id__isnull=True)
            .exclude(device_user_id="")
            .select_related("branch", "department")
            .order_by("employee_number")
        )
        rows = []
        for e in employees:
            rows.append(
                {
                    "employee_number": e.employee_number,
                    "name": e.full_name,
                    "device_user_id": e.device_user_id,
                    "branch": e.branch.name if e.branch else None,
                    "department": e.department.name if e.department else None,
                    "employment_status": e.employment_status,
                    "is_deleted": e.is_deleted,
                    "punch_count": PunchLog.objects.filter(employee=e).count(),
                }
            )
        return JsonResponse({"count": len(rows), "employees": rows})
