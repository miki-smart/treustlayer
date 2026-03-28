/** Decode JWT exp (seconds since epoch) without verifying signature — TrustIdLayer still authorizes via introspect. */

export function getJwtExpSeconds(token: string): number | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = JSON.parse(Buffer.from(parts[1], "base64url").toString("utf8"));
    return typeof payload.exp === "number" ? payload.exp : null;
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string, nowSeconds = Math.floor(Date.now() / 1000)): boolean {
  const exp = getJwtExpSeconds(token);
  if (exp === null) return true;
  return nowSeconds >= exp;
}
