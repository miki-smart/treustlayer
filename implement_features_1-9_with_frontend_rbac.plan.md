---
name: Features 1-9 Backend+Frontend RBAC
overview: Complete implementation plan for 9 features with backend (Clean Architecture) and frontend (React + TypeScript) including role-based access control for admin, kyc_approver, app_owner, and user roles. Each feature includes both API endpoints and corresponding UI pages.
todos:
  - id: feature-1-auth-backend
    content: "[Backend] Implement Auth Module (OIDC/OAuth2) - Domain, Application, Infrastructure, Presentation"
    status: pending
  - id: feature-1-auth-frontend
    content: "[Frontend] No new pages needed - login already exists"
    status: pending
  - id: feature-2-kyc-backend
    content: "[Backend] Implement KYC Module - Document upload, Gemini OCR, admin approval"
    status: pending
  - id: feature-2-kyc-frontend
    content: "[Frontend] Add KYC Admin Queue page for kyc_approver and admin roles"
    status: pending
  - id: feature-3-trust-backend
    content: "[Backend] Implement Trust Module API endpoints"
    status: pending
  - id: feature-3-trust-frontend
    content: "[Frontend] Add Trust Score widget to Dashboard"
    status: pending
  - id: feature-4-consent-backend
    content: "[Backend] Implement Consent Module - Domain, Application, Infrastructure, Presentation"
    status: pending
  - id: feature-4-consent-frontend
    content: "[Frontend] Enhance ConsentPage with full CRUD operations"
    status: pending
  - id: feature-5-app-registry-backend
    content: "[Backend] Implement App Registry Module - OAuth2 client management"
    status: pending
  - id: feature-5-app-registry-frontend
    content: "[Frontend] Create App Registry pages for app_owner and admin"
    status: pending
  - id: feature-6-session-backend
    content: "[Backend] Implement Session Module - Refresh token management"
    status: pending
  - id: feature-6-session-frontend
    content: "[Frontend] Enhance SessionPage with device info and revocation"
    status: pending
  - id: feature-7-webhook-backend
    content: "[Backend] Implement Webhook Module - Subscriptions, delivery worker"
    status: pending
  - id: feature-7-webhook-frontend
    content: "[Frontend] Create Webhook Management page for app_owner and admin"
    status: pending
  - id: feature-8-dashboard-backend
    content: "[Backend] Implement Dashboard Module - Analytics endpoints"
    status: pending
  - id: feature-8-dashboard-frontend
    content: "[Frontend] Create Admin Analytics Dashboard"
    status: pending
  - id: feature-9-audit-backend
    content: "[Backend] Implement Audit Module - Immutable audit trail"
    status: pending
  - id: feature-9-audit-frontend
    content: "[Frontend] Create Audit Logs page for admin"
    status: pending
isProject: false
---

# Complete Implementation Plan: Features #1-#9 (Backend + Frontend with RBAC)

## Executive Summary

This plan implements 9 critical features across **backend** (FastAPI + Clean Architecture) and **frontend** (React + TypeScript) with comprehensive **role-based access control (RBAC)**.

### Roles

- **user**: Regular users (personal data access only)
- **app_owner**: Developers who register OAuth2 apps
- **kyc_approver**: Staff who approve KYC submissions
- **admin**: Full system access (all features + analytics)

### RBAC Status

✅ **Already Implemented**:

- Backend: `[backend-merged/app/api/dependencies.py](backend-merged/app/api/dependencies.py)` — `require_admin()`, `require_kyc_approver()`
- Frontend: `[frontend/src/contexts/AuthContext.tsx](frontend/src/contexts/AuthContext.tsx)` — Role extraction from JWT
- Frontend: `[frontend/src/App.tsx](frontend/src/App.tsx)` — `ProtectedRoute` with role checking
- Frontend: `[frontend/src/components/layout/AppSidebar.tsx](frontend/src/components/layout/AppSidebar.tsx)` — Role-based navigation

---

## RBAC Access Matrix


| Feature/Page                | User | App Owner | KYC Approver | Admin |
| --------------------------- | ---- | --------- | ------------ | ----- |
| **Dashboard (Personal)**    | ✓    | ✓         | ✓            | ✓     |
| **eKYC Submit**             | ✓    | ✓         | ✓            | ✓     |
| **eKYC Admin Queue**        | ✗    | ✗         | ✓            | ✓     |
| **Biometric Submit**        | ✓    | ✓         | ✓            | ✓     |
| **Biometric Admin Review**  | ✗    | ✗         | ✓            | ✓     |
| **Digital Identity**        | ✓    | ✓         | ✓            | ✓     |
| **Trust Score**             | ✓    | ✓         | ✓            | ✓     |
| **Consent Management**      | ✓    | ✓         | ✓            | ✓     |
| **Session Management**      | ✓    | ✓         | ✓            | ✓     |
| **App Registry (View)**     | ✗    | ✓         | ✗            | ✓     |
| **App Registry (Register)** | ✗    | ✓         | ✗            | ✓     |
| **App Registry (Approve)**  | ✗    | ✗         | ✗            | ✓     |
| **Webhooks**                | ✗    | ✓         | ✗            | ✓     |
| **Admin Analytics**         | ✗    | ✗         | ✗            | ✓     |
| **Audit Logs**              | ✗    | ✗         | ✗            | ✓     |
| **User Management**         | ✗    | ✗         | ✗            | ✓     |


