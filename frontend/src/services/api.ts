/**
 * TrustLayer ID — API client
 * Base URL: /api/v1  (proxied by nginx to the FastAPI backend)
 */

const BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

// ── Token storage ─────────────────────────────────────────────────────────────

export const tokenStore = {
  get: () => localStorage.getItem("access_token"),
  set: (t: string) => localStorage.setItem("access_token", t),
  clear: () => { localStorage.removeItem("access_token"); localStorage.removeItem("refresh_token"); },
  getRefresh: () => localStorage.getItem("refresh_token"),
  setRefresh: (t: string) => localStorage.setItem("refresh_token", t),
};

// ── Core fetch wrapper ────────────────────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = true,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (auth) {
    const token = tokenStore.get();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data?.detail || data?.message || `HTTP ${res.status}`;
    throw new Error(Array.isArray(msg) ? msg.map((e: { msg: string }) => e.msg).join("; ") : msg);
  }
  return data as T;
}

export const api = {
  get:    <T>(path: string) => request<T>(path, { method: "GET" }),
  post:   <T>(path: string, body?: unknown, auth = true) => request<T>(path, { method: "POST",  body: JSON.stringify(body) }, auth),
  patch:  <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

// ── Types ─────────────────────────────────────────────────────────────────────

export interface UserResponse {
  id: string;
  email: string;
  username: string;
  role: string;
  full_name: string | null;
  phone_number: string | null;
  is_active: boolean;
  is_email_verified: boolean;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  username: string;
  role: string;
}

export interface KYCResponse {
  id: string;
  user_id: string;
  user_name?: string | null;
  user_email?: string | null;
  status: string;
  tier: string;
  trust_score: number;
  document_type: string | null;
  document_number: string | null;
  rejection_reason: string | null;
  face_similarity_score: number | null;
  ocr_confidence?: number | null;
  submitted_at?: string | null;
  reviewed_at?: string | null;
  extracted_data?: Record<string, unknown> | null;
}

export interface OcrExtractedData {
  full_name: string | null;
  date_of_birth: string | null;
  id_number: string | null;
  gender: string | null;
  nationality: string | null;
  place_of_birth: string | null;
  issue_date: string | null;
  expiry_date: string | null;
  address: string | null;
  billing_name: string | null;
  service_provider: string | null;
  service_type: string | null;
  bill_date: string | null;
  account_number: string | null;
  mrz_line1: string | null;
  mrz_line2: string | null;
  id_ocr_confidence: number;
  utility_ocr_confidence: number;
  overall_confidence: number;
  documents_processed: string[];
}

export interface OcrResponse {
  success: boolean;
  extracted: OcrExtractedData;
  warnings: string[];
  model_used: string;
}

export interface AppResponse {
  id: string;
  name: string;
  client_id: string;
  client_secret?: string | null;
  api_key?: string | null;
  owner_id?: string | null;
  allowed_scopes: string[];
  redirect_uris: string[];
  description: string;
  is_active: boolean;
  is_approved: boolean;
}

export interface ConsentResponse {
  id: string;
  user_id: string;
  client_id: string;
  scopes: string[];
  is_active: boolean;
  granted_at: string;
  revoked_at?: string | null;
}

export interface ActiveSessionResponse {
  id: string;
  client_id: string;
  scopes: string[];
  expires_at: string;
  created_at: string;
}

export interface WebhookSubscriptionResponse {
  id: string;
  client_id: string;
  event_type: string;
  target_url: string;
  signing_secret?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface WebhookDeliveryResponse {
  id: string;
  client_id: string;
  event_type: string;
  target_url: string;
  status: string;
  attempts: number;
  max_attempts: number;
  delivered_at?: string | null;
  response_code?: number | null;
  created_at: string;
}

export interface TrustProfile {
  trust_score: number;
  kyc_tier: number;
  risk_level: string;
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (username: string, password: string) =>
    api.post<LoginResponse>("/auth/login", { email: username, password }, false),

  logout: (refresh_token: string) =>
    api.post<void>("/auth/logout", { refresh_token }),

  me: () => api.get<UserResponse>("/identity/users/me"),

  register: (body: {
    email: string; username: string; password: string;
    full_name?: string; phone_number?: string;
  }) => api.post<UserResponse>("/identity/register", body, false),

  forgotPassword: (email: string) =>
    api.post<unknown>("/identity/forgot-password", { email }, false),

  resetPassword: (token: string, new_password: string) =>
    api.post<unknown>("/identity/reset-password", { token, new_password }, false),

  changePassword: (user_id: string, current_password: string, new_password: string) =>
    api.post<unknown>(`/identity/users/${user_id}/change-password`, { current_password, new_password }),

  sendVerificationEmail: () =>
    api.post<unknown>("/identity/send-verification-email", {}),

  verifyEmail: (token: string) =>
    api.post<unknown>("/identity/verify-email", { token }, false),
};

// ── Identity / Users ──────────────────────────────────────────────────────────

export const identityApi = {
  getUser: (user_id: string) => api.get<UserResponse>(`/identity/users/${user_id}`),
  updateUser: (user_id: string, body: { full_name?: string; phone_number?: string }) =>
    api.patch<UserResponse>(`/identity/users/${user_id}`, body),
  listUsers: (skip = 0, limit = 50) =>
    api.get<UserResponse[]>(`/identity/users?skip=${skip}&limit=${limit}`),
  assignRole: (user_id: string, role: string) =>
    api.patch<UserResponse>(`/identity/users/${user_id}/role`, { role }),
  deactivateUser: (user_id: string) =>
    api.post<UserResponse>(`/identity/users/${user_id}/deactivate`),
};

// ── KYC ───────────────────────────────────────────────────────────────────────

export const kycApi = {
  /** Upload 3 documents for Gemini OCR. Returns extracted + editable fields. */
  runOcr: async (idFront: File, idBack: File, utilityBill: File): Promise<OcrResponse> => {
    const formData = new FormData();
    formData.append("id_front", idFront);
    formData.append("id_back", idBack);
    formData.append("utility_bill", utilityBill);
    const token = tokenStore.get();
    const res = await fetch(`${BASE}/kyc/ocr`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data?.detail || `OCR failed: HTTP ${res.status}`);
    return data as OcrResponse;
  },

  submitKyc: async (idFront: File, idBack: File | null, utilityBill: File, faceImage: File): Promise<KYCResponse> => {
    const formData = new FormData();
    formData.append("id_front", idFront);
    if (idBack) formData.append("id_back", idBack);
    formData.append("utility_bill", utilityBill);
    formData.append("face_image", faceImage);
    const token = tokenStore.get();
    const res = await fetch(`${BASE}/kyc/submit`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data?.detail || `KYC submission failed: HTTP ${res.status}`);
    return data as KYCResponse;
  },

  getStatus: () => api.get<KYCResponse>(`/kyc/status`),

  listQueue: (status = "pending", skip = 0, limit = 50) =>
    api.get<KYCResponse[]>(`/kyc/queue?status=${status}&skip=${skip}&limit=${limit}`),

  approve: (kyc_id: string, tier: string, notes?: string) => 
    api.post<KYCResponse>(`/kyc/approve/${kyc_id}`, { tier, notes }),
  reject: (kyc_id: string, reason: string) =>
    api.post<KYCResponse>(`/kyc/reject/${kyc_id}`, { reason }),
};

// ── Consent ───────────────────────────────────────────────────────────────────

export const consentApi = {
  grant: (user_id: string, client_id: string, scopes: string[]) =>
    api.post<ConsentResponse>("/consent/grant", { user_id, client_id, scopes }),
  revoke: (user_id: string, client_id: string) =>
    api.post<void>("/consent/revoke", { user_id, client_id }),
  listForUser: (user_id: string) =>
    api.get<ConsentResponse[]>(`/consent/user/${user_id}`),
};

// ── Apps ──────────────────────────────────────────────────────────────────────

export const appsApi = {
  register: (body: { name: string; allowed_scopes: string[]; redirect_uris: string[]; description?: string }) =>
    api.post<AppResponse>("/apps/", body),
  list: (skip = 0, limit = 50) => api.get<AppResponse[]>(`/apps/?skip=${skip}&limit=${limit}`),
  get: (app_id: string) => api.get<AppResponse>(`/apps/${app_id}`),
  update: (app_id: string, body: { name?: string; description?: string; allowed_scopes?: string[]; redirect_uris?: string[] }) =>
    api.patch<AppResponse>(`/apps/${app_id}`, body),
  approve: (app_id: string) => api.post<AppResponse>(`/apps/${app_id}/approve`),
  deactivate: (app_id: string) => api.post<AppResponse>(`/apps/${app_id}/deactivate`),
  rotateApiKey: (app_id: string) => api.post<AppResponse>(`/apps/${app_id}/rotate-api-key`),
  rotateSecret: (app_id: string) => api.post<AppResponse>(`/apps/${app_id}/rotate-secret`),
  marketplace: () => api.get<AppResponse[]>("/apps/marketplace"),
  mine: () => api.get<AppResponse[]>("/apps/mine"),
};

// ── Webhooks ──────────────────────────────────────────────────────────────────

export const webhooksApi = {
  subscribe: (client_id: string, event_type: string, target_url: string) =>
    api.post<WebhookSubscriptionResponse>("/webhooks/subscribe", { client_id, event_type, target_url }),
  deactivate: (sub_id: string) => api.delete<void>(`/webhooks/subscriptions/${sub_id}`),
  listSubscriptions: (skip = 0, limit = 50) =>
    api.get<WebhookSubscriptionResponse[]>(`/webhooks/subscriptions?skip=${skip}&limit=${limit}`),
  listDeliveries: () => api.get<WebhookDeliveryResponse[]>("/webhooks/deliveries"),
  getDelivery: (id: string) => api.get<WebhookDeliveryResponse>(`/webhooks/deliveries/${id}`),
  retry: (delivery_id: string) => api.post<WebhookDeliveryResponse>(`/webhooks/retry/${delivery_id}`),
  deliveriesForSub: (sub_id: string, skip = 0, limit = 50) =>
    api.get<WebhookDeliveryResponse[]>(`/webhooks/subscriptions/${sub_id}/deliveries?skip=${skip}&limit=${limit}`),
};

// ── Sessions ──────────────────────────────────────────────────────────────────

export const sessionApi = {
  listActive: (skip = 0, limit = 20) =>
    api.get<ActiveSessionResponse[]>(`/session/me/active?skip=${skip}&limit=${limit}`),
  revoke: (token_id: string) => api.delete<void>(`/session/${token_id}`),
  revokeAll: () => api.post<void>("/session/revoke-all"),
};

// ── Trust ─────────────────────────────────────────────────────────────────────

export const trustApi = {
  getProfile: () => api.get<TrustProfile>("/trust/profile"),
  getUserProfile: (userId: string) => api.get<TrustProfile>(`/trust/profile/${userId}`),
  evaluate: () => api.post<TrustProfile>("/trust/evaluate"),
};
