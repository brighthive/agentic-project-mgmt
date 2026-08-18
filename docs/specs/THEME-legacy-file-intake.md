---
title: "Drop in your legacy pipeline files, get answers back"
epic: "BH-1255"
owner: "drchinca"
status: "Draft"
created: "2026-08-18"
supersedes:
  - project-files-pipeline-artifact-intake.md
  - project-files-dbt-github-bridge.md
  - pipeline-artifact-parser-registry.md
  - ssis-ssrs-proactive-pipeline-source.md
---

# Drop in your legacy pipeline files, get answers back

> Delegation unit. Cap 150 lines.

## The goal

A customer sitting on decades of SSIS packages and SSRS reports uploads them and immediately gets
something useful: what these pipelines do, what's broken or risky in them, and — for SQL — a pull
request they can review. They learn something about their legacy estate without rewriting it
first.

## Why now

This is the "we have thousands of these and no idea what's in them" conversation, and the parsing
capability already exists — SSIS package analysis and SSRS report analysis both ship. What's
missing is the front door: no way for a customer to hand us a file and get the analysis back.

## What to build

1. `brighthive-webapp` + `brighthive-platform-core` — Project Files accepts `.dtsx`, `.rdl`, and
   `.sql` uploads as diagnostic input, not just storage.
2. `brightbot` — **one** file-type → analyser lookup, used by every caller. Three specs each
   invented their own; there must be exactly one.
3. `brightbot` — SSRS (`.rdl`) as a monitored source, matching what SSIS already does. SSIS ships;
   this is the parity gap.
4. `brightbot` — an uploaded `.sql` file becomes a dbt model proposal as a GitHub pull request,
   through the existing repo proxy. Never a direct write to the customer's repo.
5. Unsupported file types fail loudly with a clear message. Silently ignoring an upload is the
   worst outcome — the customer thinks it worked.

## Done when

- [ ] Uploading a real `.dtsx` returns a diagnosis in the UI
- [ ] Uploading a real `.rdl` does the same, and shows up as a monitored source
- [ ] Uploading a `.sql` opens a reviewable PR; no direct repo write happens
- [ ] An unsupported extension produces a clear error, never silence
- [ ] `grep` finds exactly **one** extension → analyser mapping in the codebase
- [ ] Real-behavior test against real captured `.dtsx` / `.rdl` fixtures, not synthetic XML

## Don't do

- **Regenerate SSIS/SSRS into dbt.** That's a separate, parked concept — its spec runs 643 lines
  for work marked out of trial scope and mapping to none of the nine trial criteria. In-trial
  posture is **diagnose and operate, don't author**.
- **Rewrite the existing parsers.** They return a plain dictionary; carry it through unchanged.
  This theme adds a front door and one lookup, not new parsing.
- **A new file-storage system** — Project Files already exists.
- **On-prem file access** — owned by
  [Work where the customer's data lives](THEME-onprem-engineering.md). This theme is only about
  files the customer uploads to us.

## Where it lives

| Repo | What changes |
|---|---|
| `brightbot` | one extension lookup, SSRS monitored source, `.sql` → PR path |
| `brighthive-platform-core` | accept and route diagnostic uploads |
| `brighthive-webapp` | upload affordance + diagnosis display |
| `brighthive-e2e` | upload → diagnosis, and unsupported-extension error test |

**Tickets:** BH-1255 (epic), BH-1274 ⚠️ (needs a named secret-write confirmation before it
starts), BH-1275, BH-1276, BH-1277, BH-1301, BH-1302, BH-1303

---

## Notes for whoever picks this up

**Item 2 is the whole reason this is one theme.** The same extension → analyser dispatch was
independently invented three times across these four specs, under three different names, all
wrapping the same two functions, and none of the three references the others. Pick one name, put
it in one place, and delete the other two designs. If you finish this theme and there are still
two mappings, the theme failed.

**BH-1274 is gated.** It writes to a workspace secret to register the customer's SSIS package
locations, which requires an explicit named confirmation from Kuri before any work starts — not a
general "go ahead" on this theme. Everything else here is pick-up-and-go.
