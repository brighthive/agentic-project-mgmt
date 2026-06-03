---
title: "Longaeva trial guide — verbose technical prep (paste-back content)"
client: longaeva
related_doc: "https://docs.google.com/document/d/1zfStzSxMsim4cfy_yvKDu4vuFuPh0Ern6CFWfCIB9t4"
related_epic: BH-526
created: "2026-06-03"
last_reviewed: "2026-06-04"
---

# Longaeva Trial Guide — verbose technical prep

> **Purpose**: replace the prep sections of the Longaeva trial guide with content at the depth of the existing "Automated Deployment via AWS CDK" section, so Longaeva's DevOps / Platform / SecEng teams can actually prepare deliverables before Day 1 — not just nod along.
>
> Each section below is intended to be pasted directly into the Google Doc in place of its current bullet-only treatment. Headings match the doc's heading levels.

---

## GitHub Enterprise Access & Source Code Integration

To initiate the integration, our automated dbt engineering agent (BrightAgent) needs secure, scoped access to your GitHub Enterprise (GHE) environment. The agent functions as an active contributor — it reads existing dbt models, generates new SQL/YAML, opens feature branches, and submits Pull Requests for your engineers to review. All write operations are reviewable; nothing the agent does is auto-merged.

To establish this connection safely and avoid blockers on Day 1, your team should prepare the following in advance.

### 1. GitHub Enterprise authentication

Choose **one** of the following authentication models. We recommend (a) in order of preference.

**(a) GitHub App (preferred — production posture)**

Create a private GitHub App within your GHE organization (`Settings → Developer settings → GitHub Apps → New GitHub App`).

| Setting | Value / Guidance |
|---|---|
| App name | `brighthive-brightagent-trial` |
| Homepage URL | `https://brighthive.io` |
| Webhook | **Disabled** for trial (we poll on demand) |
| Repository access | **Only select repositories** — scope to the dbt repo only |
| Account permissions | None |
| Repository permissions | `Contents: Read & write`, `Pull requests: Read & write`, `Metadata: Read-only`, `Commit statuses: Read-only` |

After creation:
- Generate a **private key (PEM)** — download once, store in your secrets vault, share with BrightHive via 1Password / shared encrypted channel
- Note the **App ID** and **Installation ID** (visible after installing the App on your org)
- Install the App, restricting installation to the targeted dbt repository only

**(b) OAuth App (acceptable — interactive grant)**

