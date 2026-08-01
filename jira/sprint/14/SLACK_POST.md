🍯 BrightHive Sprint 14 Release
Release Date: Aug 1, 2026
Sprint Period: July 21 – Aug 1, 2026

This one's organized per person — Kuri first, then each engineer.

🌟 Kuri (drchinca) — the through-line of the whole sprint
57 PRs · 69.5% of the sprint · 15 tickets Done, 10 carried · +38,402/−3,556 code lines
Owned all three backbone initiatives end-to-end — backend, frontend, tests, docs, release train.
• 🩺 Warehouse-health snapshot → home band (BH-1280): worst-of health fold, never optimistic; engine-neutral disk/failed-job surfacing; 3-engine e2e fixtures — shipped to staging
• 🧬 Engine-agnostic lineage + staged quality (BH-1036): 6-tier medallion lineage, tiers from declared structure not table names, re-runnable immutable pipeline segments, boot-time schema guardrail
• 🔌 MCP prod-test hardening — 13-fix sweep (BH-1181 family): hyphenated Redshift DBs, Spectrum external tables, honest `pending` vs 120s timeout, `bad_request` vs generic errors, stale lock reclaim, new BrightSignals read tool
• 🤖 BrightRoutines cadence/feedback (BH-993), GSI5 leaderboard (BH-1207), OpenMetadata N+1 perf gate (BH-1242), MFA2 V1, full 3.0.0 release train

👤 Harbour (Nano-233) — the product-surface craftsman
17 PRs · all code · 12 tickets Done · +2,020/−575
• 🧹 Catalog + Projects UX sweep — 11 fixes (BH-1154→BH-1162): real Switch toggles, correct write-mode labels, aligned casing, missing JSON Schema tab, project-file Tags field, backwards governance labels
• 🐛 resourceType() only matched the first extension per type (BH-1162) — real correctness fix behind a cosmetic ticket
• ✅ Atomic project creation — create-with-rollback, toast on failure, no orphans
• 🧠 KB retrieval precision: reranking (BH-1164), grounding to cut hallucination (BH-1165), file-id scoping for graph aliases (BH-1163)

👤 Marwan (Marwan-Samih-Brighthive) — schema-file intake, end to end
8 PRs · +1,391/−185 · one clean vertical slice across backend + frontend
• 📄 platform-core: resourceContent query (#1144) + resourceContentUploadUrl (#1148) for raw schema files
• 📄 webapp: XSD/XML schema-file uploads in Project Files (#1377) + a dedicated XSD/XML schema editor (#1383)

📊 By the Numbers
• Tickets Resolved: 28 (27 Done, 1 Canceled)
• PRs Merged: 82 (62 code + 20 release/promotion)
• Code Lines: +41,813 / −4,316 (release re-merges excluded)
• Repos Touched: 5 (platform-core, webapp, apm, e2e, platform-saas-ai-context)
• In Flight: 10 (all default-warehouse ingestion + unstructured-data stack)

🎯 What's Next: Sprint 15 Focus
• Close the BH-1023 default-warehouse ingestion chain (in flight all sprint)
• Unstructured-data stack into workspace AWS accounts (BH-293/285/302)
• Open a formal Jira sprint object — end the 4-sprint drift

⚠️ Sprint Health
• Fourth unofficial (date-range) sprint in a row — completion/velocity are reconstructed
• Authorship concentration ~70% on one engineer, unchanged from Sprint 13
• 10 tickets carrying to Sprint 15

📎 Links
📋 Release Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/14/RELEASE_NOTES.md
📣 Marketing Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/14/MARKETING_RELEASE_NOTES.md
📊 Notion Sprint 14: https://app.notion.com/p/3af02437dde481cc9aa1c0aa8389d95a
🎯 Jira Board: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
