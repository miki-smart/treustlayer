// ============================================================
// MOCK DATA — replace with real API calls when backend is ready
// ============================================================

export type UserRole = "admin" | "user" | "kyc_approver" | "app_owner";

export interface AppUser {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar?: string;
}

export const mockUsers: AppUser[] = [
  { id: "u1", name: "Admin User", email: "admin@fininfra.io", role: "admin" },
  { id: "u2", name: "Abebe Kebede", email: "abebe@example.com", role: "user" },
];

// ---- Module A — Biometric Verification ----
export interface BiometricRecord {
  id: string;
  userId: string;
  userName: string;
  type: "face" | "voice";
  status: "pending" | "verified" | "failed" | "flagged";
  livenessScore: number;
  spoofProbability: number;
  timestamp: string;
  riskLevel: "low" | "medium" | "high";
}

export const mockBiometricRecords: BiometricRecord[] = [
  { id: "b1", userId: "u2", userName: "Abebe Kebede", type: "face", status: "verified", livenessScore: 0.97, spoofProbability: 0.02, timestamp: "2026-03-25T10:30:00Z", riskLevel: "low" },
  { id: "b2", userId: "u3", userName: "Sara Ahmed", type: "face", status: "flagged", livenessScore: 0.61, spoofProbability: 0.48, timestamp: "2026-03-25T11:15:00Z", riskLevel: "high" },
  { id: "b3", userId: "u4", userName: "John Tadesse", type: "face", status: "pending", livenessScore: 0, spoofProbability: 0, timestamp: "2026-03-25T14:00:00Z", riskLevel: "medium" },
  { id: "b4", userId: "u5", userName: "Hana Girma", type: "voice", status: "verified", livenessScore: 0.92, spoofProbability: 0.05, timestamp: "2026-03-24T09:20:00Z", riskLevel: "low" },
  { id: "b5", userId: "u6", userName: "Daniel Mekonnen", type: "face", status: "failed", livenessScore: 0.35, spoofProbability: 0.78, timestamp: "2026-03-24T16:45:00Z", riskLevel: "high" },
];

export const biometricModelMetrics = {
  accuracy: 0.964,
  precision: 0.951,
  recall: 0.978,
  f1Score: 0.964,
  falseAcceptRate: 0.003,
  falseRejectRate: 0.022,
  biasMetrics: {
    genderGap: 0.012,
    ageGroupGap: 0.018,
    skinToneGap: 0.009,
  },
};

// ---- Module B — eKYC ----
export type KYCStatus = "pending" | "in_review" | "approved" | "rejected" | "flagged";

export interface KYCApplication {
  id: string;
  userId: string;
  applicantName: string;
  email: string;
  status: KYCStatus;
  riskScore: number;
  documentsSubmitted: string[];
  ocrConfidence: number;
  syntheticIdProbability: number;
  submittedAt: string;
  reviewedAt?: string;
  reviewer?: string;
  notes?: string;
}

export const mockKYCApplications: KYCApplication[] = [
  { id: "kyc1", userId: "u2", applicantName: "Abebe Kebede", email: "abebe@example.com", status: "approved", riskScore: 12, documentsSubmitted: ["National ID", "Utility Bill"], ocrConfidence: 0.96, syntheticIdProbability: 0.01, submittedAt: "2026-03-20T08:00:00Z", reviewedAt: "2026-03-21T10:00:00Z", reviewer: "Admin User" },
  { id: "kyc2", userId: "u3", applicantName: "Sara Ahmed", email: "sara@example.com", status: "flagged", riskScore: 72, documentsSubmitted: ["Passport"], ocrConfidence: 0.78, syntheticIdProbability: 0.34, submittedAt: "2026-03-22T09:30:00Z", notes: "Document quality low; possible manipulation detected" },
  { id: "kyc3", userId: "u4", applicantName: "John Tadesse", email: "john@example.com", status: "in_review", riskScore: 35, documentsSubmitted: ["National ID", "Bank Statement"], ocrConfidence: 0.91, syntheticIdProbability: 0.05, submittedAt: "2026-03-24T14:00:00Z" },
  { id: "kyc4", userId: "u5", applicantName: "Hana Girma", email: "hana@example.com", status: "pending", riskScore: 18, documentsSubmitted: ["Driver License"], ocrConfidence: 0.94, syntheticIdProbability: 0.02, submittedAt: "2026-03-25T07:00:00Z" },
  { id: "kyc5", userId: "u6", applicantName: "Daniel Mekonnen", email: "daniel@example.com", status: "rejected", riskScore: 89, documentsSubmitted: ["National ID"], ocrConfidence: 0.52, syntheticIdProbability: 0.67, submittedAt: "2026-03-19T11:00:00Z", reviewedAt: "2026-03-20T09:00:00Z", reviewer: "Admin User", notes: "Synthetic identity detected" },
];