Suitable if your security policy prefers user-delegated access over machine identity.
- Create OAuth App in `Settings → Developer settings → OAuth Apps`
- Authorization callback URL: `https://app.brighthive.io/oauth/github/callback` (we will provide the exact callback for your tenant during provisioning)
- Required scopes: `repo` (write to private repos in the targeted org), `read:org` (resolve org membership for the agent's bot user)

**(c) Fine-grained PAT (fallback — sandbox / Phase B only)**

If GitHub App provisioning is blocked by internal review, a fine-grained Personal Access Token bound to a dedicated service-account user is acceptable for the sandbox phase.
- Create on a dedicated `brighthive-agent` user (not a human's account)
- Resource owner: your dbt repo's owning org
- Repository access: **Only select repositories** → the dbt repo
- Repository permissions: `Contents: Read & write`, `Pull requests: Read & write`, `Metadata: Read-only`
- Expiration: ≤ 90 days (trial duration + buffer)

> **Important**: classic PATs (the `ghp_…` kind with org-wide scope) are not acceptable. We will refuse a classic PAT during configuration because it cannot be scoped to a single repo.

### 2. Network access — IP allowlisting

If your GHE environment is fronted by a corporate firewall, WAF, or has the GitHub-Enterprise-level "IP allow list" feature enabled, you must allowlist BrightHive's outbound egress IPs.

| Item | What we will provide | What you must do |
|---|---|---|
| Static egress NAT IP block | `/29` CIDR from our trial AWS account (provided during kickoff) | Add to your perimeter firewall + GHE IP allow list (`Enterprise settings → Authentication security → IP allow list`) |
| Source services | BrightAgent Lambdas + Bedrock Code Interpreter outbound | Tag the rule with `brighthive-trial` for audit |
| Port / protocol | HTTPS / 443 (TCP) outbound only | Inbound from BrightHive: **none required** |
| Renewal | NAT IPs are static for trial duration; re-issue if we migrate accounts | Confirm the rule survives any planned firewall maintenance window |

If your GHE is hosted at a custom hostname (e.g. `ghe.longaeva.com`), confirm:
- TLS chain — public CA (e.g. DigiCert, Sectigo) **or** internal CA (Longaeva root)?
- If internal CA: provide the root + any intermediate certs in PEM format. We bundle them into the Lambda layer via `NODE_EXTRA_CA_CERTS` (see BH-570).
- DNS — resolvable publicly, or split-horizon? If split-horizon, we will need a public CNAME or you'll need to peer to our VPC.

### 3. Repository preparation

| Requirement | Why | How to validate |
|---|---|---|
| Default branch protected | We open PRs against `main` (or your default) — direct pushes are not used | `Settings → Branches → Branch protection rules` exists on default |
| `.github/pull_request_template.md` present (if you use one) | BrightAgent populates required fields (Jira-id, description) when submitting PRs — see BH-566 | Open the file and confirm fields are explicit (e.g. `## Jira ID`, not free-form prose) |
| Required status checks documented | We surface required-check failures back to the user so they can fix locally before our PR lands | List of required checks shared with us in advance |
| CODEOWNERS configured (optional) | Auto-routes our PRs to the right reviewer | If present, ensure dbt project paths are covered |
| dbt project at repo root **or** documented subpath | The agent needs to find `dbt_project.yml` | If subpath, confirm the path during provisioning |

### 4. Scoping & blast-radius limits

By design, the trial agent's GHE access is constrained to:
- **One repository** (the dbt repo you specify)
- **Read + Pull-Request write only** (no force-push, no branch deletion outside agent-created branches, no admin operations)
- **No webhooks created from our side** (we do not subscribe to push events during trial)
- **All API traffic** routed exclusively to your GHE host — never to `api.github.com` (enforced and verified — see "Host isolation verification" below)

### 5. Host isolation verification (security claim)

Because BrightAgent supports both `github.com` and GHE customers in the same platform, we explicitly verify that **for your workspace, no API calls ever reach `api.github.com`**. This is asserted as part of our pre-trial smoke (Phase A, scenario S5):

```
For every BrightAgent run against your workspace:
  • All GitHub API spans have gen_ai.tool.github.host = <your GHE host>
  • CloudWatch log-analytics query `filter @message like /api.github.com/`
    over the run window returns zero rows
```

We provide a copy of this evidence on request before Day 1 and at trial close.

### 6. What we need from you to start

A pre-trial checklist your team can run against — every "yes" unblocks one stage of integration:

- [ ] GHE host URL (e.g. `https://ghe.longaeva.com`)
- [ ] dbt repository URL (full HTTPS clone URL)
- [ ] Authentication artifact (GitHub App private key + App ID + Installation ID, **or** OAuth client_id+secret, **or** fine-grained PAT)
- [ ] TLS chain confirmation (public CA vs internal — and PEM bundle if internal)
- [ ] BrightHive egress IPs added to your allow list (confirmation email sufficient)
- [ ] Confirmation that one round-trip (clone → branch → commit → PR) works for a human user with the same identity model we'll use

---

## Snowflake Data Warehouse Access & Service Accounts

To allow BrightHive to interact securely with your data products, we require two distinct Snowflake service accounts, each scoped under the principle of least privilege. These are **not** human-shared accounts — they are dedicated machine identities that should be created fresh, never reusing existing tooling accounts.

### 1. Read-only service account (metadata + ingestion)

**Identity**

```sql
-- Create the role + user — adjust warehouse to your trial-sized WH
CREATE ROLE BRIGHTHIVE_READER_ROLE;

CREATE USER BRIGHTHIVE_READER
  RSA_PUBLIC_KEY = '<provided by BrightHive — see Key-pair auth below>'
  DEFAULT_ROLE   = BRIGHTHIVE_READER_ROLE
  DEFAULT_WAREHOUSE = BRIGHTHIVE_TRIAL_WH
  MUST_CHANGE_PASSWORD = FALSE
  COMMENT = 'BrightHive trial — read-only metadata + ingestion';

GRANT ROLE BRIGHTHIVE_READER_ROLE TO USER BRIGHTHIVE_READER;
```

**Privileges**

```sql
-- Warehouse
GRANT USAGE ON WAREHOUSE BRIGHTHIVE_TRIAL_WH TO ROLE BRIGHTHIVE_READER_ROLE;

-- Database + schemas (repeat per database in scope)
GRANT USAGE ON DATABASE <DB_NAME> TO ROLE BRIGHTHIVE_READER_ROLE;
GRANT USAGE ON ALL SCHEMAS IN DATABASE <DB_NAME> TO ROLE BRIGHTHIVE_READER_ROLE;
GRANT USAGE ON FUTURE SCHEMAS IN DATABASE <DB_NAME> TO ROLE BRIGHTHIVE_READER_ROLE;

-- Object-level (tables + views)
GRANT SELECT ON ALL TABLES IN DATABASE <DB_NAME> TO ROLE BRIGHTHIVE_READER_ROLE;
GRANT SELECT ON ALL VIEWS  IN DATABASE <DB_NAME> TO ROLE BRIGHTHIVE_READER_ROLE;
GRANT SELECT ON FUTURE TABLES IN DATABASE <DB_NAME> TO ROLE BRIGHTHIVE_READER_ROLE;
GRANT SELECT ON FUTURE VIEWS  IN DATABASE <DB_NAME> TO ROLE BRIGHTHIVE_READER_ROLE;

-- Semantic views (required for MCP discover/describe protocol)
GRANT REFERENCES ON ALL SEMANTIC VIEWS IN DATABASE <DB_NAME> TO ROLE BRIGHTHIVE_READER_ROLE;

-- Account-level — required for OpenMetadata lineage discovery
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE BRIGHTHIVE_READER_ROLE;
```

The `SNOWFLAKE` shared database grant is what allows OpenMetadata to read `ACCOUNT_USAGE.ACCESS_HISTORY` for lineage. If your security policy forbids it, we degrade gracefully (no column-level lineage); flag this explicitly during provisioning.

**Usage**: this account is used by (a) OpenMetadata for schema + lineage scanning and (b) BrightAgent for SELECT-only query execution during MCP downstream validation.

### 2. Scoped write/execution account (dbt engineering agent)

**Identity**

```sql
CREATE ROLE BRIGHTHIVE_DBT_ROLE;

CREATE USER BRIGHTHIVE_DBT
  RSA_PUBLIC_KEY = '<provided by BrightHive>'
  DEFAULT_ROLE = BRIGHTHIVE_DBT_ROLE
  DEFAULT_WAREHOUSE = BRIGHTHIVE_TRIAL_WH
  COMMENT = 'BrightHive trial — dbt agent write/execute on staging schemas only';

GRANT ROLE BRIGHTHIVE_DBT_ROLE TO USER BRIGHTHIVE_DBT;
```

**Privileges** — scoped to staging/target schemas only, never to raw or production data:

```sql
GRANT USAGE ON WAREHOUSE BRIGHTHIVE_TRIAL_WH TO ROLE BRIGHTHIVE_DBT_ROLE;

GRANT USAGE ON DATABASE <DBT_TARGET_DB> TO ROLE BRIGHTHIVE_DBT_ROLE;

-- Staging / dev schemas only — confirm names with us at provisioning
GRANT ALL PRIVILEGES ON SCHEMA <DBT_TARGET_DB>.BRIGHTHIVE_STAGING TO ROLE BRIGHTHIVE_DBT_ROLE;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA <DBT_TARGET_DB>.BRIGHTHIVE_STAGING TO ROLE BRIGHTHIVE_DBT_ROLE;
GRANT ALL PRIVILEGES ON FUTURE VIEWS  IN SCHEMA <DBT_TARGET_DB>.BRIGHTHIVE_STAGING TO ROLE BRIGHTHIVE_DBT_ROLE;

-- Read sources required to materialize models
GRANT USAGE ON SCHEMA <SOURCE_DB>.<SOURCE_SCHEMA> TO ROLE BRIGHTHIVE_DBT_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA <SOURCE_DB>.<SOURCE_SCHEMA> TO ROLE BRIGHTHIVE_DBT_ROLE;
```

**Hard boundary**: this role is intentionally not granted on raw, production, or PII-tagged schemas. The agent cannot accidentally write to production because it has no privilege to do so — verified by `SHOW GRANTS TO ROLE BRIGHTHIVE_DBT_ROLE`.

### 3. Key-pair authentication (required — no password auth)

We do **not** authenticate with passwords for service accounts. BrightHive generates a 2048-bit RSA keypair per service account; we share the **public key** for you to paste into the `RSA_PUBLIC_KEY` attribute above. The private key remains in AWS Secrets Manager on our side, with rotation every 90 days.

```sql
-- Validate the public key was applied correctly:
DESCRIBE USER BRIGHTHIVE_READER;
-- Look for the RSA_PUBLIC_KEY_FP field
```

### 4. Network access — Snowflake side

If your account uses a network policy:

```sql
ALTER NETWORK POLICY <YOUR_POLICY>
  SET ALLOWED_IP_LIST = (... existing ips ..., '<brighthive /29>');
```

Confirm with `SHOW NETWORK POLICIES;` then `DESCRIBE NETWORK POLICY <name>;` that our CIDR is present.

If you use PrivateLink to Snowflake and want us to route the same way, this is a paid Snowflake feature and adds 1–2 days of provisioning. Confirm at kickoff.

### 5. Query tagging (audit trail)

Every BrightAgent query is tagged with `QUERY_TAG = 'brighthive:trial:<workspace_id>:<run_id>'` so your team can filter the query history independently of our spans:

```sql
SELECT query_id, query_text, total_elapsed_time
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE query_tag LIKE 'brighthive:trial:%'
  AND start_time >= DATEADD(day, -1, CURRENT_TIMESTAMP)
ORDER BY start_time DESC;
```

### 6. What we need from you

- [ ] Account identifier (`<org>-<account>` format)
- [ ] Region + cloud (e.g. `AWS us-east-1`)
- [ ] Confirmation that the two SQL blocks above were executed (or your team's equivalent)
- [ ] `SHOW GRANTS TO ROLE BRIGHTHIVE_READER_ROLE;` output (paste in a private channel)
- [ ] Same for `BRIGHTHIVE_DBT_ROLE`
- [ ] Confirmation that key-pair auth works (we'll send a 1-line connectivity test)
- [ ] Network policy name (if any) + confirmation our CIDR was added

---

## BrightAgent Infrastructure & Execution Environment (AWS)

BrightAgent operates within your AWS account using a **cross-account assume-role** model — no static credentials are stored on our side. The execution environment is composed of (1) an Amazon Bedrock Code Interpreter for ephemeral compute, (2) a scoped S3 bucket for persistent artifacts, and (3) a tightly scoped IAM trust policy. All three are deployed by our CDK package (next section).

### 1. AWS account & region selection

Decide before Day 1:
- **AWS account**: a dedicated sub-account is preferred (cleanest blast-radius boundary). If reusing an existing account, isolate via tagging (`brighthive:trial = true` on every resource) and a dedicated OU if your Org policy supports it.
- **Region**: must be a region where **all three** services are GA — Amazon Bedrock (with Claude 4.x model access), Bedrock AgentCore, and Bedrock Code Interpreter. We default to `us-east-1`. Confirm Bedrock model access is enabled in the target region:

```bash
aws bedrock list-foundation-models --region us-east-1 \
  --query 'modelSummaries[?contains(modelId, `claude-opus`)].modelId'
```

If empty, request access in the Bedrock console: `Model access → Manage access → Anthropic Claude Opus 4.x`.

### 2. Amazon Bedrock Code Interpreter (sandbox)

**What it is**: an AWS-managed, ephemeral container provided by Bedrock AgentCore. When BrightAgent needs to execute Python (data shaping, profile-stats validation, plotting), it sends code to this sandbox. The container has no persistent disk, no network egress to your VPC, and is destroyed at the end of each invocation.

**Service quotas to verify before Day 1** (region defaults shown — request increases ahead of time if your trial scope exceeds these):

| Quota | Default | Recommended for trial |
|---|---|---|
| Concurrent Code Interpreter sessions | 10 | 25 |
| Bedrock model invocations / min (Claude Opus) | 50 | 200 |
| AgentCore agent runtime instances | 5 | 10 |

Request increases via `Service Quotas console → Amazon Bedrock`.

**Cost**: pay-per-second of compute + Bedrock model token cost. We provide a daily cost report tagged to `brighthive:trial`.

### 3. Amazon S3 bucket (filesystem)

A dedicated S3 bucket serves as BrightAgent's persistent filesystem for session artifacts, generated code packages, intermediate DataFrames, and execution logs. Created by the CDK stack with the following posture:

| Setting | Value | Reason |
|---|---|---|
| Bucket name | `brighthive-trial-<account-id>-<region>` | Unique, predictable |
| Block all public access | **On** (all 4 sub-settings) | No public exposure |
| Encryption | SSE-KMS with customer-managed key | You hold the key; we use it via grant |
| Versioning | Enabled | Auditability + accidental-delete protection |
| Lifecycle | Objects → IA at 30 days, expire at 90 days | Trial-bounded retention |
| Object Lock | Off | (Enable post-trial if you retain artifacts long-term) |
| Logging | Server access logs → separate `…-logs` bucket | Audit who-did-what |
| Tags | `brighthive:trial=true`, `brighthive:client=longaeva` | Cost allocation |

**Why a customer-managed KMS key**: it gives you a one-click revocation path. If you ever need to instantly cut BrightHive's access, deny the key — every artifact becomes unreadable to us within minutes, without touching IAM.

### 4. IAM roles & cross-account trust

We use the standard cross-account assume-role pattern. **No static access keys are issued.**

**Role 1 — `BrightHiveAgentExecutionRole`** (assumed by our Bedrock AgentCore)

Trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "AWS": "arn:aws:iam::<brighthive-account-id>:role/brighthive-prod-agent-runtime" },
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": { "sts:ExternalId": "<unique-per-trial-external-id>" }
    }
  }]
}
```

Permissions (managed by the CDK stack):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvoke",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock-agent-runtime:InvokeAgent",
        "bedrock-agent-runtime:InvokeCodeInterpreter"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3ArtifactBucket",
      "Effect": "Allow",
      "Action": ["s3:GetObject","s3:PutObject","s3:DeleteObject","s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::brighthive-trial-<acct>-<region>",
        "arn:aws:s3:::brighthive-trial-<acct>-<region>/*"
      ]
    },
    {
      "Sid": "KMSForArtifactKey",
      "Effect": "Allow",
      "Action": ["kms:Decrypt","kms:GenerateDataKey"],
      "Resource": "arn:aws:kms:<region>:<acct>:key/<key-id>"
    }
  ]
}
```

