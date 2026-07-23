# Sandbox Reachability — the deciding factor for agentic remediation

> **Question:** can an AgentCore Code Interpreter (the "computer" we'd give
> BrightAgent) actually reach a customer's warehouse to run an investigative
> query? If no, the whole "investigate a novel failure in a sandbox" approach
> collapses and investigation must go through the existing warehouse connection
> instead. This is the single unknown everything above the investigation layer
> rests on.
>
> **Date:** 2026-07-23 · **Status:** architecturally CONFIRMED YES (AWS docs);
> empirical confirmation pending AWS creds (spike is built + ready to run).

## The architectural answer: YES (confirmed from AWS's own API reference)

AgentCore Code Interpreter supports three network modes, and one of them places
the sandbox inside a VPC where it can reach private resources:

| Source | Fact |
|---|---|
| [`CodeInterpreterNetworkConfiguration`](https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/API_CodeInterpreterNetworkConfiguration.html) | `networkMode` valid values: **`PUBLIC \| SANDBOX \| VPC`** (required field) |
| [`CreateCodeInterpreter`](https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/API_CreateCodeInterpreter.html) | `networkConfiguration.vpcConfig` = `{ subnets[], securityGroups[], requireServiceS3Endpoint }` — required when `networkMode == VPC` |
| [Code Interpreter overview](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-tool.html) | "…perform complex workflows and data analysis in sandbox environments, while **accessing internal data sources** without exposing sensitive data" |
| Resource/session mgmt | Network is chosen at create time (**Sandbox or Public** for the managed path); an **execution role** defines what AWS resources the interpreter can access |

**Interpretation:** a Code Interpreter created with `networkMode=VPC` and a
`vpcConfig` whose subnets + security group can route to the warehouse's host:port
**should** open that connection — exactly the customer-BYOW shape (a private SQL
Server / Snowflake / Databricks reached over the same network path the existing
warehouse connection already uses). This retires the biggest risk in
`agentic-remediation-sandbox.md`: it is not a research gamble, it is a supported
configuration.

### The three modes, and which one we need

- **`SANDBOX`** — isolated, **no** inbound/outbound to your networks. Right for
  pure compute (math, parsing, transforming data already handed in). This is the
  safe default for READ_ONLY investigation that doesn't need the live warehouse.
- **`PUBLIC`** — internet egress, but not your private VPC resources.
- **`VPC`** — the decisive one: placed in your VPC, reaches private resources via
  the supplied subnets/security groups. **This is the mode that answers Frank's
  "how do you reach the SQL server" objection** — the sandbox sits where the
  warehouse connection already reaches.

## The empirical confirmation: `sandbox_reachability_spike.py`

The docs prove it's *supported*; the spike proves it *works for us*, end to end,
and measures the exact failure mode if it doesn't. It cannot run in this repo's
offline env (needs real AWS creds + the `bedrock-agentcore` SDK) — by design it
is a **live spike, not a unit test**. It is written, parses, and handles missing
prerequisites correctly (exits 2 = "couldn't run", never a false pass/fail).

Three escalating probes, each an independent yes/no:

| Probe | Mode | Proves |
|---|---|---|
| 1 | PUBLIC | sandbox executes code + has internet egress at all (cheapest sanity) |
| 2 | PUBLIC | sandbox opens a TCP socket to a **publicly-reachable** db host:port (driver + egress path work) |
| 3 | **VPC** | **DECISIVE:** VPC-mode sandbox opens TCP to a **private** warehouse — the customer-BYOW shape |

Raw TCP first (not a full query) deliberately isolates "can I route to the port"
from "are my driver/credentials right" — two failure modes that must not be
conflated when reading the result.

### How to run it (when you have AWS creds)

```bash
cd clients/trials/loopcapital/sandbox/eval
uv add bedrock-agentcore boto3          # or pip install
export AWS_REGION=us-east-1

python sandbox_reachability_spike.py --probe 1      # sanity
python sandbox_reachability_spike.py --probe 2      # needs SPIKE_DB_HOST/PORT (public)

# Probe 3 — the decisive one. Needs a private target + the VPC wiring:
export SPIKE_DB_HOST=<private-warehouse-host> SPIKE_DB_PORT=1433
export SPIKE_VPC_SUBNETS=subnet-aaa,subnet-bbb
export SPIKE_VPC_SECURITY_GROUPS=sg-ccc         # SG must allow egress to the db port
export SPIKE_EXECUTION_ROLE_ARN=arn:aws:iam::<acct>:role/<role>
python sandbox_reachability_spike.py --probe 3
```

Exit `0` = reachable (viable). Exit `1` = not reachable (records the failure
mode). Exit `2` = prerequisites missing (not a reachability result).

### What each Probe-3 outcome means for the build

- **PASS** → the sandbox approach is viable end-to-end. Proceed to build the
  `DiagnosticSandbox` READ_ONLY adapter (spec §2) on AgentCore Code Interpreter,
  VPC mode, scoped execution role per workspace (Invariant 11).
- **FAIL** → do **not** build investigation-in-sandbox against BYOW sources on
  this path. Fall back: investigate via the **existing `WarehouseTool`
  connection** (which already reaches the warehouse), and scope the sandbox to
  **compute-only** (`SANDBOX` mode — transform/analyze data handed to it, never
  reach the live DB). The remediation decision core we already shipped is
  unaffected either way — it runs *after* investigation, on the diagnosis,
  wherever that diagnosis came from.

## Bottom line

The deciding factor is **decided at the architecture level: YES, it can reach a
customer warehouse (VPC mode).** The remaining step is a ~1-hour live spike to
confirm it against real infra and shake out VPC/SG/role wiring — not a research
question, a verification. Everything downstream (the investigation adapter, then
the already-built retry/gate/fix-memory decision core) is unblocked the moment
Probe 3 goes green.
