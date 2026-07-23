# Sandbox Reachability — the deciding factor for agentic remediation

> **Question:** can an AgentCore Code Interpreter (the "computer" we'd give
> BrightAgent) actually reach a customer's warehouse to run an investigative
> query? If no, the whole "investigate a novel failure in a sandbox" approach
> collapses and investigation must go through the existing warehouse connection
> instead. This is the single unknown everything above the investigation layer
> rests on.
>
> **Date:** 2026-07-23 · **Status:** architecturally CONFIRMED YES for AgentCore
> in general (AWS docs — VPC/PUBLIC modes exist and support it). **The SPECIFIC
> tool `brightagent_code_interpreter_tool` currently deployed is CONFIRMED
> `Security: Sandbox` mode (AWS console, screenshot) — it CANNOT reach any
> warehouse.** This is expected (it was built for a different job — sandboxing
> Airbyte connector code) and fixable by provisioning a SECOND tool in
> `Public` or `VPC` mode dedicated to investigation. See "CONFIRMED: current
> tool is SANDBOX mode" below for the exact ask.

## Live run log — first real attempt, 2026-07-23

`--probe sanity` run from the brightbot repo (real `.env`, real AWS creds) failed
with an **IAM permission error**, not a reachability result:

```
AccessDeniedException: User: arn:aws:iam::873769991712:user/brightagent-deployer
is not authorized to perform: bedrock-agentcore:StartCodeInterpreterSession on
resource: arn:aws:bedrock-agentcore:us-east-1:873769991712:code-interpreter-custom/
brightagent_code_interpreter_tool-pKSS3YdeSV because no identity-based policy
allows the bedrock-agentcore:StartCodeInterpreterSession action
```

**What this means:** the credentials are valid and the tool ID exists — the AWS
user (`brightagent-deployer`) just has never been granted permission to *start a
session* on this specific Code Interpreter resource. This is a known, one-line
IAM fix, not evidence against the approach — the SANDBOX-vs-PUBLIC-vs-VPC
network-mode question this probe was designed to test is **still open**,
because the call failed one step earlier than that.

**Fix needed (someone with IAM admin on account `873769991712`):** attach a
policy granting `brightagent-deployer` (or whatever role/user brightbot's `.env`
resolves to) these actions on that resource ARN:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "bedrock-agentcore:StartCodeInterpreterSession",
      "bedrock-agentcore:InvokeCodeInterpreter",
      "bedrock-agentcore:StopCodeInterpreterSession",
      "bedrock-agentcore:GetCodeInterpreterSession"
    ],
    "Resource": "arn:aws:bedrock-agentcore:us-east-1:873769991712:code-interpreter-custom/brightagent_code_interpreter_tool-pKSS3YdeSV"
  }]
}
```

**Next step once fixed:** re-run the identical `--probe sanity` command with no
code changes. If it then reports `reached_internet: true`, proceed to
`--probe snowflake` / `redshift` / `dbt`. If it reports `status: success` but
`reached_internet: false`, that's the SANDBOX-network-mode hypothesis confirmed
— see "Use brightbot's own sandbox" below for what that implies.

## CONFIRMED: the current tool is `Security: Sandbox` mode — cannot reach any warehouse

**2026-07-23, later — confirmed directly from the AWS console (not inferred from
a docstring anymore):**

```
Name:                 brightagent_code_interpreter_tool
IAM role:             brightagent_amazon_bedrock_code_interpreter_s3
Status:               Ready
Security:             Sandbox
Tool resource ARN:    arn:aws:bedrock-agentcore:us-east-1:873769991712:
                       code-interpreter-custom/brightagent_code_interpreter_tool-pKSS3YdeSV
