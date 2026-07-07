from datetime import date

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.employees.models import Employee
from apps.leave.models import LeaveBalance, LeavePolicy, LeaveType
from apps.organization.models import Branch, Department, Position, WorkShift

DEMO_PASSWORD = "ChangeMe123!"


class Command(BaseCommand):
    help = "Seeds minimal demo data (branch, department, manager + employee, leave type) for local exploration."

    def handle(self, *args, **options):
        branch, _ = Branch.objects.get_or_create(
            code="HQ", defaults={"name": "Head Office", "city": "Nairobi"}
        )
        department, _ = Department.objects.get_or_create(
            code="ENG", defaults={"name": "Engineering", "branch": branch}
        )
        position, _ = Position.objects.get_or_create(
            code="DEV", defaults={"title": "Software Developer"}
        )
        shift, _ = WorkShift.objects.get_or_create(
            name="Day Shift",
            defaults={"start_time": "08:00", "end_time": "17:00", "working_days": [1, 2, 3, 4, 5]},
        )

        manager_user, created = User.objects.get_or_create(
            email="manager@nexashrm.local", defaults={"role": User.Role.DEPARTMENT_MANAGER}
        )
        if created:
            manager_user.set_password(DEMO_PASSWORD)
            manager_user.save()

        manager_employee, _ = Employee.objects.get_or_create(
            national_id="M0001",
            defaults=dict(
                user=manager_user,
                first_name="Mary",
                last_name="Manager",
                gender="FEMALE",
                employment_date=date(2022, 1, 10),
                employment_type="FULL_TIME",
                department=department,
                position=position,
                branch=branch,
                work_shift=shift,
            ),
        )
        department.head = manager_employee
        department.save()

        emp_user, created = User.objects.get_or_create(
            email="employee@nexashrm.local", defaults={"role": User.Role.EMPLOYEE}
        )
        if created:
            emp_user.set_password(DEMO_PASSWORD)
            emp_user.save()

        Employee.objects.get_or_create(
            national_id="E0001",
            defaults=dict(
                user=emp_user,
                first_name="John",
                last_name="Employee",
                gender="MALE",
                employment_date=date(2023, 3, 1),
                employment_type="FULL_TIME",
                department=department,
                position=position,
                branch=branch,
                work_shift=shift,
                reporting_manager=manager_employee,
            ),
        )
        employee = Employee.objects.get(national_id="E0001")

        leave_type, _ = LeaveType.objects.get_or_create(
            code="ANNUAL", defaults={"name": "Annual Leave", "is_paid": True}
        )
        LeavePolicy.objects.get_or_create(
            leave_type=leave_type, defaults={"default_days_per_year": 21}
        )
        LeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=leave_type,
            year=date.today().year,
            defaults={"allocated_days": 21},
        )

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
        self.stdout.write(f"  Manager login:  manager@nexashrm.local / {DEMO_PASSWORD}")
        self.stdout.write(f"  Employee login: employee@nexashrm.local / {DEMO_PASSWORD}")
