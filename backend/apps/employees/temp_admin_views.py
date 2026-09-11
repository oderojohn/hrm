"""TEMPORARY — one-off endpoint to run merge_duplicate_employees against
production (no shell/DB access to the Vercel deployment otherwise). Delete
this file and its url entry once the merge has been applied and verified.
"""
import hmac
import os

from django.http import Http404, JsonResponse
from django.views import View

from apps.employees.services import merge_duplicate_employees


class TempMergeDuplicateEmployeesView(View):
    def get(self, request):
        expected = os.environ.get("ADMIN_TASK_TOKEN", "")
        token = request.GET.get("token", "")
        if not expected or not hmac.compare_digest(token, expected):
            raise Http404

        dry_run = request.GET.get("apply") != "1"
        report = merge_duplicate_employees(dry_run=dry_run)
        return JsonResponse({"dry_run": dry_run, "report": report})