**Important constraints**:
- The `ExternalId` is unique per trial and rotated at trial close — defends against the confused-deputy class of attacks
- No `iam:*`, `ec2:*`, `lambda:*`, or `secretsmanager:*` permissions are granted to the execution role
- No wildcards on resources except for Bedrock (where the model ARN is bounded by region + model-access settings)

**Revocation**: detach `BrightHiveAgentExecutionRole`'s trust policy, **or** disable the `ExternalId`. Either cuts our access within ~1 minute (STS token TTL).

### 5. CloudWatch + observability

Every BrightAgent run emits OpenTelemetry GenAI spans (`gen_ai.tool.*`, `gen_ai.completion.*`) into CloudWatch Logs in **your** account. The retention is configured by the CDK stack (default 90 days). You see exactly what the agent did, when, against which resource — with no involvement from BrightHive needed to audit.

Two log groups are created:
- `/aws/brighthive/agent/<workspace>` — agent-level spans + LLM completions
- `/aws/brighthive/code-interpreter/<workspace>` — Code Interpreter stdout/stderr

A pre-built CloudWatch Insights query for audit is included in the CDK package:

```
fields @timestamp, gen_ai.tool.name, gen_ai.request.model, brightagent.workspace.id
| filter ispresent(gen_ai.tool.name)
| stats count(*) by gen_ai.tool.name
| sort count desc
```

