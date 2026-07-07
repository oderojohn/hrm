import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck, Users2, Clock4 } from "lucide-react";
import { login as loginApi } from "../api/auth";
import { useAuthStore } from "../store/authStore";
import { extractErrorMessage } from "../api/client";
import { Input } from "../components/ui/Input";
import { Label } from "../components/ui/Label";
import { Button } from "../components/ui/Button";

export function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otpToken, setOtpToken] = useState("");
  const [requires2FA, setRequires2FA] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const response = await loginApi({ email, password, otp_token: otpToken || undefined });
      setAuth(response);
      navigate("/", { replace: true });
    } catch (err) {
      const data = (err as { response?: { data?: { requires_2fa?: boolean } } })?.response?.data;
      if (data?.requires_2fa) {
        setRequires2FA(true);
        setError("Enter the 6-digit code from your authenticator app.");
      } else {
        setError(extractErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Brand panel — hidden on small screens */}
      <div className="relative hidden w-1/2 overflow-hidden bg-gradient-to-br from-brand-600 via-brand-700 to-slate-900 lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="pointer-events-none absolute -top-24 -right-24 h-96 w-96 rounded-full bg-white/10 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 left-0 h-72 w-72 rounded-full bg-brand-400/20 blur-3xl" />

        <div className="relative flex items-center gap-2 rounded-lg bg-white/95 px-3 py-2 shadow-sm backdrop-blur w-fit">
          <img src="/emboita-logo.png" alt="Emboita Hotel" className="h-7 w-auto" />
        </div>

        <div className="relative space-y-8">
          <div>
            <h2 className="text-3xl font-semibold leading-tight text-white">
              One system for your <br /> entire workforce.
            </h2>
            <p className="mt-3 max-w-sm text-sm text-brand-100">
              Employees, leave, attendance, and reporting — connected end to end, with real
              biometric device integration.
            </p>
          </div>

          <div className="space-y-4">
            <FeatureRow icon={Users2} text="Employee records synced with your biometric devices" />
            <FeatureRow icon={Clock4} text="Attendance, leave workflows, and analytics in one place" />
            <FeatureRow icon={ShieldCheck} text="Role-based access with full audit history" />
          </div>
        </div>

        <p className="relative text-xs text-brand-100">© {new Date().getFullYear()} Emboita Hotel</p>
      </div>

      {/* Form panel */}
      <div className="flex w-full items-center justify-center px-4 py-12 lg:w-1/2">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex flex-col items-center lg:items-start">
            <img src="/emboita-logo.png" alt="Emboita Hotel" className="mb-4 h-9 w-auto lg:hidden" />
            <h1 className="text-xl font-semibold text-slate-900">Welcome back</h1>
            <p className="text-sm text-slate-500">Sign in to your Emboita Hotel HRM account</p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            {error && (
              <div className="mb-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">{error}</div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              {requires2FA && (
                <div>
                  <Label htmlFor="otp">Authenticator Code</Label>
                  <Input
                    id="otp"
                    inputMode="numeric"
                    maxLength={6}
                    value={otpToken}
                    onChange={(e) => setOtpToken(e.target.value)}
                    autoFocus
                  />
                </div>
              )}
              <Button type="submit" className="w-full" loading={loading}>
                Sign in
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

function FeatureRow({ icon: Icon, text }: { icon: typeof Users2; text: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/10 text-white">
        <Icon className="h-4 w-4" />
      </div>
      <p className="text-sm text-brand-50">{text}</p>
    </div>
  );
}
