---
title: "Catch a bad number before your customers do"
epic: "BH-1061"
owner: "drchinca"
status: "Draft"
created: "2026-08-18"
supersedes:
  - lineage-aware-data-quality.md
---

# Catch a bad number before your customers do

> Delegation unit. Cap 150 lines.

## The goal

When a source table starts producing wrong or missing data, the platform says which downstream
reports, dashboards, and Gold tables are affected — before anyone reads a bad number off one of
them. Today a customer learns about it from whoever noticed the dashboard looked odd.

## Why now

The two halves already exist and have never been connected. The platform detects anomalies on a
table (row counts, nulls, distribution shifts), and dbt already knows the lineage graph. Nothing
joins them, so an anomaly alert names one table and says nothing about the twelve things
downstream of it. The blast radius is the part a data leader actually cares about.

## What to build

1. `brightbot` — read lineage from the engine that already computes it, behind one provider so
   dbt is the first source and others can follow. Do not re-derive lineage ourselves.
2. `brighthive-platform-core` — store those dependency edges in the graph so they can be walked
   in both directions.
3. `brightbot` — when an anomaly fires, walk downstream and attach the affected assets to the
   alert.
4. `brightbot-slack-server` + `brighthive-webapp` — the alert says what broke *and* what it
   affects, ordered by tier so Gold and Platinum come first.

## Done when

- [ ] A seeded anomaly on a source table produces an alert naming real downstream assets
- [ ] The lineage edges come from dbt's own graph, not a name-matching heuristic
- [ ] An asset with no downstream dependents produces an alert that says so, rather than an
      empty section
- [ ] Gold/Platinum impact appears above lower tiers in the alert
- [ ] Real-behavior test against a real dbt project's lineage, not a hand-built graph fixture

## Don't do

- **Snowflake and Databricks lineage providers** — dbt is the first provider. Add others when a
  customer is actually on them, as new provider registrations.
- **Re-deriving lineage from SQL parsing.** The engines publish it; read it.
- **Anomaly detection itself** — it ships. This theme consumes its output.
- **The webapp UI defect audit** bundled into the source spec as "Track D" (~130 lines on mobile
  responsiveness, dead legacy code, accessibility). It has **zero lineage dependency** and its own
  text admits it is "NOT yet a committed scope." It belongs in a webapp tech-debt ticket set.

## Where it lives

| Repo | What changes |
|---|---|
| `brightbot` | lineage provider, downstream walk, anomaly enrichment |
| `brighthive-platform-core` | dependency edges in the graph |
| `brightbot-slack-server` | impact-bearing alert card |
| `brighthive-webapp` | impact display |

**Tickets:** BH-1061 (epic), BH-1062, BH-1063, BH-1064, BH-1065, BH-1066, BH-1069 · deferred:
BH-1068, BH-1074 (non-dbt providers)

---

## ⚠️ Rewrite the source spec, don't extend it

`lineage-aware-data-quality.md` is **2,282 lines** — four and a half times the house cap — with
**23 invariants** (cap 15) and **21 scenarios** (cap 20). Its real scope is the 9 tickets above:
roughly 250 lines of spec per ticket, against ~55 for a healthy spec.

The excess is a revision transcript left in the document body: annotations running to **"pass 78"**
with phrases like "CORRECTED pass 55" and "CRITICAL, pass 44" woven through every section. That is
PR history, not a contract — and it is why nobody has picked this up.

Do not extend it. Rewrite as four specs under 500 lines each, following this theme's four build
items, and delete every "pass N" annotation as you go:

1. Lineage provider + dbt adapter (BH-1062)
2. Graph schema + edge upsert (BH-1063, BH-1069)
3. Anomaly enrichment + alert rendering (BH-1064, BH-1065, BH-1066)
4. Non-dbt providers — deferred (BH-1068, BH-1074)

Keep only §1, §2, and the ticket breakdown from the original as source material. Everything else
in those 2,282 lines is either superseded, duplicated, or narration.
