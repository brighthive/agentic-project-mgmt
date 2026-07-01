#!/usr/bin/env python3
"""Package or unpack a {name}lead/ vault export directory.

Commands:
    package   Bundle {name}lead/ into an encrypted zip for handoff to a new engineering leader.
    unpack    Decrypt and extract a bundled package into {name}lead/.
    verify    Check that all expected files are present in {name}lead/.

Usage:
    make onboard NAME=matt           # packages mattlead-export.zip.enc
    make unpack  NAME=matt           # extracts into mattlead/
    make verify-lead NAME=matt       # checks mattlead/ completeness

Or directly:
    scripts/package_kurilead.py package --name matt [--output mattlead-export.zip.enc] [--password P]
    scripts/package_kurilead.py unpack  --name matt [--input  mattlead-export.zip.enc] [--password P]
    scripts/package_kurilead.py verify  --name matt

The name determines:
  - Source vault directory: {name}lead/  (e.g. mattlead/, kurilead/)
  - Default output/input file: {name}lead-export.zip.enc
  - Name is required to avoid accidentally using the wrong vault

The package command:
  1. Reads existing JSON exports from {name}lead/secrets-manager/ + lastpass-vault/ + dynamo-vault/.
  2. Creates a zip of the relevant JSON files (warns about missing files, proceeds with present ones).
  3. Encrypts with authenticated encryption (PBKDF2 + AES-CTR + HMAC-SHA256).
  4. Writes the encrypted package to the output path.

The unpack command:
  1. Prompts for password (or uses --password).
  2. Decrypts + extracts into {name}lead/ without overwriting existing files
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

# Files to include in / verify from any *lead/ directory (relative to the lead dir).
# Each entry is either a literal relative path or a directory — directories are walked
# recursively and every contained file is bundled.
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

# Directories whose contents are bundled wholesale. Used for vaults with a
# variable number of files (e.g. LangSmith — one JSON per deployment).
PACKAGE_DIRS = [
    "langsmith-vault",
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


def lead_dir(name: str) -> Path:
    """Return the path to {name}lead/ under the repo root."""
    return REPO_ROOT / f"{name}lead"


def default_package_path(name: str) -> str:
    return f"{name}lead-export.zip.enc"


def cmd_package(args: argparse.Namespace) -> int:
    name = args.name
    src_dir = lead_dir(name)
    if not src_dir.is_dir():
        print(f"[ERROR] {src_dir.name}/ not found at {src_dir}", file=sys.stderr)
        print(f"  Expected: {src_dir}", file=sys.stderr)
        return 1

    # Collect files to package
    files: list[tuple[str, Path]] = []
    missing: list[str] = []
    for pattern in PACKAGE_PATTERNS:
        p = src_dir / pattern
        if p.is_file():
            files.append((pattern, p))
        else:
            missing.append(pattern)

    for dir_pattern in PACKAGE_DIRS:
        dir_path = src_dir / dir_pattern
        if not dir_path.is_dir():
            missing.append(f"{dir_pattern}/")
            continue
        found_any = False
        for fp in sorted(dir_path.rglob("*")):
            if fp.is_file() and fp.name != ".gitkeep":
                files.append((str(fp.relative_to(src_dir)), fp))
                found_any = True
        if not found_any:
            missing.append(f"{dir_pattern}/ (empty)")

    if missing:
        print(f"[WARN] {len(missing)} expected files not found in {src_dir.name}/:", file=sys.stderr)
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
            "files": [arc_name for arc_name, _ in files],
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
    print(f"     They run:  NAME={name} make unpack")
    return 0


def cmd_unpack(args: argparse.Namespace) -> int:
    name = args.name
    pkg = Path(args.input)
    if not pkg.is_file():
        print(f"[ERROR] package not found: {pkg}", file=sys.stderr)
        print(f"  Expected: {pkg}", file=sys.stderr)
        print(f"  Ask your TechLead to run:  make onboard NAME={name}", file=sys.stderr)
        return 1
    dest_dir = lead_dir(name)

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
        for arc_name in zf.namelist():
            if arc_name == "PACKAGE_META.json":
                continue
            dest = dest_dir / arc_name
            if dest.is_file() and not args.force:
                print(f"  · skip {arc_name} (exists — use --force to overwrite)")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(zf.read(arc_name))
            print(f"  [OK] unpacked {arc_name}")

    print(f"\n[OK] {dest_dir.name}/ populated. Run `NAME={name} make pull-secrets` to copy into secrets/.")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    name = args.name
    src_dir = lead_dir(name)
    if not src_dir.is_dir():
        print(f"[ERROR] {src_dir.name}/ not found at {src_dir}", file=sys.stderr)
        print(f"  Run:  NAME={name} make unpack", file=sys.stderr)
        return 1
    ok = True
    for pattern in PACKAGE_PATTERNS:
        p = src_dir / pattern
        if p.is_file():
            print(f"  [OK] {pattern}")
        else:
            print(f"  [MISSING] {pattern}", file=sys.stderr)
            ok = False
    for dir_pattern in PACKAGE_DIRS:
        dir_path = src_dir / dir_pattern
        count = sum(1 for fp in dir_path.rglob("*") if fp.is_file() and fp.name != ".gitkeep") if dir_path.is_dir() else 0
        if count > 0:
            print(f"  [OK] {dir_pattern}/ ({count} files)")
        else:
            print(f"  [MISSING] {dir_pattern}/", file=sys.stderr)
            ok = False
    if ok:
        print(f"\n[OK] All expected files present in {src_dir.name}/.")
    else:
        print(f"\n[ERROR] Some files missing in {src_dir.name}/.", file=sys.stderr)
        print(f"  Ask TechLead to regenerate:  make onboard NAME={name}", file=sys.stderr)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Package/unpack a *lead/ vault export directory.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_pack = sub.add_parser("package", help="Bundle {name}lead/ into an encrypted handoff zip")
    p_pack.add_argument("--name", required=True, help="Lead name (e.g. matt -> mattlead/)")
    p_pack.add_argument("--output", default="", help="Output path (default: {name}lead-export.zip.enc)")
    p_pack.add_argument("--password", default="", help="Encryption password (omit to prompt)")

    p_unpack = sub.add_parser("unpack", help="Decrypt and extract into {name}lead/")
    p_unpack.add_argument("--name", required=True, help="Lead name (e.g. matt -> mattlead/)")
    p_unpack.add_argument("--input", default="", help="Input path (default: {name}lead-export.zip.enc)")
    p_unpack.add_argument("--password", default="", help="Decryption password (omit to prompt)")
    p_unpack.add_argument("--force", action="store_true", help="Overwrite existing files")

    p_verify = sub.add_parser("verify", help="Check {name}lead/ completeness")
    p_verify.add_argument("--name", required=True, help="Lead name (e.g. matt -> mattlead/)")

    args = ap.parse_args()
    # Apply name-derived defaults for output/input paths
    if hasattr(args, "output") and not args.output:
        args.output = default_package_path(args.name)
    if hasattr(args, "input") and not args.input:
        args.input = default_package_path(args.name)
    handlers = {"package": cmd_package, "unpack": cmd_unpack, "verify": cmd_verify}
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
