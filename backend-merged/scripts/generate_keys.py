"""
Generate RSA-256 key pair for JWT signing.

Usage:
    python scripts/generate_keys.py

Output:
    - keys/private_key.pem
    - keys/public_key.pem
    
Then add to .env:
    JWT_PRIVATE_KEY=<content of private_key.pem>
    JWT_PUBLIC_KEY=<content of public_key.pem>
"""
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from pathlib import Path


def generate_rsa_keys():
    """Generate RSA-2048 key pair."""
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    public_key = private_key.public_key()
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    keys_dir = Path(__file__).parent.parent / "keys"
    keys_dir.mkdir(exist_ok=True)
    
    private_key_path = keys_dir / "private_key.pem"
    public_key_path = keys_dir / "public_key.pem"
    
    private_key_path.write_bytes(private_pem)
    public_key_path.write_bytes(public_pem)
    
    print(f"✅ RSA key pair generated:")
    print(f"   Private: {private_key_path}")
    print(f"   Public:  {public_key_path}")
    print()
    print("📋 Add to .env:")
    print(f'JWT_PRIVATE_KEY="{private_pem.decode()}"')
    print()
    print(f'JWT_PUBLIC_KEY="{public_pem.decode()}"')


if __name__ == "__main__":
    generate_rsa_keys()
