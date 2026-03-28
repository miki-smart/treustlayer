import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { ACCESS_COOKIE } from "@/lib/cookies";
import { getIdentityIntrospectionSnapshot } from "@/lib/loan-service";

/**
 * Returns TrustIdLayer introspection JSON for the current session access token.
 * Same claim shape as POST /api/v1/auth/introspect on the IdP.
 */
export async function GET() {
  const jar = await cookies();
  const token = jar.get(ACCESS_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "not_authenticated" }, { status: 401 });
  }

  const r = await getIdentityIntrospectionSnapshot(token);
  if (!r.ok) {
    const status = r.reason === "inactive" ? 401 : 503;
    return NextResponse.json({ error: r.reason }, { status });
  }

  return NextResponse.json(r.snapshot);
}
