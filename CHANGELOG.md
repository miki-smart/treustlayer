# 📋 TrustLayer ID — Changelog

All notable changes to the merged backend project.

---

## [2.0.0] - 2026-03-27

### 🎉 Major Features Added

#### Biometric Verification Module (NEW)
- ✅ Face verification with liveness detection
- ✅ Voice verification with spoof detection
- ✅ Risk level assessment (low/medium/high)
- ✅ Biometric status tracking (pending/verified/failed/flagged)
- ✅ Admin review workflow (approve/reject/flag)
- ✅ 9 API endpoints
- ✅ Face matching with ID document photo
- ✅ Quality score assessment

**Technologies:**
- `face-recognition` (face detection + matching)
- `opencv-python` (image processing)
- `librosa` (voice processing)
- `numpy` (numerical operations)
- `pillow` (image manipulation)

**Database:**
- New schema: `biometric`
- New table: `biometric.records`

**API Endpoints:**
- `POST /api/v1/biometric/face/verify`
- `POST /api/v1/biometric/voice/verify`
- `GET /api/v1/biometric/records`
- `GET /api/v1/biometric/records/{id}`
- `DELETE /api/v1/biometric/records/{id}`
- `GET /api/v1/biometric/submissions` [Admin]
- `POST /api/v1/biometric/{id}/approve` [Admin]
- `POST /api/v1/biometric/{id}/reject` [Admin]
- `POST /api/v1/biometric/{id}/flag` [Admin]

---

#### Digital Identity Module (NEW)
- ✅ Unique digital identity per user (DID format: `did:trustlayer:<hash>`)
- ✅ Identity attributes (key-value pairs with shareability control)
- ✅ Verifiable credentials issuance
- ✅ Credential revocation
- ✅ Identity status management (active/suspended/revoked/pending)
- ✅ 12 API endpoints

**Database:**
- New schema: `digital_identity`
- New tables:
  - `digital_identity.identities`
  - `digital_identity.attributes`
  - `digital_identity.credentials`

**API Endpoints:**
- `POST /api/v1/identity/create`
- `GET /api/v1/identity/me`
- `GET /api/v1/identity/{identity_id}`
- `POST /api/v1/identity/{identity_id}/attributes`
- `GET /api/v1/identity/{identity_id}/attributes`
- `PATCH /api/v1/identity/{identity_id}/attributes/{key}`
- `DELETE /api/v1/identity/{identity_id}/attributes/{key}`
- `POST /api/v1/identity/{identity_id}/credentials` [Admin]
- `GET /api/v1/identity/{identity_id}/credentials`
- `POST /api/v1/identity/{identity_id}/credentials/{id}/revoke` [Admin]
- `POST /api/v1/identity/{identity_id}/suspend` [Admin]
- `POST /api/v1/identity/{identity_id}/activate` [Admin]

---

### 🔧 Enhanced Features

#### KYC Module (Enhanced)
**Added 20+ new fields:**
- Personal info: `full_name`, `date_of_birth`, `gender`, `nationality`, `place_of_birth`
- Document info: `document_type`, `document_number`, `issue_date`, `expiry_date`
- Address info: `address`, `billing_name`, `service_provider`, `service_type`, `bill_date`, `account_number`
- MRZ: `mrz_line1`, `mrz_line2`
- Document URLs: `id_front_url`, `id_back_url`, `utility_bill_url`, `face_image_url`
- OCR scores: `id_ocr_confidence`, `utility_ocr_confidence`, `overall_confidence`
- Risk assessment: `risk_score`, `synthetic_id_probability`, `face_similarity_score`

**Database:**
- Enhanced table: `kyc.verifications` (now 30+ fields, was 10)

---

#### Trust Scoring Module (Enhanced)
**Added 3 new factors:**
- Face biometric verified: +10 points
- Voice biometric verified: +5 points
- Digital identity active: +5 points

**Updated algorithm:**
```
trust_score = (
    (20 if email_verified else 0) +
    (15 if phone_verified else 0) +
    {0: 0, 1: 15, 2: 25, 3: 35}[kyc_tier] +
    (10 if face_verified else 0) +          # NEW
    (5 if voice_verified else 0) +          # NEW
    (5 if digital_identity_active else 0) + # NEW
    min(10, (account_age_days / 90) * 10)
)
```

**Maximum score:** 100 (was 90)

**Database:**
- Enhanced table: `trust.profiles` (added `face_verified`, `voice_verified`, `digital_identity_active` flags)

---

#### JWT Claims (Enhanced)
**Added 5 new claims:**
- `biometric_verified` (boolean)
- `face_verified` (boolean)
- `voice_verified` (boolean)
- `digital_identity_id` (string)
- `identity_status` (string)

**Example JWT:**
```json
{
  "sub": "user_id",
  "kyc_tier": "tier_3",
  "trust_score": 95,
  "biometric_verified": true,
  "face_verified": true,
  "voice_verified": true,
  "digital_identity_id": "did:trustlayer:abc123",
  "identity_status": "active"
}
```

---

### 🎨 Frontend Updates

