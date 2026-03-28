import { randomBytes } from "crypto";
import { NextRequest, NextResponse } from "next/server";
import {
  OAUTH_STATE_COOKIE,
  OAUTH_VERIFIER_COOKIE,
  cookieBase,
} from "@/lib/cookies";
import { codeChallengeS256, generateCodeVerifier } from "@/lib/pkce";
import {
  buildBrowserOAuthAuthorizationUrl,
  getOAuthAuthorizePageUrl,
} from "@/lib/trustidlayer/client";

function base64Url(buf: Buffer): string {
  return buf
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function getConfig() {
  const mockMode = process.env.TRUSTIDLAYER_MOCK === "true";
  const clientId = process.env.TRUSTIDLAYER_CLIENT_ID ?? "";
  const redirectUri =
    process.env.TRUSTIDLAYER_REDIRECT_URI ?? "http://localhost:3000/auth/callback";
  return { mockMode, clientId, redirectUri };
}

export async function GET(req: NextRequest) {
  const state = base64Url(randomBytes(16));
  const codeVerifier = generateCodeVerifier();
  const codeChallenge = codeChallengeS256(codeVerifier);
  const { mockMode, clientId, redirectUri } = getConfig();

  const cookieOpts = { ...cookieBase, maxAge: 600, httpOnly: true };

  if (mockMode) {
    const target = new URL("/auth/callback", req.nextUrl.origin);
    target.searchParams.set("code", "mock_code_oauth");
    target.searchParams.set("state", state);
    const res = NextResponse.redirect(target);
    res.cookies.set(OAUTH_STATE_COOKIE, state, cookieOpts);
    res.cookies.set(OAUTH_VERIFIER_COOKIE, codeVerifier, cookieOpts);
    return res;
  }

  const authorizePageUrl = getOAuthAuthorizePageUrl();
  if (!authorizePageUrl || !clientId) {
    return NextResponse.redirect(
      new URL("/login?error=oauth_not_configured", req.nextUrl.origin),
    );
  }

  const location = buildBrowserOAuthAuthorizationUrl({
    authorizePageUrl,
    clientId,
    redirectUri,
    state,
    codeChallenge,
  });

  const res = NextResponse.redirect(location);
  res.cookies.set(OAUTH_STATE_COOKIE, state, cookieOpts);
  res.cookies.set(OAUTH_VERIFIER_COOKIE, codeVerifier, cookieOpts);
  return res;
}