```

`Security: Sandbox` is the console's label for AWS's `SANDBOX` network mode
(no internet, no VPC — S3/DNS only). **This settles the open question: the
tool as currently deployed cannot reach Snowflake, Redshift, or dbt Cloud, full
stop — regardless of the IAM fix above.** This is not a flaw; it's the correct,
intentionally-locked-down mode for the job this tool was ACTUALLY provisioned
for (sandboxing untrusted Airbyte connector code — see
`tests/integration/test_connector_sandbox_integration.py`). It was never meant
to reach a live warehouse, and doing so would be a real security regression for
that existing use case if "fixed" by loosening it.

**The correct fix is a SECOND, dedicated Code Interpreter tool, not
reconfiguring this one:**

| For | Needs | Notes |
|---|---|---|
| Snowflake + dbt Cloud | a NEW tool with `Security: Public` | Both are SaaS reached over the internet — no VPC needed |
| Redshift | a NEW tool with `Security: VPC` + subnets/SG that reach the cluster | Redshift is AWS-hosted; may be cross-account (see the cross-account note in the script's docstring) — confirm with whoever owns that account before requesting subnets |

**The exact ask for whoever has AWS console access (Ahmed, per this org's
infra split):**

1. Create a new AgentCore Code Interpreter (console: Bedrock → AgentCore →
   Code Interpreter → Create), name it something like
   `brightagent_investigation_sandbox`, **Security = Public**.
2. Attach an execution role with least-privilege access (no need to reuse
   `brightagent_amazon_bedrock_code_interpreter_s3` — that role is scoped for
   the S3/Airbyte job).
3. Grant the same `brightagent-deployer` (or whichever principal) IAM actions
   as above (Start/Invoke/Stop/GetCodeInterpreterSession), scoped to the NEW
   tool's ARN.
4. Share the new tool ID back — test with it via a NEW env var (don't overwrite
   `BRIGHTAGENT_CODE_INTERPRETER_TOOL_ID`, which the Airbyte sandboxing feature
   depends on) — e.g. `SPIKE_INVESTIGATION_TOOL_ID`.
5. If Redshift is in scope too, a second `Security = VPC` tool (or the same
   Public tool won't work for a private-network Redshift — confirm which
   applies before assuming Public covers it).

Once that new tool ID exists, the probes need one small code change (pointing
at the new tool ID instead of the default) — flag this back and it'll be made.

## Use brightbot's own sandbox, not a new one

**Don't build a fresh AgentCore setup for this.** `brightbot/utils/sandbox_utils.py`
already has `invoke_bedrock_code_interpreter()` — a working, tested function
wired to real credentials ALREADY in brightbot's `.env`
(`AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
`BRIGHTAGENT_CODE_INTERPRETER_TOOL_ID`). A passing integration test
(`tests/integration/test_connector_sandbox_integration.py`) proves that exact
tool ID already executes Python and shell commands successfully — installing
`airbyte-cdk`, running shell setup, base64 round-trips. **The "does the sandbox
even work" question is already answered: yes, and has been for a while.**

**The open question this raises, found by reading `agent_tools/sandbox_tools.py`'s
own tool docstring (not assumed):**

> "Runs in a sandboxed Linux environment with **limited network access (S3 and
> DNS only)**." / "Network: Only S3 and DNS access (no general internet)"

That phrasing matches AWS's **`SANDBOX`** network mode — no internet, no VPC.
**If that's what the currently-configured `BRIGHTAGENT_CODE_INTERPRETER_TOOL_ID`
actually is, it CANNOT reach Snowflake, Redshift, or dbt Cloud today — not
because of bad credentials, but because the network mode itself blocks
outbound reach.** This was written for a different use case (sandboxing Airbyte
connectors, which only needs S3+DNS) and has never been tested against a real
warehouse. It's an inference from a docstring, not a confirmed fact — the new
script below tests it directly.

**Use `brightbot_sandbox_reachability.py`** (not `sandbox_reachability_spike.py`
below, which builds its own boto3 client from scratch) — it calls the real,
already-tested brightbot function directly, reusing its workspace-scoped
credential resolution (STS cross-account role assumption) instead of
reinventing it. Run FROM the brightbot repo so its `.env` loads:

```bash
cd brightbot
uv run python ../agentic-project-mgmt/clients/trials/loopcapital/sandbox/eval/brightbot_sandbox_reachability.py --probe sanity
```

If `sanity` reports `reached_internet: false` while `status: success` — that
CONFIRMS the SANDBOX-mode hypothesis, and the fix is reconfiguring
`BRIGHTAGENT_CODE_INTERPRETER_TOOL_ID` (or provisioning a second, PUBLIC/VPC-mode
Code Interpreter dedicated to investigation) before probes 4/5/6 mean anything.
If `sanity` passes, proceed straight to `--probe snowflake` / `redshift` / `dbt`.