### 6. What we need from you

- [ ] Target AWS account ID + region
- [ ] Confirmation that Bedrock model access for Claude Opus 4.x is enabled in that region
- [ ] VPC ID + subnet IDs (private for OMD compute, public for ALB — see OMD section)
- [ ] Service quota increases requested (or confirmation defaults are enough)
- [ ] Whether you'll provide the customer-managed KMS key, or have CDK create one in your account
- [ ] Acceptable CloudWatch log retention period (default 90 days)

---

## Metadata Management — OpenMetadata (OMD)

The OpenMetadata instance is the metadata-and-lineage spine for the trial. It scans your Snowflake account, emits webhook events to a BrightHive-owned Lambda on every schema change, runs PII detection on sampled data, and serves as the authoritative source for what BrightAgent thinks your warehouse looks like.

### 1. Network architecture

The CDK package deploys OMD in this topology — your team controls the VPC/subnet inputs:

```
Internet
   │
   ▼
[Application Load Balancer]  ◀── public subnets, internet-facing
   │  (HTTPS:443, ACM cert)
   ▼
[EC2 instance — OMD server]  ◀── private subnet, no public IP
   │
   ├── Snowflake (egress via NAT)
   ├── Metadata DB (RDS in same VPC, private)
   └── ElasticSearch / OpenSearch (managed, private)
```

**You must provide**:

| Input | Description | Where to find |
|---|---|---|
| `vpc_id` | The VPC OMD will deploy into | AWS Console → VPC |
| `public_subnet_ids` | At least 2 public subnets in distinct AZs (for ALB) | Must have IGW routing |
| `private_subnet_ids` | At least 2 private subnets in distinct AZs (for EC2 + RDS) | Must have NAT egress for Snowflake calls |
| `acm_certificate_arn` | ACM cert for the OMD hostname (e.g. `omd.longaeva-trial.com`) | ACM in same region |
| `route53_hosted_zone_id` (optional) | If we should create the DNS record for you | Else you create it manually post-deploy |

