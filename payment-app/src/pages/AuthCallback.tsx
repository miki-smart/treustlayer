import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { setAccessToken } from "@/lib/session";
import { toast } from "sonner";

/**
 * Handles OAuth-style redirect if TrustIdLayer returns the user to this URL with ?code=.
 * PKCE verifier must be in sessionStorage from the login step that started the flow.
 */
export default function AuthCallback() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [msg, setMsg] = useState("Completing sign-in…");

  useEffect(() => {
    const code = params.get("code");
    const redirectUri = `${window.location.origin}/auth/callback`;
    const verifier = sessionStorage.getItem("pkce_code_verifier");

    if (!code || !verifier) {
      setMsg("Missing code or PKCE verifier. Use the in-app login form or demo token.");
      return;
    }

    (async () => {
      try {
        const tokenRes = await fetch("/api/auth/token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            grant_type: "authorization_code",
            code,
            redirect_uri: redirectUri,
            code_verifier: verifier,
          }),
        });
        const tokenJson = (await tokenRes.json().catch(() => ({}))) as Record<string, unknown>;
        const accessToken = typeof tokenJson.access_token === "string" ? tokenJson.access_token : "";
        sessionStorage.removeItem("pkce_code_verifier");
        if (!tokenRes.ok || !accessToken) {
          setMsg("Token exchange failed.");
          toast.error("Token exchange failed");
          return;
        }
        setAccessToken(accessToken);
        toast.success("Signed in");
        navigate("/", { replace: true });
      } catch {
        setMsg("Network error.");
      }
    })();
  }, [params, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center space-y-4 max-w-md">
        <Loader2 className="animate-spin mx-auto text-primary" />
        <p className="text-sm text-muted-foreground">{msg}</p>
        <Link to="/" className="text-primary text-sm hover:underline block">
          Home
        </Link>
      </div>
    </div>
  );
}
