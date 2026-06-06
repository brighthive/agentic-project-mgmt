---
title: "DRAFT — Email to Grant Langseth reframing trial as co-build"
to: "Grant Langseth, Longaeva Partners"
from: "Kuri / Matt"
cc: "Corinne, Sumukh (BrightHive); Longaeva data-eng + data-science participants TBC"
status: "DRAFT — not sent. Awaiting Kuri review."
date_drafted: "2026-06-05"
intended_send: "2026-06-08 (start of trial week -1)"
based_on: "multi-agent trial review (architect, llm-systems-engineer, qa, sales-strategist) 2026-06-05"
---

# Email to Grant — trial reframe + creds unblock

> **Why this draft exists.** Multi-agent review of the trial state on 2026-06-05
> concluded that Day 1 black-box demo of the POC §2 (Atlas YAML semantic-view
> scaffolding) carries materially higher risk than reframing it as a Day 6–8
> joint co-build. This email proposes the reframe and pulls forward the two
> external dependencies (GHE creds, MCP auth decision) into a face-to-face call.
>
> **Do not send without Kuri review.** Tone is direct + collaborative —
> calibrate to your current relationship with Grant before pressing send.

---

## Suggested subject line

`Longaeva trial — proposing a small framing tweak to make Day 1 land harder`

(Alt: `Longaeva trial — let's co-build the semantic view, not demo it`)

---

## Email body

Grant —

Quick note ahead of the trial. We've been doing our own pre-flight on what Day
1 through Day 14 looks like end-to-end, and we want to propose a small but
meaningful framing change to how we run the centerpiece.

**What's solid:** the sandbox is real. We stood up a parity Snowflake account
with your medallion + semantic-view + share + RBAC shape, ran every POC use
case against it, and 10 of 10 resolve. The *target* is de-risked. We also
have the Atlas YAML contract distilled from the three examples you sent on
the 1st — we know exactly what good output looks like.

**Where we'd like to reframe:** the original plan had Day 1–5 as context
build, Day 6–8 as ingestion execution, Day 8–10 as semantic-view enrollment
"with BrightHive handling scaffolding and validation". We'd like to flip the
semantic-view block from "BrightHive autonomously enrolls and you review" to
"BrightHive and one of your data scientists co-build the first one,
hands-on." Concretely: on Day 6 we pick a Silver table together
(`int_enriched_holdings` is our default candidate — speak now if you'd
rather another), and we sit in a room (or a Zoom) and walk the workflow as
a pair-programming session. Our agent does the scaffolding; your DS does the
domain enrichment + accept/reject; we both watch what the agent gets right
and where it needs human steering.

**Why this is the better trial for you, not just for us:**

- A polished demo proves a product can do *the thing we rehearsed*. A
  co-build proves your team can use BrightHive on *the things you'll
  actually face* — the moment we hand-off, your DS already owns the pattern.
- The most honest evaluation criterion isn't "did the agent get it right?"
  It's "did the agent + your DS produce a better semantic view, faster, than
  your DS alone?" That comparison is meaningful for the buy decision.
- It also means Day 6–8 is no longer gated on every edge case we haven't
  seen in your real data. We learn together; you get a working artifact.

**What we keep unchanged:**

- Day 1–5 ingestion (S3, REST, Snowflake Data Share — Section 1) stays as
  scoped. We're confident here and the sandbox proves it.
- Day 10–12 MCP feedback loop (Section 3) — same as planned, contingent on
  the auth decision below.
- Day 12+ self-healing + anomaly monitoring (Section 4) — same as planned.
- Day 14 evaluation + commercial discussion — same as planned.

**Two things we'd like to unblock this week on a 30-min call:**

1. **GHE access** — sandbox PAT + host URL + the TLS chain (your CA if it's
   not a public root). We can get every PR-creation flow working in our
   staging environment 48h after we have these. Without them, Day 1 starts
   with a broken proxy and we lose two days.
