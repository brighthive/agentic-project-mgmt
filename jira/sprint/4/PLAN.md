# Sprint 4 Plan

**Sprint**: 4
**Status**: Planning
**Duration**: 2 weeks (TBD start date)

---

## Sprint Goals

| Goal | Owner(s) | EPIC | Status |
|------|----------|------|--------|
| Background Agent Analyst v0 | Team | BH-111 | 🆕 Design |
| Slack Auth Solution Design v0 | Team | BH-117 | 🆕 Design |
| Unstructured data as source | Ahmed | BH-115 | 🆕 New |
| Workspace Portal + Context Engineering | Marwan, Kuri | BH-114, BH-110 | 🆕 New |
| Projects v0 + BHAgent integration | Harbour, Marwan | BH-116 | 🔄 Continue |
| Internal improvements DevOps | Ahmed | BH-171 | 🔄 Carryover |

---

## Tickets

### New Tickets (7)

| Key | Summary | Epic | Points | Assignee |
|-----|---------|------|--------|----------|
| TBD | [BE] Background Agent Analyst - Design spec | BH-111 | 3 | Team |
| TBD | [Design] Slack Auth - OAuth flow design | BH-117 | 2 | Team |
| TBD | [BE] Unstructured data source - S3/GCS connector | BH-115 | 5 | Ahmed |
| TBD | [FE] Workspace Portal - Context copywriting UI | BH-114 | 3 | Marwan |
| TBD | [BE] Context Engineering - Workspace context API | BH-110 | 3 | Kuri |
| TBD | [BE] Projects - BHAgent integration | BH-116 | 5 | Harbour |
| TBD | [FE] Projects - Agent interaction UI | BH-116 | 3 | Marwan |

### Carryover from Sprint 3 (3)

| Key | Summary | Status | Points | Assignee |
|-----|---------|--------|--------|----------|
| BH-232 | GitOps approach for server resources | In Progress | 3 | Ahmed |
| BH-136 | Performance monitoring audit | To Do | 2 | Ahmed |
| BH-226 | GetResources mutation bug fix | To Do | 1 | Ahmed |

### Total

- **Tickets**: 10
- **Story Points**: ~27
- **New**: 7 tickets (24 pts)
- **Carryover**: 3 tickets (6 pts)

---

## Team Assignments

| Team Member | Tickets | Points | Focus Area |
|-------------|---------|--------|------------|
| Ahmed | 4 | 11 | DevOps, Unstructured data |
| Marwan | 2 | 6 | Frontend (Portal, Projects) |
| Kuri | 1 | 3 | Context Engineering API |
| Harbour | 1 | 5 | Projects BHAgent integration |
| Team (all) | 2 | 5 | Design specs (Agent Analyst, Slack) |

---

## Backlog Cleanup

### Canceled Tickets (14)

| Key | Reason |
|-----|--------|
| BH-215 | Done as BH-198 (AWS Bedrock) |
| BH-216 | Done as BH-176 (E2B sandbox) |
| BH-223 | Vague, no owner (A2A Output) |
| BH-222 | Vague, no owner (A2A MCP) |
| BH-221 | Generic, no owner (Circuit breaker) |
| BH-220 | Generic, no owner (Workflow traceability) |
| BH-219 | Covered by BH-199 (Quality profiling) |
| BH-218 | Vague, no owner (Schema mismatch) |
| BH-149 | Stale (Distributed task queue) |
| BH-148 | Stale (Parallel processing) |
| BH-145 | Not in roadmap (MS Teams) |
| BH-143 | Vague, stale (Automation workflow) |
| BH-135 | Stale (Persona analytics) |
| BH-134 | Stale (Persona data model) |

### Kept for Future (4)

| Key | Reason |
|-----|--------|
| BH-217 | Valid security work (ABAC restriction) |
| BH-167 | Useful documentation (Connector guide) |
| BH-137 | Valid observability (Distributed tracing) |
| BH-233 | Valid work in progress (EnhancedOMD) |

---

## Dependencies

- Context Engineering (BH-110) ↔ Workspace Portal (BH-114): API supports frontend
- Projects BHAgent (BH-116): Builds on Sprint 3 Projects v0 work
- Background Agent Analyst: Builds on existing BrightAgent infrastructure

---

## Dropped from Sprint 4

| Key | Summary | Reason |
|-----|---------|--------|
| BH-202 | Claude Skills PoC | User request - can be picked up later |

---

## Notes

- Background Agent Analyst and Slack Auth are **team design efforts** - all 4 members collaborate
- Context Engineering spans **two EPICs** (BH-110, BH-114) - coordinate across teams
- BH-202 (Claude Skills) dropped per user request - available for future sprint
