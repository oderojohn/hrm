from django.db import models

from apps.core.models import BaseModel


class SyncAgent(BaseModel):
    """A registered local sync agent installation (the Tkinter desktop app
    running next to a physical ZK device at a branch). Authenticates to the
    push endpoint with a long-lived API key instead of a user login — see
    apps.attendance.authentication.SyncAgentAuthentication.
    """

    # Duck-types as a DRF auth principal so request.user.is_authenticated
    # works without this being a real Django user.
    is_authenticated = True

    name = models.CharField(max_length=150)
    branch = models.ForeignKey(
        "organization.Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="sync_agents"
    )
    key_prefix = models.CharField(max_length=16, unique=True, editable=False)
    key_hash = models.CharField(max_length=64, editable=False)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SyncEvent(BaseModel):
    """A record of every communication from a SyncAgent — pushes, auth
    failures, errors — so a cloud admin can see exactly what each local
    installation has been doing.
    """

    class EventType(models.TextChoices):
        AUTH_FAILED = "AUTH_FAILED", "Authentication Failed"
        PUSH = "PUSH", "Data Push"
        ERROR = "ERROR", "Error"

    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    agent = models.ForeignKey(
        SyncAgent, null=True, blank=True, on_delete=models.SET_NULL, related_name="sync_events"
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    status = models.CharField(max_length=10, choices=Status.choices)
    summary = models.CharField(max_length=255)
    payload = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"])]

    def __str__(self):
        return f"{self.get_event_type_display()} — {self.summary}"


class Device(BaseModel):
    """A physical attendance-capture device (e.g. a ZKTeco biometric unit).

    Kept as its own model (rather than hardcoded settings) so the system can
    support more than one device per branch without further schema changes.
    """

    class DeviceType(models.TextChoices):
        ZKTECO = "ZKTECO", "ZKTeco Biometric"

    name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, choices=DeviceType.choices, default=DeviceType.ZKTECO)
    branch = models.ForeignKey(
        "organization.Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="devices"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    port = models.PositiveIntegerField(default=4370)
    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AttendanceRecord(BaseModel):
    class Method(models.TextChoices):
        MANUAL = "MANUAL", "Manual"
        GPS = "GPS", "GPS"
        QR = "QR", "QR Code"
        BIOMETRIC = "BIOMETRIC", "Fingerprint"
        FACE = "FACE", "Face Recognition"

    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="attendance_records"
    )
    device = models.ForeignKey(
        Device, null=True, blank=True, on_delete=models.SET_NULL, related_name="attendance_records"
    )
    date = models.DateField()
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.MANUAL)
    clock_in_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_in_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_out_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    clock_out_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_late = models.BooleanField(default=False)
    is_early_departure = models.BooleanField(default=False)
    overtime_minutes = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ["employee", "date"]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.employee} - {self.date}"


class PunchLog(BaseModel):
    """Every individual clock event, kept verbatim (unlike AttendanceRecord,
    which collapses a day down to first-in/last-out). Lets HR see exactly how
    many times someone punched in a given day, not just the net result.
    """

    class Event(models.TextChoices):
        IN = "IN", "In"
        OUT = "OUT", "Out"
        UNKNOWN = "UNKNOWN", "Unknown"

    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="punch_logs"
    )
    device = models.ForeignKey(
        Device, null=True, blank=True, on_delete=models.SET_NULL, related_name="punch_logs"
    )
    timestamp = models.DateTimeField()
    event = models.CharField(max_length=10, choices=Event.choices, default=Event.UNKNOWN)
    method = models.CharField(
        max_length=20, choices=AttendanceRecord.Method.choices, default=AttendanceRecord.Method.BIOMETRIC
    )
    raw_status = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        unique_together = ["employee", "device", "timestamp"]
        indexes = [models.Index(fields=["employee", "timestamp"])]

    def __str__(self):
        return f"{self.employee} {self.event} @ {self.timestamp}"


class BreakRecord(BaseModel):
    attendance = models.ForeignKey(
        AttendanceRecord, on_delete=models.CASCADE, related_name="breaks"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"Break for {self.attendance}"


class AttendanceCorrectionRequest(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    class SupervisorStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SKIPPED = "SKIPPED", "Skipped"

    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="correction_requests"
    )
    attendance = models.ForeignKey(
        AttendanceRecord,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="correction_requests",
    )
    date = models.DateField()
    requested_clock_in = models.DateTimeField(null=True, blank=True)
    requested_clock_out = models.DateTimeField(null=True, blank=True)
    reason = models.TextField()
    # Two-step approval: Employee -> Supervisor (employee.reporting_manager,
    # resolved at submission time so history is stable even if the manager
    # later changes) -> HR. `supervisor_status` defaults to SKIPPED so rows
    # created before this workflow existed (and any created for an employee
    # with no reporting_manager) go straight to the HR stage below.
    supervisor = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="corrections_to_approve",
    )
    supervisor_status = models.CharField(
        max_length=20, choices=SupervisorStatus.choices, default=SupervisorStatus.SKIPPED
    )
    supervisor_reviewed_at = models.DateTimeField(null=True, blank=True)
    supervisor_comment = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_corrections",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Correction for {self.employee} on {self.date}"

    @property
    def current_stage(self):
        if self.status != self.Status.PENDING:
            return "DONE"
        if self.supervisor_status == self.SupervisorStatus.PENDING:
            return "SUPERVISOR"
        return "HR"


class AttendanceSettings(models.Model):
    """Effectively a singleton — one row holds company-wide attendance
    defaults. Per-shift working_days/grace_period on WorkShift always win;
    weekend_days here is only the fallback used for employees with no
    work_shift assigned (previously silently treated as working every day).
    """

    weekend_days = models.JSONField(
        default=list,
        help_text="ISO weekday numbers (1=Mon..7=Sun) treated as non-working "
        "for employees with no work shift assigned.",
    )

    class Meta:
        verbose_name = "Attendance Settings"
        verbose_name_plural = "Attendance Settings"

    def __str__(self):
        return "Attendance Settings"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"weekend_days": [6, 7]})
        return obj


class QRToken(BaseModel):
    branch = models.ForeignKey(
        "organization.Branch", null=True, blank=True, on_delete=models.CASCADE, related_name="qr_tokens"
    )
    work_shift = models.ForeignKey(
        "organization.WorkShift", null=True, blank=True, on_delete=models.CASCADE, related_name="qr_tokens"
    )
    token = models.CharField(max_length=64, unique=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-valid_from"]

    def __str__(self):
        return f"QR {self.token[:8]}... ({self.branch})"