#### Restored Pages (2)
- ✅ `BiometricPage` — Face + voice verification UI
- ✅ `IdentityPage` — Digital identity management UI

#### Updated Navigation
- ✅ Added "Biometric" navigation item (ScanFace icon)
- ✅ Added "Digital Identity" navigation item (Fingerprint icon)
- ✅ Updated navigation for all roles (admin, kyc_approver, app_owner, user)

**Total pages:** 8 (was 6)

---

### 🗄️ Database Changes

#### New Schemas (2)
- `biometric` — Face + voice verification
- `digital_identity` — DID system

**Total schemas:** 11 (was 9)

#### New Tables (4)
- `biometric.records`
- `digital_identity.identities`
- `digital_identity.attributes`
- `digital_identity.credentials`

**Total tables:** 13 (was 9)

#### Enhanced Tables (2)
- `kyc.verifications` — Added 20+ fields
- `trust.profiles` — Added 3 biometric flags

---

### 📦 Dependencies

#### Added (5)
- `opencv-python==4.9.0.80` — Image processing
- `face-recognition==1.3.0` — Face detection + matching
- `librosa==0.10.1` — Voice processing
- `numpy==1.26.4` — Numerical operations
- `pillow==10.2.0` — Image manipulation

**Total dependencies:** 24 (was 18)

---

### 📚 Documentation

#### New Documents (3)
- `UPDATED_IDAAS_ARCHITECTURE.md` — Enhanced architecture design
- `FINAL_ARCHITECTURE_SUMMARY.md` — Executive summary
- `UPDATED_IMPLEMENTATION_STATUS.md` — Current status + roadmap
- `CHANGELOG.md` — This document

#### Updated Documents (2)
- `backend-merged/README.md` — Updated with biometric + DID features
- `DECISION_MATRIX.md` — Updated comparison

---

### 🔧 Infrastructure

#### New Services (2)
- `app/infrastructure/ai/face_verification_service.py` — Face verification logic
- `app/infrastructure/ai/voice_verification_service.py` — Voice verification logic

#### Updated Migration
- `001_initial_idaas_schema.py` — Added biometric + DID tables, enhanced KYC table

---

## [1.0.0] - 2026-03-27 (Initial)

### Initial Release

#### Core Infrastructure
- ✅ Clean Architecture (4 layers)
- ✅ Schema isolation (9 schemas)
- ✅ Event-driven design
- ✅ RSA-256 JWT
- ✅ PKCE support

#### Modules
- ✅ Identity module (100% complete)
- ✅ Auth module (stub)
- ✅ KYC module (stub)
- ✅ Trust module (stub)
- ✅ Consent module (stub)
- ✅ App registry module (stub)
- ✅ Session module (stub)
- ✅ Webhook module (stub)
- ✅ Dashboard module (stub)

#### Database
- ✅ 9 schemas
- ✅ 9 tables
- ✅ Initial migration

#### Frontend
- ✅ 6 pages
- ✅ API client

---

## Summary of Changes

### Version 2.0.0 (Current)
- **Modules:** 11 (was 9) — Added biometric + digital_identity
- **Complete modules:** 3 (was 1) — Added biometric + digital_identity
- **Enhanced modules:** 2 — KYC + Trust
- **Database schemas:** 11 (was 9)
- **Database tables:** 13 (was 9)
- **API endpoints:** 44 (was 23)
- **Frontend pages:** 8 (was 6)
- **Dependencies:** 24 (was 18)
- **Overall completion:** ~45% (was ~25%)

### Key Improvements
1. ✅ Biometric verification (face + voice)
2. ✅ Digital identity (DID)
3. ✅ Enhanced KYC (30+ fields)
4. ✅ Enhanced trust scoring (9 factors, was 6)
5. ✅ Enhanced JWT claims (5 new claims)
6. ✅ Restored frontend pages (biometric + identity)

---

## Migration Guide (1.0.0 → 2.0.0)

### Database Migration
```bash
# Backup existing database
pg_dump trustlayer > backup.sql

# Run new migration
alembic upgrade head
```

### Environment Variables
No new environment variables required. Existing `.env` is compatible.

### API Changes
**Breaking changes:** None

**New endpoints:** 21 (9 biometric + 12 digital identity)

**Enhanced endpoints:** KYC endpoints now return 30+ fields (was 10)

### Frontend Changes
**Breaking changes:** None

**New pages:** 2 (BiometricPage, IdentityPage)

**New navigation items:** 2 (Biometric, Digital Identity)

---

## Roadmap

### v2.1.0 (Next)
- Implement Auth module (OIDC flows)
- Implement KYC module (OCR + approval)
- Add comprehensive tests

### v2.2.0
- Implement Consent module
- Implement App Registry module
- Implement Session module
- Implement Webhook module

### v2.3.0
- Implement Dashboard module
- Implement Audit module
- Add monitoring & observability

### v3.0.0
- Production deployment
- Load balancing
- Auto-scaling
- CI/CD pipeline

---

**Current Version:** 2.0.0  
**Status:** ✅ Architecture complete, ready for Phase 1 (OIDC implementation)
