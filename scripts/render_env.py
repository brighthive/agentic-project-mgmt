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
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"\{\{\s*([\w.\[\]\-\"']+)\s*\}\}")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return sha256_text(path.read_text(encoding="utf-8"))


def load_secrets(secrets_dir: Path) -> dict[str, Any]:
    """Merge all vault JSON exports into a single nested dict.

    Layout expected:
        secrets/aws/{env}.json       → secrets["aws"][env] = {...}
        secrets/lastpass.json        → secrets["lastpass"] = {...}
        secrets/dynamo/{env}.json    → secrets["dynamo"][env] = {...}
    """
    merged: dict[str, Any] = {"aws": {}, "lastpass": {}, "dynamo": {}}

    aws_dir = secrets_dir / "aws"
    if aws_dir.is_dir():
        for f in aws_dir.glob("*.json"):
            env = f.stem
            try:
                merged["aws"][env] = json.loads(f.read_text())
            except json.JSONDecodeError as e:
                print(f"⚠ {f}: invalid JSON ({e})", file=sys.stderr)

    lp_file = secrets_dir / "lastpass.json"
    if lp_file.is_file():
        try:
            merged["lastpass"] = json.loads(lp_file.read_text())
        except json.JSONDecodeError as e:
            print(f"⚠ {lp_file}: invalid JSON ({e})", file=sys.stderr)

    dyn_dir = secrets_dir / "dynamo"
    if dyn_dir.is_dir():
        for f in dyn_dir.glob("*.json"):
            env = f.stem
            try:
                merged["dynamo"][env] = json.loads(f.read_text())
            except json.JSONDecodeError as e:
                print(f"⚠ {f}: invalid JSON ({e})", file=sys.stderr)

    return merged


def walk_path(data: Any, path: str) -> Any:
    """Walk a dotted/bracketed path into a nested dict.

    Supports:
        aws.staging.cognito_user_pool_id
        aws.staging["pool-id"]
        lastpass.openai_api_key

    Returns the value or raises KeyError with a clear message.
    """
    # Tokenize: split on '.' but keep ["..."] / ['...'] segments intact
    segments: list[str] = []
    i = 0
    s = path
    while i < len(s):
        if s[i] == "[":
            # bracketed lookup
            end = s.index("]", i)
            key = s[i + 1 : end].strip("\"'")
            segments.append(key)
            i = end + 1
            # skip a trailing dot, if present
            if i < len(s) and s[i] == ".":
                i += 1
        else:
            # dotted lookup up to next . or [
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
        if not isinstance(cur, dict):
            raise KeyError(f"cannot index non-dict at '{seg}' in path '{path}'")
        if seg not in cur:
            raise KeyError(f"missing key '{seg}' in path '{path}'")
        cur = cur[seg]
    return cur


def render(template_text: str, secrets: dict[str, Any]) -> tuple[str, list[str]]:
    """Resolve {{ source.key }} tokens. Returns (rendered, missing_keys)."""
    missing: list[str] = []

    def resolver(match: re.Match[str]) -> str:
        path = match.group(1)
        try:
            value = walk_path(secrets, path)
        except KeyError as e:
            missing.append(f"{path}  ({e})")
            return f"<<UNRESOLVED:{path}>>"
        if value is None:
            missing.append(f"{path}  (value is null)")
            return f"<<UNRESOLVED:{path}>>"
        return str(value)

    rendered = TOKEN_RE.sub(resolver, template_text)
    return rendered, missing


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--template", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--secrets-dir", default=Path("secrets"), type=Path)
    ap.add_argument("--state-dir", default=Path(".state"), type=Path)
    ap.add_argument("--key", help="Meta-record key (e.g. brightbot-local). Defaults to template stem.")
    ap.add_argument("--dry-run", action="store_true", help="Render to stdout; do not write.")
    ap.add_argument("--verify", action="store_true", help="Render and exit 0 iff output matches.")
    args = ap.parse_args()

    if not args.template.is_file():
        print(f"✗ template not found: {args.template}", file=sys.stderr)
        return 4

    if not args.secrets_dir.is_dir():
        print(f"✗ secrets dir not found: {args.secrets_dir}", file=sys.stderr)
        print("  Run `make pull-secrets` first.", file=sys.stderr)
        return 4

    template_text = args.template.read_text(encoding="utf-8")
    template_sha = sha256_text(template_text)

    secrets = load_secrets(args.secrets_dir)
    secrets_sha = sha256_text(json.dumps(secrets, sort_keys=True, default=str))

    rendered, missing = render(template_text, secrets)

    if missing:
        print(
            f"✗ {len(missing)} unresolved token(s) in {args.template.name}:",
            file=sys.stderr,
        )
        for m in missing:
            print(f"    - {m}", file=sys.stderr)
        return 1

    rendered_sha = sha256_text(rendered)
    key = args.key or args.template.stem

    if args.dry_run:
        sys.stdout.write(rendered)
        return 0

    if args.verify:
        actual_sha = sha256_file(args.output)
        if actual_sha == rendered_sha:
            print(f"✓ {args.output} matches rendered ({rendered_sha[:12]})")
            return 0
        print(f"✗ {args.output} differs from rendered (expected {rendered_sha[:12]}, got {actual_sha[:12]})")
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
            # File is byte-identical to what we'd render — safe to adopt silently.
            meta_file.parent.mkdir(parents=True, exist_ok=True)
            _write_meta(meta_file, template_sha, secrets_sha, rendered_sha)
            print(f"✓ {args.output} already current — adopted ownership (no write)")
            return 0
        print(f"✗ Unmanaged file present: {args.output}", file=sys.stderr)
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

        # Case: nothing changed — skip
        if (
            recorded_template == template_sha
            and recorded_secrets == secrets_sha
            and existing_sha == recorded_rendered
        ):
            print(f"  ✓ {args.output} (skipped — already current)")
            return 0

        # Case: user edited the file
        if existing_sha != recorded_rendered:
            print(f"✗ User edits detected in {args.output}", file=sys.stderr)
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
        print(f"✓ Adopted existing {args.output} (baseline SHA recorded)")
        return 0

    # Write the rendered output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    meta_file.parent.mkdir(parents=True, exist_ok=True)
    _write_meta(meta_file, template_sha, secrets_sha, rendered_sha)
    print(f"  ✓ wrote {args.output} ({rendered_sha[:12]})")
    return 0


def _write_meta(meta_file: Path, template_sha: str, secrets_sha: str, rendered_sha: str) -> None:
    from datetime import datetime, timezone
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


if __name__ == "__main__":
    sys.exit(main())
