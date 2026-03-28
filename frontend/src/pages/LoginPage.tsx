import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { authApi } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Shield, ScanFace, KeyRound, Fingerprint, Eye, EyeOff, Loader2, AlertCircle } from "lucide-react";

/** Seeded demo users — see backend `scripts/seed_demo_users.py` */
const DEMO_ACCOUNTS = [
  { label: "Admin", email: "admin@fininfra.io", password: "admin123" },
  { label: "User", email: "abebe@example.com", password: "user123" },
  { label: "KYC approver", email: "kyc@example.com", password: "kyc123" },
  { label: "App owner", email: "dev@example.com", password: "dev123" },
] as const;

const LoginPage = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<"login" | "register">("login");

  // Register form
  const [regEmail, setRegEmail] = useState("");
  const [regUsername, setRegUsername] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regName, setRegName] = useState("");
  const [regLoading, setRegLoading] = useState(false);
  const [regError, setRegError] = useState("");

  const { login } = useAuth();
  const navigate = useNavigate();

  const fillDemoAccount = (email: string, pw: string) => {
    setUsername(email);
    setPassword(pw);
    setError("");
    setTab("login");
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const ok = await login(username, password);
    setLoading(false);
    if (ok) {
      navigate("/dashboard");
    } else {
      setError("Invalid username or password. Please try again.");
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegError("");
    setRegLoading(true);
    try {
      await authApi.register({
        email: regEmail,
        username: regUsername,
        password: regPassword,
        full_name: regName || undefined,
      });
      // Auto-login after registration
      const ok = await login(regUsername, regPassword);
      if (ok) navigate("/dashboard");
    } catch (err: unknown) {
      setRegError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setRegLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <div className="w-full max-w-[960px] grid grid-cols-1 lg:grid-cols-2 rounded-2xl overflow-hidden shadow-2xl">
        {/* Left — branded panel */}
        <div className="login-gradient relative flex flex-col justify-end p-10 min-h-[520px]">
          <div className="absolute inset-0 opacity-[0.06]">
            <div className="absolute top-16 right-12 w-48 h-48 border border-white rounded-full" />
            <div className="absolute bottom-20 left-8 w-64 h-64 border border-white rounded-full" />
          </div>
          <div className="relative z-10 space-y-6">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Shield className="h-7 w-7 text-white" />
                <span className="text-2xl font-bold text-white tracking-tight">TrustLayer ID</span>
              </div>
              <p className="text-white/60 text-sm">Production-grade Digital Identity Infrastructure</p>
            </div>
            <h2 className="text-2xl font-bold text-white leading-snug max-w-xs">
              OIDC · KYC · Consent · Trust Scoring
            </h2>
            <div className="flex flex-wrap gap-3 pt-2">
              {[
                { icon: ScanFace, label: "eKYC" },
                { icon: Fingerprint, label: "Identity" },
                { icon: KeyRound, label: "OIDC / SSO" },
                { icon: Shield, label: "Trust Engine" },
              ].map(({ icon: Icon, label }) => (
                <div key={label} className="bg-white/10 backdrop-blur-sm rounded-lg px-3 py-2 flex items-center gap-2">
                  <Icon className="h-4 w-4 text-white/80" />
                  <span className="text-xs text-white/80">{label}</span>
                </div>
              ))}
            </div>
            <div className="pt-4 border-t border-white/10 space-y-2">
              <p className="text-white/50 text-xs">Quick demo — tap to fill sign-in form</p>
              <div className="flex flex-wrap gap-2">
                {DEMO_ACCOUNTS.map((d) => (
                  <button
                    key={d.email}
                    type="button"
                    onClick={() => fillDemoAccount(d.email, d.password)}
                    className="text-xs font-medium rounded-full px-3 py-1.5 bg-white/10 text-white/90 hover:bg-white/20 border border-white/15 transition-colors"
                  >
                    {d.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right — auth form */}
        <div className="bg-card flex flex-col justify-center p-10">
          {/* Tab switcher */}
          <div className="flex border rounded-lg overflow-hidden mb-8">
            <button
              className={`flex-1 py-2.5 text-sm font-medium transition-colors ${tab === "login" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"}`}
              onClick={() => { setTab("login"); setError(""); }}
            >
              Sign In
            </button>
            <button
              className={`flex-1 py-2.5 text-sm font-medium transition-colors ${tab === "register" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"}`}
              onClick={() => { setTab("register"); setRegError(""); }}
            >
              Register
            </button>
          </div>

          {tab === "login" ? (
            <form onSubmit={handleLogin} className="space-y-5">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">Username or Email</label>
                <Input
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter username or email"
                  className="h-11"
                  autoComplete="username"
                  required
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">Password</label>
                <div className="relative">
                  <Input
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    className="h-11 pr-10"
                    autoComplete="current-password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs text-muted-foreground">Quick demo — click to fill email and password</p>
                <div className="flex flex-wrap gap-2">
                  {DEMO_ACCOUNTS.map((d) => (
                    <Button
                      key={d.email}
                      type="button"
                      variant="secondary"
                      size="sm"
                      className="h-8 text-xs font-medium"
                      onClick={() => fillDemoAccount(d.email, d.password)}
                    >
                      {d.label}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Checkbox id="remember" checked={remember} onCheckedChange={(v) => setRemember(!!v)} />
                  <label htmlFor="remember" className="text-sm text-muted-foreground cursor-pointer">Remember me</label>
                </div>
                <button type="button" className="text-sm font-medium text-primary hover:underline">
                  Forgot password?
                </button>
              </div>

              {error && (
                <div className="flex items-center gap-2 text-destructive text-sm bg-destructive/10 rounded-lg px-3 py-2">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full h-11 text-sm font-medium" disabled={loading}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                {loading ? "Signing in…" : "Sign In"}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Full Name</label>
                  <Input value={regName} onChange={(e) => setRegName(e.target.value)} placeholder="Abebe Kebede" className="h-10" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Username <span className="text-destructive">*</span></label>
                  <Input value={regUsername} onChange={(e) => setRegUsername(e.target.value)} placeholder="abebe" className="h-10" required />
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Email <span className="text-destructive">*</span></label>
                <Input value={regEmail} onChange={(e) => setRegEmail(e.target.value)} type="email" placeholder="abebe@example.com" className="h-10" required />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Password <span className="text-destructive">*</span></label>
                <Input value={regPassword} onChange={(e) => setRegPassword(e.target.value)} type="password" placeholder="Min 8 characters" className="h-10" required minLength={8} />
              </div>

              {regError && (
                <div className="flex items-center gap-2 text-destructive text-sm bg-destructive/10 rounded-lg px-3 py-2">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {regError}
                </div>
              )}

              <Button type="submit" className="w-full h-11 text-sm font-medium" disabled={regLoading}>
                {regLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                {regLoading ? "Creating account…" : "Create Account"}
              </Button>

              <p className="text-xs text-muted-foreground text-center">
                By registering you agree to TrustLayer ID's Terms of Service.
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
