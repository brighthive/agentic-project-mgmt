#!/usr/bin/env python3
"""Render an env template by resolving {{ source.key }} tokens against cached vault data.

Usage:
    scripts/render_env.py --template config/env-templates/brightbot-local.env.tmpl \\
                          --output ../brightbot/.env \\
                          --secrets-dir secrets

Modes:
    --dry-run        Render to stdout, do not write.
    --verify         Render and compare SHA against --output; exit 1 if mismatch.

Adoption / safety modes (read from environment):
    ADOPT=1          If output file exists but no .meta record, snapshot the
                     existing file as the baseline rendered_sha (no overwrite).
    FORCE=1          Always overwrite, ignoring user-edit detection.

Exit codes:
    0  success (rendered, or skipped because nothing changed)
    1  unresolved tokens (lists what was missing)
    2  user-edited file detected (would overwrite without FORCE=1)
    3  unmanaged file detected (needs ADOPT=1 or FORCE=1)
    4  template, secrets, or output path error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"\{\{\s*([\w.\[\]\-\"']+)\s*\}\}")

# Repo root — used to anchor default paths so the script works regardless of CWD.
_REPO_ROOT = Path(__file__).parent.parent

# Compatibility aliases for legacy brightbot template key names.
# Maps new normalized key → tuple of older names to register as well.
# Uses setdefault so the canonical value always wins on collision.
AWS_KEY_ALIASES: dict[str, tuple[str, ...]] = {
    "apollo_url": ("graphql_url",),
    "core_api_password": ("brightbot_service_user_password",),
    "core_api_username": ("brightbot_service_user_username",),
    "neo4j_url": ("neo4j_uri",),
    "ogm_api_url": ("ogm_url",),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return sha256_text(path.read_text(encoding="utf-8"))


def normalize_key(raw: str) -> str:
    """Convert secret names/keys into template-friendly snake_case.

    Empty or whitespace-only input returns "" — callers must check for this.
    Pure non-ASCII input (after lower()) also returns "" via the strip("_").
    """
    return re.sub(r"[^a-z0-9]+", "_", raw.strip().lower()).strip("_")


def normalize_nested_keys(value: Any) -> Any:
    """Recursively normalize dict keys so templates can use predictable paths.

    `Any` is intentional: vault JSON contains unknown shapes (dict/list/scalar).
    """
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, inner in value.items():
            nk = normalize_key(str(key))
            if nk:  # skip empty normalized keys silently
                result[nk] = normalize_nested_keys(inner)
        return result
    if isinstance(value, list):
        return [normalize_nested_keys(item) for item in value]
    return value


def _values_equal(a: Any, b: Any) -> bool:
    """Deep-equality check for normalized vault values (handles dict/list/scalar)."""
    return a == b


def set_aws_key(env_data: dict[str, Any], key: str, value: Any) -> None:
    """Store a flattened AWS secret key plus any compatibility aliases.

    Primary key uses plain assignment (last-write-wins for multiple secrets
    that normalize to the same key).  Aliases use setdefault (first-write-wins)
    so they do not clobber a canonical key that arrived earlier.
    """
    env_data[key] = value
    for alias in AWS_KEY_ALIASES.get(key, ()):
        env_data.setdefault(alias, value)


# ---------------------------------------------------------------------------
# Vault loaders
# ---------------------------------------------------------------------------

def flatten_aws_export(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Flatten *lead-style Secrets Manager exports into a template-friendly map.

    Each entry has shape {"name": "...", "value_parsed": {...}, "value": "..."}.

    Result layout:
        flattened[<normalized_secret_name>] = {<inner key>: <value>, ...}
            — always populated, allows namespaced template refs like
              aws.staging["staging_platform_neo4j_credentials"].neo4j_uri
        flattened[<inner_key>] = <value>
            — only populated when the inner key is UNIQUE across all entries
              (i.e. exactly one secret defines it). Colliding keys are dropped
              from the flat namespace so templates fail loudly with an
              unresolved-token error rather than silently picking whichever
              value won the last-write race.

    Colliding keys are reported once in a single summary line, not per-pair.
    """
    flattened: dict[str, Any] = {}

    # First pass: store each secret under its namespaced key and count
    # how many secrets contribute each inner key.
    inner_key_owners: dict[str, list[tuple[str, Any]]] = {}

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        raw_name = str(entry.get("name", ""))
        normalized_name = normalize_key(raw_name)
        parsed_value = entry.get("value_parsed")

        if isinstance(parsed_value, dict):
            normalized_secret = normalize_nested_keys(parsed_value)
            if normalized_name:
                flattened[normalized_name] = normalized_secret

            for raw_key, raw_value in parsed_value.items():
                nk = normalize_key(str(raw_key))
                if not nk:
                    continue
                inner_key_owners.setdefault(nk, []).append(
                    (raw_name, normalize_nested_keys(raw_value))
                )
            continue

        raw_value = entry.get("value")
        if normalized_name and raw_value not in (None, ""):
            inner_key_owners.setdefault(normalized_name, []).append(
                (raw_name, raw_value)
            )

    # Second pass: promote keys to the flat namespace when either:
    #   - exactly one secret defines it, OR
    #   - multiple secrets define it with the same value (redundant copies).
    # Real value-divergence collisions are skipped — templates must use
    # namespaced refs to disambiguate.
    colliding: dict[str, list[str]] = {}
    for nk, owners in inner_key_owners.items():
        values = [v for _, v in owners]
        all_same = all(_values_equal(values[0], v) for v in values[1:])
        if all_same:
            set_aws_key(flattened, nk, values[0])
        else:
            colliding[nk] = [name for name, _ in owners]

    if colliding:
        print(
            f"[INFO] {len(colliding)} key(s) skipped due to collision — "
            f"use namespaced refs (e.g. aws.<env>['<secret-name>'].<key>) "
            f"instead of bare keys. Colliding keys:",
            file=sys.stderr,
        )
        for nk in sorted(colliding):
            owners = colliding[nk]
            preview = ", ".join(owners[:3])
            if len(owners) > 3:
                preview += f", … (+{len(owners) - 3} more)"
            print(f"    - {nk}  ({preview})", file=sys.stderr)

    return flattened