## The architectural answer (AWS docs): a suitable network mode EXISTS

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

## Credentials — two separate surfaces, don't conflate them

**(1) AWS credentials — to create/run the sandbox itself** (infra-level, not
per-warehouse):

| What | Why |
|---|---|
| AWS account + region with Bedrock AgentCore enabled | Where the sandbox runs |
| IAM principal with `bedrock-agentcore:CreateCodeInterpreter`/`StartCodeInterpreterSession`/`InvokeCodeInterpreter`/`StopCodeInterpreterSession`/`GetCodeInterpreter`/`DeleteCodeInterpreter` | To create + drive the spike |
| An **execution role** (`SPIKE_EXECUTION_ROLE_ARN`) trusting `bedrock-agentcore.amazonaws.com` | What the sandbox itself runs as once inside |
| For VPC mode: **subnet + security group IDs** with a network path to the warehouse | Not a credential, but the SG must allow egress to the db port or nothing below works |

**(2) Warehouse credentials — to query Snowflake/Redshift/dbt once inside.**
brightbot already has all three in Secrets Manager, in these exact shapes
(confirmed by reading the real connection code) — the spike's probes 4-6 use
the SAME field names, so this is a drop-in test against real staging secrets:

| Target | Real brightbot source | Required fields |
|---|---|---|
| Snowflake | workspace secret `{warehouses: {[id]: {...}}}`, read by `SnowflakeConnection.connect()` (`warehouse_connections.py:801-820`) | `account`, `user`/`username`, `password`; optional `warehouse`, `database`, `schema`, `role` |
| Redshift | same shape, `RedshiftConnection.connect()` | `host`, `database`, `port` (default 5439), `user`, `password` |
| dbt Cloud | Secrets Manager `dbt/cloud-api/{service_id}` (`credentials_tools.py`) | `apiToken`, `accountId`, optional `apiEndpoint` |

**Important distinction dbt makes clear:** dbt Cloud is a SaaS HTTPS API
(`cloud.getdbt.com`), not a private customer resource — reaching it is a
**PUBLIC**-mode question (does the sandbox have internet egress), not a VPC
question. Snowflake/Redshift ARE typically private-network resources — those
need **VPC** mode. Don't test dbt in VPC mode; it's the wrong mode for that
target and would give a misleading pass/fail.

## The empirical confirmation: `sandbox_reachability_spike.py`

The docs prove it's *supported*; the spike proves it *works for us*, end to end,
and measures the exact failure mode if it doesn't. It cannot run in this repo's
offline env (needs real AWS creds + the `bedrock-agentcore` SDK) — by design it
is a **live spike, not a unit test**. It is written, parses, and handles missing
prerequisites correctly (exits 2 = "couldn't run", never a false pass/fail).

Six probes — 1-3 are generic TCP/internet checks; **4-6 are the real
per-warehouse tests**, using the exact credential shapes from the table above:

| Probe | Mode | Target | Proves |
|---|---|---|---|
| 1 | PUBLIC | — | sandbox executes code + has internet egress at all (cheapest sanity) |
| 2 | PUBLIC | generic | TCP to a **publicly-reachable** db host:port (driver + egress path work) |
| 3 | **VPC** | generic | **DECISIVE (generic):** TCP to a **private** db host:port — the customer-BYOW shape |
| 4 | **VPC** | **Snowflake** | real `snowflake.connector.connect(...)` + `SELECT 1` inside the sandbox |
| 5 | **VPC** | **Redshift** | real `psycopg2.connect(...)` + `SELECT 1` inside the sandbox |
| 6 | PUBLIC | **dbt Cloud** | authenticated HTTPS GET against the real dbt Cloud Admin API |

