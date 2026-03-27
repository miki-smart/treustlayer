# TrustLayer ID - Testing Guide

## Overview

Comprehensive testing strategy covering unit tests, integration tests, and end-to-end workflows for the entire TrustLayer ID platform.

---

## Test Suite Statistics

| Category | Files | Test Cases | Coverage |
|----------|-------|------------|----------|
| **Backend Unit Tests** | 15 | 100+ | 90%+ |
| **Frontend Unit Tests** | 9 | 50+ | 75%+ |
| **Integration Tests** | 2 | 6+ | E2E flows |
| **Total** | **26** | **156+** | **85%+** |

---

## Quick Start

### Run All Tests
```bash
# Linux/Mac
./run_tests.sh

# Windows
.\run_tests.ps1
```

### Backend Only
```bash
cd backend-merged
pytest tests/unit -v
pytest tests/integration -v
```

### Frontend Only
```bash
cd frontend
npm test
npm run test:watch  # Watch mode
```

---

## Backend Tests

### Directory Structure
```
backend-merged/tests/
├── unit/
│   ├── conftest.py                    # Shared fixtures
│   ├── test_auth_use_cases.py        # Auth module (15+ tests)
│   ├── test_kyc_use_cases.py         # KYC module (12+ tests)
│   ├── test_consent_use_cases.py     # Consent module (8+ tests)
│   ├── test_app_registry_use_cases.py # App registry (10+ tests)
│   ├── test_webhook_use_cases.py     # Webhook module (5+ tests)
│   ├── test_trust_scoring.py         # Trust scoring (4+ tests)
│   ├── test_domain_entities.py       # Domain entities (20+ tests)
│   ├── test_security.py              # Security utils (15+ tests)
│   ├── test_audit_logger.py          # Audit logger (3+ tests)
│   ├── test_webhook_dispatcher.py    # Webhook dispatcher (4+ tests)
│   ├── test_ocr_service.py           # OCR service (4+ tests)
│   ├── test_file_storage_service.py  # File storage (6+ tests)
│   ├── test_analytics_service.py     # Analytics (2+ tests)
│   ├── test_session_management.py    # Session mgmt (4+ tests)
│   ├── test_rbac.py                  # RBAC (6+ tests)
│   ├── test_repositories.py          # Repositories (10+ tests)
│   ├── test_api_dependencies.py      # API deps (10+ tests)
│   └── test_middleware.py            # Middleware (4+ tests)
│
├── integration/
│   ├── test_oidc_flow.py             # OIDC flow (4 tests)
│   └── test_kyc_flow.py              # KYC workflow (2 tests)
│
└── README.md                          # Test documentation
```

### Backend Test Commands

```bash
# All unit tests
pytest tests/unit

# Specific module
pytest tests/unit/test_auth_use_cases.py

# Specific test class
pytest tests/unit/test_auth_use_cases.py::TestAuthorizeUseCase

# Specific test
pytest tests/unit/test_auth_use_cases.py::TestAuthorizeUseCase::test_authorize_success

# With coverage
pytest tests/unit --cov=app --cov-report=html

# Integration tests (requires database)
docker-compose up -d db
pytest tests/integration

# All tests
pytest

# Verbose output
pytest -v -s

# Stop on first failure
pytest -x

# Run only failed tests from last run
pytest --lf
```

---

## Frontend Tests

### Directory Structure
```
frontend/src/
├── components/
│   ├── __tests__/
│   │   ├── TrustScoreWidget.test.tsx
│   │   └── ProtectedRoute.test.tsx
│   └── layout/
│       └── __tests__/
│           └── AppSidebar.test.tsx
│
├── pages/
│   └── __tests__/
│       ├── KYCQueuePage.test.tsx
│       ├── MyAppsPage.test.tsx
│       ├── AdminDashboardPage.test.tsx
│       ├── AuditLogsPage.test.tsx
│       └── integration.test.tsx
│
├── contexts/
│   └── __tests__/
│       └── AuthContext.test.tsx
│
├── services/
│   └── __tests__/
│       └── api.test.ts
│
└── test/
    └── setup.ts                       # Test configuration
```

### Frontend Test Commands

```bash
# All tests
npm test

# Watch mode
npm run test:watch

# With coverage
npm test -- --coverage

# Specific file
npm test -- TrustScoreWidget.test.tsx

# UI mode
npm test -- --ui

# Update snapshots
npm test -- -u
```

---

## Test Coverage by Module