def load_aws_export(path: Path) -> dict[str, Any]:
    """Load either flat env JSON or *lead-style secret-entry exports.

    `Any` is intentional: the JSON shape is unknown until inspected.
    """
    data: Any = json.loads(path.read_text())

    if isinstance(data, list):
        return flatten_aws_export(data)

    if isinstance(data, dict) and isinstance(data.get("secrets"), list):
        return flatten_aws_export(data["secrets"])

    if isinstance(data, dict):
        return normalize_nested_keys(data)

    return {}


def load_lastpass_export(path: Path) -> dict[str, Any]:
    """Load either a flat lastpass mapping or the lastpass-vault CLI export payload.

    `Any` is intentional: the JSON shape is unknown until inspected.
    """
    data: Any = json.loads(path.read_text())

    if isinstance(data, dict) and isinstance(data.get("secrets"), list):
        flattened: dict[str, Any] = {}
        for secret in data["secrets"]:
            if not isinstance(secret, dict):
                continue

            candidates = [
                secret.get("normalized_name", ""),
                normalize_key(str(secret.get("name", ""))),
                normalize_key(str(secret.get("grouping", ""))),
            ]
            password = secret.get("password")
            username = secret.get("username")
            url = secret.get("url")

            for candidate in candidates:
                if not candidate:
                    continue
                if password not in (None, ""):
                    flattened.setdefault(candidate, password)
                if username not in (None, ""):
                    flattened.setdefault(f"{candidate}_username", username)
                if url not in (None, ""):
                    flattened.setdefault(f"{candidate}_url", url)

        return flattened

    if isinstance(data, dict):
        return normalize_nested_keys(data)

    return {}


def load_secrets(secrets_dir: Path) -> dict[str, Any]:
    """Merge all vault JSON exports into a single nested dict.

    Layout expected (all produced by `make pull-secrets`):
        secrets/aws/{env}.json       → secrets["aws"][env] = {...}
        secrets/lastpass.json        → secrets["lastpass"] = {...}
        secrets/dynamo/{env}.json    → secrets["dynamo"][env] = {...}

    If secrets/ is empty, prints a [WARN] and returns an empty map — the
    subsequent token-resolution step will fail loudly listing each missing key,
    so the engineer knows exactly what to pull.  No silent fallbacks.
    """
    merged: dict[str, Any] = {"aws": {}, "lastpass": {}, "dynamo": {}}

    aws_dir = secrets_dir / "aws"
    if aws_dir.is_dir():
        for f in aws_dir.glob("*.json"):
            env = f.stem
            try:
                merged["aws"][env] = load_aws_export(f)
            except json.JSONDecodeError as e:
                print(f"[WARN] {f}: invalid JSON ({e})", file=sys.stderr)

    lp_file = secrets_dir / "lastpass.json"
    if lp_file.is_file():
        try:
            merged["lastpass"] = load_lastpass_export(lp_file)
        except json.JSONDecodeError as e:
            print(f"[WARN] {lp_file}: invalid JSON ({e})", file=sys.stderr)

    dyn_dir = secrets_dir / "dynamo"
    if dyn_dir.is_dir():
        for f in dyn_dir.glob("*.json"):
            env = f.stem
            try:
                merged["dynamo"][env] = normalize_nested_keys(json.loads(f.read_text()))
            except json.JSONDecodeError as e:
                print(f"[WARN] {f}: invalid JSON ({e})", file=sys.stderr)

    # No silent fallbacks. If secrets/ is empty, the caller must run
    # `make pull-secrets` (or `NAME=<you> make unpack` then `make pull-secrets`).
    # Fail loudly on missing data so the engineer knows exactly what to fix.
    if not merged["aws"]:
        print("[WARN] secrets/aws/ is empty — run `make pull-aws-secrets`", file=sys.stderr)

    return merged


