#!/usr/bin/env python3
"""
Generate RSA key pair for JWT signing.
Run once and add the output to your .env file.

Usage:
    python scripts/generate_keys.py
"""
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


def generate_rsa_keys() -> None:
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    print("=" * 60)
    print("Add these to your .env file:")
    print("=" * 60)
    # repr() converts newlines to \n literals for single-line env values
    print(f"\nJWT_PRIVATE_KEY={repr(private_pem)}")
    print(f"\nJWT_PUBLIC_KEY={repr(public_pem)}")
    print("\n" + "=" * 60)

    with open("private_key.pem", "w") as f:
        f.write(private_pem)
    with open("public_key.pem", "w") as f:
        f.write(public_pem)

    print("Keys also saved to private_key.pem and public_key.pem")
    print("WARNING: Keep private_key.pem secret — never commit it to git!")


if __name__ == "__main__":
    generate_rsa_keys()
