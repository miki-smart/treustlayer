"""
Seed the database with sample data matching frontend mockData.ts.
Run: python seed.py
Safe to run multiple times — skips existing records.
"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config import settings
from app.database import Base
from app.models.user import User, UserRole
from app.models.biometric import BiometricRecord, BiometricType, BiometricStatus, RiskLevel
from app.models.kyc import KYCApplication, KYCStatus
from app.models.identity import DigitalIdentity, IdentityAttribute, IdentityCredential, IdentityStatus
from app.models.sso import SSOProvider, SSOSession, ConsentRecord, SSOProtocol, SSOProviderStatus, SSOSessionStatus, ConsentStatus
from app.models.card import FinCard, CardTransaction, CardRule, CardStatus, CardType, TransactionType, TransactionStatus
from app.models.audit import AuditEntry
from app.models.app_registry import RegisteredApp, AppStatus, AppCategory, UserApp
from app.models.trust import TrustProfile
from app.utils.security import hash_password


engine = create_async_engine(settings.DATABASE_URL, echo=False)
Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


async def seed():
    async with Session() as db:
        # --- Users ---
        users_data = [
            {"id": "00000000-0000-0000-0000-000000000001", "name": "Admin User", "email": "admin@fininfra.io", "password": "admin123", "role": UserRole.admin},
            {"id": "00000000-0000-0000-0000-000000000002", "name": "Abebe Kebede", "email": "abebe@example.com", "password": "user123", "role": UserRole.user},
            {"id": "00000000-0000-0000-0000-000000000003", "name": "Sara Ahmed", "email": "sara@example.com", "password": "user123", "role": UserRole.user},
            {"id": "00000000-0000-0000-0000-000000000004", "name": "John Tadesse", "email": "john@example.com", "password": "user123", "role": UserRole.user},
            {"id": "00000000-0000-0000-0000-000000000005", "name": "Hana Girma", "email": "hana@example.com", "password": "user123", "role": UserRole.user},
            {"id": "00000000-0000-0000-0000-000000000006", "name": "Daniel Mekonnen", "email": "daniel@example.com", "password": "user123", "role": UserRole.user},
        ]
        user_map: dict[str, uuid.UUID] = {}
        for u in users_data:
            uid = uuid.UUID(u["id"])
            user_map[u["id"]] = uid
            existing = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
            if not existing:
                db.add(User(
                    id=uid,
                    name=u["name"],
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                    role=u["role"],
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                ))
        await db.commit()
        print("✓ Users seeded")

        u1 = user_map["00000000-0000-0000-0000-000000000001"]
        u2 = user_map["00000000-0000-0000-0000-000000000002"]
        u3 = user_map["00000000-0000-0000-0000-000000000003"]
        u4 = user_map["00000000-0000-0000-0000-000000000004"]
        u5 = user_map["00000000-0000-0000-0000-000000000005"]
        u6 = user_map["00000000-0000-0000-0000-000000000006"]

        # --- Biometric Records ---
        bio_data = [
            {"id": "b1000000-0000-0000-0000-000000000001", "user_id": u2, "type": BiometricType.face, "status": BiometricStatus.verified, "liveness": 0.97, "spoof": 0.02, "risk": RiskLevel.low, "ts": "2026-03-25T10:30:00Z"},
            {"id": "b2000000-0000-0000-0000-000000000002", "user_id": u3, "type": BiometricType.face, "status": BiometricStatus.flagged, "liveness": 0.61, "spoof": 0.48, "risk": RiskLevel.high, "ts": "2026-03-25T11:15:00Z"},
            {"id": "b3000000-0000-0000-0000-000000000003", "user_id": u4, "type": BiometricType.face, "status": BiometricStatus.pending, "liveness": 0.0, "spoof": 0.0, "risk": RiskLevel.medium, "ts": "2026-03-25T14:00:00Z"},
            {"id": "b4000000-0000-0000-0000-000000000004", "user_id": u5, "type": BiometricType.voice, "status": BiometricStatus.verified, "liveness": 0.92, "spoof": 0.05, "risk": RiskLevel.low, "ts": "2026-03-24T09:20:00Z"},
            {"id": "b5000000-0000-0000-0000-000000000005", "user_id": u6, "type": BiometricType.face, "status": BiometricStatus.failed, "liveness": 0.35, "spoof": 0.78, "risk": RiskLevel.high, "ts": "2026-03-24T16:45:00Z"},
        ]
        for b in bio_data:
            bid = uuid.UUID(b["id"])
            if not (await db.execute(select(BiometricRecord).where(BiometricRecord.id == bid))).scalar_one_or_none():
                db.add(BiometricRecord(
                    id=bid, user_id=b["user_id"], type=b["type"], status=b["status"],
                    liveness_score=b["liveness"], spoof_probability=b["spoof"], risk_level=b["risk"],
                    created_at=dt(b["ts"]),
                ))
        await db.commit()
        print("✓ Biometric records seeded")

        # --- KYC Applications ---
        kyc_data = [
            {"id": "c1000000-0000-0000-0000-000000000001", "user_id": u2, "status": KYCStatus.approved, "risk": 12, "docs": ["National ID", "Utility Bill"], "ocr": 0.96, "synth": 0.01, "submitted": "2026-03-20T08:00:00Z", "reviewed": "2026-03-21T10:00:00Z", "reviewer": u1, "notes": None},
            {"id": "c2000000-0000-0000-0000-000000000002", "user_id": u3, "status": KYCStatus.flagged, "risk": 72, "docs": ["Passport"], "ocr": 0.78, "synth": 0.34, "submitted": "2026-03-22T09:30:00Z", "reviewed": None, "reviewer": None, "notes": "Document quality low; possible manipulation detected"},
            {"id": "c3000000-0000-0000-0000-000000000003", "user_id": u4, "status": KYCStatus.in_review, "risk": 35, "docs": ["National ID", "Bank Statement"], "ocr": 0.91, "synth": 0.05, "submitted": "2026-03-24T14:00:00Z", "reviewed": None, "reviewer": None, "notes": None},
            {"id": "c4000000-0000-0000-0000-000000000004", "user_id": u5, "status": KYCStatus.pending, "risk": 18, "docs": ["Driver License"], "ocr": 0.94, "synth": 0.02, "submitted": "2026-03-25T07:00:00Z", "reviewed": None, "reviewer": None, "notes": None},
            {"id": "c5000000-0000-0000-0000-000000000005", "user_id": u6, "status": KYCStatus.rejected, "risk": 89, "docs": ["National ID"], "ocr": 0.52, "synth": 0.67, "submitted": "2026-03-19T11:00:00Z", "reviewed": "2026-03-20T09:00:00Z", "reviewer": u1, "notes": "Synthetic identity detected"},
        ]
        for k in kyc_data:
            kid = uuid.UUID(k["id"])
            if not (await db.execute(select(KYCApplication).where(KYCApplication.id == kid))).scalar_one_or_none():
                db.add(KYCApplication(
                    id=kid, user_id=k["user_id"], status=k["status"], risk_score=k["risk"],
                    documents_submitted=k["docs"], ocr_confidence=k["ocr"], synthetic_id_probability=k["synth"],
                    submitted_at=dt(k["submitted"]),
                    reviewed_at=dt(k["reviewed"]) if k["reviewed"] else None,
                    reviewer_id=k["reviewer"],
                    notes=k["notes"],
                ))
        await db.commit()
        print("✓ KYC applications seeded")

        # --- Digital Identities ---
        did1_id = uuid.UUID("d1000000-0000-0000-0000-000000000001")
        did2_id = uuid.UUID("d2000000-0000-0000-0000-000000000002")
        did3_id = uuid.UUID("d3000000-0000-0000-0000-000000000003")

        identities_data = [
            {
                "id": did1_id, "user_id": u2, "unique_id": "DID:FIN:ETH:0x7a9f...3b2c",
                "status": IdentityStatus.active, "created": "2026-01-15T08:00:00Z", "verified": "2026-03-25T10:30:00Z",
                "attrs": [
                    ("Full Name", "Abebe Kebede", True), ("Date of Birth", "1990-05-12", False),
                    ("Nationality", "Ethiopian", True), ("Phone", "+251911234567", False), ("Address", "Addis Ababa, Ethiopia", True),
                ],
                "creds": [
                    ("National ID", "Ethiopian Immigration", "2030-01-15", "active"),
                    ("KYC Verified", "FinInfra Platform", "2027-03-25", "active"),
                ],
            },
            {
                "id": did2_id, "user_id": u3, "unique_id": "DID:FIN:ETH:0x3c1d...8e4a",
                "status": IdentityStatus.suspended, "created": "2026-02-10T09:00:00Z", "verified": "2026-03-22T11:15:00Z",
                "attrs": [
                    ("Full Name", "Sara Ahmed", True), ("Date of Birth", "1995-08-22", False), ("Nationality", "Ethiopian", True),
                ],
                "creds": [("Passport", "Ethiopian Immigration", "2028-06-10", "active")],
            },
            {
                "id": did3_id, "user_id": u4, "unique_id": "DID:FIN:ETH:0x9b2e...1f7d",
                "status": IdentityStatus.active, "created": "2026-03-01T10:00:00Z", "verified": "2026-03-24T14:00:00Z",
                "attrs": [
                    ("Full Name", "John Tadesse", True), ("Date of Birth", "1988-12-03", True),
                    ("Nationality", "Ethiopian", True), ("Email", "john@example.com", True),
                ],
                "creds": [
                    ("National ID", "Ethiopian Immigration", "2029-03-01", "active"),
                    ("Bank Account Verified", "Commercial Bank of Ethiopia", "2027-03-01", "active"),
                ],
            },
        ]
        for identity_d in identities_data:
            if not (await db.execute(select(DigitalIdentity).where(DigitalIdentity.id == identity_d["id"]))).scalar_one_or_none():
                di = DigitalIdentity(
                    id=identity_d["id"], user_id=identity_d["user_id"], unique_id=identity_d["unique_id"],
                    status=identity_d["status"], created_at=dt(identity_d["created"]), last_verified=dt(identity_d["verified"]),
                )
                db.add(di)
                await db.flush()
                for key, val, shared in identity_d["attrs"]:
                    db.add(IdentityAttribute(id=uuid.uuid4(), identity_id=di.id, key=key, value=val, shared=shared))
                for typ, issuer, exp, stat in identity_d["creds"]:
                    db.add(IdentityCredential(id=uuid.uuid4(), identity_id=di.id, type=typ, issuer=issuer, expires_at=exp, status=stat))
        await db.commit()
        print("✓ Digital identities seeded")

        # --- SSO Providers ---
        sso_providers_data = [
            {"id": "e1000000-0000-0000-0000-000000000001", "name": "Commercial Bank of Ethiopia", "protocol": SSOProtocol.openid_connect, "status": SSOProviderStatus.active, "connected": "2025-11-01", "sync": "2026-03-25T09:00:00Z", "users": 12500, "region": "East Africa"},
            {"id": "e2000000-0000-0000-0000-000000000002", "name": "Dashen Bank", "protocol": SSOProtocol.oauth2, "status": SSOProviderStatus.active, "connected": "2025-12-15", "sync": "2026-03-25T08:30:00Z", "users": 8300, "region": "East Africa"},
            {"id": "e3000000-0000-0000-0000-000000000003", "name": "Telebirr", "protocol": SSOProtocol.openid_connect, "status": SSOProviderStatus.active, "connected": "2026-01-20", "sync": "2026-03-25T10:00:00Z", "users": 45000, "region": "East Africa"},
            {"id": "e4000000-0000-0000-0000-000000000004", "name": "M-Pesa Kenya", "protocol": SSOProtocol.oauth2, "status": SSOProviderStatus.pending, "connected": "2026-03-10", "sync": None, "users": 0, "region": "East Africa"},
            {"id": "e5000000-0000-0000-0000-000000000005", "name": "Visa Network", "protocol": SSOProtocol.openid_connect, "status": SSOProviderStatus.inactive, "connected": "2026-02-01", "sync": "2026-02-28T12:00:00Z", "users": 0, "region": "Global"},
        ]
        sso_provider_map: dict[str, uuid.UUID] = {}
        for p in sso_providers_data:
            pid = uuid.UUID(p["id"])
            sso_provider_map[p["id"]] = pid
            if not (await db.execute(select(SSOProvider).where(SSOProvider.id == pid))).scalar_one_or_none():
                db.add(SSOProvider(
                    id=pid, name=p["name"], protocol=p["protocol"], status=p["status"],
                    connected_at=p["connected"], last_sync=p["sync"], users_count=p["users"], region=p["region"],
                ))
        await db.commit()
        print("✓ SSO providers seeded")

        p1 = sso_provider_map["e1000000-0000-0000-0000-000000000001"]
        p2 = sso_provider_map["e2000000-0000-0000-0000-000000000002"]
        p3 = sso_provider_map["e3000000-0000-0000-0000-000000000003"]

        # --- SSO Sessions ---
        sessions_data = [
            {"id": "f1000000-0000-0000-0000-000000000001", "user_id": u2, "provider_id": p1, "ip": "196.188.45.12", "device": "Chrome / Windows", "login": "2026-03-25T08:00:00Z", "expires": "2026-03-25T20:00:00Z", "status": SSOSessionStatus.active},
            {"id": "f2000000-0000-0000-0000-000000000002", "user_id": u2, "provider_id": p3, "ip": "196.188.45.12", "device": "Mobile App / Android", "login": "2026-03-25T09:30:00Z", "expires": "2026-03-25T21:30:00Z", "status": SSOSessionStatus.active},
            {"id": "f3000000-0000-0000-0000-000000000003", "user_id": u3, "provider_id": p2, "ip": "41.215.12.88", "device": "Safari / macOS", "login": "2026-03-24T14:00:00Z", "expires": "2026-03-25T02:00:00Z", "status": SSOSessionStatus.expired},
            {"id": "f4000000-0000-0000-0000-000000000004", "user_id": u4, "provider_id": p1, "ip": "196.189.100.5", "device": "Firefox / Linux", "login": "2026-03-25T07:45:00Z", "expires": "2026-03-25T19:45:00Z", "status": SSOSessionStatus.active},
        ]
        for s in sessions_data:
            sid = uuid.UUID(s["id"])
            if not (await db.execute(select(SSOSession).where(SSOSession.id == sid))).scalar_one_or_none():
                db.add(SSOSession(
                    id=sid, user_id=s["user_id"], provider_id=s["provider_id"],
                    ip_address=s["ip"], device=s["device"],
                    login_at=dt(s["login"]), expires_at=dt(s["expires"]), status=s["status"],
                ))
        await db.commit()
        print("✓ SSO sessions seeded")

        # --- Consents ---
        consents_data = [
            {"id": "c1000000-0000-0000-0000-000000000001", "user_id": u2, "app": "Loan Portal", "provider_id": p1, "scopes": ["profile", "account_balance", "transaction_history"], "granted": "2026-03-20T10:00:00Z", "status": ConsentStatus.active},
            {"id": "c2000000-0000-0000-0000-000000000002", "user_id": u2, "app": "Insurance App", "provider_id": p2, "scopes": ["profile", "kyc_status"], "granted": "2026-03-15T08:00:00Z", "status": ConsentStatus.active},
            {"id": "c3000000-0000-0000-0000-000000000003", "user_id": u2, "app": "Credit Score Service", "provider_id": p3, "scopes": ["profile", "payment_history"], "granted": "2026-02-28T12:00:00Z", "status": ConsentStatus.revoked},
        ]
        for c in consents_data:
            cid = uuid.UUID(c["id"])
            if not (await db.execute(select(ConsentRecord).where(ConsentRecord.id == cid))).scalar_one_or_none():
                db.add(ConsentRecord(
                    id=cid, user_id=c["user_id"], app_name=c["app"], provider_id=c["provider_id"],
                    scopes_granted=c["scopes"], granted_at=dt(c["granted"]), status=c["status"],
                ))
        await db.commit()
        print("✓ Consents seeded")

        # --- Cards ---
        card1_id = uuid.UUID("a1000000-0000-0000-0000-000000000001")
        card2_id = uuid.UUID("a2000000-0000-0000-0000-000000000002")
        card3_id = uuid.UUID("a3000000-0000-0000-0000-000000000003")

        cards_data = [
            {"id": card1_id, "user_id": u2, "holder": "Abebe Kebede", "number": "4532 •••• •••• 7891", "type": CardType.virtual, "status": CardStatus.active, "expires": "2028-03", "daily": 50000, "monthly": 500000, "spend": 12500, "identity_id": did1_id, "tokenized": True, "cvv": "847", "issued": "2026-01-15", "bio": True},
            {"id": card2_id, "user_id": u3, "holder": "Sara Ahmed", "number": "5421 •••• •••• 3456", "type": CardType.physical, "status": CardStatus.frozen, "expires": "2027-11", "daily": 30000, "monthly": 300000, "spend": 0, "identity_id": did2_id, "tokenized": True, "cvv": "---", "issued": "2026-02-10", "bio": False},
            {"id": card3_id, "user_id": u4, "holder": "John Tadesse", "number": "4916 •••• •••• 5678", "type": CardType.biometric, "status": CardStatus.active, "expires": "2028-06", "daily": 100000, "monthly": 1000000, "spend": 67800, "identity_id": did3_id, "tokenized": True, "cvv": "215", "issued": "2026-03-01", "bio": True},
        ]
        for card_d in cards_data:
            if not (await db.execute(select(FinCard).where(FinCard.id == card_d["id"]))).scalar_one_or_none():
                db.add(FinCard(
                    id=card_d["id"], user_id=card_d["user_id"], holder_name=card_d["holder"],
                    card_number_masked=card_d["number"], card_type=card_d["type"], status=card_d["status"],
                    expires_at=card_d["expires"], daily_limit=card_d["daily"], monthly_limit=card_d["monthly"],
                    current_spend=card_d["spend"], linked_identity_id=card_d["identity_id"],
                    tokenized=card_d["tokenized"], dynamic_cvv=card_d["cvv"],
                    issued_at=card_d["issued"], biometric_bound=card_d["bio"],
                ))
        await db.commit()
        print("✓ Cards seeded")

        # --- Card Transactions ---
        txns_data = [
            {"id": "71000000-0000-0000-0000-000000000001", "card_id": card1_id, "type": TransactionType.payment, "amount": 2500, "currency": "ETB", "merchant": "Sheger Supermarket", "status": TransactionStatus.completed, "ts": "2026-03-25T10:15:00Z", "loc": "Addis Ababa", "offline": False},
            {"id": "72000000-0000-0000-0000-000000000002", "card_id": card1_id, "type": TransactionType.transfer, "amount": 5000, "currency": "ETB", "merchant": "P2P Transfer", "status": TransactionStatus.completed, "ts": "2026-03-25T09:00:00Z", "loc": "Addis Ababa", "offline": False},
            {"id": "73000000-0000-0000-0000-000000000003", "card_id": card1_id, "type": TransactionType.payment, "amount": 1200, "currency": "ETB", "merchant": "Ride Service", "status": TransactionStatus.completed, "ts": "2026-03-24T18:30:00Z", "loc": "Addis Ababa", "offline": True},
            {"id": "74000000-0000-0000-0000-000000000004", "card_id": card3_id, "type": TransactionType.payment, "amount": 45000, "currency": "ETB", "merchant": "Electronics Store", "status": TransactionStatus.flagged, "ts": "2026-03-25T11:00:00Z", "loc": "Hawassa", "offline": False},
            {"id": "75000000-0000-0000-0000-000000000005", "card_id": card3_id, "type": TransactionType.withdrawal, "amount": 10000, "currency": "ETB", "merchant": "ATM CBE", "status": TransactionStatus.completed, "ts": "2026-03-24T14:00:00Z", "loc": "Addis Ababa", "offline": False},
            {"id": "76000000-0000-0000-0000-000000000006", "card_id": card3_id, "type": TransactionType.payment, "amount": 800, "currency": "ETB", "merchant": "Coffee Shop", "status": TransactionStatus.completed, "ts": "2026-03-24T08:30:00Z", "loc": "Addis Ababa", "offline": True},
            {"id": "77000000-0000-0000-0000-000000000007", "card_id": card1_id, "type": TransactionType.refund, "amount": 3800, "currency": "ETB", "merchant": "Online Store", "status": TransactionStatus.pending, "ts": "2026-03-23T16:00:00Z", "loc": "Online", "offline": False},
        ]
        for t in txns_data:
            tid = uuid.UUID(t["id"])
            if not (await db.execute(select(CardTransaction).where(CardTransaction.id == tid))).scalar_one_or_none():
                db.add(CardTransaction(
                    id=tid, card_id=t["card_id"], type=t["type"], amount=t["amount"],
                    currency=t["currency"], merchant=t["merchant"], status=t["status"],
                    timestamp=dt(t["ts"]), location=t["loc"], offline=t["offline"],
                ))
        await db.commit()
        print("✓ Card transactions seeded")

        # --- Card Rules ---
        rules_data = [
            {"id": "91000000-0000-0000-0000-000000000001", "card_id": card1_id, "name": "High-value alert", "cond": "Transaction > 10,000 ETB", "action": "Require biometric confirmation", "enabled": True},
            {"id": "92000000-0000-0000-0000-000000000002", "card_id": card1_id, "name": "International block", "cond": "Transaction outside Ethiopia", "action": "Block and notify", "enabled": True},
            {"id": "93000000-0000-0000-0000-000000000003", "card_id": card1_id, "name": "Night spending limit", "cond": "Transaction between 11PM–6AM", "action": "Limit to 5,000 ETB", "enabled": False},
            {"id": "94000000-0000-0000-0000-000000000004", "card_id": card3_id, "name": "Merchant category block", "cond": "Gambling merchants", "action": "Block transaction", "enabled": True},
        ]
        for r in rules_data:
            rid = uuid.UUID(r["id"])
            if not (await db.execute(select(CardRule).where(CardRule.id == rid))).scalar_one_or_none():
                db.add(CardRule(id=rid, card_id=r["card_id"], rule_name=r["name"], condition=r["cond"], action=r["action"], enabled=r["enabled"]))
        await db.commit()
        print("✓ Card rules seeded")

        # --- Audit Log ---
        audit_data = [
            {"id": "a0100000-0000-0000-0000-000000000001", "action": "KYC Approved", "actor_id": u1, "actor": "Admin User", "target": "Abebe Kebede", "ts": "2026-03-25T10:30:00Z", "details": "Application kyc1 approved after manual review"},
            {"id": "a0200000-0000-0000-0000-000000000002", "action": "Identity Suspended", "actor_id": None, "actor": "System", "target": "Sara Ahmed", "ts": "2026-03-24T11:15:00Z", "details": "Auto-suspended due to flagged biometric verification"},
            {"id": "a0300000-0000-0000-0000-000000000003", "action": "Card Issued", "actor_id": u1, "actor": "Admin User", "target": "John Tadesse", "ts": "2026-03-24T09:00:00Z", "details": "Biometric card issued — card3"},
            {"id": "a0400000-0000-0000-0000-000000000004", "action": "Transaction Flagged", "actor_id": None, "actor": "Fraud Engine", "target": "John Tadesse", "ts": "2026-03-25T11:00:00Z", "details": "Unusual high-value transaction at Electronics Store"},
            {"id": "a0500000-0000-0000-0000-000000000005", "action": "SSO Session Revoked", "actor_id": u3, "actor": "Sara Ahmed", "target": "Dashen Bank", "ts": "2026-03-24T15:00:00Z", "details": "User revoked session manually"},
        ]
        for a in audit_data:
            aid = uuid.UUID(a["id"])
            if not (await db.execute(select(AuditEntry).where(AuditEntry.id == aid))).scalar_one_or_none():
                db.add(AuditEntry(
                    id=aid, action=a["action"], actor_id=a["actor_id"], actor_name=a["actor"],
                    target=a["target"], timestamp=dt(a["ts"]), details=a["details"],
                ))
        await db.commit()
        print("✓ Audit log seeded")

        # --- Registered Apps (Marketplace) ---
        u1 = user_map["00000000-0000-0000-0000-000000000001"]
        apps_data = [
            {
                "id": "a0000000-0000-0000-0000-000000000001",
                "client_id": "app_dashen_bank",
                "name": "Dashen Bank",
                "description": "Full-service digital banking with mobile payments and savings accounts.",
                "logo_url": "https://ui-avatars.com/api/?name=Dashen+Bank&background=1a56db&color=fff",
                "website_url": "https://dashenbank.com",
                "category": AppCategory.banking,
                "status": AppStatus.approved,
                "scopes": ["openid", "profile", "email", "kyc_status", "trust_score"],
                "redirect_uris": ["https://dashenbank.com/callback", "http://localhost:3001/callback"],
            },
            {
                "id": "a0000000-0000-0000-0000-000000000002",
                "client_id": "app_ethio_pay",
                "name": "EthioPay Wallet",
                "description": "Fast, secure digital wallet for ETB transactions and merchant payments.",
                "logo_url": "https://ui-avatars.com/api/?name=EthioPay&background=0694a2&color=fff",
                "website_url": "https://ethiopay.et",
                "category": AppCategory.payments,
                "status": AppStatus.approved,
                "scopes": ["openid", "profile", "email", "phone", "kyc_status"],
                "redirect_uris": ["https://ethiopay.et/callback"],
            },
            {
                "id": "a0000000-0000-0000-0000-000000000003",
                "client_id": "app_amhara_loan",
                "name": "Amhara MicroLoan",
                "description": "AI-driven micro-credit platform with instant approval for KYC-verified users.",
                "logo_url": "https://ui-avatars.com/api/?name=Amhara+MicroLoan&background=7e3af2&color=fff",
                "website_url": "https://amharaloan.et",
                "category": AppCategory.lending,
                "status": AppStatus.approved,
                "scopes": ["openid", "profile", "email", "kyc_status", "trust_score", "address"],
                "redirect_uris": ["https://amharaloan.et/callback"],
            },
            {
                "id": "a0000000-0000-0000-0000-000000000004",
                "client_id": "app_nib_insurance",
                "name": "NIB Insurance",
                "description": "Comprehensive life and health insurance with identity-verified claims.",
                "logo_url": "https://ui-avatars.com/api/?name=NIB+Insurance&background=e02424&color=fff",
                "website_url": "https://nibinsurance.et",
                "category": AppCategory.insurance,
                "status": AppStatus.approved,
                "scopes": ["openid", "profile", "email", "kyc_status"],
                "redirect_uris": ["https://nibinsurance.et/callback"],
            },
            {
                "id": "a0000000-0000-0000-0000-000000000005",
                "client_id": "app_ethio_invest",
                "name": "EthioInvest",
                "description": "Stock and bond investment platform — trade on the Ethiopian Securities Exchange.",
                "logo_url": "https://ui-avatars.com/api/?name=EthioInvest&background=057a55&color=fff",
                "website_url": "https://ethioinvest.et",
                "category": AppCategory.investment,
                "status": AppStatus.approved,
                "scopes": ["openid", "profile", "email", "kyc_status", "trust_score"],
                "redirect_uris": ["https://ethioinvest.et/callback"],
            },
            {
                "id": "a0000000-0000-0000-0000-000000000006",
                "client_id": "app_new_fintech",
                "name": "NextGen FinTech",
                "description": "Cutting-edge financial services startup — awaiting admin review.",
                "logo_url": "https://ui-avatars.com/api/?name=NextGen&background=ff5a1f&color=fff",
                "website_url": "https://nextgenfintech.et",
                "category": AppCategory.wallet,
                "status": AppStatus.pending,
                "scopes": ["openid", "profile", "email"],
                "redirect_uris": ["https://nextgenfintech.et/callback"],
            },
        ]
        for a in apps_data:
            aid = uuid.UUID(a["id"])
            if not (await db.execute(select(RegisteredApp).where(RegisteredApp.id == aid))).scalar_one_or_none():
                db.add(RegisteredApp(
                    id=aid,
                    client_id=a["client_id"],
                    client_secret_hash=hash_password("demo-secret-" + a["client_id"]),
                    name=a["name"],
                    description=a["description"],
                    logo_url=a["logo_url"],
                    website_url=a["website_url"],
                    category=a["category"],
                    status=a["status"],
                    owner_id=u1,
                    allowed_scopes=a["scopes"],
                    redirect_uris=a["redirect_uris"],
                    is_public=True,
                    created_at=datetime.now(timezone.utc),
                    approved_at=datetime.now(timezone.utc) if a["status"] == AppStatus.approved else None,
                    approved_by_id=u1 if a["status"] == AppStatus.approved else None,
                ))
        await db.commit()
        print("✓ Marketplace apps seeded")

        # --- Trust Profiles ---
        trust_data = [
            # (user_id_key, score, tier)
            ("00000000-0000-0000-0000-000000000001", 95.0, 3),
            ("00000000-0000-0000-0000-000000000002", 70.0, 2),
            ("00000000-0000-0000-0000-000000000003", 45.0, 1),
            ("00000000-0000-0000-0000-000000000004", 30.0, 1),
            ("00000000-0000-0000-0000-000000000005", 60.0, 2),
            ("00000000-0000-0000-0000-000000000006", 10.0, 0),
        ]
        for uid_key, score, tier in trust_data:
            uid = user_map[uid_key]
            if not (await db.execute(select(TrustProfile).where(TrustProfile.user_id == uid))).scalar_one_or_none():
                db.add(TrustProfile(
                    id=uuid.uuid4(),
                    user_id=uid,
                    trust_score=score,
                    kyc_tier=tier,
                    factors={"email_verified": score > 20, "phone_verified": score > 35, "kyc_status": "approved" if tier >= 2 else "pending", "active_identity": tier >= 2},
                    last_evaluated=datetime.now(timezone.utc),
                ))
        await db.commit()
        print("✓ Trust profiles seeded")

        print("\n✅ Database seeded successfully!")
        print("   Admin: admin@fininfra.io / admin123")
        print("   User:  abebe@example.com / user123")


if __name__ == "__main__":
    asyncio.run(seed())
