import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Briefcase, Building2, Hash, KeyRound, ShieldAlert, ShieldCheck, User as UserIcon } from "lucide-react";
import { fetchMyEmployeeProfile, updateMyEmployeeProfile, type MyEmployeeProfile } from "../api/employees";
import { changePassword, fetchMe, updateMe } from "../api/auth";
import { extractErrorMessage } from "../api/client";
import { useAuthStore } from "../store/authStore";
import type { User } from "../types";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Label } from "../components/ui/Label";
import { Select } from "../components/ui/Select";
import { FullPageSpinner } from "../components/ui/Spinner";
import { ProfileHeaderBanner } from "../components/ProfileHeaderBanner";

const MARITAL_OPTIONS = [
  { value: "SINGLE", label: "Single" },
  { value: "MARRIED", label: "Married" },
  { value: "DIVORCED", label: "Divorced" },
  { value: "WIDOWED", label: "Widowed" },
];

export function MyProfilePage() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="space-y-5">
      {user?.employee_id ? <EmployeeProfileSection /> : <AccountSettingsSection />}
      <ChangePasswordCard />
    </div>
  );
}

/** For users with no linked Employee record (e.g. a pure admin/HR account) —
 * basic account fields via /auth/me/, no employee-specific data to show. */
function AccountSettingsSection() {
  const setUser = useAuthStore((s) => s.setUser);
  const [form, setForm] = useState<Partial<User> | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: me, isLoading } = useQuery({
    queryKey: ["my-account"],
    queryFn: fetchMe,
  });

  const updateMutation = useMutation({
    mutationFn: (payload: Partial<User>) => updateMe(payload),
    onSuccess: (data) => {
      setUser(data);
      setSuccessMessage("Account updated.");
      setFormError(null);
    },
    onError: (err) => {
      setFormError(extractErrorMessage(err));
      setSuccessMessage(null);
    },
  });

  if (isLoading || !me) return <FullPageSpinner />;
  const values = form ?? me;
  const displayName = [me.first_name, me.last_name].filter(Boolean).join(" ") || me.email;

  const setField = (field: keyof User, value: string) => setForm({ ...values, [field]: value });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!form) return;
    updateMutation.mutate(form);
  };

  return (
    <>
      <ProfileHeaderBanner
        name={displayName}
        subtitle={me.email}
        metaItems={[{ icon: ShieldCheck, label: me.role.replaceAll("_", " ") }]}
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserIcon className="h-4 w-4 text-slate-400" /> Account Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-4 text-sm text-slate-500">No employee record is linked to this account.</p>

          {successMessage && (
            <div className="mb-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{successMessage}</div>
          )}
          {formError && <div className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <Label>First Name</Label>
                <Input value={values.first_name ?? ""} onChange={(e) => setField("first_name", e.target.value)} />
              </div>
              <div>
                <Label>Last Name</Label>
                <Input value={values.last_name ?? ""} onChange={(e) => setField("last_name", e.target.value)} />
              </div>
              <div>
                <Label>Email</Label>
                <Input type="email" value={values.email ?? ""} onChange={(e) => setField("email", e.target.value)} />
              </div>
              <div>
                <Label>Phone Number</Label>
                <Input value={values.phone_number ?? ""} onChange={(e) => setField("phone_number", e.target.value)} />
              </div>
            </div>
            <div className="flex justify-end border-t border-slate-100 pt-4">
              <Button type="submit" loading={updateMutation.isPending}>
                Save Changes
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </>
  );
}

