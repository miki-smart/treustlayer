import { randomBytes } from "crypto";
import { NextResponse } from "next/server";
import { ACCESS_COOKIE, REFRESH_COOKIE, cookieBase } from "@/lib/cookies";
import { codeChallengeS256, generateCodeVerifier } from "@/lib/pkce";
import { authorize, exchangeCode } from "@/lib/trustidlayer/client";

export async function POST(req: Request) {
  let body: { username?: string; password?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }
  const username = body.username?.trim();
  const password = body.password;
  if (!username || !password) {
    return NextResponse.json({ error: "Username and password required" }, { status: 400 });
  }

  const codeVerifier = generateCodeVerifier();
  const codeChallenge = codeChallengeS256(codeVerifier);
  const state = base64Url(randomBytes(16));

  const auth = await authorize({
    username,
    password,
    state,
    codeVerifier,
    codeChallenge,
  });
  if (!auth.ok) {
    return NextResponse.json({ error: auth.error }, { status: 401 });
  }

  const tok = await exchangeCode(auth.code, codeVerifier);
  if (!tok.ok) {
    return NextResponse.json({ error: tok.error }, { status: 401 });
  }

  const res = NextResponse.json({ ok: true, redirect: "/loan" });
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

function base64Url(buf: Buffer): string {
  return buf
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}
