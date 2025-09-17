#!/usr/bin/env python3
"""
Generate admin credentials and save to .env

This creates/updates a .env file with:
ADMIN_SALT=<hex salt>
ADMIN_HASH=<hex derived key>
ADMIN_ITER=<iterations>

Run: python3 gen_admin_credentials.py
"""
import os
import sys
import hashlib
import secrets
import getpass
from pathlib import Path

# Configuration: PBKDF2 parameters
HASH_NAME = "sha256"
ITERATIONS = 200_000   # strong, but adjust if needed for your environment
SALT_BYTES = 16        # 16 bytes = 128 bits

ENV_PATH = Path(".env")
KEY_SALT = "ADMIN_SALT"
KEY_HASH = "ADMIN_HASH"
KEY_ITER = "ADMIN_ITER"

def derive_key(password: bytes, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac(HASH_NAME, password, salt, iterations)

def write_env(salt_hex: str, hash_hex: str, iterations: int):
    # Read existing lines and replace matching keys, or append if not present
    lines = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    # Build a dict for easy replace
    kv = {}
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            kv[k.strip()] = v.strip()

    kv[KEY_SALT] = salt_hex
    kv[KEY_HASH] = hash_hex
    kv[KEY_ITER] = str(iterations)

    # Write back to file (preserve other keys)
    with ENV_PATH.open("w", encoding="utf-8") as f:
        for k, v in kv.items():
            f.write(f"{k}={v}\n")

    print(f"Saved credentials to {ENV_PATH.resolve()}")

def main():
    print("Admin credential generator")
    pw = getpass.getpass("Type new admin password: ")
    if not pw:
        print("No password entered. Aborting.")
        sys.exit(1)
    pw2 = getpass.getpass("Confirm password: ")
    if pw != pw2:
        print("Passwords did not match. Aborting.")
        sys.exit(1)

    password_bytes = pw.encode("utf-8")
    salt = secrets.token_bytes(SALT_BYTES)
    derived = derive_key(password_bytes, salt, ITERATIONS)

    salt_hex = salt.hex()
    hash_hex = derived.hex()

    # Save to .env
    write_env(salt_hex, hash_hex, ITERATIONS)

    print("Done. Important:")
    print("- Add .env to your .gitignore so these never get pushed to GitHub.")
    print("- Keep the .env file secure. To change the password, re-run this script.")

if __name__ == "__main__":
    main()