function EmployeeProfileSection() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<Partial<MyEmployeeProfile> | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: profile, isLoading } = useQuery({
    queryKey: ["my-profile"],
    queryFn: fetchMyEmployeeProfile,
  });

  const updateMutation = useMutation({
    mutationFn: (payload: Partial<MyEmployeeProfile>) => updateMyEmployeeProfile(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-profile"] });
      setSuccessMessage("Profile updated.");
      setFormError(null);
    },
    onError: (err) => {
      setFormError(extractErrorMessage(err));
      setSuccessMessage(null);
    },
  });

  if (isLoading || !profile) return <FullPageSpinner />;
  const values = form ?? profile;

  const setField = (field: keyof MyEmployeeProfile, value: string) => {
    setForm({ ...values, [field]: value });
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!form) return;
    updateMutation.mutate(form);
  };

  return (
    <>
      <ProfileHeaderBanner
        name={profile.full_name}
        photoUrl={profile.photo}
        metaItems={[
          { icon: Hash, label: profile.employee_number },
          { icon: Briefcase, label: profile.position_title ?? "No position" },
          { icon: Building2, label: profile.department_name ?? "No department" },
        ]}
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserIcon className="h-4 w-4 text-slate-400" /> Contact Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          {successMessage && (
            <div className="mb-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{successMessage}</div>
          )}
          {formError && <div className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <Label>Email</Label>
                <Input type="email" value={values.email ?? ""} onChange={(e) => setField("email", e.target.value)} />
              </div>
              <div>
                <Label>Phone Number</Label>
                <Input value={values.phone_number ?? ""} onChange={(e) => setField("phone_number", e.target.value)} />
              </div>
              <div>
                <Label>Alternative Phone</Label>
                <Input
                  value={values.alternative_phone ?? ""}
                  onChange={(e) => setField("alternative_phone", e.target.value)}
                />
              </div>
              <div>
                <Label>Marital Status</Label>
                <Select value={values.marital_status ?? ""} onChange={(e) => setField("marital_status", e.target.value)}>
                  <option value="">Select...</option>
                  {MARITAL_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="sm:col-span-2">
                <Label>Address</Label>
                <Input value={values.address ?? ""} onChange={(e) => setField("address", e.target.value)} />
              </div>
              <div>
                <Label>County</Label>
                <Input value={values.county ?? ""} onChange={(e) => setField("county", e.target.value)} />
              </div>
              <div>
                <Label>Sub County</Label>
                <Input value={values.sub_county ?? ""} onChange={(e) => setField("sub_county", e.target.value)} />
              </div>
              <div>
                <Label>Postal Address</Label>
                <Input value={values.postal_address ?? ""} onChange={(e) => setField("postal_address", e.target.value)} />
              </div>
            </div>

            <div className="flex justify-end border-t border-slate-100 pt-4">
              <Button type="submit" loading={updateMutation.isPending}>
                Save Changes
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-slate-400" /> Emergency Contact
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <Label>Name</Label>
                <Input
                  value={values.emergency_contact_name ?? ""}
                  onChange={(e) => setField("emergency_contact_name", e.target.value)}
                />
              </div>
              <div>
                <Label>Phone</Label>
                <Input
                  value={values.emergency_contact_phone ?? ""}
                  onChange={(e) => setField("emergency_contact_phone", e.target.value)}
                />
              </div>
              <div>
                <Label>Relationship</Label>
                <Input
                  value={values.emergency_contact_relationship ?? ""}
                  onChange={(e) => setField("emergency_contact_relationship", e.target.value)}
                />
              </div>
            </div>
            <div className="flex justify-end border-t border-slate-100 pt-4">
              <Button type="submit" loading={updateMutation.isPending}>
                Save Changes
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </>
  );
}

function ChangePasswordCard() {
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => changePassword(oldPassword, newPassword),
    onSuccess: () => {
      setMessage("Password updated.");
      setError(null);
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
    },
    onError: (err) => {
      setError(extractErrorMessage(err));
      setMessage(null);
    },
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }
    mutation.mutate();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <KeyRound className="h-4 w-4 text-slate-400" /> Change Password
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="mb-4 text-sm text-slate-500">
          Choose a strong password you don't use anywhere else. You'll stay signed in on this device.
        </p>
        {message && <div className="mb-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div>}
        {error && <div className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <Label>Current Password</Label>
            <Input type="password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} required />
          </div>
          <div>
            <Label>New Password</Label>
            <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
          </div>
          <div>
            <Label>Confirm New Password</Label>
            <Input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          <div className="sm:col-span-3 flex justify-end">
            <Button type="submit" loading={mutation.isPending}>
              Update Password
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
