from pydantic import BaseModel


class DashboardStats(BaseModel):
    totalUsers: int
    activeIdentities: int
    kycCompleted: int
    cardIssued: int
    transactionsToday: int
    fraudBlocked: int
    ssoLogins: int
    biometricVerifications: int


class MonthlyDataPoint(BaseModel):
    month: str
    users: int
    kyc: int
    transactions: int


class AuditEntryOut(BaseModel):
    id: str
    action: str
    actor: str
    target: str
    timestamp: str
    details: str

    model_config = {"from_attributes": True}
