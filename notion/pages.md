# Brighthive Notion Pages

**Last Updated**: 2026-03-27

This document contains key Notion pages and workspace structure for the Brighthive project.

---

## Workspace Structure

### Primary Hubs

- **Brighthive Home** (ID: `5e0a81f4-5dce-4f7b-b918-96374fc10488`)
  - Company-wide hub: policies, team docs, onboarding, brand, meeting notes
  - URL: https://www.notion.so/Brighthive-Home-5e0a81f45dce4f7bb91896374fc10488

- **Engineering** (Untitled - ID: `5ee7add1-1228-424c-b470-190b94e8a39d`)
  - Engineering processes, runbooks, architecture, deployments

- **Product Management** (ID: `1fa02437-dde4-8052-8360-f15c28339fec`)
  - Product docs, roadmap/vision, designs
  - URL: https://www.notion.so/Product-Management-1fa02437dde480528360f15c28339fec

- **Go-To-Market** (ID: `19302437-dde4-80e5-b46d-de6c7e701ebf`)
  - Messaging, positioning, sales enablement
  - URL: https://www.notion.so/Go-To-Market-19302437dde480e5b46dde6c7e701ebf

### Quick Navigation Map

- **Team / announcements / context** → Brighthive Home → Team column (Jam Notes, What's New, Mission/Vision/Values)
- **Policies & compliance** → Brighthive Home → Policies column (Handbook, Fiscal Policies, Security Policy, SOCII)
- **People / org info** → Brighthive Home → People Directory (database)
- **Brand** → Brand Assets (database)
- **Notes** → Meeting Notes (database) and Jam Notes
- **Customer delivery** → Customer Success area (customer pages like Indiana Tech)

### Glossary

- **The Hive** — Brighthive knowledge center concept (resources, terms, schemas)
- **BrightAgent / BrightBot** — Brighthive agentic system
- **BYOW** — bring your own warehouse

---

## Brighthive Platform Features

**Page ID**: `2ae02437-dde4-80fd-88cc-fe44c2bcf10f`
**URL**: https://www.notion.so/brighthive/Brighthive-Platform-Features-2ae02437dde480fd88ccfe44c2bcf10f

### Ingestion
- Connect to 600+ data sources/databases via Airbyte connectors (CRM, marketing tools, databases like MySQL, PostgreSQL, Snowflake, Mixpanel, Google Analytics)
- Upload CSV files directly to Data Asset Catalog
- Upload non-tabular content (images, videos, links) via Files option

### Governance
- **Data Asset Catalog** - centralized hub for all datasets with unified view across sources
- **Glossary** - define and align on business-specific terms across teams
- **Schemas** - create data structure blueprints manually or via JSON
- **Policies** - add custom compliance standards with reference documents
- **Data Quality Tests** - validate datasets for missing values, duplicates, inconsistent formats, anomalies

### Analytics
- Perform natural language queries on datasets (trends, retention rates, aggregated metrics)
- Create visualizations (bar charts, pie charts, line charts, scatter plots, area charts)
- Generate insights with visual, sourced answers
- Export or download results
- **Jupyter Notebooks** - create analytical workflows including data loading, cleaning, exploration, visualization, and modeling (in development)

### Data Cleaning/Transformation
- Writes dbt queries, creates models, commits to GitHub, handles data transformations

### BrightAgent
- **Six Specialized Agents**
- Agentic policy enforcement - All policies will be applied
- Workspace memory - Remembers user preferences and business context
- Conversational engagement with rigorous agentic reasoning
- **Security**: LLM never accesses raw data, only metadata

### Configuration
- **Warehouse Service** - Connect to your data warehouse (Redshift, Snowflake) or use fully managed option
- **Ingestion Service** - Connect to Airbyte for data ingestion or use fully managed option
- **Transform Service** - Integrate with dbt Cloud for transformations or use fully managed option

---

## Notion CLI Setup

**Token**: Configured via environment variable `NOTION_TOKEN`

### Useful Commands

```bash
# List all accessible pages
NOTION_TOKEN="ntn_Fl..." notion-cli search "" -f json

# Get page metadata
NOTION_TOKEN="ntn_Fl..." notion-cli pages get <page-id> -f json

# Get page content (blocks)
NOTION_TOKEN="ntn_Fl..." notion-cli blocks children <page-id> -f json

# Search for pages
NOTION_TOKEN="ntn_Fl..." notion-cli search "query" -f json
```

### Key Page IDs

| Page Name | Page ID |
|-----------|---------|
| Brighthive Home | `5e0a81f4-5dce-4f7b-b918-96374fc10488` |
| Workspace Index (Kuri) | `7117b971-b642-4eb9-8e38-298ee66612d5` |
| Brighthive Platform Features | `2ae02437-dde4-80fd-88cc-fe44c2bcf10f` |
| Product Management | `1fa02437-dde4-8052-8360-f15c28339fec` |
| Go-To-Market | `19302437-dde4-80e5-b46d-de6c7e701ebf` |
| Sprint Planning | `142bbca0-9ba0-4d84-9960-420aa06889be` |
| Active Sprint | `2f202437-dde4-8110-8851-c7ce0cac1c89` |
| Q1 Roadmap & Milestones | `2f202437-dde4-81f1-911a-fd4d7782e19d` |
| Sprint Archive | `2f202437-dde4-8191-b4a2-fe4b5d72f0e2` |
| Sprint 1 | `2fd02437-dde4-81fc-8391-ec370f547957` |
| Sprint 2 | `2fd02437-dde4-81f2-942b-fd6e3d4294d8` |
| Sprint 3 | `2fd02437-dde4-81fe-b7e2-e7b689fc0679` |
| Sprint 4 | `30402437-dde4-81ec-96e2-e68d53bf77c5` |
| Sprint 5 | `30c02437-dde4-8127-808d-c79ee7d75a7a` |
| Sprint 6 | `31902437-dde4-81cd-851d-d24b875bff29` |
| Sprint 7 (Unofficial) | `32e02437-dde4-8133-a1f8-d3f7120ee877` |
| Q1 2026 Summary — CEO Report | `32602437-dde4-8124-8ab2-e17283318cb4` |

---

## Sprint Planning

**Page ID**: `142bbca0-9ba0-4d84-9960-420aa06889be`
**URL**: https://www.notion.so/142bbca09ba04d849960420aa06889be
**Icon**: ⛽
**Parent**: Engineering

### Child Pages

| Page | ID | URL |
|------|----|-----|
| Active Sprint | `2f202437-dde4-8110-8851-c7ce0cac1c89` | https://www.notion.so/2f202437dde481108851c7ce0cac1c89 |
| Q1 Roadmap & Milestones | `2f202437-dde4-81f1-911a-fd4d7782e19d` | https://www.notion.so/2f202437dde481f1911afd4d7782e19d |
| Sprint Archive | `2f202437-dde4-8191-b4a2-fe4b5d72f0e2` | https://www.notion.so/2f202437dde48191b4a2fe4b5d72f0e2 |
| Sprint 1 (Jan 13-20, 2026) | `2fd02437-dde4-81fc-8391-ec370f547957` | https://www.notion.so/2fd02437dde481fc8391ec370f547957 |
| Sprint 2 (Jan 20-27, 2026) | `2fd02437-dde4-81f2-942b-fd6e3d4294d8` | https://www.notion.so/2fd02437dde481f2942bfd6e3d4294d8 |
| Sprint 3 (Jan 27 - Feb 3, 2026) | `2fd02437-dde4-81fe-b7e2-e7b689fc0679` | https://www.notion.so/2fd02437dde481feb7e2e7b689fc0679 |
| Sprint 4 (Feb 3-10, 2026) | `30402437-dde4-81ec-96e2-e68d53bf77c5` | https://www.notion.so/30402437dde481ec96e2e68d53bf77c5 |
| Sprint 5 (Feb 10-17, 2026) | `30c02437-dde4-8127-808d-c79ee7d75a7a` | https://www.notion.so/30c02437dde48127808dc79ee7d75a7a |
| Sprint 6 (Feb 19 - Mar 4, 2026) | `31902437-dde4-81cd-851d-d24b875bff29` | https://www.notion.so/31902437dde481cd851dd24b875bff29 |
| Sprint 7 — Unofficial (Mar 4-24, 2026) | `32e02437-dde4-8133-a1f8-d3f7120ee877` | https://www.notion.so/32e02437dde48133a1f8d3f7120ee877 |
| Q1 2026 Summary — CEO Report | `32602437-dde4-8124-8ab2-e17283318cb4` | https://www.notion.so/32602437dde481248ab2e17283318cb4 |
| Jira & Process | `2f202437-dde4-810e-8417-db7724461c44` | https://www.notion.so/2f202437dde4810e8417db7724461c44 |

### Sprint Emojis

| Sprint | Emoji |
|--------|-------|
| Sprint 1 | 🍇 |
| Sprint 2 | 🥝 |
| Sprint 3 | 🍎 |
| Sprint 4 | 🍍 |
| Sprint 5 | 🍋 |
| Sprint 6 | 🍉 |
| Sprint 7 | 🔧 |

---

## Notes

- Pages must be explicitly shared with your Notion integration to be accessible via API
- Parent page access (like Brighthive Home) grants access to all child pages
- The Workspace Index page provides a comprehensive map of the Notion workspace structure
