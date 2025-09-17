#!/usr/bin/env python3
"""
Check admin password against values stored in .env

Run: python3 check_admin.py
"""
import hashlib
import hmac
import getpass
from pathlib import Path
import sys

ENV_PATH = Path(".env")
KEY_SALT = "ADMIN_SALT"
KEY_HASH = "ADMIN_HASH"
KEY_ITER = "ADMIN_ITER"
HASH_NAME = "sha256"

def load_env(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run gen_admin_credentials.py first.")
    data = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data

def derive_key(password: bytes, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac(HASH_NAME, password, salt, iterations)

def main():
    try:
        env = load_env(ENV_PATH)
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    try:
        salt_hex = env[KEY_SALT]
        stored_hash_hex = env[KEY_HASH]
        iterations = int(env.get(KEY_ITER, "200000"))
    except KeyError as e:
        print(f"Missing key in {ENV_PATH}: {e}")
        sys.exit(1)

    salt = bytes.fromhex(salt_hex)
    stored_hash = bytes.fromhex(stored_hash_hex)

    pw = getpass.getpass("Enter admin password to verify: ")
    if not pw:
        print("No password entered. Aborting.")
        sys.exit(1)

    derived = derive_key(pw.encode("utf-8"), salt, iterations)

    if hmac.compare_digest(derived, stored_hash):
        print("Password OK — match.")
        sys.exit(0)
    else:
        print("Password incorrect.")
        sys.exit(2)

if __name__ == "__main__":
    main()
