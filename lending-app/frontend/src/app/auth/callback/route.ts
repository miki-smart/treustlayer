import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import {
  ACCESS_COOKIE,
  OAUTH_STATE_COOKIE,
  OAUTH_VERIFIER_COOKIE,
  REFRESH_COOKIE,
  cookieBase,
} from "@/lib/cookies";
import { exchangeCode } from "@/lib/trustidlayer/client";

function clearOAuthCookies(res: NextResponse) {
  res.cookies.set(OAUTH_STATE_COOKIE, "", { ...cookieBase, maxAge: 0 });
  res.cookies.set(OAUTH_VERIFIER_COOKIE, "", { ...cookieBase, maxAge: 0 });
}

export async function GET(req: NextRequest) {
  const url = req.nextUrl;
  const oauthError = url.searchParams.get("error");
  if (oauthError) {
    const res = NextResponse.redirect(
      new URL(`/login?error=${encodeURIComponent(oauthError)}`, url.origin),
    );
    clearOAuthCookies(res);
    return res;
  }

  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");

  if (!code || !state) {
    return new NextResponse(
      `<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"/><title>Auth callback</title></head>
<body style="font-family:system-ui,sans-serif;max-width:28rem;margin:4rem auto;padding:0 1.5rem;line-height:1.5">
  <h1 style="font-size:1.25rem">Auth callback</h1>
  <p style="color:#666;font-size:0.875rem">This URL is registered with TrustIdLayer for the authorization-code flow. Use <strong>Sign in with TrustIdLayer</strong> on the login page to complete OAuth here.</p>
  <p><a href="/login" style="color:#2563eb">Go to login</a></p>
</body>
</html>`,
      { headers: { "Content-Type": "text/html; charset=utf-8" } },
    );
  }

  const jar = await cookies();
  const expectedState = jar.get(OAUTH_STATE_COOKIE)?.value;
  const codeVerifier = jar.get(OAUTH_VERIFIER_COOKIE)?.value;

  if (!expectedState || state !== expectedState || !codeVerifier) {
    const res = NextResponse.redirect(
      new URL("/login?error=invalid_oauth_state", url.origin),
    );
    clearOAuthCookies(res);
    return res;
  }

  const tok = await exchangeCode(code, codeVerifier);
  if (!tok.ok) {
    const res = NextResponse.redirect(
      new URL(
        `/login?error=${encodeURIComponent(tok.error.slice(0, 200))}`,
        url.origin,
      ),
    );
    clearOAuthCookies(res);
    return res;
  }

  const res = NextResponse.redirect(new URL("/loan?identity=1", url.origin));
  clearOAuthCookies(res);
  res.cookies.set(ACCESS_COOKIE, tok.tokens.access_token, {
    ...cookieBase,
    maxAge: tok.tokens.expires_in ?? 900,
  });
  if (tok.tokens.refresh_token) {
    res.cookies.set(REFRESH_COOKIE, tok.tokens.refresh_token, {
      ...cookieBase,
      maxAge: 60 * 60 * 24 * 30,
    });
  }
  return res;
}
