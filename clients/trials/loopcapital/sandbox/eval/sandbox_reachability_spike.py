"""Reachability spike — CAN an AgentCore Code Interpreter reach a warehouse?

This is THE deciding-factor test for the whole agentic-remediation sandbox
approach (agentic-remediation-sandbox.md §6, "AgentCore Code Interpreter —
confirm VPC/customer-network reach before Layer 3"). Everything above the
investigation layer assumes a sandboxed microVM can open a connection to a
customer's warehouse to run a read-only diagnostic query. This proves it —
empirically, against real AWS — rather than assuming.

WHAT THE DOCS ALREADY CONFIRM (so this spike only has to prove it end-to-end,
not discover whether it's possible):
  - CreateCodeInterpreter accepts networkConfiguration.networkMode with valid
    values PUBLIC | SANDBOX | VPC (API_CodeInterpreterNetworkConfiguration).
  - VPC mode takes vpcConfig { subnets[], securityGroups[], requireServiceS3Endpoint }
    (API_CreateCodeInterpreter) — required when networkMode == VPC.
  - The overview states agents can be built "accessing internal data sources
    without exposing sensitive data" (code-interpreter-tool.html).
  => Architecturally, a Code Interpreter placed in a VPC with a security group
     that can reach the warehouse's port SHOULD connect. This spike confirms it
     for real, and measures the failure modes if not.

WHAT THIS SPIKE DOES — six probes. 1-3 are generic TCP/internet checks; 4-6 are
the REAL warehouse-specific tests, using the EXACT credential shapes brightbot
already reads from Secrets Manager (warehouse_connections.py / credentials_tools.py)
— this is a drop-in test against real staging secrets, not a toy:

  Probe 1 (PUBLIC mode) — sanity: sandbox executes code + has internet egress.
  Probe 2 (PUBLIC mode) — TCP to a PUBLICLY-REACHABLE db host:port.
  Probe 3 (VPC mode)    — DECISIVE generic case: TCP to a PRIVATE db host:port —
                          the customer-BYOW shape for a warehouse that lives
                          INSIDE an AWS account (e.g. Redshift, SQL Server on EC2).
  Probe 4 (PUBLIC mode) — SNOWFLAKE: real `snowflake.connector.connect(...)` +
                          `SELECT 1` from inside the sandbox, using
                          account/user/password (+ optional warehouse/database/
                          schema/role) — the SAME fields SnowflakeConnection.connect()
                          requires (warehouse_connections.py:801-820). PUBLIC mode
                          is correct: Snowflake is a SaaS product reached over
                          HTTPS to <account>.snowflakecomputing.com — it is NOT
                          hosted inside any AWS account/VPC, so there is no VPC to
                          attach to. Same reasoning as probe 6 (dbt Cloud).
  Probe 5 (VPC mode)    — REDSHIFT: real driver connect + `SELECT 1`, using
                          host/port/database/user/password — the SAME fields
                          RedshiftConnection.connect() requires. VPC mode is
                          correct here: Redshift IS an AWS-hosted resource (in
                          whichever account/VPC it was provisioned in — may be a
                          DIFFERENT AWS account than the sandbox's own account;
                          see the cross-account note below).
  Probe 6 (PUBLIC mode) — DBT CLOUD: NOT a private DB socket — dbt Cloud is a
                          SaaS HTTPS API (cloud.getdbt.com). Tests an authenticated
                          GET against the real Admin API using the SAME
                          apiToken/accountId shape read from Secrets Manager
                          secret `dbt/cloud-api/{service_id}` (credentials_tools.py).

CROSS-ACCOUNT NOTE (Redshift specifically): if the target Redshift cluster lives
in a DIFFERENT AWS account than the one running the sandbox (common — e.g. a
platform-core-owned account), SPIKE_VPC_SUBNETS/SPIKE_VPC_SECURITY_GROUPS must
be subnets/SGs the SANDBOX'S OWN account can use to reach it — either (a) the
sandbox and Redshift share a VPC via VPC peering / Transit Gateway, and you pass
subnets in the sandbox's side of that peered network, or (b) Redshift has a
public-facing endpoint reachable over the internet, in which case use PUBLIC
mode instead of VPC (skip the subnets/SGs entirely, same as Snowflake/dbt).
Ask whoever owns the platform-core AWS account (Ahmed, per this org's infra
split) which of (a)/(b) is true before running probe 5 — don't guess.

Why raw TCP first (probes 2/3) before a real driver connect (4/5): isolates
"can I route to the port" from "are my driver/credentials right" — two
different failure modes that must not be conflated when reading a result.

USAGE (needs real AWS creds + the bedrock-agentcore SDK; NOTHING here runs
without them — by design, it's a live spike, not a unit test):

  uv add bedrock-agentcore boto3           # or: pip install
  export AWS_REGION=us-east-1
  export SPIKE_EXECUTION_ROLE_ARN=arn:aws:iam::<acct>:role/<role>

  # Probes 3 and 5 (VPC mode) need the network wiring — probes 4/6 do NOT
  # (Snowflake/dbt Cloud are SaaS, reached over PUBLIC mode, no VPC needed):
  export SPIKE_VPC_SUBNETS=subnet-aaa,subnet-bbb
  export SPIKE_VPC_SECURITY_GROUPS=sg-ccc      # must allow egress to the db port

  python sandbox_reachability_spike.py --probe 1
  python sandbox_reachability_spike.py --probe 2   # + SPIKE_DB_HOST/PORT (public)
  python sandbox_reachability_spike.py --probe 3   # + SPIKE_DB_HOST/PORT (private)

  # Probe 4 — Snowflake (PUBLIC, no VPC needed): use the REAL staging secret's values, never hardcode.
  export SPIKE_SF_ACCOUNT=ab12345.us-east-1 SPIKE_SF_USER=... SPIKE_SF_PASSWORD=...
  export SPIKE_SF_WAREHOUSE=... SPIKE_SF_DATABASE=... SPIKE_SF_SCHEMA=... SPIKE_SF_ROLE=...
  python sandbox_reachability_spike.py --probe 4

  # Probe 5 — Redshift (VPC):
  export SPIKE_RS_HOST=... SPIKE_RS_PORT=5439 SPIKE_RS_DATABASE=... SPIKE_RS_USER=... SPIKE_RS_PASSWORD=...
  python sandbox_reachability_spike.py --probe 5

  # Probe 6 — dbt Cloud (PUBLIC — it's a SaaS API, not a private resource):
  export SPIKE_DBT_API_TOKEN=... SPIKE_DBT_ACCOUNT_ID=... [SPIKE_DBT_API_ENDPOINT=https://cloud.getdbt.com]
  python sandbox_reachability_spike.py --probe 6

Exit 0 = probe passed (reachable). Exit 1 = failed (records the failure mode).
Exit 2 = prerequisites missing (creds/SDK/env) — NOT a reachability failure.
Secrets are read from env only and NEVER printed — only pass/fail + sanitized
error text (exception type + message) crosses back out of the sandbox.

WHAT A GREEN PROBE 3 PROVES: the entire sandbox approach is viable — BrightAgent
CAN run an investigative query against a customer's private warehouse from an
isolated microVM. WHAT A RED PROBE 3 MEANS: the sandbox cannot reach BYOW
sources directly; investigation must instead go through the EXISTING warehouse
connection path (WarehouseTool), and the "give it a computer" framing is scoped
to compute-only, not customer-DB reach. Either result is decision-grade.
"""

