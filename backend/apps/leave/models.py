from django.db import models

from apps.accounts.models import User
from apps.core.models import BaseModel


class LeaveType(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=255, blank=True)
    is_paid = models.BooleanField(default=True)
    requires_attachment = models.BooleanField(default=False)
    allow_half_day = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LeavePolicy(BaseModel):
    leave_type = models.OneToOneField(LeaveType, on_delete=models.CASCADE, related_name="policy")
    default_days_per_year = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    accrual_rate_per_month = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_carry_forward_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    max_consecutive_days = models.PositiveIntegerField(null=True, blank=True)
    min_service_months = models.PositiveIntegerField(default=0)
    requires_approval = models.BooleanField(default=True)
    allow_negative_balance = models.BooleanField(
        default=False, help_text="If enabled, employees may submit requests exceeding their remaining balance."
    )

    class Meta:
        verbose_name_plural = "Leave Policies"

    def __str__(self):
        return f"Policy for {self.leave_type.name}"


class LeaveBalance(BaseModel):
    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="leave_balances"
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name="balances")
    year = models.PositiveIntegerField()
    allocated_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    carried_forward_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    used_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)

    class Meta:
        unique_together = ["employee", "leave_type", "year"]
        ordering = ["-year"]

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.year})"

    @property
    def remaining_days(self):
        return (self.allocated_days + self.carried_forward_days) - self.used_days


class LeaveRequest(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"
        RETURNED = "RETURNED", "Returned for Correction"

    class HalfDayPeriod(models.TextChoices):
        AM = "AM", "Morning"
        PM = "PM", "Afternoon"

    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="leave_requests"
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name="requests")
    start_date = models.DateField()
    end_date = models.DateField()
    is_half_day = models.BooleanField(default=False)
    half_day_period = models.CharField(
        max_length=2, choices=HalfDayPeriod.choices, blank=True
    )
    total_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    reason = models.TextField(blank=True)
    attachment = models.FileField(upload_to="leave/attachments/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    cancelled_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date} to {self.end_date})"


class WorkflowTemplate(BaseModel):
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(
        default=False, help_text="Used as a fallback when no other template's assignment rules match."
    )
    priority = models.PositiveIntegerField(
        default=0, help_text="When multiple templates match a request, the highest priority wins."
    )
    require_all_parallel_approvers = models.BooleanField(
        default=False,
        help_text="When a step has multiple approvers (same order), require all of them rather than any one.",
    )
    departments = models.ManyToManyField(
        "organization.Department", blank=True, related_name="leave_workflow_templates"
    )
    branches = models.ManyToManyField(
        "organization.Branch", blank=True, related_name="leave_workflow_templates"
    )
    leave_types = models.ManyToManyField(LeaveType, blank=True, related_name="workflow_templates")
    employment_types = models.JSONField(
        default=list, blank=True, help_text="List of Employee.EmploymentType values. Empty = applies to any."
    )

    class Meta:
        ordering = ["-priority", "name"]

    def __str__(self):
        return self.name

    def matches(self, leave_request):
        employee = leave_request.employee
        if self.departments.exists() and employee.department_id not in self.departments.values_list("id", flat=True):
            return False
        if self.branches.exists() and employee.branch_id not in self.branches.values_list("id", flat=True):
            return False
        if self.leave_types.exists() and leave_request.leave_type_id not in self.leave_types.values_list(
            "id", flat=True
        ):
            return False
        if self.employment_types and employee.employment_type not in self.employment_types:
            return False
        return True


class WorkflowStep(BaseModel):
    class ResolverType(models.TextChoices):
        REPORTING_MANAGER = "REPORTING_MANAGER", "Reporting Manager"
        SKIP_LEVEL_MANAGER = "SKIP_LEVEL_MANAGER", "Manager's Manager (N levels up)"
        DEPARTMENT_HEAD = "DEPARTMENT_HEAD", "Department Head"
        BRANCH_MANAGER = "BRANCH_MANAGER", "Branch Manager"
        SPECIFIC_EMPLOYEE = "SPECIFIC_EMPLOYEE", "Specific Employee"
        SYSTEM_ROLE = "SYSTEM_ROLE", "Anyone with a System Role"

    template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, related_name="steps")
    step_order = models.PositiveIntegerField()
    name = models.CharField(max_length=100, help_text="Admin-facing label, e.g. 'Head of Department'.")
    resolver_type = models.CharField(max_length=30, choices=ResolverType.choices)
    specific_employee = models.ForeignKey(
        "employees.Employee", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    system_role = models.CharField(max_length=30, choices=User.Role.choices, blank=True)
    skip_levels = models.PositiveIntegerField(
        default=1, help_text="For 'Manager's Manager' — how many reporting-manager hops to walk up."
    )
    min_days = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        help_text="Only include this step if the request's total days is at least this.",
    )
    max_days = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        help_text="Only include this step if the request's total days is at most this.",
    )
    reminder_after_hours = models.PositiveIntegerField(null=True, blank=True)
    escalation_after_hours = models.PositiveIntegerField(null=True, blank=True)
    escalate_to_employee = models.ForeignKey(
        "employees.Employee", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["step_order"]

    def __str__(self):
        return f"{self.template.name} — Step {self.step_order}: {self.name}"


class LeaveApprovalStep(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SKIPPED = "SKIPPED", "Skipped"

    leave_request = models.ForeignKey(
        LeaveRequest, on_delete=models.CASCADE, related_name="approval_steps"
    )
    source_step = models.ForeignKey(
        WorkflowStep, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    step_order = models.PositiveIntegerField()
    name = models.CharField(max_length=100, blank=True)
    resolver_type = models.CharField(max_length=30, choices=WorkflowStep.ResolverType.choices, blank=True)
    system_role = models.CharField(max_length=30, choices=User.Role.choices, blank=True)
    approver = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leave_steps_to_approve",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    comment = models.CharField(max_length=255, blank=True)
    acted_by = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leave_steps_acted",
    )
    acted_at = models.DateTimeField(null=True, blank=True)
    entered_at = models.DateTimeField(
        null=True, blank=True, help_text="When this step became the active pending step."
    )
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["step_order"]

    def __str__(self):
        return f"Step {self.step_order} ({self.name or self.resolver_type}) - {self.status}"