2. **MCP auth decision** — Sumukh has options on the table (federated Okta
   via Cognito vs. a scoped service-account token for the trial). Federated
   Okta is the right end-state, but the DNS + cert + identity-provider
   handshake is a 24–48h chain we'd rather not start during Day 1. Our
   recommendation for the trial is the scoped service-account token,
   federate post-trial. Want to confirm.

Could we grab 30 minutes Wednesday or Thursday? Even 20 if your week is
already packed. Happy to bring Matt + whoever from our side is most useful;
on yours, maybe whoever owns Atlas + whoever runs your GHE.

We're more excited about this trial than any other on our docket right now
— want to make sure Day 1 lands hard.

Best,
Kuri

---

## What this email is NOT saying (and why)

The multi-agent review surfaced honest gaps. This email handles them by
*proposing a frame that absorbs them*, not by hiding them or by leading with
them. Specifically:

- **NOT saying**: "We don't have the agent capability ready." Saying that to
  the buyer two weeks out reads as "you should have shipped." It's also
  technically inaccurate — the capability exists at sandbox + scaffold-tool
  level; what's missing is the LLM-enrichment quality gate and the agent
  routing wiring. Co-build framing is honest about *what the agent does and
  what the human does* without leading with weakness.
- **NOT saying**: "Can we slip 2 weeks?" Slipping a trial after the champion
  has internally committed signals "not ready, not disciplined." Wrong
  signal. (Reserved if BH-590..594 won't be at demo-quality by Day 3 — we
  re-evaluate then, not now.)
- **NOT saying**: numbers like "≥90% inference accuracy" from the scorecard.
  Multi-agent review (sales lens) flagged these as fog: chosen without
  baseline measurement. If Grant asks, there's no answer. Remove from
  external comms until we have sandbox-measured baselines.

## Suggested follow-up artifacts (post-Grant reply)

If Grant agrees to the call + the reframe:

1. **Send a 1-pager** ahead of the call summarizing the revised Day-by-Day
   (no slides, just a structured doc). Sets the agenda; saves call time for
   creds + auth decision.
2. **Open `clients/trials/longaeva/artifacts/trial-day-by-day-v2.md`** —
   revised schedule reflecting the co-build. Land it before Day 1.
3. **Brief Marwan + Ahmed + AI/ML** that the headline demo is now a paired
   workshop, not an autonomous one. Their agent code can be 80% of the way
   there instead of 100%, as long as the LLM enrichment doesn't hallucinate
   under their watch (BH-596 + BH-597 still must land).

If Grant pushes back on the co-build reframe (most likely concern: "is this
because you're not ready?"):

- Honest response: "We can ship an autonomous demo; the co-build framing
  isn't about hiding readiness, it's about generating a more meaningful
  evaluation outcome for you. Happy to do whichever you'd prefer — wanted
  to put the option on the table before we baked the plan."
- Then run the autonomous version. BH-597 (E2E eval harness) becomes
  non-negotiable; without it the demo is a coin flip.

## What gets killed from external comms regardless of reframe outcome

Per the multi-agent review (sales lens), the following lines should NOT
appear in any Longaeva-facing artifact going forward:

| Killed line | Why | Where it currently lives |
|---|---|---|
| "Confidence to win: HIGH" | Drift; amended to MEDIUM | `BRIGHTHIVE_GAPS.md` (now fixed) |
| "This is not a stretch. It is a fit." | Closer's line, not engineer's | `poc-response-plan.md` |
| "Brighthive handling scaffolding and validation" (autonomous framing) | Sets expectation we may not meet | `poc-response-plan.md` |
| "≥90% inference accuracy", "≤5% MCP error rate" | No baseline, can't defend | `scorecard.md` |
| The "Why Brighthive Wins" comparison table | Vendor strawman; Grant has seen this from 5 vendors | `poc-response-plan.md` |

Replace with: one concrete artifact per claim. "Here's the YAML our agent
produces for `int_enriched_holdings`, and here's the YAML your DS produces
without it — compare for yourself."