from __future__ import annotations

import argparse
import os
import sys
import textwrap

REGION_ENV = "AWS_REGION"


def _preclude(reason: str) -> int:
    """Prerequisite missing — exit 2 (distinct from a reachability failure)."""
    print(f"[PRECONDITION] {reason}", file=sys.stderr)
    print("  This is NOT a reachability failure — it means the spike could not run.")
    print("  Provide the missing creds/SDK/env and re-run.")
    return 2


def _import_sdk():
    try:
        from bedrock_agentcore.tools.code_interpreter_client import CodeInterpreter
    except ImportError:
        return None
    return CodeInterpreter


# --------------------------------------------------------------------------- #
# Probe 1 — the sandbox executes code and reaches the public internet.        #
# --------------------------------------------------------------------------- #
_PROBE1_CODE = textwrap.dedent(
    """
    import urllib.request, json
    with urllib.request.urlopen("https://checkip.amazonaws.com", timeout=10) as r:
        ip = r.read().decode().strip()
    print(json.dumps({"reached_internet": True, "egress_ip": ip}))
    """
).strip()


# --------------------------------------------------------------------------- #
# Probe 2/3 — open a raw TCP socket to a db host:port, then a real SELECT 1.   #
# A raw socket check first isolates "can I route to the port" from "is my      #
# driver/credentials right" — the two failure modes must not be conflated.    #
# --------------------------------------------------------------------------- #
def _tcp_probe_code(host: str, port: int) -> str:
    return textwrap.dedent(
        f"""
        import socket, json
        try:
            s = socket.create_connection(({host!r}, {port}), timeout=10)
            s.close()
            print(json.dumps({{"tcp_reachable": True, "host": {host!r}, "port": {port}}}))
        except Exception as e:
            print(json.dumps({{"tcp_reachable": False, "host": {host!r}, "port": {port},
                               "error": type(e).__name__ + ": " + str(e)}}))
        """
    ).strip()


