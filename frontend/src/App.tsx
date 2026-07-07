import { Routes, Route } from "react-router-dom";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EmployeesPage } from "./pages/EmployeesPage";
import { EmployeeProfilePage } from "./pages/EmployeeProfilePage";
import { OrgChartPage } from "./pages/OrgChartPage";
import { LeavePage } from "./pages/LeavePage";
import { LeaveWorkflowsPage } from "./pages/LeaveWorkflowsPage";
import { LeaveSetupPage } from "./pages/LeaveSetupPage";
import { AttendancePage } from "./pages/AttendancePage";
import { EmployeeAttendanceDetailPage } from "./pages/EmployeeAttendanceDetailPage";
import { MyProfilePage } from "./pages/MyProfilePage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { UsersPage } from "./pages/UsersPage";
import { OrganizationPage } from "./pages/OrganizationPage";
import { SystemSettingsPage } from "./pages/SystemSettingsPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { AppLayout } from "./components/layout/AppLayout";
import { ProtectedRoute, RoleRoute } from "./routes/ProtectedRoute";

// Nav items with no page built yet — route them to the placeholder 404
// instead of leaving the content area blank. Remove each entry here as its
// page is built.
const UNBUILT_PATHS = [
  "/recruitment",
  "/performance",
  "/training",
  "/assets",
  "/documents",
  "/announcements",
  "/helpdesk",
  "/disciplinary",
  "/exit-management",
  "/reports",
];

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/profile" element={<MyProfilePage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/employees" element={<EmployeesPage />} />
          <Route path="/employees/:id" element={<EmployeeProfilePage />} />
          <Route path="/org-chart" element={<OrgChartPage />} />
          <Route path="/leave" element={<LeavePage />} />
          <Route path="/attendance" element={<AttendancePage />} />
          <Route path="/attendance/employee/:id" element={<EmployeeAttendanceDetailPage />} />

          <Route element={<RoleRoute roles={["SUPER_ADMIN", "HR_MANAGER"]} />}>
            <Route path="/leave/workflows" element={<LeaveWorkflowsPage />} />
            <Route path="/leave/setup" element={<LeaveSetupPage />} />
          </Route>

          <Route element={<RoleRoute roles={["SUPER_ADMIN", "HR_MANAGER", "DEPARTMENT_MANAGER"]} />}>
            <Route path="/organization" element={<OrganizationPage />} />
          </Route>

          <Route element={<RoleRoute roles={["SUPER_ADMIN"]} />}>
            <Route path="/users" element={<UsersPage />} />
            <Route path="/settings" element={<SystemSettingsPage />} />
          </Route>

          {UNBUILT_PATHS.map((path) => (
            <Route key={path} path={path} element={<NotFoundPage title="Coming soon" message="This module hasn't been built yet — check back later." />} />
          ))}
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