The CDK package validates these inputs before any resource is created — invalid VPC inputs fail at synth time, not at deploy time.

### 2. Compute sizing

| Component | Default | Notes |
|---|---|---|
| EC2 instance type | `t3.large` (2 vCPU / 8 GB) | Sufficient for trial; bump to `m5.xlarge` if catalog > 10k tables |
| RDS engine + size | PostgreSQL 15, `db.t3.medium` | Encrypted at rest |
| OpenSearch | 1 node, `t3.small.search` | Single-AZ for trial; multi-AZ for production |
| Storage | gp3 EBS, 100 GB | Auto-expands via CloudWatch alarm |

### 3. Snowflake connector configuration

The CDK deploys OMD pre-configured with the Snowflake connector. After first boot, OMD pulls credentials from AWS Secrets Manager — we populate the secret using the read-only service account you created in the Snowflake section.

Default scan schedule:

| Pipeline | Frequency | What it does |
|---|---|---|
| Metadata ingestion | Every 6h | Refresh table/column metadata, schema drift detection |
| Lineage | Every 12h | Parse `ACCESS_HISTORY` for upstream/downstream relationships |
| Profiler | Daily, off-peak | Row counts, null %, min/max, distinct counts |
| PII detection | Daily, off-peak | Sample-based regex + NLP scan (see below) |
| Usage | Hourly | Most-queried tables, popular columns |

Frequencies are tunable post-deploy via the OMD UI; defaults are calibrated for trial scope (10s of schemas).

### 4. Webhook → BrightHive change-event Lambda

OMD emits webhook events on every schema change (tables created, columns added/removed, types changed, etc.) to a Lambda function in the same account. The Lambda relays to BrightHive's platform via signed cross-account API call, which then triggers a re-embed of the changed surfaces.

- Webhook URL: pre-populated by CDK at deploy time
- Webhook secret: generated by CDK, stored in Secrets Manager, used for HMAC verification
- Event types subscribed: `entityCreated`, `entityUpdated`, `entitySoftDeleted` for `table`, `databaseSchema`, `dashboard`
- Retry policy: 3 attempts with exponential backoff; DLQ → SQS queue for inspection

### 5. PII detection

OMD's PII scanner samples up to 100 rows per column and flags matches against:

- **Built-in patterns**: SSN, email, phone, credit-card, IP, address
- **Custom patterns**: Longaeva-supplied regex/keyword lists for finance-specific identifiers (CUSIP, ISIN, internal account numbers) — supply during provisioning

When a column is tagged `PII.Sensitive`, BrightAgent's tool layer enforces:
- No raw column values surface to the LLM context (only schema metadata + aggregates)
- No `SELECT *` queries return the column verbatim — substituted with `<redacted>`
- Audit log entry every time the column is referenced

### 6. Time-bound admin authentication

OMD admin tokens issued for the trial expire on the trial end date + 14 days. The CDK package emits a CloudWatch alarm 7 days before expiry. Rotation is one CLI call documented in the CDK README.

### 7. What we need from you

- [ ] VPC + subnet IDs (public + private, 2 AZs each)
- [ ] ACM cert ARN or confirmation we should provision one
- [ ] DNS approach (Route 53 hosted zone or manual record)
- [ ] Custom PII patterns (regex + descriptions)
- [ ] Backup retention window for the RDS instance (default 7 days)
- [ ] Confirmation that the `BRIGHTHIVE_READER_ROLE` (from Snowflake section) is created — OMD needs it before first boot

---

## Local CLI / SDK Installation — uv-based, reproducible

The BrightHive CLI (`brighthive`) and Python SDK are how your engineers interact with the trial environment from their laptops or CI runners — kicking off agent runs, fetching logs, validating connectivity, and exercising the MCP locally before wiring it to a host.

