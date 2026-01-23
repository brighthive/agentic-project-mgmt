# Brighthive Notion Pages

**Last Updated**: 2026-01-14

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

---

## Notes

- Pages must be explicitly shared with your Notion integration to be accessible via API
- Parent page access (like Brighthive Home) grants access to all child pages
- The Workspace Index page provides a comprehensive map of the Notion workspace structure