Raw TCP first (probes 2/3, before 4/5's real driver connect) deliberately
isolates "can I route to the port" from "are my driver/credentials right" — two
failure modes that must not be conflated when reading a result. Note probe 6 is
correctly **PUBLIC**, not VPC — see the credentials note above.

### How to run it (when you have AWS creds)

```bash
cd clients/trials/loopcapital/sandbox/eval
uv add bedrock-agentcore boto3          # or pip install
export AWS_REGION=us-east-1
export SPIKE_EXECUTION_ROLE_ARN=arn:aws:iam::<acct>:role/<role>

python sandbox_reachability_spike.py --probe 1      # sanity
python sandbox_reachability_spike.py --probe 2      # needs SPIKE_DB_HOST/PORT (public)

# Probe 3 — generic decisive one. Needs a private target + the VPC wiring:
export SPIKE_DB_HOST=<private-warehouse-host> SPIKE_DB_PORT=1433
export SPIKE_VPC_SUBNETS=subnet-aaa,subnet-bbb
export SPIKE_VPC_SECURITY_GROUPS=sg-ccc         # SG must allow egress to the db port
python sandbox_reachability_spike.py --probe 3

# Probe 4 — Snowflake (VPC). Use the REAL staging secret's values, never hardcode:
export SPIKE_SF_ACCOUNT=ab12345.us-east-1 SPIKE_SF_USER=... SPIKE_SF_PASSWORD=...
export SPIKE_SF_WAREHOUSE=... SPIKE_SF_DATABASE=... SPIKE_SF_SCHEMA=... SPIKE_SF_ROLE=...
python sandbox_reachability_spike.py --probe 4

# Probe 5 — Redshift (VPC):
export SPIKE_RS_HOST=... SPIKE_RS_PORT=5439 SPIKE_RS_DATABASE=... SPIKE_RS_USER=... SPIKE_RS_PASSWORD=...
python sandbox_reachability_spike.py --probe 5

# Probe 6 — dbt Cloud (PUBLIC — it's a SaaS API, not a private resource):
export SPIKE_DBT_API_TOKEN=... SPIKE_DBT_ACCOUNT_ID=...
python sandbox_reachability_spike.py --probe 6
```

Exit `0` = reachable (viable). Exit `1` = not reachable (records the failure
mode). Exit `2` = prerequisites missing (not a reachability result). Secrets
are read from env only and never printed — only pass/fail + sanitized error
text (exception type + message) crosses back out of the sandbox.

### What the outcomes mean for the build

- **PASS on 3/4/5** → the sandbox approach is viable end-to-end for that
  warehouse. Proceed to build the `DiagnosticSandbox` READ_ONLY adapter (spec §2)
  on AgentCore Code Interpreter, VPC mode, scoped execution role per workspace
  (Invariant 11).
- **FAIL on 3, but 4/5 pass** → the generic TCP probe used the wrong host/port
  for this environment; trust 4/5 (the real per-warehouse drivers) over the
  generic probe.
- **FAIL on 4 or 5 specifically** → read the error text: a driver-not-installed
  error means bake the driver into the sandbox's runtime image, not a
  reachability problem; a network/timeout error means the VPC/SG wiring doesn't
  route to that warehouse yet; an auth error means the credentials are wrong,
  not the network path. Each is a different fix — don't conflate them.
- **FAIL on 3/4/5 categorically (network)** → do **not** build
  investigation-in-sandbox against BYOW sources on this path. Fall back:
  investigate via the **existing `WarehouseTool` connection** (which already
  reaches the warehouse), and scope the sandbox to **compute-only** (`SANDBOX`
  mode). The remediation decision core we already shipped is unaffected either
  way — it runs *after* investigation, on the diagnosis, wherever that came from.
- **Probe 6 (dbt) is independent of 3/4/5** — dbt Cloud is a SaaS API reached
  over PUBLIC egress, not the VPC. A FAIL here is a token/account_id/egress
  issue, never a VPC wiring issue.

## Bottom line

The deciding factor is **decided at the architecture level: YES, it can reach a
customer warehouse (VPC mode) and dbt Cloud's API (PUBLIC mode).** The remaining
step is a live spike (~1-2 hours across all 6 probes) to confirm it against real
staging infra/secrets and shake out VPC/SG/role wiring — not a research
question, a verification. Everything downstream (the investigation adapter, then
the already-built retry/gate/fix-memory decision core) is unblocked the moment
probes 3/4/5/6 go green.
