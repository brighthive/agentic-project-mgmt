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

WHAT THIS SPIKE DOES (three escalating probes, each an independent yes/no):
  Probe 1 (PUBLIC mode)  — sanity: can the sandbox execute code + reach the
                           public internet at all? Cheapest possible check.
  Probe 2 (PUBLIC mode)  — can it open a TCP socket to a PUBLICLY-REACHABLE db
                           host:port (e.g. a test RDS with a public endpoint)?
                           Proves the driver + egress path work before VPC.
  Probe 3 (VPC mode)     — THE real test: a Code Interpreter created with
                           networkMode=VPC + the subnets/SG that can route to a
                           PRIVATE warehouse, runs a real `SELECT 1`. This is the
                           customer-BYOW shape (private SQL Server / Snowflake /
                           Databricks reached over the existing connection).

USAGE (needs real AWS creds + the bedrock-agentcore SDK; NOTHING here runs
without them — by design, it's a live spike, not a unit test):

  uv add bedrock-agentcore boto3           # or: pip install
  export AWS_REGION=us-east-1
  # Probe 3 also needs a reachable target + VPC wiring:
  export SPIKE_DB_HOST=... SPIKE_DB_PORT=5432
  export SPIKE_VPC_SUBNETS=subnet-aaa,subnet-bbb
  export SPIKE_VPC_SECURITY_GROUPS=sg-ccc
  export SPIKE_EXECUTION_ROLE_ARN=arn:aws:iam::<acct>:role/<role>

  python sandbox_reachability_spike.py --probe 1
  python sandbox_reachability_spike.py --probe 2
  python sandbox_reachability_spike.py --probe 3

Exit 0 = probe passed (reachable). Exit 1 = failed (records the failure mode).
Exit 2 = prerequisites missing (creds/SDK/env) — NOT a reachability failure.

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
    ap.add_argument("--probe", type=int, choices=[1, 2, 3], required=True,
                    help="1=internet, 2=public-db TCP, 3=VPC private-db TCP")
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

    # probe 3 — the decisive one
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

    print(f"PROBE 3 — DECISIVE: VPC-mode sandbox opens TCP to PRIVATE db {host}:{port}")
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


if __name__ == "__main__":
    sys.exit(main())
