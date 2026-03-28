import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Shield, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { generatePkcePair } from "@/lib/pkce";
import { setAccessToken, storeIdentitySnapshotFromTokenResponse } from "@/lib/session";
import { toast } from "sonner";

function randomState(): string {
  return base64Url(crypto.getRandomValues(new Uint8Array(16)));
}

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/** Must stay in sync with TrustIdLayer AuthorizeUseCase valid_scopes + app registry allowed_scopes. */
const OIDC_SCOPES = [
  "openid",
  "profile",
  "email",
  "phone",
  "kyc_status",
  "trust_score",
] as const;

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const redirectUri = `${window.location.origin}/auth/callback`;

  const handleDemoToken = () => {
    setAccessToken("demo:usr_001");
    toast.success("Demo session: token demo:usr_001");
    navigate("/");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const state = randomState();
      const { code_verifier, code_challenge } = await generatePkcePair();

      const authRes = await fetch("/api/auth/authorize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          password,
          redirect_uri: redirectUri,
          scopes: [...OIDC_SCOPES],
          state,
          code_challenge,
          code_challenge_method: "S256",
        }),
      });

      const authJson = (await authRes.json().catch(() => ({}))) as Record<string, unknown>;
      const code =
        (typeof authJson.code === "string" && authJson.code) ||
        (typeof authJson.authorization_code === "string" && authJson.authorization_code) ||
        "";

      if (!authRes.ok || !code) {
        toast.error(typeof authJson.detail === "string" ? authJson.detail : "Authorization failed");
        setLoading(false);
        return;
      }

      const tokenRes = await fetch("/api/auth/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          grant_type: "authorization_code",
          code,
          redirect_uri: redirectUri,
          code_verifier,
        }),
      });

      const tokenJson = (await tokenRes.json().catch(() => ({}))) as Record<string, unknown>;
      const accessToken = typeof tokenJson.access_token === "string" ? tokenJson.access_token : "";

      if (!tokenRes.ok || !accessToken) {
        toast.error("Token exchange failed");
        setLoading(false);
        return;
      }

      setAccessToken(accessToken);
      storeIdentitySnapshotFromTokenResponse(tokenJson);
      toast.success("Signed in");
      navigate("/");
    } catch {
      toast.error("Network error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-md card-elevated p-8 space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <Shield size={20} className="text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-bold">Sign in — TrustIdLayer</h1>
            <p className="text-xs text-muted-foreground">Authorization code + PKCE (secret stays on the API)</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-muted-foreground uppercase tracking-wider">Email</label>
            <Input
              type="email"
              className="mt-1 bg-muted border-border"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground uppercase tracking-wider">Password</label>
            <Input
              type="password"
              className="mt-1 bg-muted border-border"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="animate-spin" size={16} /> Signing in…
              </span>
            ) : (
              "Continue"
            )}
          </Button>
        </form>

        <div className="border-t border-border pt-4 space-y-3">
          <p className="text-xs text-muted-foreground text-center">Local demo (no TrustIdLayer host)</p>
          <Button type="button" variant="secondary" className="w-full" onClick={handleDemoToken}>
            Use demo token (Jane / tier_2)
          </Button>
        </div>

        <p className="text-center text-sm">
          <Link to="/" className="text-primary hover:underline">
            Back to dashboard
          </Link>
        </p>
      </div>
    </div>
  );
}