// ---- Module C — Digital Identity ----
export type IdentityStatus = "active" | "suspended" | "revoked" | "pending";

export interface DigitalIdentity {
  id: string;
  userId: string;
  holderName: string;
  uniqueId: string;
  status: IdentityStatus;
  createdAt: string;
  lastVerified: string;
  attributes: { key: string; value: string; shared: boolean }[];
  credentials: { type: string; issuer: string; expiresAt: string; status: string }[];
}

export const mockIdentities: DigitalIdentity[] = [
  {
    id: "did1", userId: "u2", holderName: "Abebe Kebede", uniqueId: "DID:FIN:ETH:0x7a9f...3b2c", status: "active", createdAt: "2026-01-15T08:00:00Z", lastVerified: "2026-03-25T10:30:00Z",
    attributes: [
      { key: "Full Name", value: "Abebe Kebede", shared: true },
      { key: "Date of Birth", value: "1990-05-12", shared: false },
      { key: "Nationality", value: "Ethiopian", shared: true },
      { key: "Phone", value: "+251911234567", shared: false },
      { key: "Address", value: "Addis Ababa, Ethiopia", shared: true },
    ],
    credentials: [
      { type: "National ID", issuer: "Ethiopian Immigration", expiresAt: "2030-01-15", status: "active" },
      { type: "KYC Verified", issuer: "FinInfra Platform", expiresAt: "2027-03-25", status: "active" },
    ],
  },
  {
    id: "did2", userId: "u3", holderName: "Sara Ahmed", uniqueId: "DID:FIN:ETH:0x3c1d...8e4a", status: "suspended", createdAt: "2026-02-10T09:00:00Z", lastVerified: "2026-03-22T11:15:00Z",
    attributes: [
      { key: "Full Name", value: "Sara Ahmed", shared: true },
      { key: "Date of Birth", value: "1995-08-22", shared: false },
      { key: "Nationality", value: "Ethiopian", shared: true },
    ],
    credentials: [
      { type: "Passport", issuer: "Ethiopian Immigration", expiresAt: "2028-06-10", status: "active" },
    ],
  },
  {
    id: "did3", userId: "u4", holderName: "John Tadesse", uniqueId: "DID:FIN:ETH:0x9b2e...1f7d", status: "active", createdAt: "2026-03-01T10:00:00Z", lastVerified: "2026-03-24T14:00:00Z",
    attributes: [
      { key: "Full Name", value: "John Tadesse", shared: true },
      { key: "Date of Birth", value: "1988-12-03", shared: true },
      { key: "Nationality", value: "Ethiopian", shared: true },
      { key: "Email", value: "john@example.com", shared: true },
    ],
    credentials: [
      { type: "National ID", issuer: "Ethiopian Immigration", expiresAt: "2029-03-01", status: "active" },
      { type: "Bank Account Verified", issuer: "Commercial Bank of Ethiopia", expiresAt: "2027-03-01", status: "active" },
    ],
  },
];

// ---- Module D — SSO ----
export interface SSOProvider {
  id: string;
  name: string;
  protocol: "OAuth2" | "OpenID Connect" | "SAML";
  status: "active" | "inactive" | "pending";
  connectedAt: string;
  lastSync: string;
  usersCount: number;
  region: string;
}

export const mockSSOProviders: SSOProvider[] = [
  { id: "sso1", name: "Commercial Bank of Ethiopia", protocol: "OpenID Connect", status: "active", connectedAt: "2025-11-01", lastSync: "2026-03-25T09:00:00Z", usersCount: 12500, region: "East Africa" },
  { id: "sso2", name: "Dashen Bank", protocol: "OAuth2", status: "active", connectedAt: "2025-12-15", lastSync: "2026-03-25T08:30:00Z", usersCount: 8300, region: "East Africa" },
  { id: "sso3", name: "Telebirr", protocol: "OpenID Connect", status: "active", connectedAt: "2026-01-20", lastSync: "2026-03-25T10:00:00Z", usersCount: 45000, region: "East Africa" },
  { id: "sso4", name: "M-Pesa Kenya", protocol: "OAuth2", status: "pending", connectedAt: "2026-03-10", lastSync: "", usersCount: 0, region: "East Africa" },
  { id: "sso5", name: "Visa Network", protocol: "OpenID Connect", status: "inactive", connectedAt: "2026-02-01", lastSync: "2026-02-28T12:00:00Z", usersCount: 0, region: "Global" },
];

