# Loop Capital demo — real SQL Server EC2

Standalone, self-contained CDK app provisioning ONE EC2 instance running a
real Microsoft SQL Server container (`mcr.microsoft.com/mssql/server:2022`,
the SAME image `../sandbox/docker-compose.yml` runs locally) — reachable
from staging's platform-core so the real BYOW watchdog (GC-15) can poll it.

**Not** the full `brighthive-admin` per-workspace-AWS-account provisioning
factory (creates a permanent new AWS account, 7 CDK stacks, Cognito, Neo4j
entity, welcome email — the real paying-client onboarding flow). This is a
single, isolated, easy-to-tear-down EC2 instance in the EXISTING shared
STAGE account (`873769991712`), scoped only to this demo.

## What this creates

- One `t3.medium` EC2 instance (Amazon Linux 2023, Docker installed via
  user-data) running the real SQL Server container on boot, seeded with
  the same synthetic Loop Capital data `../sandbox/setup.sh` builds locally.
- A dedicated security group allowing inbound `1433` ONLY from platform-core's
  known egress IP ranges (not `0.0.0.0/0`) — TODO: confirm platform-core's
  real egress CIDR before deploy, currently a placeholder.
- Tags: `Project=loopcapital-demo`, `Owner=drchinca`, `TemporaryUntil=2026-07-18`
  (one day after the 7/17 demo) — for easy identification + teardown.

## Cost

`t3.medium` on-demand, us-east-1: ~$0.0416/hr ≈ **$30/month** if left running,
or a few dollars for the demo window if stopped/terminated immediately after.
**No RDS, no Multi-AZ, no backups configured** — this is demo infra, not
production; do not point real client data at it beyond the synthetic set.

## Deploy (requires explicit human approval — DO NOT auto-run)

```bash
cd clients/trials/loopcapital/infra
uv venv && source .venv/bin/activate
uv pip install -e .
cdk bootstrap aws://873769991712/us-east-1 --profile brighthive-staging  # once, if not already done
cdk diff --profile brighthive-staging       # REVIEW before deploying
cdk deploy --profile brighthive-staging     # requires explicit confirmation
```

## Teardown (after the demo)

```bash
cdk destroy --profile brighthive-staging
```

## Status

**Not yet deployed.** This stack was written and reviewed but never applied —
provisioning real, billable AWS infrastructure requires an explicit,
separate confirmation from whoever owns AWS spend decisions, not an
agent's own judgment call mid-session. See `../overview.md` Open Blocker #5
for the decision trail.
