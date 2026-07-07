import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { KeyRound, ShieldCheck, UserPlus } from "lucide-react";
import {
  createEmployeeAccount,
  resetEmployeePassword,
  type AccountCredentials,
  type EmployeeProfile,
} from "../../api/employees";
import { extractErrorMessage } from "../../api/client";
import { useAuthStore } from "../../store/authStore";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Button } from "../ui/Button";
import { Dialog } from "../ui/Dialog";
import { Input } from "../ui/Input";
import { Label } from "../ui/Label";
import { Select } from "../ui/Select";
import { CredentialRevealDialog } from "../CredentialRevealDialog";

const ROLE_OPTIONS = [
  { value: "EMPLOYEE", label: "Employee" },
  { value: "DEPARTMENT_MANAGER", label: "Department Manager" },
  { value: "HR_MANAGER", label: "HR Manager" },
  { value: "SUPER_ADMIN", label: "Super Administrator" },
];

export function AccountPanel({ employee }: { employee: EmployeeProfile }) {
  const currentUser = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [email, setEmail] = useState(employee.email);
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("EMPLOYEE");
  const [formError, setFormError] = useState<string | null>(null);
  const [credentials, setCredentials] = useState<AccountCredentials | null>(null);

  const availableRoles =
    currentUser?.role === "SUPER_ADMIN" ? ROLE_OPTIONS : ROLE_OPTIONS.filter((r) => r.value !== "SUPER_ADMIN");

  const invalidateProfile = () => queryClient.invalidateQueries({ queryKey: ["employee-profile", employee.id] });

  const createMutation = useMutation({
    mutationFn: () => createEmployeeAccount(employee.id, { email, password: password || undefined, role }),
    onSuccess: (data) => {
      setCredentials(data);
      setCreateOpen(false);
      invalidateProfile();
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  const resetMutation = useMutation({
    mutationFn: () => resetEmployeePassword(employee.id),
    onSuccess: (data) => setCredentials(data),
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-slate-400" /> Login Account
        </CardTitle>
      </CardHeader>
      <CardContent>
        {employee.user ? (
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-800">Account active</p>
              <p className="text-xs text-slate-500">This employee can sign in to Emboita Hotel HRM.</p>
            </div>
            <Button size="sm" variant="outline" onClick={() => resetMutation.mutate()} loading={resetMutation.isPending}>
              <KeyRound className="h-3.5 w-3.5" /> Reset Password
            </Button>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-800">No login account</p>
              <p className="text-xs text-slate-500">Create one so this employee can sign in.</p>
            </div>
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <UserPlus className="h-3.5 w-3.5" /> Create Account
            </Button>
          </div>
        )}

        <Dialog
          open={createOpen}
          onClose={() => {
            setCreateOpen(false);
            setFormError(null);
          }}
          title="Create Login Account"
        >
          <div className="space-y-4">
            {formError && <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>}
            <div>
              <Label>Email (used to sign in)</Label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div>
              <Label>Password (leave blank to auto-generate)</Label>
              <Input type="text" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Auto-generate" />
            </div>
            <div>
              <Label>Role</Label>
              <Select value={role} onChange={(e) => setRole(e.target.value)}>
                {availableRoles.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
              <Button variant="outline" onClick={() => setCreateOpen(false)}>
                Cancel
              </Button>
              <Button onClick={() => createMutation.mutate()} loading={createMutation.isPending} disabled={!email}>
                Create Account
              </Button>
            </div>
          </div>
        </Dialog>

        <CredentialRevealDialog
          open={!!credentials}
          onClose={() => setCredentials(null)}
          title="Account Credentials"
          warning="Save this password now — it will not be shown again."
          fields={credentials ? [{ label: "Email", value: credentials.email }, { label: "Password", value: credentials.password }] : []}
        />
      </CardContent>
    </Card>
  );
}