We standardize on **[uv](https://docs.astral.sh/uv/)** (Astral's Rust-based Python toolchain) as the supported installer. `pip` still works, but uv is faster, lockfile-aware, and avoids the global-environment pitfalls that we have repeatedly seen burn 30+ minutes during prior trials. Both paths are documented; uv is the recommended path.

### 1. Prerequisites

| Item | Required version | Check |
|---|---|---|
| Python | 3.11 or 3.12 (3.13 currently unverified for two transitive deps — pin to 3.12) | `python3 --version` |
| uv | ≥ 0.4.0 | `uv --version` |
| OS | macOS 13+, Ubuntu 22.04+, WSL2 on Windows 11 | — |

Install uv (one-time, no admin rights needed):

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via Homebrew / pipx if your team already has them
brew install uv
```

`uv` self-manages Python interpreters — you do **not** need to install Python separately. If `python3` is missing or the wrong version, uv will fetch a managed CPython on first use (`uv python install 3.12`).

### 2. Recommended path — `uv tool install` (isolated, global CLI)

This installs the BrightHive CLI into an isolated environment that uv manages on your `PATH`. The CLI works from any directory; nothing is installed into your system Python.

```bash
# Pinned release (recommended for trial)
uv tool install 'brighthive==<X.Y.Z>'

# Or track latest minor (use only if your team is comfortable with weekly updates)
uv tool install 'brighthive>=1.4,<2.0'

# Verify
brighthive --version
brighthive doctor   # one-shot connectivity + auth diagnostic
```

Upgrade later with `uv tool upgrade brighthive`. Uninstall with `uv tool uninstall brighthive`. No `sudo`, no global site-packages mutation, no virtualenv to remember to activate.

### 3. Project-embedded path — `uv add` (reproducible, lockfile-tracked)

If your team is integrating the BrightHive SDK into a repo — e.g. wiring it into your existing dbt CI or a notebook project — install via `uv add` so the dependency is captured in `pyproject.toml` + `uv.lock`. This is what we use internally and what we recommend for any code your team checks in.

```bash
# In your repo root
uv init                    # if no pyproject.toml yet
uv add 'brighthive==<X.Y.Z>'
uv sync                    # creates .venv/ and installs from the lockfile

# Run any command via uv (no need to activate the venv)
uv run brighthive doctor
uv run python -c "import brighthive; print(brighthive.__version__)"
```

`uv.lock` should be committed. It pins the full transitive graph (hashes included), so a deploy 6 months from now resolves to the exact same wheels you tested today. This is the single biggest win over `pip install -r requirements.txt`.

### 4. Pip-based path — only if uv is blocked by policy

Some enterprise security teams require packages flow through an internal mirror that does not yet support uv's fetch protocol. In that case, fall back to pip — but keep the venv discipline.

```bash
# Always use a project-local venv. Never install into the system Python.
python3.12 -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install 'brighthive==<X.Y.Z>'

brighthive --version
```

Anti-patterns we will reject during a support call:

- `sudo pip install ...` — corrupts the system interpreter
- `pip install ...` on macOS's bundled `/usr/bin/python3` — same issue, just slower to manifest
- `pip install ...` without a venv on Linux — Debian/Ubuntu now block this with PEP 668; if it works on your machine, you're using the wrong Python
- Mixing `pip` and `conda` in one environment — resolution races, undefined behavior

### 5. Internal package mirror (air-gapped or restricted networks)

If outbound to PyPI is blocked, configure uv (or pip) to point at your internal mirror. The BrightHive CLI is a normal PyPI-published wheel — any standards-compliant index works.

```bash
# uv — env vars
export UV_INDEX_URL="https://pypi.longaeva.internal/simple/"
export UV_EXTRA_INDEX_URL="https://pypi.org/simple/"   # if you allow public fallback

# uv — pyproject.toml (preferred; checked into the repo)
[tool.uv]
index-url = "https://pypi.longaeva.internal/simple/"

# pip — ~/.config/pip/pip.conf
[global]
index-url = https://pypi.longaeva.internal/simple/
```

If the BrightHive package is not yet mirrored on your index, your security team can pull `brighthive==<X.Y.Z>` (and its dependencies) from public PyPI ahead of the trial. We will provide a SHA256 manifest of the exact wheels we publish so your team can verify integrity before mirroring.

### 6. Authentication — first-run setup

After install, one-time auth to your trial workspace:

```bash
brighthive auth login --workspace <workspace-id>
# Opens a browser; OIDC device-code flow against your IdP (Okta / Azure AD / Google).
# No long-lived API tokens stored on disk by default.
```

For headless / CI use, exchange the user grant for a short-lived service token:

```bash
brighthive auth issue-service-token \
  --workspace <workspace-id> \
  --name longaeva-ci \
  --ttl 24h
# Outputs token to stdout. Inject as $BRIGHTHIVE_TOKEN; do not commit.
```

Service tokens are scoped per workspace, audit-logged on every call, and revocable from the BrightHive admin console at any time.

### 7. Verification — ten-second smoke test

```bash
brighthive doctor
# ✓ CLI version            1.X.Y
# ✓ Python                 3.12.7 (uv-managed)
# ✓ Auth                   ok (workspace=longaeva-trial, expires in 23h)
# ✓ API reachability       https://api.brighthive.io  (220 ms)
# ✓ Bedrock cross-account  arn:aws:iam::...:role/BrightHiveAgentExecutionRole  ok
# ✓ S3 artifact bucket     brighthive-trial-...  ok
# ✓ MCP echo               round-trip 180 ms
```

If any line fails, the output prints the exact next action — most failures are auth (re-run `brighthive auth login`) or network (egress to `api.brighthive.io` not yet allowlisted).

### 8. What we need from you

- [ ] Confirm Python 3.12 is allowed by your engineering laptop policy (or which version is)
- [ ] Confirm uv is permitted (else we use the pip fallback path)
- [ ] If air-gapped: hostname of the internal PyPI mirror + whether `brighthive` and its deps are pre-mirrored
- [ ] IdP for `brighthive auth login` (Okta tenant URL, Azure AD tenant ID, or Google Workspace domain)
- [ ] Whether CI service tokens are needed at trial start, or only after Day 5 once humans have validated the flow

---

## Automated Deployment — Terraform (recommended) or AWS CDK

> **Status (2026-06-04)**: Following our 2026-06-03 call, BrightHive committed to delivering a Terraform module as the primary supported deployment path for Longaeva, given your cloud team's existing Terraform fluency. The CDK path remains supported as an alternative for teams who prefer it. **The Terraform module is the recommended path for Longaeva's trial.**
>
> Both paths produce the same AWS resources, the same IAM posture, and the same OMD topology — they are functionally equivalent. The choice is purely about which IaC framework your platform team operates day-to-day.

This section is the operator's reference for both paths. Run through whichever you'll use once before the live deployment so the actual deploy is uneventful.

### Path A — Terraform module (recommended)

#### Distribution

The BrightHive Terraform module is published to a private registry that your team gets credentialed access to during kickoff. It is **not** copy-pasted source code — it is a versioned module you reference by source URL, pin to a tag, and `terraform get` against, exactly like any HashiCorp / community module.

```hcl
# longaeva-trial/main.tf
terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
  # State backend — your team's existing convention. Example:
  backend "s3" {
    bucket         = "longaeva-tfstate-prod"
    key            = "brighthive/trial/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "longaeva-tfstate-locks"
  }
}

module "brighthive_trial" {
  source  = "git::ssh://git@github.com/brighthive/brighthive-longaeva-trial-tf.git//modules/trial?ref=v1.0.0"

