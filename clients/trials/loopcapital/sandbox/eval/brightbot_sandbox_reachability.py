"""Reachability probes using brightbot's OWN, already-live Code Interpreter.

SUPERSEDES the standalone sandbox_reachability_spike.py's warehouse probes for
one reason: brightbot already has a WORKING, TESTED Code Interpreter integration
--- brightbot/utils/sandbox_utils.py's invoke_bedrock_code_interpreter() --- wired
to real credentials already sitting in brightbot's own .env
(AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
BRIGHTAGENT_CODE_INTERPRETER_TOOL_ID). There is a passing integration test
(tests/integration/test_connector_sandbox_integration.py) proving that tool ID
already executes Python and shell commands successfully.

THE IMPORTANT FINDING THIS SCRIPT EXISTS TO CONFIRM OR REFUTE, found while
reading the existing code (not assumed): agent_tools/sandbox_tools.py's own
tool docstring says, verbatim:

    "Runs in a sandboxed Linux environment with limited network access
     (S3 and DNS only)."
    "Network: Only S3 and DNS access (no general internet)"

That phrasing matches AWS's `SANDBOX` network mode (no internet, no VPC) --
NOT `PUBLIC` (internet egress) or `VPC` (private network reach). If that's what
BRIGHTAGENT_CODE_INTERPRETER_TOOL_ID is actually configured with, it CANNOT
reach Snowflake, Redshift, or dbt Cloud today, no matter how correct the
credentials are -- the network mode, not the credentials, would be the
blocker. This has never been tested; it's inferred from a docstring written for
a different use case (Airbyte connector sandboxing, which only needs S3+DNS).
This script tests it directly and reports the ACTUAL configured network mode's
behavior, not what the docstring claims.

WHY THIS SCRIPT, SEPARATE FROM sandbox_reachability_spike.py: that script
builds its own boto3 client from scratch. This one calls the REAL,
ALREADY-TESTED brightbot function directly -- reusing its workspace-scoped
credential resolution (STS cross-account role assumption via
_resolve_workspace_code_interpreter_config) instead of reinventing it. Run this
one first; it needs zero new AWS setup beyond what's already in brightbot's .env.

USAGE (run FROM the brightbot repo root, or with brightbot importable):

  cd brightbot
  uv run python ../agentic-project-mgmt/clients/trials/loopcapital/sandbox/eval/brightbot_sandbox_reachability.py --probe sanity
  uv run python ../agentic-project-mgmt/clients/trials/loopcapital/sandbox/eval/brightbot_sandbox_reachability.py --probe snowflake
  uv run python ../agentic-project-mgmt/clients/trials/loopcapital/sandbox/eval/brightbot_sandbox_reachability.py --probe redshift
  uv run python ../agentic-project-mgmt/clients/trials/loopcapital/sandbox/eval/brightbot_sandbox_reachability.py --probe dbt

Credentials: reused from brightbot's own .env for the AWS/AgentCore side
(nothing new to export). For the WAREHOUSE side, export the same shapes as
before (never printed, never logged):

  export SPIKE_SF_ACCOUNT=... SPIKE_SF_USER=... SPIKE_SF_PASSWORD=...
  export SPIKE_RS_HOST=... SPIKE_RS_PORT=5439 SPIKE_RS_DATABASE=... SPIKE_RS_USER=... SPIKE_RS_PASSWORD=...
  export SPIKE_DBT_API_TOKEN=... SPIKE_DBT_ACCOUNT_ID=...

Exit 0 = reachable. Exit 1 = not reachable (records the failure mode -- read it
to tell "network mode blocks this" apart from "bad credentials"). Exit 2 =
prerequisites missing (creds/import/env), not a reachability result.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import textwrap


def _preclude(reason: str) -> int:
    print(f"[PRECONDITION] {reason}", file=sys.stderr)
    print("  This is NOT a reachability failure — it means the probe could not run.")
    return 2


def _import_brightbot():
    try:
        from brightbot.utils.sandbox_utils import invoke_bedrock_code_interpreter
    except ImportError as exc:
        return None, str(exc)
    return invoke_bedrock_code_interpreter, None


_SANITY_CODE = textwrap.dedent(
    """
    import urllib.request, json
    try:
        with urllib.request.urlopen("https://checkip.amazonaws.com", timeout=8) as r:
            ip = r.read().decode().strip()
        print(json.dumps({"reached_internet": True, "egress_ip": ip}))
    except Exception as e:
        print(json.dumps({"reached_internet": False,
                           "error": type(e).__name__ + ": " + str(e)}))
    """
).strip()


def _snowflake_code(*, account: str, user: str, password: str,
                    warehouse: str | None, database: str | None,
                    schema: str | None, role: str | None) -> str:
    optional = {"warehouse": warehouse, "database": database, "schema": schema, "role": role}
    optional_literal = repr({k: v for k, v in optional.items() if v})
    return textwrap.dedent(
        f"""
        import json, subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                        "snowflake-connector-python"], check=False)
        try:
            import snowflake.connector
        except ImportError as e:
            print(json.dumps({{"connected": False, "target": "snowflake",
                               "error": "driver not available: " + str(e)}}))
        else:
            try:
                kwargs = {{"account": {account!r}, "user": {user!r}, "password": {password!r},
                          "client_session_keep_alive": False, "login_timeout": 15}}
                kwargs.update({optional_literal})
                conn = snowflake.connector.connect(**kwargs)
                cur = conn.cursor()
                cur.execute("SELECT 1")
                row = cur.fetchone()
                cur.close(); conn.close()
                print(json.dumps({{"connected": True, "target": "snowflake", "select_1": row[0]}}))
            except Exception as e:
                print(json.dumps({{"connected": False, "target": "snowflake",
                                   "error": type(e).__name__ + ": " + str(e)}}))
        """
    ).strip()


def _redshift_code(*, host: str, port: int, database: str, user: str, password: str) -> str:
    return textwrap.dedent(
        f"""
        import json, subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "psycopg2-binary"],
                       check=False)
        try:
            import psycopg2
        except ImportError as e:
            print(json.dumps({{"connected": False, "target": "redshift",
                               "error": "driver not available: " + str(e)}}))
        else:
            try:
                conn = psycopg2.connect(host={host!r}, port={port}, dbname={database!r},
                                        user={user!r}, password={password!r}, connect_timeout=10)
                cur = conn.cursor()
                cur.execute("SELECT 1")
                row = cur.fetchone()
                cur.close(); conn.close()
                print(json.dumps({{"connected": True, "target": "redshift", "select_1": row[0]}}))
            except Exception as e:
                print(json.dumps({{"connected": False, "target": "redshift",
                                   "error": type(e).__name__ + ": " + str(e)}}))
        """
    ).strip()


def _dbt_cloud_code(*, api_token: str, account_id: str, api_endpoint: str) -> str:
    url = f"{api_endpoint.rstrip('/')}/api/v2/accounts/{account_id}/"
    return textwrap.dedent(
        f"""
        import json, urllib.request
        try:
            req = urllib.request.Request({url!r}, headers={{"Authorization": "Token {api_token}"}})
            with urllib.request.urlopen(req, timeout=10) as r:
                status = r.status
            print(json.dumps({{"connected": status == 200, "target": "dbt_cloud",
                               "http_status": status}}))
        except Exception as e:
            print(json.dumps({{"connected": False, "target": "dbt_cloud",
                               "error": type(e).__name__ + ": " + str(e)}}))
        """
    ).strip()


async def _run(invoke, code: str, session_id: str) -> dict:
    return await invoke(session_id=session_id, python_code=code)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe", choices=["sanity", "snowflake", "redshift", "dbt"], required=True)
    args = ap.parse_args()

    invoke, err = _import_brightbot()
    if invoke is None:
        return _preclude(
            f"could not import brightbot.utils.sandbox_utils ({err}). "
            "Run this from the brightbot repo (or with it on PYTHONPATH), "
            "e.g.: cd brightbot && uv run python <path to this file> --probe sanity"
        )
    if not os.getenv("BRIGHTAGENT_CODE_INTERPRETER_TOOL_ID"):
        return _preclude(
            "BRIGHTAGENT_CODE_INTERPRETER_TOOL_ID not set — brightbot's .env should "
            "already have this; make sure you're running with that .env loaded "
            "(sandbox_utils.py calls load_dotenv() itself, but only finds .env in "
            "the current/parent directory — run from the brightbot repo root)."
        )

    if args.probe == "sanity":
        print("SANITY — brightbot's existing Code Interpreter tool executes code "
              "+ has internet egress?")
        result = asyncio.run(_run(invoke, _SANITY_CODE, "reachability-sanity"))
        print(result.get("output", result))
        passed = result.get("status") == "success" and '"reached_internet": true' in \
            result.get("output", "").lower()
        print("\nRESULT:", "PASS" if passed else "FAIL")
        if not passed:
            print("  If status=success but reached_internet=false: the configured tool")
            print("  is in SANDBOX network mode (S3+DNS only, per sandbox_tools.py's own")
            print("  docstring) — this is the finding this script exists to confirm.")
        return 0 if passed else 1

    if args.probe == "snowflake":
        account, user, password = (os.getenv(k) for k in
                                   ("SPIKE_SF_ACCOUNT", "SPIKE_SF_USER", "SPIKE_SF_PASSWORD"))
        if not account or not user or not password:
            return _preclude("SPIKE_SF_ACCOUNT, SPIKE_SF_USER, SPIKE_SF_PASSWORD must be set")
        print(f"SNOWFLAKE — brightbot's Code Interpreter connects to account {account}?")
        code = _snowflake_code(account=account, user=user, password=password,
                               warehouse=os.getenv("SPIKE_SF_WAREHOUSE"),
                               database=os.getenv("SPIKE_SF_DATABASE"),
                               schema=os.getenv("SPIKE_SF_SCHEMA"),
                               role=os.getenv("SPIKE_SF_ROLE"))
        result = asyncio.run(_run(invoke, code, "reachability-snowflake"))
        print(result.get("output", result))
        passed = '"connected": true' in result.get("output", "").lower()
        print("\nRESULT:", "PASS" if passed else "FAIL — see error above")
        return 0 if passed else 1

    if args.probe == "redshift":
        host, database, user, password = (os.getenv(k) for k in
            ("SPIKE_RS_HOST", "SPIKE_RS_DATABASE", "SPIKE_RS_USER", "SPIKE_RS_PASSWORD"))
        port = int(os.getenv("SPIKE_RS_PORT", "5439"))
        if not host or not database or not user or not password:
            return _preclude(
                "SPIKE_RS_HOST, SPIKE_RS_DATABASE, SPIKE_RS_USER, SPIKE_RS_PASSWORD must be set"
            )
        print(f"REDSHIFT — brightbot's Code Interpreter connects to {host}:{port}/{database}?")
        code = _redshift_code(host=host, port=port, database=database, user=user, password=password)
        result = asyncio.run(_run(invoke, code, "reachability-redshift"))
        print(result.get("output", result))
        passed = '"connected": true' in result.get("output", "").lower()
        print("\nRESULT:", "PASS" if passed else "FAIL — see error above "
              "(if it's a timeout/connection-refused, this is likely a NETWORK MODE or "
              "cross-account VPC-routing issue, not credentials — see SANDBOX_REACHABILITY.md)")
        return 0 if passed else 1

    # dbt
    api_token, account_id = os.getenv("SPIKE_DBT_API_TOKEN"), os.getenv("SPIKE_DBT_ACCOUNT_ID")
    api_endpoint = os.getenv("SPIKE_DBT_API_ENDPOINT", "https://cloud.getdbt.com")
    if not api_token or not account_id:
        return _preclude("SPIKE_DBT_API_TOKEN and SPIKE_DBT_ACCOUNT_ID must be set")
    print(f"DBT CLOUD — brightbot's Code Interpreter calls {api_endpoint} for account {account_id}?")
    code = _dbt_cloud_code(api_token=api_token, account_id=account_id, api_endpoint=api_endpoint)
    result = asyncio.run(_run(invoke, code, "reachability-dbt-cloud"))
    print(result.get("output", result))
    passed = '"connected": true' in result.get("output", "").lower()
    print("\nRESULT:", "PASS" if passed else "FAIL — see error above")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