# ---------------------------------------------------------------------------
# Path resolver
# ---------------------------------------------------------------------------

def walk_path(data: Any, path: str) -> Any:
    """Walk a dotted/bracketed path into a nested dict.

    Supports:
        aws.staging.cognito_user_pool_id
        aws.staging["pool-id"]
        lastpass.openai_api_key

    Returns the value or raises KeyError with a clear message.
    Raises ValueError on malformed bracket tokens (unclosed `[`).

    `Any` is intentional: values at any level may be str/int/dict/list.
    """
    segments: list[str] = []
    i = 0
    s = path
    while i < len(s):
        if s[i] == "[":
            # bracketed lookup — find closing ]
            end = s.find("]", i)
            if end == -1:
                raise ValueError(f"unclosed '[' in path '{path}'")
            key = s[i + 1 : end].strip("\"'")
            segments.append(key)
            i = end + 1
            # skip trailing dot after ]
            if i < len(s) and s[i] == ".":
                i += 1
        else:
            # dotted segment — up to next . or [
            j = i
            while j < len(s) and s[j] not in ".[":
                j += 1
            segments.append(s[i:j])
            i = j
            if i < len(s) and s[i] == ".":
                i += 1

    cur = data
    for seg in segments:
        if seg == "":
            continue
        # Normalize segment to match how vault keys are stored (lowercase snake_case).
        # Allows templates to use {{ aws.staging.CognitoUserPoolId }} or the normalized form.
        seg_norm = normalize_key(seg) if seg else seg
        if not isinstance(cur, dict):
            raise KeyError(f"cannot index non-dict at '{seg}' in path '{path}'")
        # Try normalized key first, fall back to the original segment (preserves raw-key access).
        lookup = seg_norm if seg_norm in cur else seg
        if lookup not in cur:
            raise KeyError(f"missing key '{seg}' in path '{path}'")
        cur = cur[lookup]
    return cur


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render(template_text: str, secrets: dict[str, Any]) -> tuple[str, list[str]]:
    """Resolve {{ source.key }} tokens. Returns (rendered_text, missing_key_descriptions).

    `Any` is intentional: secrets values may be any JSON scalar or container.
    """
    missing: list[str] = []

    def resolver(match: re.Match[str]) -> str:
        path = match.group(1)
        try:
            value = walk_path(secrets, path)
        except (KeyError, ValueError) as e:
            missing.append(f"{path}  ({e})")
            return f"<<UNRESOLVED:{path}>>"
        if value is None:
            missing.append(f"{path}  (value is null)")
            return f"<<UNRESOLVED:{path}>>"
        return str(value)

    rendered = TOKEN_RE.sub(resolver, template_text)
    return rendered, missing


# ---------------------------------------------------------------------------
# Meta file helpers  (defined before main for readability)
# ---------------------------------------------------------------------------