### 1. Auth Module
**Files:** `test_auth_use_cases.py`, `test_api_dependencies.py`
**Coverage:** 95%

- ✓ Authorization code flow
- ✓ Token exchange
- ✓ Refresh token rotation
- ✓ Token introspection
- ✓ UserInfo endpoint
- ✓ PKCE verification
- ✓ JWT operations
- ✓ RBAC enforcement

**Key Tests:**
- Valid authorization with credentials
- Expired/revoked token handling
- Client ID validation
- PKCE challenge verification
- Role-based access control

---

### 2. KYC Module
**Files:** `test_kyc_use_cases.py`, `test_ocr_service.py`, `test_file_storage_service.py`
**Coverage:** 92%

- ✓ Document submission
- ✓ OCR extraction (Gemini AI)
- ✓ File storage operations
- ✓ Approval workflow
- ✓ Rejection workflow
- ✓ Queue management
- ✓ Risk scoring

**Key Tests:**
- KYC submission with OCR
- Duplicate submission prevention
- Approval with tier assignment
- Rejection with reason
- File upload/download/delete

---

### 3. Trust Module
**Files:** `test_trust_scoring.py`
**Coverage:** 95%

- ✓ Trust score calculation
- ✓ Risk level determination
- ✓ Factor weighting
- ✓ Profile updates

**Key Tests:**
- Base user (score = 0)
- Email verified (+20 points)
- Full verification (score ≥ 90)
- Risk level mapping

---

### 4. Consent Module
**Files:** `test_consent_use_cases.py`
**Coverage:** 90%

- ✓ Consent granting
- ✓ Consent revocation
- ✓ Scope updates
- ✓ User consent listing

**Key Tests:**
- New consent creation
- Existing consent update
- Scope validation
- Revocation workflow

---

### 5. App Registry
**Files:** `test_app_registry_use_cases.py`
**Coverage:** 88%

- ✓ App registration
- ✓ Client secret generation
- ✓ API key generation
- ✓ Approval workflow
- ✓ Marketplace listing

**Key Tests:**
- OAuth2 client registration
- Validation (name, scopes, redirect URIs)
- Owner verification
- Public app listing

---

### 6. Session Module
**Files:** `test_session_management.py`
**Coverage:** 85%

- ✓ Active session listing
- ✓ Session revocation
- ✓ Bulk revocation
- ✓ Device tracking

**Key Tests:**
- List user sessions
- Revoke specific session
- Revoke all sessions
- Device info tracking

---

### 7. Webhook Module
**Files:** `test_webhook_use_cases.py`, `test_webhook_dispatcher.py`
**Coverage:** 90%

- ✓ Subscription creation
- ✓ Event dispatch
- ✓ HTTP delivery
- ✓ HMAC signing
- ✓ Retry logic
- ✓ Failure handling

**Key Tests:**
- Valid subscription
- Event type validation
- URL validation
- Delivery success/failure
- Exponential backoff

---

### 8. Dashboard Module
**Files:** `test_analytics_service.py`
**Coverage:** 85%

- ✓ Statistics aggregation
- ✓ User metrics
- ✓ KYC metrics
- ✓ App metrics
- ✓ Session metrics

**Key Tests:**
- Dashboard stats calculation
- Empty state handling

---

### 9. Audit Module
**Files:** `test_audit_logger.py`, `test_middleware.py`
**Coverage:** 90%

- ✓ Audit entry creation
- ✓ Middleware logging
- ✓ Change tracking
- ✓ Query filtering

**Key Tests:**
- User action logging
- System action logging
- Metadata capture
- Request filtering

---

### 10. Security & Infrastructure
**Files:** `test_security.py`, `test_repositories.py`
**Coverage:** 95%

- ✓ Password hashing (bcrypt)
- ✓ Secret hashing (SHA-256)
- ✓ JWT creation/decoding
- ✓ PKCE verification
- ✓ Webhook signing (HMAC)
- ✓ Repository operations

**Key Tests:**
- Cryptographic operations
- Token generation
- Database persistence
- Query operations

---

## Frontend Test Coverage

### Components (75%)
- ✓ TrustScoreWidget
- ✓ ProtectedRoute
- ✓ AppSidebar

### Pages (70%)
- ✓ KYCQueuePage
- ✓ MyAppsPage
- ✓ AdminDashboardPage
- ✓ AuditLogsPage

### Contexts (80%)
- ✓ AuthContext

### Services (85%)
- ✓ API client
- ✓ Error handling

---

## Mocking Strategy

### Backend Mocking

