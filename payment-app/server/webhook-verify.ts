import crypto from "node:crypto";

/** Verifies `X-TrustLayer-Signature` as hex HMAC-SHA256 of the raw body. */
export function verifyTrustLayerSignature(
  rawBody: string,
  signatureHeader: string | undefined,
  signingSecret: string
): boolean {
  if (!signatureHeader || !signingSecret) return false;
  const sig = signatureHeader.replace(/^sha256=/, "").trim();
  const hmac = crypto.createHmac("sha256", signingSecret).update(rawBody, "utf8").digest("hex");
  try {
    const a = Buffer.from(hmac, "hex");
    const b = Buffer.from(sig, "hex");
    if (a.length !== b.length) return false;
    return crypto.timingSafeEqual(a, b);
  } catch {
    return false;
  }
}
