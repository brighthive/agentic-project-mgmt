# AI-Driven Engineering: One Engineer Running an Agentic Delivery System

Kuri did not only write code with AI help. Kuri built and ran an agentic way of working that covers the roles a delivery team normally splits across several people: project management, business analysis, quality assurance (QA) and senior engineering review. This repo, `agentic-project-mgmt`, is the working example. Source: `scripts/yearone/collect_ai_engineering.py` → `data/ai_engineering.json`, plus the other collectors in this folder.

## The four roles, and what each left behind

| Role covered | Before (Oct 2025) | After (Oct 2026) | Evidence you can open |
|---|---|---|---|
| **Project management** | 69-idea backlog, no delivery epics, no release notes | 16 sprints, each with release notes; 1,507 Jira issues under 48 epics (88.6% under an epic, 97.7% described); 24 epics led | `jira/sprint/1…16/`, `SPRINTS.md`, `BOARD_REPORT_OCT_2025_MAY_2026.md`, [JIRA.md](JIRA.md), [MILESTONES.md](MILESTONES.md) |
| **Business analysis** | No specs | 123 specs, 79 with Gherkin acceptance scenarios (570 scenarios); 16 theme specs; 10 of 10 Longaeva use cases with gap analysis; 14 golden success paths; user acceptance guides for technical and non-technical users | `docs/specs/`, `clients/trials/longaeva/` (`UAT_GUIDE.md`, `NON_TECH_UAT.md`), [PRODUCT-IDEAS.md](PRODUCT-IDEAS.md) |
| **QA specialist** | `brightbot` 10 test files, `platform-core` 3, no end-to-end suite | 413 and 237 test files; 571 end-to-end tests across 8 surfaces and 3 environments, including a read-only production smoke test; a 16-scenario agent evaluation framework; a 100-persona evaluation harness in v3 | [CICD-AND-E2E.md](CICD-AND-E2E.md), `brighthive-e2e`, `brightbot` #623 |
| **Senior engineering review** | 1 pipeline file in `brightbot`, no written standards | Automated Claude PR review workflow in 7 of 9 repos checked; 35 CLAUDE.md / AGENTS.md contracts; 20 ADRs across 5 repos; conventional commits 12.3% → 72.8% | [PRACTICES.md](PRACTICES.md), `data/ai_engineering.json` |

## The framework, in four moves

| Move | What it does | Where it lives |
|---|---|---|
| **Spec first** | Every feature starts as a spec with typed contracts, invariants, Gherkin scenarios and a test-coverage step. The spec is the prompt agents work from. | `docs/specs/SPEC_TEMPLATE.md`, 123 specs |
| **Contracts for agents** | Each repo tells an agent what it may and may not do before it touches code. | 35 contract files in 8 repos |
| **Skills for repeatable work** | Ticket creation, trial call-outs and trial delivery run as checked-in agent skills. | `.claude/skills/` (3 skills) |
| **Records that regenerate** | Sprint stats, release notes, board reports and this year-one evidence are produced by scripts, not meetings. | 66 documented `make` targets, 16 collectors and renderers in `scripts/yearone/` |

## Agentic systems Kuri designed and shipped

| System | What it shows | Status |
|---|---|---|
| Pipeline monitoring and fix loop | Agents watch customer pipelines, diagnose failures and open fix PRs. The loop never merges; a person approves. | 🟡 staging |
| BrightRoutines | An agent notices recurring requests and offers to schedule them, gated by a recall floor and a calibration ceiling. | 🟡 staging |
| BrightAgent v3 on CEMAF | Own multi-agent framework with Bedrock as sole model provider and evaluation checks that can stop a run. | ⚪ foundation, 9.6% cut over |
| On-premises engineering runner | Agent drafts, a person applies; nothing leaves the customer network. | ⚪ built, not deployed to a customer |
| This repo | Project management, business analysis and reporting run as agent-readable artifacts. | 🟢 in daily use |

## Stated plainly

- **AI share of code is not measured.** Commits carry no AI attribution by policy, so there is no honest "percent written by AI". Volume (1,931 merged PRs) is context, not proof of effort. We do not convert it into headcount.
- **The role roster is not in a repo.** The sequence of reviewer roles (architect, senior engineer, QA, fresh-eyes junior) is defined in Kuri's own agent setup, outside any repository. This page therefore claims the role coverage from the artifacts above, not from a checked-in roster. Checking the role definitions into this repo would make that claim verifiable by anyone.
- **Review quality is not measured.** We count that the Claude PR review workflow exists in 7 repos. We do not yet measure how many findings were accepted or what they caught.
- **Reviews by someone other than the author may include review bots.** The 49.1% in [PRACTICES.md](PRACTICES.md) counts any non-author review, so the share reviewed by a person is at most that.
- **Concentration is the other side of this story.** One engineer ran all four roles, which is also why 62% of Jira items and 67.5% of merged PRs sit with Kuri. See [DATA-QUALITY.md](DATA-QUALITY.md).