---

## Feature #1: Auth Module (OIDC/OAuth2)

### Backend Implementation

**Priority**: CRITICAL | **Time**: 6-8 hours

#### 1.1 Domain Layer

**Create:**

- `backend-merged/app/modules/auth/domain/entities/refresh_token.py`
- `backend-merged/app/modules/auth/domain/repositories/auth_repository.py`
- `backend-merged/app/modules/auth/domain/events/auth_events.py`

```python
# refresh_token.py
@dataclass
class RefreshToken:
    user_id: str
    client_id: str
    token_hash: str
    scopes: List[str]
    expires_at: datetime
    is_revoked: bool = False
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

#### 1.2 Application Layer

**Create use cases:**

- `backend-merged/app/modules/auth/application/use_cases/authorize.py`
- `backend-merged/app/modules/auth/application/use_cases/exchange_token.py`
- `backend-merged/app/modules/auth/application/use_cases/refresh_token.py`
- `backend-merged/app/modules/auth/application/use_cases/introspect_token.py`

**Key Logic: AuthorizeUseCase**

```python
class AuthorizeUseCase:
    async def execute(self, request: AuthorizeRequest) -> AuthorizationCode:
        # 1. Validate user credentials
        user = await self.user_repo.get_by_email(request.email)
        if not verify_password(request.password, user.hashed_password):
            raise UnauthorizedError("Invalid credentials")
        
        # 2. Validate client_id (check app_registry)
        app = await self.app_repo.get_by_client_id(request.client_id)
        if not app or not app.is_approved:
            raise BadRequestError("Invalid or unapproved client")
        
        # 3. Validate redirect_uri
        if request.redirect_uri not in app.redirect_uris:
            raise BadRequestError("Invalid redirect_uri")
        
        # 4. Validate scopes
        invalid_scopes = set(request.scopes) - set(app.allowed_scopes)
        if invalid_scopes:
            raise BadRequestError(f"Invalid scopes: {invalid_scopes}")
        
        # 5. Check/create consent
        consent = await self.consent_repo.get_by_user_and_client(user.id, request.client_id)
        if not consent:
            # Auto-grant consent (or require explicit consent flow)
            consent = await self.consent_repo.create(ConsentRecord(
                user_id=user.id,
                client_id=request.client_id,
                scopes=request.scopes
            ))
        
        # 6. Generate authorization code
        code = AuthorizationCode(
            client_id=request.client_id,
            user_id=user.id,
            redirect_uri=request.redirect_uri,
            scopes=request.scopes,
            code_challenge=request.code_challenge,
            code_challenge_method=request.code_challenge_method
        )
        
        # 7. Store code
        await self.auth_repo.save_authorization_code(code)
        
        return code
