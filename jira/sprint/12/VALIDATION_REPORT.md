# Sprint 12 Validation Report
**Period**: June 13–23, 2026

---

## PR ↔ Ticket Coverage

| Category | Count |
|----------|-------|
| Feature/fix PRs merged | 223 |
| PRs with BH- ticket ref in title/body | ~80 (BH-695–712 series) |
| PRs retroactively ticketed (BH-713–739) | ~120 |
| Remaining truly orphan PRs | ~23 |

---

## Orphan PRs (no ticket, not retroactively covered)

These are small fixes, docs-only, or changes that don't warrant standalone tickets:

**brightbot**
- #583 fix(repo): untrack self-referential .venv symlink
- #571 docs(mcp): reflect /bh-mcp path move
- #618 docs(claude): document legacy graph aliases
- #621 docs(evals): SPEC-EVAL-FRAMEWORK four-layer eval foundation
- #623 feat(evals): L1 single-source + L2 baseline + RouteClass
- #627 docs(spec): SPEC-GRAPHQL-SCHEMA-INDEX-SDL fix prod introspection block
- #631 docs(claude): trim CLAUDE.md under 40k char budget
- #634 docs(BH-674): pivot OKTA_AUTH design note to resolver-side JIT
- #669 docs(claude): how to run develop locally against staging

**brightbot-slack-server**
- #57 docs: README + ops docs for observability + enricher retry
- #67 docs: SSE push delivery + per-workspace poll model
- #77 docs(slack): INTERRUPTS_ENABLED + notification flags + HITL flow

**brighthive-platform-core**
- #862 docs(om): clarify OLD lambda — /workflow scan DEAD, /team CRUD LIVE
- #864 docs(om): REMOVAL.md runbook for old scanner lambda
- #867 docs(admin): superadmin self-service cleanup spec
- #888 docs(mcp): reflect dedicated brightagent-mcp ingress
- #892 docs(okta): Neo4j provisioning phase + okta-idp-cdk in runbook
- #919 feat(audit): BH-700 IaC (subsequently removed in #921 — cleanup, not shipped)
- #921 chore(audit): remove unused BH-700 DynamoDB/WORM audit IaC
- #922 docs(claude): how to connect to staging Neo4j from laptop

**brighthive-webapp**
- #1175 docs: document VITE_MCP_URL env var
- #1179 docs(spec): Okta SSO login spec
- #1183 docs(env): document VITE_LONGITUDINAL_MONITORING_ENABLED
- #1192 chore(deprecate): mark BbAssistant as dead code

---

## Tickets Without PRs (Done tickets that seem code-free)

All Done tickets in this sprint have corresponding PRs — either directly referenced in the PR title/body or covered by the retroactive BH-713–739 group.

---

## Estimation Gaps

- All 27 retroactive tickets (BH-713–739) have **0 story points** — need a sweep.
- BH-695 epic sub-tickets (BH-696–707) also have 0 points.
- Recommend: 30-minute estimation session for Sprint 12 backlog before Sprint 13 starts.

---

## Branch Naming

Most branches follow `fix/`, `feat/`, `develop =>` patterns. No systematic BH-XXX branch naming — expected for an unofficial sprint. The BH-695 series and BH-67x series are properly named in commit messages.
