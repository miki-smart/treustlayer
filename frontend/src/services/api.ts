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
  avatar?: string | null;
  is_active: boolean;
  is_email_verified: boolean;
  phone_verified?: boolean;
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

/** Backend KYCResponse (queue + status); optional fields differ by endpoint */
export interface KYCResponse {
  id: string;
  user_id: string;
  status: string;
  tier: string;
  full_name?: string | null;
  date_of_birth?: string | null;
  document_type?: string | null;
  document_number?: string | null;
  address?: string | null;
  id_front_url?: string | null;
  id_back_url?: string | null;
  utility_bill_url?: string | null;
  face_image_url?: string | null;
  overall_confidence?: number;
  risk_score?: number;
  rejection_reason?: string | null;
  reviewer_id?: string | null;
  submitted_at?: string | null;
  reviewed_at?: string | null;
  user_name?: string | null;
  user_email?: string | null;
  trust_score?: number;
  face_similarity_score?: number | null;
  ocr_confidence?: number | null;
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
  /** Raw OCR key-value blobs for side-by-side forms */
  id_front: Record<string, unknown>;
  id_back: Record<string, unknown>;
  warnings: string[];
  model_used: string;
}

export interface KycSubmitOverrides {
  id_front?: Record<string, unknown>;
  id_back?: Record<string, unknown>;
  utility?: Record<string, unknown>;
  document_type?: string;
}

export interface KycApproverUserDetail {
  user: UserResponse;
  kyc: KYCResponse | null;
  trust: TrustProfile;
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
  logo_url?: string | null;
  category?: string;
  is_active: boolean;
  is_approved: boolean;
  is_public?: boolean;
  created_at?: string;
  updated_at?: string;
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
  device_info?: string | null;
  ip_address?: string | null;
  expires_at: string;
  created_at: string;
  last_used_at?: string | null;
}

export interface WebhookSubscriptionResponse {
  id: string;
  client_id: string;
  event_type: string;
  target_url: string;
  /** Returned once on subscribe; backend field name `secret` */
  secret?: string | null;
  signing_secret?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface WebhookDeliveryResponse {
  id: string;
  subscription_id: string;
  event_type: string;
  target_url: string;
  status: string;
  attempts: number;
  last_attempt_at?: string | null;
  next_retry_at?: string | null;
  response_status?: number | null;
  error_message?: string | null;
  created_at: string;
}

/** Matches backend TrustProfileResponse */
export interface TrustProfile {
  user_id: string;
  trust_score: number;
  risk_level: string;
  email_verified: boolean;
  phone_verified: boolean;
  kyc_tier: number;
  face_verified: boolean;
  voice_verified: boolean;
  digital_identity_active: boolean;
  account_age_days: number;
  last_calculated_at: string;
}

/** Matches backend BiometricRecordResponse */
export interface BiometricRecord {
  id: string;
  user_id: string;
  type: string;
  status: string;
  liveness_score: number;
  spoof_probability: number;
  quality_score: number;
  risk_level: string;
  device_info?: Record<string, unknown> | null;
  ip_address?: string | null;
  biometric_data_url?: string | null;
  verified_at?: string | null;
  created_at: string;
}

export interface DashboardStats {
  total_users: number;
  verified_users: number;
  kyc_pending: number;
  kyc_in_review: number;
  kyc_approved: number;
  kyc_rejected: number;
  total_apps: number;
  apps_pending: number;
  active_sessions: number;
}

export interface AuditEntryResponse {
  id: string;
  actor_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  metadata: Record<string, unknown>;
  changes: Record<string, unknown>;
  timestamp: string;
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
  /** KYC approver / admin manual verification */
  verifyEmailManual: (user_id: string) =>
    api.post<UserResponse>(`/identity/users/${user_id}/verify-email`, {}),
  verifyPhoneManual: (user_id: string) =>
    api.post<UserResponse>(`/identity/users/${user_id}/verify-phone`, {}),
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