```

#### 1.3 Infrastructure Layer

**Create:**

- `backend-merged/app/modules/auth/infrastructure/persistence/auth_model.py`
- `backend-merged/app/modules/auth/infrastructure/persistence/auth_repository_impl.py`

```python
# auth_model.py
class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": "session"}
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, nullable=False)
    client_id = Column(String(120), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    scopes = Column(ARRAY(String), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
```

#### 1.4 Presentation Layer

**Modify:** `[backend-merged/app/modules/auth/presentation/api/auth_router.py](backend-merged/app/modules/auth/presentation/api/auth_router.py)`

**Add endpoints:**

```python
@router.post("/authorize")
async def authorize(payload: AuthorizeRequest, session: DBSession) -> AuthorizeResponse:
    """OIDC Authorization Endpoint - Issues authorization code"""
    use_case = AuthorizeUseCase(...)
    code = await use_case.execute(payload)
    return AuthorizeResponse(
        code=code.code,
        state=payload.state,
        redirect_uri=f"{code.redirect_uri}?code={code.code}&state={payload.state}"
    )

@router.post("/token")
async def token(payload: TokenRequest, session: DBSession) -> TokenResponse:
    """OIDC Token Endpoint - Exchanges code for tokens"""
    use_case = ExchangeTokenUseCase(...)
    tokens = await use_case.execute(payload)
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        id_token=tokens.id_token,
        token_type="Bearer",
        expires_in=900
    )

@router.get("/userinfo")
async def userinfo(current_user_id: CurrentUserId, session: DBSession) -> UserInfoResponse:
    """OIDC UserInfo Endpoint - Returns user claims"""
    user = await user_repo.get_by_id(current_user_id)
    kyc = await kyc_repo.get_by_user_id(current_user_id)
    trust = await trust_repo.get_by_user_id(current_user_id)
    
    return UserInfoResponse(
        sub=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        email_verified=user.is_email_verified,
        phone_verified=user.phone_verified,
        kyc_tier=kyc.tier if kyc else "tier_0",
        trust_score=trust.trust_score if trust else 0,
        risk_level=trust.risk_level if trust else "high"
    )

@router.post("/introspect")
async def introspect(payload: IntrospectRequest, session: DBSession) -> IntrospectResponse:
    """Token Introspection (RFC 7662)"""
    try:
        claims = decode_token(payload.token)
        return IntrospectResponse(active=True, **claims)
    except JWTError:
        return IntrospectResponse(active=False)

@router.get("/.well-known/openid-configuration")
async def discovery() -> OIDCDiscoveryResponse:
    """OIDC Discovery Document"""
    return OIDCDiscoveryResponse(
        issuer=settings.ISSUER,
        authorization_endpoint=settings.AUTHORIZATION_ENDPOINT,
        token_endpoint=settings.TOKEN_ENDPOINT,
        userinfo_endpoint=settings.USERINFO_ENDPOINT,
        jwks_uri=settings.JWKS_URI,
        response_types_supported=["code"],
        grant_types_supported=["authorization_code", "refresh_token"],
        scopes_supported=["openid", "profile", "email", "kyc_status", "trust_score"],
        token_endpoint_auth_methods_supported=["client_secret_post"],
        code_challenge_methods_supported=["S256", "plain"]
    )

@router.get("/.well-known/jwks.json")
async def jwks() -> JWKSResponse:
    """JSON Web Key Set"""
    # Extract public key components from settings.JWT_PUBLIC_KEY
    # Return JWK format
```

### Frontend Implementation

**No new pages needed** - Login already exists at `[frontend/src/pages/LoginPage.tsx](frontend/src/pages/LoginPage.tsx)`

**Enhancement**: Update JWT claims handling in `[frontend/src/contexts/AuthContext.tsx](frontend/src/contexts/AuthContext.tsx)` to include new claims (kyc_tier, trust_score, etc.)

---

## Feature #2: KYC Module

### Backend Implementation

**Priority**: HIGH | **Time**: 4-6 hours

#### 2.1 Infrastructure (File Storage)

**Create:** `backend-merged/app/infrastructure/storage/file_storage.py`

```python
class FileStorageService:
    def __init__(self, base_path: str = "uploads/kyc"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def save_file(self, user_id: str, file_type: str, content: bytes) -> str:
        filename = f"{user_id}_{file_type}_{uuid.uuid4()}.jpg"
        filepath = self.base_path / filename
        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(content)
        return f"/uploads/kyc/{filename}"
```

#### 2.2 Infrastructure (Gemini OCR)

**Create:** `backend-merged/app/infrastructure/ai/ocr_service.py`

```python
class GeminiOCRService:
    async def extract_id_document(self, image_bytes: bytes) -> dict:
        """Extract data from ID using Gemini Vision"""
        prompt = """
        Extract from this ID document:
        - Full name, Date of birth, Gender, Nationality
        - Document number, Issue date, Expiry date
        - MRZ lines (if present)
        Return as JSON with confidence scores.
        """
        # Call Gemini API
        response = await self.client.generate_content([prompt, image_bytes])
        return json.loads(response.text)
```

#### 2.3 Application Layer

**Create use cases:**

- `backend-merged/app/modules/kyc/application/use_cases/submit_kyc.py`
- `backend-merged/app/modules/kyc/application/use_cases/process_ocr.py`
- `backend-merged/app/modules/kyc/application/use_cases/approve_kyc.py`
- `backend-merged/app/modules/kyc/application/use_cases/reject_kyc.py`
- `backend-merged/app/modules/kyc/application/use_cases/list_submissions.py`

#### 2.4 Presentation Layer

**Create:** `backend-merged/app/modules/kyc/presentation/api/kyc_router.py`

```python
@router.post("/submit")
async def submit_kyc(
    id_front: UploadFile,
    id_back: UploadFile,
    utility_bill: UploadFile,
    face_image: UploadFile,
    current_user_id: CurrentUserId,
    session: DBSession
) -> KYCResponse:
    """Submit KYC documents"""

@router.post("/ocr")
async def process_ocr(
    id_front: UploadFile,
    id_back: UploadFile,
    utility_bill: UploadFile
) -> OCRResponse:
    """Process OCR (preview before submit)"""

@router.get("/me")
async def get_my_kyc(current_user_id: CurrentUserId, session: DBSession) -> KYCResponse:
    """Get my KYC status"""

@router.get("/submissions")
async def list_submissions(
    session: DBSession,
    _: None = Depends(require_kyc_approver)
) -> List[KYCResponse]:
    """[KYC Approver/Admin] List all submissions"""

@router.post("/{kyc_id}/approve")
async def approve_kyc(
    kyc_id: str,
    tier: KYCTier,
    session: DBSession,
    _: None = Depends(require_kyc_approver)
) -> KYCResponse:
    """[KYC Approver/Admin] Approve KYC"""

@router.post("/{kyc_id}/reject")
async def reject_kyc(
    kyc_id: str,
    reason: str,
    session: DBSession,
    _: None = Depends(require_kyc_approver)
) -> KYCResponse:
    """[KYC Approver/Admin] Reject KYC"""
```

### Frontend Implementation

**Priority**: HIGH | **Time**: 3-4 hours

#### 2.1 Enhance Existing Page

**Modify:** `[frontend/src/pages/EKYCPage.tsx](frontend/src/pages/EKYCPage.tsx)`

**Current**: User submission form only
**Add**: Admin queue view (conditional rendering based on role)

```tsx
export default function EKYCPage() {
  const { role } = useAuth();
  const [view, setView] = useState<'submit' | 'queue'>('submit');
  
  // Show tabs for kyc_approver and admin
  const canApprove = role === 'kyc_approver' || role === 'admin';
  
  return (
    <div>
      {canApprove && (
        <Tabs value={view} onValueChange={setView}>
          <TabsList>
            <TabsTrigger value="submit">My KYC</TabsTrigger>
            <TabsTrigger value="queue">Review Queue</TabsTrigger>
          </TabsList>
        </Tabs>
      )}
      
      {view === 'submit' ? <KYCSubmitForm /> : <KYCAdminQueue />}
    </div>
  );
}
```

#### 2.2 Create Admin Queue Component

**Create:** `frontend/src/components/kyc/KYCAdminQueue.tsx`

```tsx
export function KYCAdminQueue() {
  const { data: submissions } = useQuery({
    queryKey: ['kyc', 'submissions'],
    queryFn: () => kycApi.listSubmissions()
  });
  
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>User</TableHead>
          <TableHead>Submitted</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {submissions?.map(kyc => (
          <TableRow key={kyc.id}>
            <TableCell>{kyc.full_name}</TableCell>
            <TableCell>{formatDate(kyc.created_at)}</TableCell>
            <TableCell><StatusBadge status={kyc.status} /></TableCell>
            <TableCell>
              <Button onClick={() => openReviewDialog(kyc)}>Review</Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

---

## Feature #3: Trust Module API

### Backend Implementation

**Priority**: MEDIUM | **Time**: 2-3 hours

**Create:** `backend-merged/app/modules/trust/presentation/api/trust_router.py`

```python
@router.get("/score")
async def get_my_trust_score(current_user_id: CurrentUserId, session: DBSession) -> TrustScoreResponse:
    """Get my trust score"""

@router.post("/calculate")
async def recalculate_trust_score(current_user_id: CurrentUserId, session: DBSession) -> TrustScoreResponse:
    """Force recalculation"""

@router.get("/{user_id}")
async def get_user_trust_score(
    user_id: str,
    session: DBSession,
    _: None = Depends(require_admin)
) -> TrustScoreResponse:
    """[Admin] Get any user's trust score"""
```

### Frontend Implementation

**Priority**: MEDIUM | **Time**: 2 hours

**Modify:** `[frontend/src/pages/DashboardPage.tsx](frontend/src/pages/DashboardPage.tsx)`

**Add Trust Score Widget:**

```tsx
function TrustScoreWidget() {
  const { data: trustScore } = useQuery({
    queryKey: ['trust', 'score'],
    queryFn: () => trustApi.getMyScore()
  });
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Trust Score</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-4xl font-bold">{trustScore?.trust_score}/100</div>
        <Badge variant={getRiskVariant(trustScore?.risk_level)}>
          {trustScore?.risk_level}
        </Badge>
        
        <div className="mt-4 space-y-2">
          <h4 className="text-sm font-medium">Score Breakdown</h4>
          {Object.entries(trustScore?.factors || {}).map(([key, value]) => (
            <div key={key} className="flex justify-between text-sm">
              <span>{formatFactorName(key)}</span>
              <span className="font-medium">+{value}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## Feature #4: Consent Module

### Backend Implementation

**Priority**: HIGH | **Time**: 3-4 hours

#### 4.1 Domain Layer

**Create:**

- `backend-merged/app/modules/consent/domain/entities/consent_record.py`
- `backend-merged/app/modules/consent/domain/repositories/consent_repository.py`

#### 4.2 Application Layer

**Create use cases:**

- `backend-merged/app/modules/consent/application/use_cases/grant_consent.py`
- `backend-merged/app/modules/consent/application/use_cases/revoke_consent.py`
- `backend-merged/app/modules/consent/application/use_cases/list_consents.py`

#### 4.3 Presentation Layer

**Modify:** `[backend-merged/app/modules/consent/presentation/api/consent_router.py](backend-merged/app/modules/consent/presentation/api/consent_router.py)`

```python
@router.post("/grant")
async def grant_consent(payload: GrantConsentRequest, current_user_id: CurrentUserId, session: DBSession) -> ConsentResponse:
    """Grant consent to application"""

@router.post("/revoke")
async def revoke_consent(payload: RevokeConsentRequest, current_user_id: CurrentUserId, session: DBSession) -> None:
    """Revoke consent"""

@router.get("/")
async def list_my_consents(current_user_id: CurrentUserId, session: DBSession) -> List[ConsentResponse]:
    """List my active consents"""
```

### Frontend Implementation

**Priority**: HIGH | **Time**: 2-3 hours

**Modify:** `[frontend/src/pages/ConsentPage.tsx](frontend/src/pages/ConsentPage.tsx)`

**Add full CRUD operations:**

```tsx
export default function ConsentPage() {
  const { data: consents } = useQuery({
    queryKey: ['consents'],
    queryFn: () => consentApi.listMine()
  });
  
  const revokeMutation = useMutation({
    mutationFn: (clientId: string) => consentApi.revoke(clientId),
    onSuccess: () => queryClient.invalidateQueries(['consents'])
  });
  
  return (
    <div>
      <PageHeader title="Consent Management" />
      
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Application</TableHead>
            <TableHead>Scopes</TableHead>
            <TableHead>Granted</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {consents?.map(consent => (
            <TableRow key={consent.id}>
              <TableCell>{consent.app_name}</TableCell>
              <TableCell>
                {consent.scopes.map(s => <Badge key={s}>{s}</Badge>)}
              </TableCell>
              <TableCell>{formatDate(consent.granted_at)}</TableCell>
              <TableCell>
                <Button 
                  variant="destructive" 
                  onClick={() => revokeMutation.mutate(consent.client_id)}
                >
                  Revoke
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
```

---

## Feature #5: App Registry Module

### Backend Implementation

**Priority**: HIGH | **Time**: 4-5 hours

#### 5.1 Domain Layer

**Create:**

- `backend-merged/app/modules/app_registry/domain/entities/registered_app.py`
- `backend-merged/app/modules/app_registry/domain/repositories/app_repository.py`

#### 5.2 Application Layer

**Create use cases:**

- `backend-merged/app/modules/app_registry/application/use_cases/register_app.py`
- `backend-merged/app/modules/app_registry/application/use_cases/approve_app.py`
- `backend-merged/app/modules/app_registry/application/use_cases/rotate_secret.py`

#### 5.3 Presentation Layer

**Modify:** `[backend-merged/app/modules/app_registry/presentation/api/app_router.py](backend-merged/app/modules/app_registry/presentation/api/app_router.py)`

```python
@router.post("/")
async def register_app(
    payload: RegisterAppRequest,
    current_user_id: CurrentUserId,
    session: DBSession
) -> AppResponse:
    """Register new OAuth2 client"""

@router.get("/")
async def list_apps(session: DBSession, _: None = Depends(require_admin)) -> List[AppResponse]:
    """[Admin] List all apps"""

@router.post("/{app_id}/approve")
async def approve_app(app_id: str, session: DBSession, _: None = Depends(require_admin)) -> AppResponse:
    """[Admin] Approve app"""

@router.get("/marketplace")
async def get_marketplace(session: DBSession) -> List[AppResponse]:
    """Public marketplace"""

@router.get("/mine")
async def get_my_apps(current_user_id: CurrentUserId, session: DBSession) -> List[AppResponse]:
    """My registered apps"""
```

### Frontend Implementation

**Priority**: HIGH | **Time**: 4-5 hours

#### 5.1 Create App Registry Pages

**Create:** `frontend/src/pages/AppRegistryPage.tsx`

```tsx
export default function AppRegistryPage() {
  const { role } = useAuth();
  const [view, setView] = useState<'marketplace' | 'mine' | 'admin'>('marketplace');
  
  const isAppOwner = role === 'app_owner' || role === 'admin';
  const isAdmin = role === 'admin';
  
  return (
    <div>
      <PageHeader title="App Registry" />
      
      <Tabs value={view} onValueChange={setView}>
        <TabsList>
          <TabsTrigger value="marketplace">Marketplace</TabsTrigger>
          {isAppOwner && <TabsTrigger value="mine">My Apps</TabsTrigger>}
          {isAdmin && <TabsTrigger value="admin">Admin</TabsTrigger>}
        </TabsList>
      </Tabs>
      
      {view === 'marketplace' && <AppMarketplace />}
      {view === 'mine' && <MyApps />}
      {view === 'admin' && <AppAdminPanel />}
    </div>
  );
}
```

**Create:** `frontend/src/components/apps/RegisterAppDialog.tsx`

```tsx
export function RegisterAppDialog() {
  const registerMutation = useMutation({
    mutationFn: (data: RegisterAppRequest) => appsApi.register(data)
  });
  
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Register New App</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Register OAuth2 Application</DialogTitle>
        </DialogHeader>
        <Form>
          <FormField name="name" label="App Name" />
          <FormField name="description" label="Description" />
          <FormField name="redirect_uris" label="Redirect URIs" type="array" />
          <FormField name="allowed_scopes" label="Requested Scopes" type="multiselect" />
          <FormField name="category" label="Category" type="select" />
          <Button onClick={handleSubmit}>Register</Button>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
```

#### 5.2 Update Navigation

**Modify:** `[frontend/src/components/layout/AppSidebar.tsx](frontend/src/components/layout/AppSidebar.tsx)`

Already has App Registry link for `app_owner` and `admin` roles ✓

#### 5.3 Update Routes

**Modify:** `[frontend/src/App.tsx](frontend/src/App.tsx)`

```tsx
<Route path="/apps" element={
  <ProtectedRoute allow={["admin", "app_owner"]}>
    <AppRegistryPage />
  </ProtectedRoute>
} />
```

---

## Feature #6: Session Module

### Backend Implementation

**Priority**: MEDIUM | **Time**: 2-3 hours

**Create:** `backend-merged/app/modules/session/presentation/api/session_router.py`

```python
@router.get("/")
async def list_active_sessions(current_user_id: CurrentUserId, session: DBSession) -> List[SessionResponse]:
    """List active sessions"""

@router.post("/{token_id}/revoke")
async def revoke_session(token_id: str, current_user_id: CurrentUserId, session: DBSession) -> None:
    """Revoke specific session"""

@router.post("/revoke-all")
async def revoke_all_sessions(current_user_id: CurrentUserId, session: DBSession) -> None:
    """Sign out from all devices"""
```

### Frontend Implementation

**Priority**: MEDIUM | **Time**: 2 hours

**Modify:** `[frontend/src/pages/SessionPage.tsx](frontend/src/pages/SessionPage.tsx)`

```tsx
export default function SessionPage() {
  const { data: sessions } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => sessionApi.listActive()
  });
  
  const revokeMutation = useMutation({
    mutationFn: (tokenId: string) => sessionApi.revoke(tokenId)
  });
  
  const revokeAllMutation = useMutation({
    mutationFn: () => sessionApi.revokeAll()
  });
  
  return (
    <div>
      <PageHeader 
        title="Active Sessions" 
        action={
          <Button variant="destructive" onClick={() => revokeAllMutation.mutate()}>
            Sign Out All Devices
          </Button>
        }
      />
      
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Device</TableHead>
            <TableHead>IP Address</TableHead>
            <TableHead>Last Active</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sessions?.map(session => (
            <TableRow key={session.id}>
              <TableCell>
                {session.device_info || 'Unknown Device'}
                {session.is_current && <Badge>Current</Badge>}
              </TableCell>
              <TableCell>{session.ip_address}</TableCell>
              <TableCell>{formatDate(session.last_used_at)}</TableCell>
              <TableCell>
                {!session.is_current && (
                  <Button 
                    variant="ghost" 
                    onClick={() => revokeMutation.mutate(session.id)}
                  >
                    Revoke
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
```

---

## Feature #7: Webhook Module

### Backend Implementation

**Priority**: HIGH | **Time**: 4-5 hours

#### 7.1 Domain Layer

**Create:**

- `backend-merged/app/modules/webhook/domain/entities/webhook_subscription.py`
- `backend-merged/app/modules/webhook/domain/entities/webhook_delivery.py`
- `backend-merged/app/modules/webhook/domain/repositories/webhook_repository.py`

#### 7.2 Application Layer

**Create use cases:**

- `backend-merged/app/modules/webhook/application/use_cases/subscribe_webhook.py`
- `backend-merged/app/modules/webhook/application/use_cases/deliver_webhook.py`

#### 7.3 Infrastructure Layer

**Create:** `backend-merged/app/modules/webhook/infrastructure/workers/webhook_worker.py`

```python
class WebhookWorker:
    async def run(self):
        while True:
            # Find pending deliveries
            deliveries = await self.repo.find_pending_deliveries()
            for delivery in deliveries:
                await self.deliver_use_case.execute(delivery.id)
            await asyncio.sleep(30)
```

**Register in:** `backend-merged/app/main.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    worker = WebhookWorker(...)
    worker_task = asyncio.create_task(worker.run())
    yield
    worker_task.cancel()
```

#### 7.4 Presentation Layer

**Modify:** `[backend-merged/app/modules/webhook/presentation/api/webhook_router.py](backend-merged/app/modules/webhook/presentation/api/webhook_router.py)`

```python
@router.post("/subscribe")
async def subscribe_webhook(
    payload: SubscribeRequest,
    current_user_id: CurrentUserId,
    session: DBSession
) -> WebhookSubscriptionResponse:
    """Subscribe to webhook events"""

@router.get("/subscriptions")
async def list_subscriptions(current_user_id: CurrentUserId, session: DBSession) -> List[WebhookSubscriptionResponse]:
    """List subscriptions"""

@router.get("/deliveries")
async def list_deliveries(current_user_id: CurrentUserId, session: DBSession) -> List[WebhookDeliveryResponse]:
    """List delivery history"""
```

### Frontend Implementation

**Priority**: HIGH | **Time**: 3-4 hours

**Create:** `frontend/src/pages/WebhooksPage.tsx`

```tsx
export default function WebhooksPage() {
  const { role } = useAuth();
  const canManageWebhooks = role === 'app_owner' || role === 'admin';
  
  if (!canManageWebhooks) {
    return <Navigate to="/dashboard" />;
  }
  
  const [view, setView] = useState<'subscriptions' | 'deliveries'>('subscriptions');
  
  return (
    <div>
      <PageHeader title="Webhooks" />
      
      <Tabs value={view} onValueChange={setView}>
        <TabsList>
          <TabsTrigger value="subscriptions">Subscriptions</TabsTrigger>
          <TabsTrigger value="deliveries">Delivery History</TabsTrigger>
        </TabsList>
      </Tabs>
      
      {view === 'subscriptions' ? <WebhookSubscriptions /> : <WebhookDeliveries />}
    </div>
  );
}
```

**Add route in:** `[frontend/src/App.tsx](frontend/src/App.tsx)`

```tsx
<Route path="/webhooks" element={
  <ProtectedRoute allow={["admin", "app_owner"]}>
    <WebhooksPage />
  </ProtectedRoute>
} />
```

**Update navigation in:** `[frontend/src/components/layout/AppSidebar.tsx](frontend/src/components/layout/AppSidebar.tsx)`

```tsx
const appDev: NavItem[] = [
  { title: "App Registry", url: "/apps", icon: Store },
  { title: "Webhooks", url: "/webhooks", icon: Webhook },  // Add this
];
```

---

## Feature #8: Dashboard Module (Admin Analytics)

### Backend Implementation

**Priority**: MEDIUM | **Time**: 2-3 hours

**Create:** `backend-merged/app/modules/dashboard/presentation/api/dashboard_router.py`

```python
@router.get("/stats")
async def get_user_stats(session: DBSession, _: None = Depends(require_admin)) -> UserStatsResponse:
    """[Admin] User statistics"""

@router.get("/kyc-metrics")
async def get_kyc_metrics(session: DBSession, _: None = Depends(require_admin)) -> KYCMetricsResponse:
    """[Admin] KYC metrics"""

@router.get("/biometric-stats")
async def get_biometric_stats(session: DBSession, _: None = Depends(require_admin)) -> BiometricStatsResponse:
    """[Admin] Biometric stats"""

@router.get("/app-usage")
async def get_app_usage(session: DBSession, _: None = Depends(require_admin)) -> AppUsageResponse:
    """[Admin] App usage analytics"""
```

### Frontend Implementation

**Priority**: MEDIUM | **Time**: 3-4 hours

**Create:** `frontend/src/pages/AdminDashboardPage.tsx`

```tsx
export default function AdminDashboardPage() {
  const { role } = useAuth();
  
  if (role !== 'admin') {
    return <Navigate to="/dashboard" />;
  }
  
  const { data: userStats } = useQuery({
    queryKey: ['dashboard', 'user-stats'],
    queryFn: () => dashboardApi.getUserStats()
  });
  
  const { data: kycMetrics } = useQuery({
    queryKey: ['dashboard', 'kyc-metrics'],
    queryFn: () => dashboardApi.getKYCMetrics()
  });
  
  return (
    <div>
      <PageHeader title="Admin Analytics" />
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Users" value={userStats?.total_users} />
        <StatCard title="Active Users" value={userStats?.active_users} />
        <StatCard title="KYC Pending" value={kycMetrics?.pending_count} />
        <StatCard title="Trust Score Avg" value={userStats?.avg_trust_score} />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <Card>
          <CardHeader>
            <CardTitle>KYC Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <PieChart data={kycMetrics?.by_status} />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>User Growth (30 days)</CardTitle>
          </CardHeader>
          <CardContent>
            <LineChart data={userStats?.growth_data} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

**Add route:**

```tsx
<Route path="/admin/dashboard" element={
  <ProtectedRoute allow={["admin"]}>
    <AdminDashboardPage />
  </ProtectedRoute>
} />
```

**Update navigation for admin:**

```tsx
const admin: NavItem[] = [
  { title: "Analytics", url: "/admin/dashboard", icon: BarChart },
];
```

---

## Feature #9: Audit Module

### Backend Implementation

**Priority**: LOW | **Time**: 2-3 hours

#### 9.1 Domain Layer

**Create:**

- `backend-merged/app/modules/audit/domain/entities/audit_log.py`
- `backend-merged/app/modules/audit/domain/repositories/audit_repository.py`

#### 9.2 Infrastructure Layer

**Create:** `backend-merged/app/modules/audit/infrastructure/middleware/audit_middleware.py`

```python
class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Log sensitive actions
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            await log_action(
                user_id=getattr(request.state, 'user_id', None),
                action=f"{request.method} {request.url.path}",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent")
            )
        
        return response
```

#### 9.3 Presentation Layer

**Modify:** `[backend-merged/app/modules/audit/presentation/api/audit_router.py](backend-merged/app/modules/audit/presentation/api/audit_router.py)`

```python
@router.get("/logs")
async def list_audit_logs(
    filters: AuditFilters,
    session: DBSession,
    _: None = Depends(require_admin)
) -> List[AuditLogResponse]:
    """[Admin] List audit logs"""

@router.get("/logs/{user_id}")
async def get_user_audit_trail(
    user_id: str,
    session: DBSession,
    _: None = Depends(require_admin)
) -> List[AuditLogResponse]:
    """[Admin] User audit trail"""

@router.get("/export")
async def export_compliance_report(
    date_range: DateRange,
    session: DBSession,
    _: None = Depends(require_admin)
) -> FileResponse:
    """[Admin] Export compliance report"""
```

### Frontend Implementation

**Priority**: LOW | **Time**: 2-3 hours

**Create:** `frontend/src/pages/AuditLogsPage.tsx`

```tsx
export default function AuditLogsPage() {
  const { role } = useAuth();
  
  if (role !== 'admin') {
    return <Navigate to="/dashboard" />;
  }
  
  const [filters, setFilters] = useState<AuditFilters>({});
  
  const { data: logs } = useQuery({
    queryKey: ['audit', 'logs', filters],
    queryFn: () => auditApi.listLogs(filters)
  });
  
  return (
    <div>
      <PageHeader 
        title="Audit Logs" 
        action={
          <Button onClick={handleExport}>Export Report</Button>
        }
      />
      
      <Card className="mb-4">
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Input 
              placeholder="User ID" 
              value={filters.user_id} 
              onChange={e => setFilters({...filters, user_id: e.target.value})}
            />
            <Select 
              value={filters.action} 
              onValueChange={action => setFilters({...filters, action})}
            >
              <SelectTrigger>
                <SelectValue placeholder="Action" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="login">Login</SelectItem>
                <SelectItem value="kyc_submit">KYC Submit</SelectItem>
                <SelectItem value="kyc_approve">KYC Approve</SelectItem>
              </SelectContent>
            </Select>
            <DateRangePicker 
              value={filters.date_range} 
              onChange={date_range => setFilters({...filters, date_range})}
            />
            <Button onClick={() => refetch()}>Filter</Button>
          </div>
        </CardContent>
      </Card>
      
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Timestamp</TableHead>
            <TableHead>User</TableHead>
            <TableHead>Action</TableHead>
            <TableHead>Resource</TableHead>
            <TableHead>IP Address</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {logs?.map(log => (
            <TableRow key={log.id}>
              <TableCell>{formatDateTime(log.timestamp)}</TableCell>
              <TableCell>{log.user_id}</TableCell>
              <TableCell><Badge>{log.action}</Badge></TableCell>
              <TableCell>{log.resource_type}/{log.resource_id}</TableCell>
              <TableCell>{log.ip_address}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
```

**Add route:**

```tsx
<Route path="/admin/audit" element={
  <ProtectedRoute allow={["admin"]}>
    <AuditLogsPage />
  </ProtectedRoute>
} />
```

---

## Summary: New Frontend Pages

### Pages to Create

1. ✅ **AppRegistryPage** — For `app_owner` and `admin` (Feature #5)
2. ✅ **WebhooksPage** — For `app_owner` and `admin` (Feature #7)
3. ✅ **AdminDashboardPage** — For `admin` only (Feature #8)
4. ✅ **AuditLogsPage** — For `admin` only (Feature #9)

### Pages to Enhance

1. ✅ **EKYCPage** — Add admin queue view for `kyc_approver` and `admin` (Feature #2)
2. ✅ **DashboardPage** — Add trust score widget (Feature #3)
3. ✅ **ConsentPage** — Add full CRUD operations (Feature #4)
4. ✅ **SessionPage** — Add device info and revocation (Feature #6)

### Navigation Updates

**Modify:** `[frontend/src/components/layout/AppSidebar.tsx](frontend/src/components/layout/AppSidebar.tsx)`

```tsx
const admin: NavItem[] = [
  { title: "Analytics", url: "/admin/dashboard", icon: BarChart },
  { title: "Audit Logs", url: "/admin/audit", icon: FileText },
];

const appDev: NavItem[] = [
  { title: "App Registry", url: "/apps", icon: Store },
  { title: "Webhooks", url: "/webhooks", icon: Webhook },
];
```

---

## Implementation Order (Recommended)

### Phase 1: Core Auth & KYC (10-14 hours)

1. Feature #1 (Auth Backend) — 6-8 hours
2. Feature #2 (KYC Backend + Frontend) — 4-6 hours

### Phase 2: Integration Features (11-16 hours)

1. Feature #4 (Consent Backend + Frontend) — 3-4 hours
2. Feature #5 (App Registry Backend + Frontend) — 4-5 hours
3. Feature #7 (Webhook Backend + Frontend) — 4-5 hours
4. Feature #3 (Trust API Backend + Frontend) — 2-3 hours

### Phase 3: Session & Admin (9-13 hours)

1. Feature #6 (Session Backend + Frontend) — 2-3 hours
2. Feature #8 (Dashboard Backend + Frontend) — 3-4 hours
3. Feature #9 (Audit Backend + Frontend) — 2-3 hours

**Total Estimated Time:** 30-43 hours

---

## Testing Strategy

### Backend Tests

```bash
# Unit tests
pytest tests/unit/modules/auth/
pytest tests/unit/modules/kyc/

# Integration tests
pytest tests/integration/test_oidc_flow.py
pytest tests/integration/test_kyc_approval.py
```

### Frontend Tests

```bash
# Component tests
npm run test

# E2E tests
npm run test:e2e
```

### Manual Testing Checklist

- User can login and see role-appropriate navigation
- KYC approver can see review queue
- App owner can register apps
- Admin can see analytics dashboard
- Webhooks deliver successfully
- Audit logs capture all actions

---

## Success Criteria

✅ **Backend**:

- All API endpoints return 2xx for valid requests
- OIDC flow completes (authorize → token → userinfo)
- RBAC enforced at API level
- Webhooks retry on failure

✅ **Frontend**:

- Role-based navigation works correctly
- Admin sees analytics dashboard
- KYC approver sees review queue
- App owner can manage apps and webhooks
- Users see only their own data

✅ **Integration**:

- JWT includes all required claims
- Trust score updates on KYC approval
- Webhooks trigger on events
- Audit logs capture actions

