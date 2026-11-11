---
title: "Brightbot standalone MCP serving"
epic: "AZ-101"
author: "drchinca"
status: "Draft"
created: "2026-11-11"
generates: "tickets"
tags: [mcp, azure, deployment]
related:
  features: []
  pocs: []
  bedrock: []
---

# Brightbot standalone MCP serving

## 1. Context

After the separate Brightagent one-tool proof, serve Brightbot's existing MCP
tools through the private Azure deployment in Brighthive-basic. Reuse Harbour's
Govern work in Brightbot #1213 at `9d3d1ba0456db896253f458191e5c02d7e40a4a5`;
this serving change does not establish permission-matrix enforcement or Core
readiness. The current mandatory `langgraph-api` 0.8.7 and
`langgraph-runtime-inmem` 0.28.0 use Elastic-2.0, which does not meet the user's
open-source requirement. The underlying LangGraph library is a separate component.

Existing `http/app.py` assembles the correct MCP server, middleware and metadata,
but also imports hosted thread/run APIs and scheduling routes. Tool registration
eagerly constructs agent models even when no agent is invoked. Reuse the MCP
assembly and defer those model imports until execution.

## 2. Interface contract

| Boundary | Contract |
|---|---|
| CLI | `brightbot mcp --host 127.0.0.1 --port 8000`; process owns one ASGI server |
| MCP | Existing `/bh-mcp/`, server identity `brightbot-mcp`, current tool schemas |
| Health | Public `GET /health` returns `{"status":"ok"}` only after MCP lifespan starts; process health, not downstream readiness |
| Identity | Existing `MCPAuthMiddleware`, principal resolution and public protected-resource metadata; no alternative bypass |
| Deployment | Deploy `mcp.profile=brightbot` retains Envoy `/mcp` rewrite, loopback binding, private dependencies and digest pins |
| Dependencies | Default standalone installation excludes Agent Server; explicit `hosted` extra retains that existing development/runtime option |

The executable must accept Deploy's host/port arguments. The standalone app
does not mount hosted thread, run, scheduler or Slack routes. It still registers
the real approved MCP tools; feature flags and Azure tool lockdown keep their
existing meanings. Model execution remains in-process when invoked.

## 3. Invariants

1. Startup, health and MCP metadata need no model key, LangSmith key, commercial
   license or network request to a model provider.
2. Default resolved dependencies contain neither `langgraph-api` nor
   `langgraph-runtime-inmem`; hosted use remains an explicit optional install.
3. Existing auth middleware protects every MCP call. Production-like Azure
   execution cannot enable local-dev auth or an unbound API-key caller.
4. Disabled tool groups are not imported. Deferring imports does not change
   schemas, tool names, feature flags or call-time permission checks.
5. The same MCP assembly supplies the hosted and standalone applications;
   lifespan startup/shutdown is retained, including streamable HTTP sessions.
6. Errors and logs contain no tokens, model keys or returned customer data.

## 4. Acceptance criteria

```gherkin
Feature: Standalone Brightbot MCP
  Scenario: Clean default installation
    Given the locked default dependency set in a fresh environment
    Then neither Agent Server package is installed
    And the CLI starts without model or hosted-service credentials
  Scenario: Actual HTTP boundary
    Given the standalone process with production-like Azure settings
    When a real HTTP client calls health and protected-resource metadata
    Then both respond without credentials
    And an unsigned MCP request receives 401 with a sign-in challenge
    And hosted thread and run routes return 404
  Scenario: Existing MCP tools and lifespan
    Given a synthetic authenticated principal supplied by the existing auth seam
    When a real MCP client initializes and discovers tools
    Then the server identifies as brightbot-mcp with the reviewed tool list
    And a non-model tool executes without initializing any model client
  Scenario: No local authentication bypass on Azure
    Given LOCAL_DEV_MODE=true in a production-like Azure configuration
    When an unsigned MCP request arrives
    Then it is refused
```

## 5. Out of scope

Govern READ enforcement, Core issuer/audience fixes, private Core dependencies,
customer license provenance, image promotion, Azure credentials, SQL grants,
job scheduling parity, full Agent Server APIs and the separate Brightagent
installer. Each remains a deployment acceptance gate where required; this
entrypoint alone does not establish that Brightbot is ready on Azure.

## 6. Dependencies and review slices

- Dependency packaging first, preserving existing locked versions; then shared
  MCP assembly/CLI and deferred imports. Keep each PR under 700 changed lines.
- Existing Deploy handoff: `brighthive-deploy/docs/specs/brightbot-deployment.md`.
- Before release: exact image/native/transitive license inventory, established
  application-source license rights, synthetic Core membership/matrix and a
  real private Azure run. No software relicensing is authorized by this spec.

## 7. Correctness properties

Unauthenticated transport cannot reach a tool. Lazy model construction cannot
remove authorization or tool schemas. Installing the default package cannot
silently add the optional Agent Server. These cover invariants 1–5 and all
four scenarios.

## 9. Observability

Use existing request/tool outcome logging. Health reports only process state;
no downstream connectivity, model readiness or Govern acceptance is inferred.
No model-output evaluation changes are included in this serving slice.

## 10. Test coverage update

Extend the existing MCP server/auth tests with real ASGI lifespan/HTTP checks
and a real MCP client against the same factory. Run a clean subprocess with
no inherited secrets, no dotenv loading and no model/hosted keys; check unsigned
refusal and a non-model tool. Verify locked exports for default and hosted extras.
After the application security/deployment dependencies close, extend the existing
cross-repo MCP suite for the private Azure endpoint and actual Govern decisions.
Mock-only registration tests cannot replace the clean startup/transport checks.

Sources: [Agent Server license](https://pypi.org/project/langgraph-api/0.8.7/),
[in-memory runtime license](https://pypi.org/project/langgraph-runtime-inmem/0.28.0/).