  submitKyc: async (
    idFront: File,
    idBack: File | null,
    utilityBill: File,
    faceImage: File,
    overrides?: KycSubmitOverrides,
  ): Promise<KYCResponse> => {
    const formData = new FormData();
    formData.append("id_front", idFront);
    if (idBack) formData.append("id_back", idBack);
    formData.append("utility_bill", utilityBill);
    formData.append("face_image", faceImage);
    if (overrides && Object.keys(overrides).length > 0) {
      formData.append("kyc_overrides", JSON.stringify(overrides));
    }
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

  /** Approver: user + KYC row + trust */
  getApproverUserDetail: (userId: string) =>
    api.get<KycApproverUserDetail>(`/kyc/approver/users/${userId}/detail`),

  listQueue: (status = "pending", skip = 0, limit = 50) =>
    api.get<KYCResponse[]>(`/kyc/queue?status=${status}&skip=${skip}&limit=${limit}`),

  approve: (kyc_id: string, tier: string, notes?: string) => 
    api.post<KYCResponse>(`/kyc/approve/${kyc_id}`, { tier, notes }),
  reject: (kyc_id: string, reason: string) =>
    api.post<KYCResponse>(`/kyc/reject/${kyc_id}`, { reason }),
};

// ── Consent ───────────────────────────────────────────────────────────────────

export const consentApi = {
  /** User is taken from the Bearer token; body is only client_id + scopes. */
  grant: (client_id: string, scopes: string[]) =>
    api.post<ConsentResponse>("/consent/grant", { client_id, scopes }),
  revoke: (client_id: string) => api.post<void>("/consent/revoke", { client_id }),
  /** Preferred: current user from JWT. */
  listMine: () => api.get<ConsentResponse[]>("/consent/me"),
  /** Same as listMine when `user_id` matches the authenticated user (403 otherwise). */
  listForUser: (user_id: string) => api.get<ConsentResponse[]>(`/consent/user/${user_id}`),
};

// ── Apps ──────────────────────────────────────────────────────────────────────

export const appsApi = {
  register: (body: {
    name: string;
    allowed_scopes: string[];
    redirect_uris: string[];
    description?: string;
    category?: string;
    logo_url?: string | null;
  }) => api.post<AppResponse>("/apps/", body),
  /** Admin only */
  list: (skip = 0, limit = 50) => api.get<AppResponse[]>(`/apps/?skip=${skip}&limit=${limit}`),
  approve: (app_id: string) => api.post<AppResponse>(`/apps/${app_id}/approve`),
  deactivate: (app_id: string) => api.post<AppResponse>(`/apps/${app_id}/deactivate`),
  marketplace: (skip = 0, limit = 50) =>
    api.get<AppResponse[]>(`/apps/marketplace?skip=${skip}&limit=${limit}`),
  mine: () => api.get<AppResponse[]>("/apps/mine"),
};

// ── Webhooks ──────────────────────────────────────────────────────────────────

export const webhooksApi = {
  subscribe: (client_id: string, event_type: string, target_url: string) =>
    api.post<WebhookSubscriptionResponse>("/webhooks/subscribe", { client_id, event_type, target_url }),
  deactivate: (sub_id: string) => api.delete<void>(`/webhooks/subscriptions/${sub_id}`),
  /** Required query `client_id` matches backend */
  listSubscriptions: (client_id: string) =>
    api.get<WebhookSubscriptionResponse[]>(`/webhooks/subscriptions?client_id=${encodeURIComponent(client_id)}`),
  listDeliveries: (subscription_id: string, skip = 0, limit = 50) =>
    api.get<WebhookDeliveryResponse[]>(
      `/webhooks/deliveries/${encodeURIComponent(subscription_id)}?skip=${skip}&limit=${limit}`,
    ),
  retry: (delivery_id: string) => api.post<WebhookDeliveryResponse>(`/webhooks/retry/${delivery_id}`),
};

// ── Sessions ──────────────────────────────────────────────────────────────────

export const sessionApi = {
  listActive: () => api.get<ActiveSessionResponse[]>("/session/me/active"),
  revoke: (token_id: string) => api.delete<void>(`/session/${token_id}`),
  revokeAll: () => api.post<void>("/session/revoke-all"),
};

// ── Trust ─────────────────────────────────────────────────────────────────────

export const trustApi = {
  getProfile: () => api.get<TrustProfile>("/trust/profile"),
  getUserProfile: (userId: string) => api.get<TrustProfile>(`/trust/profile/${userId}`),
  evaluate: () => api.post<TrustProfile>("/trust/evaluate"),
};

// ── Biometrics ───────────────────────────────────────────────────────────────

async function postMultipart<T>(path: string, formData: FormData): Promise<T> {
  const token = tokenStore.get();
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data?.detail || data?.message || `HTTP ${res.status}`;
    throw new Error(Array.isArray(msg) ? msg.map((e: { msg: string }) => e.msg).join("; ") : msg);
  }
  return data as T;
}

export const biometricApi = {
  verifyFace: (faceBlob: Blob, idPhotoBlob?: Blob) => {
    const formData = new FormData();
    formData.append("face_image", faceBlob, "face.jpg");
    if (idPhotoBlob) formData.append("id_photo", idPhotoBlob, "id.jpg");
    return postMultipart<BiometricRecord>("/biometric/face/verify", formData);
  },

  verifyVoice: (audioBlob: Blob, filename = "voice.wav") => {
    const formData = new FormData();
    formData.append("audio", audioBlob, filename);
    return postMultipart<BiometricRecord>("/biometric/voice/verify", formData);
  },

  listRecords: () => api.get<BiometricRecord[]>("/biometric/records"),

  deleteRecord: (recordId: string) => api.delete<void>(`/biometric/records/${recordId}`),

  /** Admin */
  listSubmissions: (skip = 0, limit = 50) =>
    api.get<BiometricRecord[]>(`/biometric/submissions?skip=${skip}&limit=${limit}`),

  approve: (recordId: string) =>
    api.post<BiometricRecord>(`/biometric/${recordId}/approve`, {}),

  reject: (recordId: string, reason: string) =>
    api.post<BiometricRecord>(`/biometric/${recordId}/reject`, { reason }),
};

// ── Dashboard (admin) ───────────────────────────────────────────────────────────

export const dashboardApi = {
  getStats: () => api.get<DashboardStats>("/dashboard/stats"),
};

// ── Audit (admin) ───────────────────────────────────────────────────────────────

export const auditApi = {
  list: (opts?: { action?: string; resource_type?: string; skip?: number; limit?: number }) => {
    const p = new URLSearchParams();
    p.set("skip", String(opts?.skip ?? 0));
    p.set("limit", String(opts?.limit ?? 100));
    if (opts?.action) p.set("action", opts.action);
    if (opts?.resource_type) p.set("resource_type", opts.resource_type);
    return api.get<AuditEntryResponse[]>(`/audit/entries?${p.toString()}`);
  },
};
