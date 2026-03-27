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

## seed_data.py
Seed the database with test data (to be implemented).

```bash
py scripts/seed_data.py
```