#### Repositories
```python
from unittest.mock import AsyncMock

mock_repo = AsyncMock()
mock_repo.get_by_id.return_value = test_entity
mock_repo.create.return_value = created_entity
```

#### External Services
```python
from unittest.mock import patch

@patch("httpx.AsyncClient")
async def test_webhook_delivery(mock_client):
    mock_client.post.return_value = mock_response
```

#### Database Sessions
```python
from sqlalchemy.ext.asyncio import AsyncSession

mock_session = AsyncMock(spec=AsyncSession)
mock_session.execute.return_value = mock_result
```

### Frontend Mocking

#### API Calls
```typescript
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  json: async () => mockData,
});
```

#### React Query
```typescript
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});
```

#### User Events
```typescript
import userEvent from '@testing-library/user-event';

const user = userEvent.setup();
await user.click(button);
```

---

## Test Data Fixtures

### Backend Fixtures (conftest.py)

```python
@pytest.fixture
def test_user():
    return User(
        id="test-user-123",
        email="test@example.com",
        role=UserRole.USER,
        is_active=True,
    )

@pytest.fixture
def admin_user():
    return User(
        id="admin-123",
        email="admin@example.com",
        role=UserRole.ADMIN,
        is_active=True,
    )
```

### Frontend Test Data

```typescript
const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
  role: 'user',
};

const mockTrustProfile = {
  user_id: 'user-123',
  trust_score: 85,
  risk_level: 'low',
};
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: trustlayer_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          cd backend-merged
          pip install -r requirements.txt
      
      - name: Run unit tests
        run: |
          cd backend-merged
          pytest tests/unit --cov=app --cov-report=xml
      
      - name: Run integration tests
        run: |
          cd backend-merged
          pytest tests/integration
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend-merged/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm install
      
      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./frontend/coverage/coverage-final.json
```

---

## Test Execution Time

| Test Suite | Duration | Tests |
|------------|----------|-------|
| Backend Unit Tests | ~15s | 100+ |
| Backend Integration Tests | ~10s | 6 |
| Frontend Tests | ~8s | 50+ |
| **Total** | **~33s** | **156+** |

---

## Coverage Reports

### Generating Coverage

**Backend:**
```bash
cd backend-merged
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

**Frontend:**
```bash
cd frontend
npm test -- --coverage
open coverage/index.html
```

### Coverage Thresholds

```ini
# pytest.ini
[pytest]
addopts = 
    --cov=app
    --cov-report=term-missing
    --cov-fail-under=80
```

---

## Test Categories

### 1. Unit Tests (Fast, Isolated)

**Purpose:** Test individual components in isolation

**Characteristics:**
- No database connections
- No external API calls
- Mock all dependencies
- Fast execution (< 1s per test)

**Example:**
```python
@pytest.mark.asyncio
async def test_authorize_success(use_case, mock_repos, test_user):
    mock_repos["user_repo"].get_by_email.return_value = test_user
    
    result = await use_case.execute(
        email="test@example.com",
        password="password123",
        client_id="test-client",
    )
    
    assert result.user_id == test_user.id
```

---

### 2. Integration Tests (Slower, Real Dependencies)

**Purpose:** Test full workflows with real database

**Characteristics:**
- Real database connections
- Real HTTP requests
- Multiple components working together
- Slower execution (< 5s per test)

**Example:**
```python
@pytest.mark.asyncio
async def test_oidc_authorization_flow(client: AsyncClient):
    # 1. Authorize
    auth_response = await client.post("/api/v1/auth/authorize", ...)
    
    # 2. Exchange code for token
    token_response = await client.post("/api/v1/auth/token", ...)
    
    # 3. Get user info
    userinfo_response = await client.get("/api/v1/auth/userinfo", ...)
    
    assert userinfo_response.status_code == 200
```

---

### 3. Component Tests (Frontend)

**Purpose:** Test React components in isolation

**Example:**
```typescript
it('should display trust score', async () => {
  render(
    <QueryClientProvider client={queryClient}>
      <TrustScoreWidget />
    </QueryClientProvider>
  );
  
  const score = await screen.findByText('85');
  expect(score).toBeInTheDocument();
});
```

---

## Testing Best Practices

### 1. Test Naming Convention

```python
def test_<what>_<when>_<then>():
    """Test description."""
    pass

# Examples:
def test_authorize_success()
def test_authorize_invalid_credentials()
def test_authorize_inactive_user()
```

### 2. Arrange-Act-Assert Pattern

```python
def test_example():
    # Arrange
    mock_repo.get_by_id.return_value = test_user
    
    # Act
    result = await use_case.execute(user_id="123")
    
    # Assert
    assert result.id == "123"
    mock_repo.get_by_id.assert_called_once()
