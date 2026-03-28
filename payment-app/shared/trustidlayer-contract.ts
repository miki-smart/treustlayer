/**
 * TrustIdLayer identity contract — mirrors access_token JWT claims from
 * ExchangeTokenUseCase and POST /api/v1/auth/introspect (decode_token + active).
 * Keep in sync with backend-merged app/modules/auth/application/use_cases/exchange_token.py
 */

/** Claims returned by introspection when active === true (same shape as JWT payload). */
export interface TrustIdLayerIdentityClaims {
  active?: boolean;
  sub?: string;
  /** JWT may use string[] for scopes */
  scopes?: string[] | string;
  aud?: string;
  client_id?: string;
  username?: string;
  email?: string;
  email_verified?: boolean;
  phone_verified?: boolean;
  role?: string;
  kyc_tier?: string;
  trust_score?: number;
  risk_level?: string;
  risk_flag?: boolean;
  biometric_verified?: boolean;
  face_verified?: boolean;
  voice_verified?: boolean;
  digital_identity_id?: string | null;
  identity_status?: string | null;
  exp?: number;
  iat?: number;
  iss?: string;
  /** Scope names as granted (OAuth scopes, not always identical to JWT `scopes` field shape) */
  scope?: string;
}