  client = "longaeva"
  env    = "trial"

  aws_region = "us-east-1"

  # Network — pre-existing VPC inputs, never created by the module
  vpc_id              = "vpc-0abcd..."
  public_subnet_ids   = ["subnet-aaa", "subnet-bbb"]
  private_subnet_ids  = ["subnet-ccc", "subnet-ddd"]
  acm_certificate_arn = "arn:aws:acm:us-east-1:111122223333:certificate/abcd-..."

  # OpenMetadata sizing
  omd_instance_type     = "t3.large"
  omd_rds_instance_type = "db.t3.medium"
  omd_domain_name       = "omd.longaeva-trial.com"

  # Cross-account trust — values BrightHive provides at kickoff
  brighthive_principal_arn = var.brighthive_principal_arn
  external_id              = var.external_id

  # KMS — let the module create, or pass your existing CMK alias
  kms_key_alias = "alias/brighthive-trial-artifacts"

  # CloudWatch
  log_retention_days = 90

  tags = {
    "brighthive:trial"  = "true"
    "brighthive:client" = "longaeva"
  }
}
```

The module is composed of three sub-modules (`network`, `agent`, `openmetadata`) that map 1:1 to the three CDK stacks below — same blast-radius separation, same staged-apply story.

#### Pre-flight

```bash
# 1. CLI versions
terraform -version          # ≥ 1.7
aws --version               # ≥ 2.15

# 2. AWS auth
aws sts get-caller-identity # confirm Account = trial target

# 3. Quota headroom (same checks as CDK path)
aws service-quotas get-service-quota --service-code ec2 --quota-code L-1216C47A
aws service-quotas get-service-quota --service-code vpc --quota-code L-DF5E4CA3

# 4. Bedrock model access
aws bedrock list-foundation-models --region us-east-1 \
  --query 'modelSummaries[?contains(modelId, `claude-opus`)].modelId'

# 5. State backend exists
aws s3api head-bucket --bucket longaeva-tfstate-prod
aws dynamodb describe-table --table-name longaeva-tfstate-locks
```

#### Plan, review, apply

```bash
terraform init                       # downloads module + provider
terraform fmt -check                  # style gate
terraform validate                    # syntax + type gate
terraform plan -out=trial.tfplan      # security team reviews this output

# Apply staged — same boundaries as CDK stacks
terraform apply -target=module.brighthive_trial.module.network        trial.tfplan
terraform apply -target=module.brighthive_trial.module.agent          trial.tfplan
terraform apply -target=module.brighthive_trial.module.openmetadata   trial.tfplan

# Or apply all at once once the staged review is done
terraform apply trial.tfplan
```

Every IAM policy, security-group rule, and bucket policy shows up in the `terraform plan` diff — your security team can sign off on the plan file before any resource is created.

#### Validation after apply

```bash
# Module emits the same outputs you'd otherwise have to look up by hand
terraform output bedrock_execution_role_arn
terraform output artifact_bucket_name
terraform output omd_url

# And it ships a verification target
make -C $(terraform output -raw module_path) verify
# → runs the same connectivity + smoke suite documented in the CDK section below
```

#### Tear-down

```bash
terraform destroy
```

S3 buckets and CloudWatch log groups have `prevent_destroy = true` lifecycle blocks for the trial duration. To purge, set `var.allow_destroy_protected = true` and re-apply, then `terraform destroy`. KMS deletion follows AWS's 7–30 day window (irreversible after).

#### Why Terraform first for Longaeva

Decision drivers from 2026-06-03 conversation:
- Your platform team operates Terraform end-to-end already (state backend, modules, plan-review gates, drift detection)
- Asking your team to install and learn CDK adds 1–3 days of cycles before the trial can start
- Terraform's `plan` artifact is what your security review process is built around — CDK's `cdk diff` is functionally similar but not what your reviewers are calibrated on
- Both frameworks emit the same CloudFormation under the hood (CDK directly; Terraform via the AWS provider's own CFN-equivalent calls), so the runtime posture is identical

If your team would rather use the CDK path (e.g. you already have CDK pipelines wired into your CI), Path B below is fully supported and is the path we use internally.

---

### Path B — AWS CDK (alternative)

#### Repository & pre-flight

The CDK package is provided as a private GitHub repo: `brighthive/brighthive-longaeva-trial-cdk` (your team gets read access during kickoff). Pin to the tagged release (`vX.Y.Z`) we communicate — `main` is treated as ongoing development.

**Pre-flight checklist** (run before `cdk deploy`):

```bash
# 1. Verify CLI versions
aws --version          # ≥ 2.15
cdk --version          # ≥ 2.140
python --version       # 3.11 or 3.12
node --version         # ≥ 20 (for CDK toolkit)

# 2. Verify AWS auth points at the right account
aws sts get-caller-identity
#   → confirm Account matches the trial target

# 3. Verify quota headroom
aws service-quotas get-service-quota \
  --service-code ec2 --quota-code L-1216C47A   # Running on-demand standard instances
aws service-quotas get-service-quota \
  --service-code vpc --quota-code L-DF5E4CA3   # NAT gateways per AZ

# 4. Verify Bedrock model access
aws bedrock list-foundation-models --region "$AWS_REGION" \
  --query 'modelSummaries[?contains(modelId, `claude-opus`)].modelId'