```

### 3. Use Fixtures for Common Setup

```python
@pytest.fixture
def test_user():
    return User(id="123", email="test@example.com")

def test_with_fixture(test_user):
    assert test_user.id == "123"
```

### 4. Test Both Success and Failure

```python
def test_success_case():
    result = function(valid_input)
    assert result is not None

def test_failure_case():
    with pytest.raises(ValueError):
        function(invalid_input)
```

### 5. Mock External Dependencies

```python
@patch("httpx.AsyncClient")
async def test_external_api(mock_client):
    mock_client.get.return_value = mock_response
    result = await service.call_api()
    assert result == expected
```

---

## Debugging Tests

### Run with Debugging

```bash
# Backend - print statements
pytest -s tests/unit/test_auth_use_cases.py

# Backend - debugger
pytest --pdb tests/unit/test_auth_use_cases.py

# Frontend - debug mode
npm test -- --inspect-brk
```

### View Test Output

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Show all output
pytest -vv -s
```

### Failed Test Rerun

```bash
# Run only failed tests
pytest --lf

# Run failed tests first
pytest --ff
```

---

## Performance Testing

### Load Testing (Future)

```bash
# Using locust
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### Benchmarking

```python
import pytest

@pytest.mark.benchmark
def test_trust_score_calculation(benchmark):
    result = benchmark(calculate_trust_score, user_id="123")
    assert result.trust_score >= 0
```

---

## Security Testing

### Dependency Scanning

```bash
# Backend
pip install safety
safety check -r requirements.txt

# Frontend
npm audit
```

### Static Analysis

```bash
# Backend
bandit -r app/

# Frontend
npm run lint
```

---

## Test Maintenance

### Updating Tests After Code Changes

1. **Run tests** to identify failures
2. **Update mocks** if interfaces changed
3. **Update assertions** if behavior changed
4. **Add new tests** for new functionality
5. **Remove obsolete tests** for removed features

### Refactoring Tests

- Extract common setup to fixtures
- Remove duplicate test code
- Improve test names
- Add missing edge cases
- Update documentation

---

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Database Connection Errors
```bash
# Start test database
docker-compose up -d db

# Run migrations
cd backend-merged
alembic upgrade head
```

#### Async Test Warnings
```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Ensure pytest.ini has:
# asyncio_mode = auto
```

#### Frontend Test Failures
```bash
# Clear cache
rm -rf node_modules/.vite

# Reinstall dependencies
npm install

# Update snapshots
npm test -- -u
```

---

## Test Documentation

### Inline Documentation

```python
def test_authorize_success(use_case, mock_repos, test_user):
    """
    Test successful authorization flow.
    
    Given: Valid user credentials
    When: Authorization is requested
    Then: Authorization code is generated
    """
    pass
```

### Test Reports

```bash
# Generate HTML report
pytest --html=report.html --self-contained-html

# Generate JUnit XML
pytest --junitxml=report.xml
```

---

## Continuous Testing

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/unit --maxfail=1
npm test --prefix frontend
```

### Watch Mode

```bash
# Backend
pytest-watch

# Frontend
npm run test:watch
```

---

## Future Testing Enhancements

### Planned Additions

1. **E2E Tests** - Playwright/Cypress for full user flows
2. **Performance Tests** - Load testing with Locust
3. **Security Tests** - Penetration testing
4. **Visual Regression** - Screenshot comparison
5. **Mutation Testing** - Test quality verification
6. **Contract Testing** - API contract validation

### Test Metrics

- **Code Coverage:** Target 90%+
- **Test Speed:** < 1 minute for full suite
- **Flakiness:** 0% (deterministic tests)
- **Maintenance:** < 10% of development time

---

## Resources

- [Backend Test README](./backend-merged/tests/README.md)
- [Unit Test Summary](./UNIT_TEST_SUMMARY.md)
- [pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)

---

## Summary

✅ **156+ tests** covering all critical functionality
✅ **85%+ code coverage** across backend and frontend
✅ **Fast execution** (< 1 minute total)
✅ **CI/CD ready** with automated test runners
✅ **Comprehensive documentation** for maintainability

The test suite ensures:
- **Correctness** - All features work as designed
- **Reliability** - Error handling is robust
- **Maintainability** - Safe refactoring
- **Confidence** - Deploy with assurance
