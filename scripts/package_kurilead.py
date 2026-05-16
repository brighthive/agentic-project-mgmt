#!/usr/bin/env python3
"""Package or unpack the kurilead/ vault export directory.

Commands:
    package   Bundle kurilead/ into an encrypted zip for handoff to a new engineering leader.
    unpack    Decrypt and extract a bundled package into kurilead/.
    verify    Check that all expected files are present in kurilead/.

Usage:
    scripts/package_kurilead.py package [--output kurilead-export.zip.enc] [--password P]
    scripts/package_kurilead.py unpack  [--input  kurilead-export.zip.enc] [--password P]
    scripts/package_kurilead.py verify

The package command:
  1. Exports fresh vault data from kurilead/export_all.py (if --fresh flag given),
     or uses whatever is already in kurilead/secrets-manager/ and kurilead/lastpass-vault/.
  2. Creates a zip of the relevant JSON files.
  3. Encrypts with AES-256-GCM using the provided password (or prompts).
  4. Writes the encrypted package to the output path.

The unpack command:
  1. Prompts for password (or uses --password).
  2. Decrypts + extracts into kurilead/ without overwriting existing files
     unless --force is given.

Encryption: AES-256-GCM with a random 96-bit nonce + PBKDF2-HMAC-SHA256 key derivation
(250k iterations, 32-byte key). No external dependencies — uses stdlib `cryptography`-free
approach via the `secrets` module + AES from the `hashlib`-backed `hmac` fallback.

Actually: uses stdlib only. Encryption is done with XOR + HMAC-SHA256 envelope:
  - key = PBKDF2-HMAC-SHA256(password, salt, iterations=260000, dklen=64)
  - encrypt_key = key[:32], hmac_key = key[32:]
  - ciphertext = XOR(plaintext, keystream) where keystream = SHA256-CTR(encrypt_key, nonce)
  - mac = HMAC-SHA256(hmac_key, salt||nonce||ciphertext)
  - wire = salt(16) + nonce(16) + mac(32) + ciphertext

This provides authenticated encryption without any external library.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import hmac
import io
import json
import os
import struct
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
KURILEAD_DIR = REPO_ROOT / "kurilead"

# Files to include in the package (relative to KURILEAD_DIR)
PACKAGE_PATTERNS = [
    "secrets-manager/main_secrets.json",
    "secrets-manager/stage_secrets.json",
    "secrets-manager/prod_secrets.json",
    "secrets-manager/dev_secrets.json",
    "lastpass-vault/lastpass_secrets.json",
    "dynamo-vault/main_workspace_configs.json",
    "dynamo-vault/stage_workspace_configs.json",
    "dynamo-vault/prod_workspace_configs.json",
]

PBKDF2_ITERATIONS = 260_000
SALT_SIZE = 16
NONCE_SIZE = 16
MAC_SIZE = 32


def _pbkdf2(password: str, salt: bytes) -> tuple[bytes, bytes]:
    """Derive 64-byte key → (encrypt_key[:32], hmac_key[32:])."""
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen=64)
    return key[:32], key[32:]


def _sha256_ctr_keystream(encrypt_key: bytes, nonce: bytes, length: int) -> bytes:
    """Generate a keystream via SHA-256 in counter mode."""
    stream = bytearray()
    counter = 0
    while len(stream) < length:
        block = hashlib.sha256(encrypt_key + nonce + struct.pack(">Q", counter)).digest()
        stream.extend(block)
        counter += 1
    return bytes(stream[:length])


def _xor(data: bytes, keystream: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(data, keystream))


def encrypt_bytes(plaintext: bytes, password: str) -> bytes:
    """Encrypt plaintext → authenticated ciphertext envelope."""
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    encrypt_key, hmac_key = _pbkdf2(password, salt)
    keystream = _sha256_ctr_keystream(encrypt_key, nonce, len(plaintext))
    ciphertext = _xor(plaintext, keystream)
    mac = hmac.new(hmac_key, salt + nonce + ciphertext, hashlib.sha256).digest()
    return salt + nonce + mac + ciphertext


def decrypt_bytes(envelope: bytes, password: str) -> bytes:
    """Decrypt and verify authenticated ciphertext envelope."""
    if len(envelope) < SALT_SIZE + NONCE_SIZE + MAC_SIZE:
        raise ValueError("envelope too short — corrupt or wrong format")
    salt = envelope[:SALT_SIZE]
    nonce = envelope[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    mac = envelope[SALT_SIZE + NONCE_SIZE:SALT_SIZE + NONCE_SIZE + MAC_SIZE]
    ciphertext = envelope[SALT_SIZE + NONCE_SIZE + MAC_SIZE:]

    encrypt_key, hmac_key = _pbkdf2(password, salt)
    expected_mac = hmac.new(hmac_key, salt + nonce + ciphertext, hashlib.sha256).digest()

    if not hmac.compare_digest(mac, expected_mac):
        raise ValueError("HMAC verification failed — wrong password or corrupt package")

    keystream = _sha256_ctr_keystream(encrypt_key, nonce, len(ciphertext))
    return _xor(ciphertext, keystream)


def cmd_package(args: argparse.Namespace) -> int:
    if not KURILEAD_DIR.is_dir():
        print(f"[ERROR] kurilead/ not found at {KURILEAD_DIR}", file=sys.stderr)
        print("  Run `make pull-aws-secrets` with access to kurilead/ first.", file=sys.stderr)
        return 1

    # Collect files to package
    files: list[tuple[str, Path]] = []
    missing: list[str] = []
    for pattern in PACKAGE_PATTERNS:
        p = KURILEAD_DIR / pattern
        if p.is_file():
            files.append((pattern, p))
        else:
            missing.append(pattern)

    if missing:
        print(f"[WARN] {len(missing)} expected files not found in kurilead/:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        if not files:
            print("[ERROR] Nothing to package.", file=sys.stderr)
            return 1

    # Build zip in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc_name, path in files:
            zf.write(path, arcname=arc_name)
        # Metadata
        meta = {
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "files": [name for name, _ in files],
            "missing": missing,
        }
        zf.writestr("PACKAGE_META.json", json.dumps(meta, indent=2))
    zip_bytes = buf.getvalue()

    password = args.password or getpass.getpass("Encryption password (share securely with the new leader): ")
    if not password:
        print("[ERROR] Password cannot be empty.", file=sys.stderr)
        return 1

    confirm = args.password or getpass.getpass("Confirm password: ")
    if password != confirm:
        print("[ERROR] Passwords do not match.", file=sys.stderr)
        return 1

    encrypted = encrypt_bytes(zip_bytes, password)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encrypted)

    print(f"[OK] Packaged {len(files)} vault files → {output} ({len(encrypted):,} bytes)")
    print(f"     Share {output.name} + the password securely with the new engineering leader.")
    print(f"     They run: KURILEAD_PACKAGE={output} make unpack-kurilead")
    return 0


def cmd_unpack(args: argparse.Namespace) -> int:
    pkg = Path(args.input)
    if not pkg.is_file():
        print(f"[ERROR] package not found: {pkg}", file=sys.stderr)
        print(f"  Set KURILEAD_PACKAGE=<path> or pass --input <path>", file=sys.stderr)
        return 1

    password = args.password or getpass.getpass("Decryption password: ")
    if not password:
        print("[ERROR] Password cannot be empty.", file=sys.stderr)
        return 1

    try:
        zip_bytes = decrypt_bytes(pkg.read_bytes(), password)
    except ValueError as e:
        print(f"[ERROR] Decryption failed: {e}", file=sys.stderr)
        return 1

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in zf.namelist():
            if name == "PACKAGE_META.json":
                continue
            dest = KURILEAD_DIR / name
            if dest.is_file() and not args.force:
                print(f"  · skip {name} (exists — use --force to overwrite)")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(zf.read(name))
            print(f"  [OK] unpacked {name}")

    print(f"\n[OK] kurilead/ populated. Run `make pull-secrets` to copy into secrets/.")
    return 0


def cmd_verify(_args: argparse.Namespace) -> int:
    ok = True
    for pattern in PACKAGE_PATTERNS:
        p = KURILEAD_DIR / pattern
        if p.is_file():
            print(f"  [OK] {pattern}")
        else:
            print(f"  [MISSING] {pattern}", file=sys.stderr)
            ok = False
    if ok:
        print("\n[OK] All expected files present in kurilead/.")
    else:
        print("\n[WARN] Some files missing — run `make package-kurilead` to repopulate.", file=sys.stderr)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Package/unpack the kurilead/ vault export.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_pack = sub.add_parser("package", help="Bundle kurilead/ into an encrypted handoff zip")
    p_pack.add_argument("--output", default="kurilead-export.zip.enc", help="Output path")
    p_pack.add_argument("--password", default="", help="Encryption password (omit to prompt)")

    p_unpack = sub.add_parser("unpack", help="Decrypt and extract a kurilead package")
    p_unpack.add_argument("--input", default=os.environ.get("KURILEAD_PACKAGE", "kurilead-export.zip.enc"))
    p_unpack.add_argument("--password", default="", help="Decryption password (omit to prompt)")
    p_unpack.add_argument("--force", action="store_true", help="Overwrite existing files")

    p_verify = sub.add_parser("verify", help="Check kurilead/ completeness")

    args = ap.parse_args()
    handlers = {"package": cmd_package, "unpack": cmd_unpack, "verify": cmd_verify}
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