```

#### Configuration

`config.json` shape (provided as a template; fill in your values):

```jsonc
{
  "client": "longaeva",
  "env": "trial",
  "aws": {
    "account": "111122223333",
    "region":  "us-east-1"
  },
  "network": {
    "vpcId":             "vpc-0abcd...",
    "publicSubnetIds":   ["subnet-aaa", "subnet-bbb"],
    "privateSubnetIds":  ["subnet-ccc", "subnet-ddd"],
    "natGatewayStrategy": "existing"  // or "create"
  },
  "tls": {
    "acmCertificateArn": "arn:aws:acm:us-east-1:111122223333:certificate/abcd-..."
  },
  "openmetadata": {
    "instanceType":   "t3.large",
    "rdsInstanceType":"db.t3.medium",
    "domainName":     "omd.longaeva-trial.com"
  },
  "agent": {
    "kmsKeyAlias":    "alias/brighthive-trial-artifacts",
    "logRetentionDays": 90
  },
  "brighthive": {
    "trustedPrincipalArn": "<we provide>",
    "externalId":          "<we provide>"
  }
}
```

#### Bootstrap (one-time per account+region)

```bash
cdk bootstrap aws://<ACCOUNT>/<REGION> \
  --trust <ACCOUNT> \
  --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess
```

If your org's CDK bootstrap is centrally managed (you already have a bootstrap stack), skip this and confirm the `CDKToolkit` stack exists in the target region.

#### Synthesis (review before deploy)

```bash
cdk synth --all > /tmp/synth.yaml
# Spot-check the rendered CloudFormation. Things to verify:
#  • IAM role principal ARN matches BrightHive's
#  • S3 bucket has BlockPublicAccess: all true
#  • Security groups have no 0.0.0.0/0 ingress except ALB:443
#  • KMS key policy includes your account root as administrator
```

#### Deploy in staged order

The CDK package is composed of 3 stacks. Deploy them in this order — each is independently rollback-able:

```bash
cdk deploy LongaevaTrialNetworkStack    # Security groups, KMS key (if creating)
cdk deploy LongaevaTrialAgentStack      # S3 bucket, IAM roles, CloudWatch log groups
cdk deploy LongaevaTrialOmdStack        # EC2, ALB, RDS, OpenSearch — the long one (~25 min)
```

`cdk deploy --all` works too, but staged deploy lets your security team review IAM diffs at each gate. Each stack respects `--require-approval broadening` — CDK will print every IAM/security-group change for explicit approval.

#### Validation after deploy

```bash
# 1. S3 bucket policy is correct
aws s3api get-bucket-policy-status \
  --bucket brighthive-trial-<acct>-<region>
#   → IsPublic: false

# 2. Cross-account trust is in place
aws iam get-role --role-name BrightHiveAgentExecutionRole \
  --query 'Role.AssumeRolePolicyDocument'

# 3. OMD is reachable
curl -sS -o /dev/null -w '%{http_code}\n' "https://${OMD_DOMAIN}/api/v1/system/version"
#   → 200

# 4. CloudWatch log groups exist
aws logs describe-log-groups --log-group-name-prefix /aws/brighthive
```

We provide a `make verify` target in the CDK repo that runs all of the above plus a synthetic agent invocation against the deployed infra. Run it before notifying BrightHive that infra is ready.

#### Troubleshooting — common failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| `cdk deploy` hangs at "CREATE_IN_PROGRESS" on RDS | Subnet IDs span fewer than 2 AZs | Confirm at least 2 AZs in `privateSubnetIds` |
| `Resource handler returned message: ... CertificateNotFound` on ALB | ACM cert is in a different region than the stack | Re-issue ACM cert in the deploy region |
| OMD health check fails after deploy completes | Snowflake creds not yet populated in Secrets Manager | Wait for the post-deploy hook; or paste manually per CDK README |
| Cross-account `sts:AssumeRole` fails (`AccessDenied`) | `ExternalId` typo in `config.json` | Re-deploy `LongaevaTrialAgentStack` with corrected value |
| KMS `Decrypt` denied when agent reads S3 | KMS key policy missing the assume-role principal | Either let CDK manage the KMS key, or add the principal to your existing key policy |
| Bedrock invoke fails with `AccessDeniedException` | Claude Opus model access not enabled in region | Bedrock console → Model access → request |

#### Tear-down (post-trial)

```bash
cdk destroy --all
```

S3 bucket and CloudWatch log groups are retained by default (deletion-protection on). To purge:

```bash
aws s3 rm s3://brighthive-trial-<acct>-<region> --recursive
aws s3api delete-bucket --bucket brighthive-trial-<acct>-<region>

aws logs delete-log-group --log-group-name /aws/brighthive/agent/longaeva
aws logs delete-log-group --log-group-name /aws/brighthive/code-interpreter/longaeva
```

KMS key is scheduled for deletion (7–30 day window) — irreversible after the window closes.

#### What we need from you (CDK path)

- [ ] AWS account ID + region confirmed
- [ ] `config.json` filled in and reviewed (paste to a shared secure channel before deploy)
- [ ] Network inputs validated (VPC + subnets exist, AZs distinct)
- [ ] CDK bootstrap stack present (or permission to create one)
- [ ] ACM cert provisioned (or confirmation we should create one)
- [ ] Sign-off from your security team on the rendered `cdk synth` output
- [ ] Date/window for the deploy session (~1 hour, joint with BrightHive on Zoom)

---

## Open items / not yet covered

These sections of the trial guide remain stubs and will be authored before kickoff:

- **Integrating BrightAgent as MCP** — covered separately in `clients/trials/longaeva/sandbox/` once Longaeva's MCP-host environment specifics are confirmed
- **Using BrightAgent** — UX walkthrough; depends on whether Longaeva uses Slack-primary or chat-primary
- **Prompt guide for BrightAgent** — written jointly with Longaeva during Days 1–3 against their actual schema

Track all pre-trial readiness items in `clients/trials/longaeva/TRACKER.md`.