export interface SSOSession {
  id: string;
  userId: string;
  userName: string;
  provider: string;
  ipAddress: string;
  device: string;
  loginAt: string;
  expiresAt: string;
  status: "active" | "expired" | "revoked";
}

export const mockSSOSessions: SSOSession[] = [
  { id: "sess1", userId: "u2", userName: "Abebe Kebede", provider: "Commercial Bank of Ethiopia", ipAddress: "196.188.45.12", device: "Chrome / Windows", loginAt: "2026-03-25T08:00:00Z", expiresAt: "2026-03-25T20:00:00Z", status: "active" },
  { id: "sess2", userId: "u2", userName: "Abebe Kebede", provider: "Telebirr", ipAddress: "196.188.45.12", device: "Mobile App / Android", loginAt: "2026-03-25T09:30:00Z", expiresAt: "2026-03-25T21:30:00Z", status: "active" },
  { id: "sess3", userId: "u3", userName: "Sara Ahmed", provider: "Dashen Bank", ipAddress: "41.215.12.88", device: "Safari / macOS", loginAt: "2026-03-24T14:00:00Z", expiresAt: "2026-03-25T02:00:00Z", status: "expired" },
  { id: "sess4", userId: "u4", userName: "John Tadesse", provider: "Commercial Bank of Ethiopia", ipAddress: "196.189.100.5", device: "Firefox / Linux", loginAt: "2026-03-25T07:45:00Z", expiresAt: "2026-03-25T19:45:00Z", status: "active" },
];

export interface ConsentRecord {
  id: string;
  appName: string;
  provider: string;
  scopesGranted: string[];
  grantedAt: string;
  status: "active" | "revoked";
}

export const mockConsents: ConsentRecord[] = [
  { id: "c1", appName: "Loan Portal", provider: "Commercial Bank of Ethiopia", scopesGranted: ["profile", "account_balance", "transaction_history"], grantedAt: "2026-03-20T10:00:00Z", status: "active" },
  { id: "c2", appName: "Insurance App", provider: "Dashen Bank", scopesGranted: ["profile", "kyc_status"], grantedAt: "2026-03-15T08:00:00Z", status: "active" },
  { id: "c3", appName: "Credit Score Service", provider: "Telebirr", scopesGranted: ["profile", "payment_history"], grantedAt: "2026-02-28T12:00:00Z", status: "revoked" },
];

// ---- Module E — Card System ----
export type CardStatus = "active" | "frozen" | "pending" | "expired" | "revoked";
export type CardType = "virtual" | "physical" | "biometric";

export interface FinCard {
  id: string;
  userId: string;
  holderName: string;
  cardNumber: string;
  cardType: CardType;
  status: CardStatus;
  expiresAt: string;
  dailyLimit: number;
  monthlyLimit: number;
  currentSpend: number;
  linkedIdentity: string;
  tokenized: boolean;
  dynamicCVV: string;
  issuedAt: string;
  biometricBound: boolean;
}

export const mockCards: FinCard[] = [
  { id: "card1", userId: "u2", holderName: "Abebe Kebede", cardNumber: "4532 •••• •••• 7891", cardType: "virtual", status: "active", expiresAt: "2028-03", dailyLimit: 50000, monthlyLimit: 500000, currentSpend: 12500, linkedIdentity: "DID:FIN:ETH:0x7a9f...3b2c", tokenized: true, dynamicCVV: "847", issuedAt: "2026-01-15", biometricBound: true },
  { id: "card2", userId: "u3", holderName: "Sara Ahmed", cardNumber: "5421 •••• •••• 3456", cardType: "physical", status: "frozen", expiresAt: "2027-11", dailyLimit: 30000, monthlyLimit: 300000, currentSpend: 0, linkedIdentity: "DID:FIN:ETH:0x3c1d...8e4a", tokenized: true, dynamicCVV: "---", issuedAt: "2026-02-10", biometricBound: false },
  { id: "card3", userId: "u4", holderName: "John Tadesse", cardNumber: "4916 •••• •••• 5678", cardType: "biometric", status: "active", expiresAt: "2028-06", dailyLimit: 100000, monthlyLimit: 1000000, currentSpend: 67800, linkedIdentity: "DID:FIN:ETH:0x9b2e...1f7d", tokenized: true, dynamicCVV: "215", issuedAt: "2026-03-01", biometricBound: true },
];

export interface CardTransaction {
  id: string;
  cardId: string;
  type: "payment" | "withdrawal" | "transfer" | "refund";
  amount: number;
  currency: string;
  merchant: string;
  status: "completed" | "pending" | "failed" | "flagged";
  timestamp: string;
  location: string;
  offline: boolean;
}

