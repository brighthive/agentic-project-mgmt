---
name: "BrightHive Dogfood — Synthetic Data"
slug: "brighthive-dogfood"
stage: "internal"
purpose: "Synthetic warehouse seed for fully-local platform testing (no staging dependency)."
last_reviewed: "2026-06-24"
---

# BrightHive Dogfood — Synthetic Data

> Seed data for running the **whole platform locally** — Neo4j + a dockerized
> Postgres warehouse + localstack — so the agent can be exercised end-to-end
> without touching staging. This is how we dogfood BrightAgent on our own.

## Why this exists

Staging runs on Snowflake. Bugs that only appear on other warehouse dialects
(e.g. [BH-763](https://brighthiveio.atlassian.net/browse/BH-763) — `min(uuid)`
has no Postgres aggregate) are invisible there. Running the agent against a
**local Postgres warehouse** surfaces them. This directory holds the seed data
that makes the local warehouse rich enough to answer the real UAT questions.

## Layout

| Path | What |
|---|---|
| `postgres/` | The canonical local seed — Longaeva warehouse schema ported to Postgres (GOLD / SILVER / BRONZE / REF + watchlist + weekly-delta). This is what `local_bootstrap` loads. |
| `_aspirational/` | The **domain-agnostic warehouse template** — one fixed 5-layer schema (`dim_workspace / dim_subject / dim_program / dim_provider / fact_enrollment / fact_outcome` + `bh_agent.fact_agent_session`) with swappable synthetic domains (automotive / food-supply / SaaS / fashion / workforce). A future direction, NOT the schema we seed today. Captured here so the design isn't lost. |

## The two schemas — which is "real"

- **`postgres/` (real, build target)**: the validated Longaeva sandbox schema
  (finance: portfolio exposure, issuers, watchlist). Mirrors what the Longaeva
  PoC actually ran on Snowflake, ported to Postgres for local use. This is the
  schema the agent + UAT exercise.
- **`_aspirational/` (reference only)**: a cleaner, domain-agnostic star schema
  that would let us swap the *data* per vertical while keeping the *structure*
  identical. Compelling, but not what we seed now — kept for when we invest in
  a multi-domain dogfood corpus.

## Running it locally

See [BH-764](https://brighthiveio.atlassian.net/browse/BH-764) and the brightbot
local runbook. High level:

```bash
# 1. Stack (neo4j + postgres + localstack on its OWN bh container — NOT a foreign one)
cd ../../../brightbot && docker compose -f docker-compose.local.yml up -d neo4j postgres localstack

# 2. Neo4j workspace/user/asset graph (platform-core comprehensive cypher seed)
cat ../brighthive-platform-core/setup/scripts/cypher/seed-comprehensive.cypher \
  | docker exec -i brightbot-neo4j cypher-shell -u neo4j -p brighthive-local-dev

# 3. Warehouse + localstack secrets/S3 + the Longaeva Postgres seed
uv run python scripts/local_bootstrap.py            # base orders/users + secret + S3
uv run python scripts/seed_longaeva_local.py        # GOLD/SILVER/REF + watchlist (BH-764)
```

> **localstack gotcha**: bh's localstack must enable `s3,secretsmanager,dynamodb`.
> A foreign `*-localstack` on 4566 from another project will NOT have
> `secretsmanager` and the bootstrap's `create_secret` fails. Use bh's own
> container (compose `localstack` service), or an alternate port.