def _write_meta(meta_file: Path, template_sha: str, secrets_sha: str, rendered_sha: str) -> None:
    meta_file.write_text(
        "template_sha={t}\nsecrets_sha={s}\nrendered_sha={r}\nwritten_at={w}\n".format(
            t=template_sha,
            s=secrets_sha,
            r=rendered_sha,
            w=datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        encoding="utf-8",
    )


def _read_meta_field(meta_file: Path, field: str) -> str:
    for line in meta_file.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{field}="):
            return line.split("=", 1)[1]
    return ""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--template", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--secrets-dir", default=_REPO_ROOT / "secrets", type=Path)
    ap.add_argument("--state-dir", default=Path(".state"), type=Path)
    ap.add_argument("--key", help="Meta-record key (e.g. brightbot-local). Defaults to template stem.")
    ap.add_argument("--dry-run", action="store_true", help="Render to stdout; do not write.")
    ap.add_argument("--verify", action="store_true", help="Render and exit 0 iff output matches.")
    args = ap.parse_args()

    if not args.template.is_file():
        print(f"[ERROR] template not found: {args.template}", file=sys.stderr)
        return 4

    if not args.secrets_dir.is_dir():
        print(f"[ERROR] secrets dir not found: {args.secrets_dir}", file=sys.stderr)
        print("  Run `make pull-secrets` first.", file=sys.stderr)
        return 4

    template_text = args.template.read_text(encoding="utf-8")
    template_sha = sha256_text(template_text)

    secrets = load_secrets(args.secrets_dir)
    secrets_sha = sha256_text(json.dumps(secrets, sort_keys=True, default=str))

    rendered, missing = render(template_text, secrets)

    if missing:
        print(
            f"[ERROR] {len(missing)} unresolved token(s) in {args.template.name}:",
            file=sys.stderr,
        )
        for m in missing:
            print(f"    - {m}", file=sys.stderr)
        print(
            "  Hint: if secrets/aws/ is empty, run `make pull-secrets NAME=<you>` first.\n"
            "  If it still fails, the key may not exist in AWS Secrets Manager for this env.",
            file=sys.stderr,
        )
        return 1

    rendered_sha = sha256_text(rendered)
    key = args.key or args.template.stem

    if args.dry_run:
        sys.stdout.write(rendered)
        return 0

    if args.verify:
        actual_sha = sha256_file(args.output)
        if actual_sha == rendered_sha:
            print(f"[OK] {args.output} matches rendered ({rendered_sha[:12]})")
            return 0
        print(f"[FAIL] {args.output} differs from rendered (expected {rendered_sha[:12]}, got {actual_sha[:12]})")
        return 2

    # --- Safety checks before writing ---
    meta_file = args.state_dir / "env" / f"{key}.meta"
    output_exists = args.output.is_file()
    meta_exists = meta_file.is_file()

    force = os.environ.get("FORCE", "0") == "1"
    adopt = os.environ.get("ADOPT", "0") == "1"

    if output_exists and not meta_exists and not force and not adopt:
        existing_sha = sha256_file(args.output)
        if existing_sha == rendered_sha:
            # File is byte-identical to what we'd render — take ownership silently.
            meta_file.parent.mkdir(parents=True, exist_ok=True)
            _write_meta(meta_file, template_sha, secrets_sha, rendered_sha)
            print(f"[OK] {args.output} already current — adopted ownership (no write)")
            return 0
        print(f"[ERROR] Unmanaged file present: {args.output}", file=sys.stderr)
        print(
            "  This file exists but was not created by the bootstrap.\n"
            "  Run with ADOPT=1 to snapshot it as your baseline (no overwrite),\n"
            "  or FORCE=1 to overwrite it with the freshly-rendered version.",
            file=sys.stderr,
        )
        return 3

    if output_exists and meta_exists and not force:
        existing_sha = sha256_file(args.output)
        recorded_rendered = _read_meta_field(meta_file, "rendered_sha")
        recorded_template = _read_meta_field(meta_file, "template_sha")
        recorded_secrets = _read_meta_field(meta_file, "secrets_sha")

        # Nothing changed — skip
        if (
            recorded_template == template_sha
            and recorded_secrets == secrets_sha
            and existing_sha == recorded_rendered
        ):
            print(f"  [OK] {args.output} (skipped — already current)")
            return 0

        # User edited the file
        if existing_sha != recorded_rendered:
            print(f"[ERROR] User edits detected in {args.output}", file=sys.stderr)
            print(
                "  The existing file's SHA doesn't match the last-rendered SHA.\n"
                "  Run with FORCE=1 to overwrite your edits.",
                file=sys.stderr,
            )
            return 2

    if adopt and output_exists and not meta_exists:
        existing_sha = sha256_file(args.output)
        meta_file.parent.mkdir(parents=True, exist_ok=True)
        _write_meta(meta_file, template_sha, secrets_sha, existing_sha)
        print(f"[OK] Adopted existing {args.output} (baseline SHA recorded)")
        return 0

    # Write the rendered output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    meta_file.parent.mkdir(parents=True, exist_ok=True)
    _write_meta(meta_file, template_sha, secrets_sha, rendered_sha)
    print(f"  [OK] wrote {args.output} ({rendered_sha[:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