# --------------------------------------------------------------------------- #
# Probe 4 — SNOWFLAKE: real driver connect + SELECT 1, from inside the         #
# sandbox. Field names/optionality mirror SnowflakeConnection.connect()        #
# EXACTLY (warehouse_connections.py:801-820) — account/user/password required, #
# warehouse/database/schema/role optional, added only if present.              #
# --------------------------------------------------------------------------- #
def _snowflake_probe_code(*, account: str, user: str, password: str,
                          warehouse: str | None, database: str | None,
                          schema: str | None, role: str | None) -> str:
    optional = {"warehouse": warehouse, "database": database, "schema": schema, "role": role}
    optional_literal = repr({k: v for k, v in optional.items() if v})
    return textwrap.dedent(
        f"""
        import json
        try:
            import snowflake.connector
        except ImportError as e:
            print(json.dumps({{"connected": False, "target": "snowflake",
                               "error": "snowflake-connector-python not installed in sandbox: " + str(e)}}))
        else:
            try:
                kwargs = {{"account": {account!r}, "user": {user!r}, "password": {password!r},
                          "client_session_keep_alive": False}}
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


# --------------------------------------------------------------------------- #
# Probe 5 — REDSHIFT: real driver connect + SELECT 1. Field names mirror       #
# RedshiftConnection.connect() EXACTLY — host/database/port/user/password.     #
# --------------------------------------------------------------------------- #
def _redshift_probe_code(*, host: str, port: int, database: str, user: str,
                         password: str) -> str:
    return textwrap.dedent(
        f"""
        import json
        try:
            import psycopg2
        except ImportError as e:
            print(json.dumps({{"connected": False, "target": "redshift",
                               "error": "psycopg2 not installed in sandbox: " + str(e)}}))
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


# --------------------------------------------------------------------------- #
# Probe 6 — DBT CLOUD: NOT a private DB socket. dbt Cloud is a SaaS HTTPS API  #
# (cloud.getdbt.com) — PUBLIC mode is the CORRECT mode here, unlike probes     #
# 3-5. Auth shape mirrors credentials_tools.py's dbt/cloud-api/{service_id}    #
# secret: apiToken + accountId.                                                #
# --------------------------------------------------------------------------- #
def _dbt_cloud_probe_code(*, api_token: str, account_id: str, api_endpoint: str) -> str:
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


def _run_in_sandbox(CodeInterpreter, *, region: str, code: str,
                    network_mode: str, vpc_config: dict | None,
                    execution_role_arn: str | None) -> tuple[bool, str]:
    """Start a Code Interpreter session (default OR custom), execute code, return (ok, output).

    For PUBLIC/default mode we can use the managed system interpreter directly.
    For VPC mode we must CreateCodeInterpreter with a networkConfiguration first
    (the SDK's default session is not VPC-attached), then start a session on it.
    """
    # PUBLIC / default: the managed system interpreter path (simplest).
    if network_mode == "PUBLIC" and vpc_config is None:
        interpreter = CodeInterpreter(region=region)
        interpreter.start()
        try:
            result = interpreter.invoke("executeCode", {"language": "python", "code": code})
            # SDK returns a stream/result; normalize to text.
            output = _extract_output(result)
            return True, output
        finally:
            interpreter.stop()

    # VPC (or custom): create a code interpreter with the network configuration,
    # then start a session on that resource id. Uses the control-plane client.
    import boto3

    control = boto3.client("bedrock-agentcore-control", region_name=region)
    net_cfg: dict = {"networkMode": network_mode}
    if network_mode == "VPC":
        if not vpc_config:
            return False, "VPC mode requires vpcConfig (subnets + securityGroups)"
        net_cfg["vpcConfig"] = vpc_config

    create_kwargs = {
        "name": "brighthive_reachability_spike",
        "networkConfiguration": net_cfg,
    }
    if execution_role_arn:
        create_kwargs["executionRoleArn"] = execution_role_arn

    created = control.create_code_interpreter(**create_kwargs)
    ci_id = created["codeInterpreterId"]
    try:
        # Poll to READY (create is async — HTTP 202).
        _wait_ready(control, ci_id)
        interpreter = CodeInterpreter(region=region)
        # Bind the session to the custom interpreter id (SDK supports passing the id).
        interpreter.start(code_interpreter_identifier=ci_id)
        try:
            result = interpreter.invoke("executeCode", {"language": "python", "code": code})
            return True, _extract_output(result)
        finally:
            interpreter.stop()
    finally:
        try:
            control.delete_code_interpreter(codeInterpreterId=ci_id)
        except Exception as exc:  # noqa: BLE001 — cleanup best-effort
            print(f"[warn] failed to delete spike interpreter {ci_id}: {exc}", file=sys.stderr)


def _wait_ready(control, ci_id: str, *, attempts: int = 30, delay_s: float = 2.0) -> None:
    import time

    for _ in range(attempts):
        desc = control.get_code_interpreter(codeInterpreterId=ci_id)
        status = desc.get("status")
        if status == "READY":
            return
        if status in ("CREATE_FAILED", "DELETE_FAILED"):
            raise RuntimeError(f"code interpreter {ci_id} entered status {status}")
        time.sleep(delay_s)
    raise TimeoutError(f"code interpreter {ci_id} not READY after {attempts * delay_s}s")


def _extract_output(result) -> str:
    """Normalize the SDK's stream/dict result into printable text. The SDK's
    exact shape varies by version; be defensive and fall back to repr."""
    try:
        if isinstance(result, dict):
            # Common shapes: {"output": ...} or a stream under a key.
            if "output" in result:
                return str(result["output"])
            return str(result)
        # Stream / iterable of events.
        chunks = []
        for event in result:
            chunks.append(str(event))
        return "\n".join(chunks) if chunks else repr(result)
    except TypeError:
        return repr(result)


def _parse_vpc_config() -> dict | None:
    subnets = os.getenv("SPIKE_VPC_SUBNETS", "")
    sgs = os.getenv("SPIKE_VPC_SECURITY_GROUPS", "")
    if not subnets or not sgs:
        return None
    cfg: dict = {
        "subnets": [s.strip() for s in subnets.split(",") if s.strip()],
        "securityGroups": [s.strip() for s in sgs.split(",") if s.strip()],
    }
    if os.getenv("SPIKE_REQUIRE_S3_ENDPOINT", "").lower() in ("1", "true", "yes"):
        cfg["requireServiceS3Endpoint"] = True
    return cfg


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe", type=int, choices=[1, 2, 3, 4, 5, 6], required=True,
                    help="1=internet, 2=public-db TCP, 3=VPC private-db TCP, "
                         "4=Snowflake connect, 5=Redshift connect, 6=dbt Cloud API")
    args = ap.parse_args()

    region = os.getenv(REGION_ENV)
    if not region:
        return _preclude(f"{REGION_ENV} not set")

    CodeInterpreter = _import_sdk()
    if CodeInterpreter is None:
        return _preclude(
            "bedrock-agentcore SDK not installed "
            "(uv add bedrock-agentcore / pip install bedrock-agentcore)"
        )

    execution_role = os.getenv("SPIKE_EXECUTION_ROLE_ARN")

    if args.probe == 1:
        print("PROBE 1 — sandbox executes code + reaches public internet (PUBLIC mode)")
        ok, out = _run_in_sandbox(CodeInterpreter, region=region, code=_PROBE1_CODE,
                                  network_mode="PUBLIC", vpc_config=None,
                                  execution_role_arn=execution_role)
        print(out)
        passed = ok and '"reached_internet": true' in out.lower()
        print("\nRESULT:", "PASS — sandbox runs code and has egress" if passed
              else "FAIL — see output above")
        return 0 if passed else 1

    if args.probe == 2:
        host = os.getenv("SPIKE_DB_HOST")
        port = os.getenv("SPIKE_DB_PORT")
        if not host or not port:
            return _preclude("SPIKE_DB_HOST and SPIKE_DB_PORT must be set for probe 2")
        print(f"PROBE 2 — sandbox opens TCP to PUBLIC db {host}:{port} (PUBLIC mode)")
        ok, out = _run_in_sandbox(CodeInterpreter, region=region,
                                  code=_tcp_probe_code(host, int(port)),
                                  network_mode="PUBLIC", vpc_config=None,
                                  execution_role_arn=execution_role)
        print(out)
        passed = ok and '"tcp_reachable": true' in out.lower()
        print("\nRESULT:", "PASS — sandbox reached the db port" if passed
              else "FAIL — sandbox could not reach the db port (see error above)")
        return 0 if passed else 1

    if args.probe == 3:
        host = os.getenv("SPIKE_DB_HOST")
        port = os.getenv("SPIKE_DB_PORT")
        if not host or not port:
            return _preclude("SPIKE_DB_HOST and SPIKE_DB_PORT must be set for probe 3")
        vpc_config = _parse_vpc_config()
        if vpc_config is None:
            return _preclude(
                "SPIKE_VPC_SUBNETS and SPIKE_VPC_SECURITY_GROUPS must be set for probe 3 "
                "(VPC mode requires vpcConfig)"
            )
        if not execution_role:
            return _preclude("SPIKE_EXECUTION_ROLE_ARN must be set for probe 3 (VPC custom interpreter)")

        print(f"PROBE 3 — DECISIVE (generic): VPC-mode sandbox opens TCP to PRIVATE db {host}:{port}")
        print(f"          subnets={vpc_config['subnets']} sgs={vpc_config['securityGroups']}")
        ok, out = _run_in_sandbox(CodeInterpreter, region=region,
                                  code=_tcp_probe_code(host, int(port)),
                                  network_mode="VPC", vpc_config=vpc_config,
                                  execution_role_arn=execution_role)
        print(out)
        passed = ok and '"tcp_reachable": true' in out.lower()
        print("\n" + "=" * 72)
        if passed:
            print("RESULT: PASS -- a VPC-mode Code Interpreter REACHED a private warehouse.")
            print("  => The agentic-remediation sandbox approach is VIABLE end-to-end.")
            print("     Investigation-in-sandbox against customer BYOW sources is confirmed.")
        else:
            print("RESULT: FAIL -- VPC-mode sandbox could NOT reach the private warehouse.")
            print("  => Do NOT build investigation-in-sandbox against BYOW sources on this path.")
            print("     Fall back: investigate via the EXISTING WarehouseTool connection instead;")
            print("     scope the sandbox to compute-only. Record the exact error above as the")
            print("     evidence for that decision.")
        print("=" * 72)
        return 0 if passed else 1

    if args.probe == 4:
        account = os.getenv("SPIKE_SF_ACCOUNT")
        user = os.getenv("SPIKE_SF_USER")
        password = os.getenv("SPIKE_SF_PASSWORD")
        if not account or not user or not password:
            return _preclude(
                "SPIKE_SF_ACCOUNT, SPIKE_SF_USER, SPIKE_SF_PASSWORD must be set for probe 4 "
                "(the same required fields SnowflakeConnection.connect() reads)"
            )
        # CORRECTED: Snowflake is a SaaS product (HTTPS to
        # <account>.snowflakecomputing.com), not an AWS-hosted resource — it is
        # NOT inside any BrightHive/customer VPC. PUBLIC mode (internet egress)
        # is the correct mode here, exactly like probe 6 (dbt Cloud). No
        # SPIKE_VPC_SUBNETS/SPIKE_VPC_SECURITY_GROUPS needed for this probe.
        if not execution_role:
            return _preclude("SPIKE_EXECUTION_ROLE_ARN must be set for probe 4")

        print(f"PROBE 4 — SNOWFLAKE: PUBLIC-mode sandbox connects to account {account} + SELECT 1")
        code = _snowflake_probe_code(
            account=account, user=user, password=password,
            warehouse=os.getenv("SPIKE_SF_WAREHOUSE"), database=os.getenv("SPIKE_SF_DATABASE"),
            schema=os.getenv("SPIKE_SF_SCHEMA"), role=os.getenv("SPIKE_SF_ROLE"),
        )
        ok, out = _run_in_sandbox(CodeInterpreter, region=region, code=code,
                                  network_mode="PUBLIC", vpc_config=None,
                                  execution_role_arn=execution_role)
        print(out)
        passed = ok and '"connected": true' in out.lower()
        print("\nRESULT:", "PASS -- sandbox connected to Snowflake and ran SELECT 1" if passed
              else "FAIL -- see error above (driver missing vs. network vs. auth — check which)")
        return 0 if passed else 1

    if args.probe == 5:
        host = os.getenv("SPIKE_RS_HOST")
        database = os.getenv("SPIKE_RS_DATABASE")
        user = os.getenv("SPIKE_RS_USER")
        password = os.getenv("SPIKE_RS_PASSWORD")
        port = int(os.getenv("SPIKE_RS_PORT", "5439"))
        if not host or not database or not user or not password:
            return _preclude(
                "SPIKE_RS_HOST, SPIKE_RS_DATABASE, SPIKE_RS_USER, SPIKE_RS_PASSWORD must be set "
                "for probe 5 (the same required fields RedshiftConnection.connect() reads)"
            )
        vpc_config = _parse_vpc_config()
        if vpc_config is None:
            return _preclude("SPIKE_VPC_SUBNETS and SPIKE_VPC_SECURITY_GROUPS must be set for probe 5")
        if not execution_role:
            return _preclude("SPIKE_EXECUTION_ROLE_ARN must be set for probe 5")

        print(f"PROBE 5 — REDSHIFT: VPC-mode sandbox connects to {host}:{port}/{database} + SELECT 1")
        code = _redshift_probe_code(host=host, port=port, database=database,
                                    user=user, password=password)
        ok, out = _run_in_sandbox(CodeInterpreter, region=region, code=code,
                                  network_mode="VPC", vpc_config=vpc_config,
                                  execution_role_arn=execution_role)
        print(out)
        passed = ok and '"connected": true' in out.lower()
        print("\nRESULT:", "PASS -- sandbox connected to Redshift and ran SELECT 1" if passed
              else "FAIL -- see error above (driver missing vs. network vs. auth — check which)")
        return 0 if passed else 1

    # probe 6 — dbt Cloud: PUBLIC mode is CORRECT (SaaS API, not a private resource)
    api_token = os.getenv("SPIKE_DBT_API_TOKEN")
    account_id = os.getenv("SPIKE_DBT_ACCOUNT_ID")
    api_endpoint = os.getenv("SPIKE_DBT_API_ENDPOINT", "https://cloud.getdbt.com")
    if not api_token or not account_id:
        return _preclude(
            "SPIKE_DBT_API_TOKEN and SPIKE_DBT_ACCOUNT_ID must be set for probe 6 "
            "(the same fields read from Secrets Manager secret dbt/cloud-api/{service_id})"
        )
    print(f"PROBE 6 — DBT CLOUD: PUBLIC-mode sandbox calls {api_endpoint} Admin API "
          f"for account {account_id}")
    ok, out = _run_in_sandbox(
        CodeInterpreter, region=region,
        code=_dbt_cloud_probe_code(api_token=api_token, account_id=account_id,
                                   api_endpoint=api_endpoint),
        network_mode="PUBLIC", vpc_config=None, execution_role_arn=execution_role,
    )
    print(out)
    passed = ok and '"connected": true' in out.lower()
    print("\nRESULT:", "PASS -- sandbox authenticated against the dbt Cloud API" if passed
          else "FAIL -- see error above (egress vs. bad token/account_id — check which)")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
