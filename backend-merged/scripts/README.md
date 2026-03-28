# Scripts

## generate_keys.py
Generate RSA-256 key pair for JWT signing.

```bash
py scripts/generate_keys.py
```

Output:
- `keys/private_key.pem`
- `keys/public_key.pem`

Add the keys to `.env`.

## generate_boilerplate.py
Generate `__init__.py` files for all module directories.

```bash
py scripts/generate_boilerplate.py
```

## generate_module_stubs.py
Generate stub implementations for all modules.

```bash
py scripts/generate_module_stubs.py
```

## seed_demo_users.py
Idempotent demo accounts for local login (passwords reset on each run for listed emails).

```bash
# From backend-merged (or `docker exec trustlayer_backend python scripts/seed_demo_users.py`)
py scripts/seed_demo_users.py
```

| Email | Password | Role |
|-------|----------|------|
| admin@fininfra.io | admin123 | admin |
| abebe@example.com | user123 | user |
| kyc@example.com | kyc123 | kyc_approver |
| dev@example.com | dev123 | app_owner |
