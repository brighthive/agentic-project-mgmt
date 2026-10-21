---
name: "Loop Capital — AI and data access control requirements (verbatim)"
slug: "loopcapital"
stage: "trial"
champion: "Frank Sung"
champion_email: ""
trial_start: ""
trial_end: ""
decision_date: ""
jira_epic: ""
notion_page: ""
workspace_id: ""
aws_account: ""
status: "active"
tags: [agent-governance, requirements, verbatim, vendor-evaluation]
---

# Loop Capital — AI and data access control requirements (verbatim)

> Source: Frank Sung (VP, Data Management, Loop Capital) → Suzanne El-Moursi, cc Matt Gee, 2026-10-16 17:24,
> "Re: [External] Brighthive : Follow Up - AI Governance". Forwarded to Kuri to lead. Captured as received;
> do not edit the requirements text. Our analysis lives in [`../GOVERNANCE_REQUIREMENTS_FIT.md`](../GOVERNANCE_REQUIREMENTS_FIT.md).

## Context Frank gave

- This is "Part 2" of the AI Governance conversation from the prior Friday.
- **Copilot at Loop:** Microsoft 365 Copilot Basic (previously Microsoft 365 Copilot Chat) is broadly open to
  employees; a smaller number of users have Microsoft 365 Premium. "Copilot" spans many Microsoft products
  (Microsoft 365 Copilot, Copilot Studio, GitHub Copilot, Azure Copilot, …).
- **Competitive evaluation:** Loop is looking at several vendors and products, including **NROC, CrowdStrike Falcon
  Guardian, Proofpoint, Zscaler**, and others, and will compare proposals against these requirements.

## AI and Data Access Control Requirements

We are seeking a vendor solution to govern, monitor, and control employee use of AI tools and related data-sharing
activity. The solution should enforce policy by user identity, account type, device type, application type, and
data sensitivity.

### 1. AI Access Control

The solution must control access to AI platforms and tools, including Microsoft Copilot, ChatGPT, Claude, Gemini,
Perplexity, and similar current or emerging services.

Required access policies:

- Allow approved Work, Team, Business, or Enterprise accounts.
- Deny Personal, Free, or Anonymous accounts.
- Enforce policies by user identity, not only by device or machine.
- Support internal-network computers, firm-issued laptops, firm-issued mobile devices, and personal mobile devices.

The solution should provide visibility and control across AI websites, AI browsers, command-line tools, AI agents,
browser extensions, VS Code extensions, Office add-ins, cloud-based AI agents, and AI mobile apps.

### 2. AI Risk Monitoring

The solution must detect, assess, and control AI-related risks, including:

- Unapproved AI tools or services
- Untrusted MCPs, connectors, plugins, skills, apps, extensions, and add-ins
- AI agents with excessive access to data, systems, repositories, or cloud environments
- Prompt injection attempts from websites, documents, emails, files, repositories, connectors, or agent workflows

The solution should categorize risks by user, application, network, device, data access, connector, and content
sensitivity, and support alerting or blocking based on risk level.

### 3. DLP and Oversharing Protection

The solution must prevent sensitive, confidential, regulated, or proprietary data from being uploaded, pasted,
shared, or exposed to unauthorized AI tools.

Coverage should include prompt text, file uploads, pasted content, browser extensions, add-ins, connectors, plugins,
AI agents, and indirect data access through integrations.

Sensitive data includes client information, financial data, material non-public information, PII, source code,
credentials, tokens, secrets, internal communications, and confidential business documents.

### 4. Reporting and Integration

The solution should provide centralized policy management, logging, alerting, dashboards, and audit-ready reporting.
The vendor should also describe integrations with identity providers, endpoint security, DLP, CASB, SWG, SIEM, SOAR,
and other security platforms, along with deployment model, limitations, licensing, and roadmap for emerging AI tools.
