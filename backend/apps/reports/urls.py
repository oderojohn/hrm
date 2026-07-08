from django.urls import path

from apps.reports.views import (
    AbsenteeismReportView,
    AssetReportView,
    AttendanceAnalyticsView,
    AttendanceReportView,
    BranchReportView,
    DashboardView,
    DepartmentReportView,
    DisciplinaryReportView,
    EmployeeAttendanceDetailView,
    EmployeeReportView,
    LateArrivalsReportView,
    LeaveReportView,
    PerformanceReportView,
    RecruitmentReportView,
    TrainingReportView,
    TurnoverReportView,
)

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("employees/", EmployeeReportView.as_view(), name="report-employees"),
    path("attendance/", AttendanceReportView.as_view(), name="report-attendance"),
    path("attendance-analytics/", AttendanceAnalyticsView.as_view(), name="report-attendance-analytics"),
    path("attendance-late-arrivals/", LateArrivalsReportView.as_view(), name="report-attendance-late-arrivals"),
    path("attendance-absenteeism/", AbsenteeismReportView.as_view(), name="report-attendance-absenteeism"),
    path(
        "attendance/employee/<int:employee_id>/",
        EmployeeAttendanceDetailView.as_view(),
        name="report-attendance-employee",
    ),
    path("leave/", LeaveReportView.as_view(), name="report-leave"),
    path("departments/", DepartmentReportView.as_view(), name="report-departments"),
    path("branches/", BranchReportView.as_view(), name="report-branches"),
    path("recruitment/", RecruitmentReportView.as_view(), name="report-recruitment"),
    path("performance/", PerformanceReportView.as_view(), name="report-performance"),
    path("training/", TrainingReportView.as_view(), name="report-training"),
    path("assets/", AssetReportView.as_view(), name="report-assets"),
    path("disciplinary/", DisciplinaryReportView.as_view(), name="report-disciplinary"),
    path("turnover/", TurnoverReportView.as_view(), name="report-turnover"),
]