export const mockCardTransactions: CardTransaction[] = [
  { id: "tx1", cardId: "card1", type: "payment", amount: 2500, currency: "ETB", merchant: "Sheger Supermarket", status: "completed", timestamp: "2026-03-25T10:15:00Z", location: "Addis Ababa", offline: false },
  { id: "tx2", cardId: "card1", type: "transfer", amount: 5000, currency: "ETB", merchant: "P2P Transfer", status: "completed", timestamp: "2026-03-25T09:00:00Z", location: "Addis Ababa", offline: false },
  { id: "tx3", cardId: "card1", type: "payment", amount: 1200, currency: "ETB", merchant: "Ride Service", status: "completed", timestamp: "2026-03-24T18:30:00Z", location: "Addis Ababa", offline: true },
  { id: "tx4", cardId: "card3", type: "payment", amount: 45000, currency: "ETB", merchant: "Electronics Store", status: "flagged", timestamp: "2026-03-25T11:00:00Z", location: "Hawassa", offline: false },
  { id: "tx5", cardId: "card3", type: "withdrawal", amount: 10000, currency: "ETB", merchant: "ATM CBE", status: "completed", timestamp: "2026-03-24T14:00:00Z", location: "Addis Ababa", offline: false },
  { id: "tx6", cardId: "card3", type: "payment", amount: 800, currency: "ETB", merchant: "Coffee Shop", status: "completed", timestamp: "2026-03-24T08:30:00Z", location: "Addis Ababa", offline: true },
  { id: "tx7", cardId: "card1", type: "refund", amount: 3800, currency: "ETB", merchant: "Online Store", status: "pending", timestamp: "2026-03-23T16:00:00Z", location: "Online", offline: false },
];

export interface CardRule {
  id: string;
  cardId: string;
  ruleName: string;
  condition: string;
  action: string;
  enabled: boolean;
}

export const mockCardRules: CardRule[] = [
  { id: "r1", cardId: "card1", ruleName: "High-value alert", condition: "Transaction > 10,000 ETB", action: "Require biometric confirmation", enabled: true },
  { id: "r2", cardId: "card1", ruleName: "International block", condition: "Transaction outside Ethiopia", action: "Block and notify", enabled: true },
  { id: "r3", cardId: "card1", ruleName: "Night spending limit", condition: "Transaction between 11PM–6AM", action: "Limit to 5,000 ETB", enabled: false },
  { id: "r4", cardId: "card3", ruleName: "Merchant category block", condition: "Gambling merchants", action: "Block transaction", enabled: true },
];

// ---- Dashboard Stats ----
export const dashboardStats = {
  totalUsers: 45230,
  activeIdentities: 38100,
  kycCompleted: 34500,
  cardIssued: 28900,
  transactionsToday: 12450,
  fraudBlocked: 23,
  ssoLogins: 8700,
  biometricVerifications: 15600,
};

export const monthlyData = [
  { month: "Oct", users: 32000, kyc: 28000, transactions: 180000 },
  { month: "Nov", users: 35000, kyc: 30500, transactions: 210000 },
  { month: "Dec", users: 38000, kyc: 32000, transactions: 245000 },
  { month: "Jan", users: 40000, kyc: 33000, transactions: 260000 },
  { month: "Feb", users: 42500, kyc: 33800, transactions: 290000 },
  { month: "Mar", users: 45230, kyc: 34500, transactions: 320000 },
];

// Audit log
export interface AuditEntry {
  id: string;
  action: string;
  actor: string;
  target: string;
  timestamp: string;
  details: string;
}

export const mockAuditLog: AuditEntry[] = [
  { id: "a1", action: "KYC Approved", actor: "Admin User", target: "Abebe Kebede", timestamp: "2026-03-25T10:30:00Z", details: "Application kyc1 approved after manual review" },
  { id: "a2", action: "Identity Suspended", actor: "System", target: "Sara Ahmed", timestamp: "2026-03-24T11:15:00Z", details: "Auto-suspended due to flagged biometric verification" },
  { id: "a3", action: "Card Issued", actor: "Admin User", target: "John Tadesse", timestamp: "2026-03-24T09:00:00Z", details: "Biometric card issued — card3" },
  { id: "a4", action: "Transaction Flagged", actor: "Fraud Engine", target: "John Tadesse", timestamp: "2026-03-25T11:00:00Z", details: "Unusual high-value transaction at Electronics Store" },
  { id: "a5", action: "SSO Session Revoked", actor: "Sara Ahmed", target: "Dashen Bank", timestamp: "2026-03-24T15:00:00Z", details: "User revoked session manually" },
];
