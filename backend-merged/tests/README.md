# TrustLayer ID - Test Suite

## Overview

Comprehensive test suite covering unit tests and integration tests for all modules.

## Test Structure

```
tests/
├── unit/                           # Unit tests (fast, isolated)
│   ├── conftest.py                # Shared fixtures
│   ├── test_auth_use_cases.py    # Auth module tests
│   ├── test_kyc_use_cases.py     # KYC module tests
│   ├── test_consent_use_cases.py # Consent module tests
│   ├── test_app_registry_use_cases.py # App registry tests
│   ├── test_webhook_use_cases.py # Webhook module tests
│   ├── test_trust_scoring.py     # Trust scoring tests
│   ├── test_domain_entities.py   # Domain entity tests
│   ├── test_security.py          # Security utility tests
│   ├── test_audit_logger.py      # Audit logger tests
│   ├── test_webhook_dispatcher.py # Webhook dispatcher tests
│   ├── test_ocr_service.py       # OCR service tests
│   └── test_file_storage_service.py # File storage tests
│
└── integration/                   # Integration tests (slower, DB required)
    ├── test_oidc_flow.py         # OIDC flow tests
    └── test_kyc_flow.py          # KYC workflow tests
```

## Running Tests

### All Tests
```bash
pytest
```

### Unit Tests Only
```bash
pytest tests/unit -m unit
```

### Integration Tests Only
```bash
pytest tests/integration -m integration
```

### Specific Module
```bash
pytest tests/unit/test_auth_use_cases.py
```

### With Coverage
```bash
pytest --cov=app --cov-report=html
```

### Verbose Output
```bash
pytest -v -s
```

## Test Categories

### Unit Tests (12 files)
- **Auth Module** (3 test classes, 15+ tests)
  - AuthorizeUseCase
  - ExchangeTokenUseCase
  - RefreshTokenUseCase

- **KYC Module** (4 test classes, 12+ tests)
  - SubmitKYCUseCase
  - ApproveKYCUseCase
  - RejectKYCUseCase
  - ListKYCQueueUseCase

- **Consent Module** (3 test classes, 8+ tests)
  - GrantConsentUseCase
  - RevokeConsentUseCase
  - ListUserConsentsUseCase

- **App Registry** (3 test classes, 10+ tests)
  - RegisterAppUseCase
  - ApproveAppUseCase
  - ListAppsUseCase

- **Webhook Module** (1 test class, 5+ tests)
  - SubscribeWebhookUseCase

- **Trust Scoring** (1 test class, 4+ tests)
  - CalculateTrustScoreUseCase

- **Domain Entities** (7 test classes, 20+ tests)
  - RefreshToken
  - AuthorizationCode
  - ConsentRecord
  - KYCVerification
  - App
  - WebhookDelivery
  - AuditEntry

- **Security** (5 test classes, 15+ tests)
  - Password hashing
  - Secret hashing
  - Token generation
  - JWT operations
  - PKCE verification
  - Webhook signing

- **Services** (3 test classes, 10+ tests)
  - AuditLogger
  - WebhookDispatcher
  - OCRService
  - FileStorageService

**Total Unit Tests: 100+ tests**

### Integration Tests (2 files)
- **OIDC Flow** (4 tests)
  - Full authorization code flow
  - Discovery document
  - JWKS endpoint
  - PKCE flow

- **KYC Flow** (2 tests)
  - Submission and approval workflow
  - Permission checks

**Total Integration Tests: 6+ tests**

## Test Coverage Goals

- **Domain Layer**: 100% (pure logic, easy to test)
- **Application Layer**: 90%+ (business logic)
- **Infrastructure Layer**: 80%+ (database operations)
- **Presentation Layer**: 70%+ (API endpoints)

## Mocking Strategy

### Unit Tests
- Mock all external dependencies (database, APIs, file system)
- Test business logic in isolation
- Fast execution (< 1 second per test)

### Integration Tests
- Use test database
- Test full request/response cycle
- Verify end-to-end workflows

## Fixtures

### Common Fixtures (conftest.py)
- `test_user` - Regular user
- `admin_user` - Admin user
- `kyc_approver_user` - KYC approver
- `app_owner_user` - App owner
- `test_app` - OAuth2 client app

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
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
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Writing New Tests

### Unit Test Template
```python
import pytest
from unittest.mock import AsyncMock

from app.modules.your_module.application.use_cases.your_use_case import YourUseCase

class TestYourUseCase:
    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_repo):
        return YourUseCase(repo=mock_repo)
    
    @pytest.mark.asyncio
    async def test_success_case(self, use_case, mock_repo):
        mock_repo.method.return_value = expected_value
        
        result = await use_case.execute(params)
        
        assert result == expected_value
        mock_repo.method.assert_called_once()
```

### Integration Test Template
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_api_endpoint(client: AsyncClient, test_user):
    response = await client.post(
        "/api/v1/endpoint",
        json={"key": "value"},
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "expected_value"
```

## Best Practices

1. **Arrange-Act-Assert** pattern
2. **One assertion per test** (when possible)
3. **Descriptive test names** (test_what_when_then)
4. **Mock external dependencies** in unit tests
5. **Use fixtures** for common setup
6. **Test edge cases** and error conditions
7. **Keep tests fast** (< 1s for unit tests)
8. **Test behavior, not implementation**

## Troubleshooting

### Tests fail with import errors
```bash
# Ensure PYTHONPATH includes app directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database connection errors
```bash
# Ensure test database is running
docker-compose up -d db
```

### Async test warnings
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

## Coverage Report

After running tests with coverage:
```bash
# View HTML report
open htmlcov/index.html

# View terminal report
pytest --cov=app --cov-report=term-missing
```
