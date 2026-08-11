# Demo Runbook — moved

The Loop Capital demo runbook now lives in **[`demo.md`](./demo.md)** — a single
canonical runbook for Frank Sung's "3 + 1" scenario: read a legacy `.xsd` contract,
rebuild the pipeline as version-controlled dbt models (committed as BrightAgent[bot]),
materialize into Azure Synapse via dbt Cloud, then compare 1:1 against Frank's live
SQL Server table and govern the result across chat, MCP, the observability page, and Slack.

This file previously held a duplicate keyed to an invented `MarketData.PriceStaging`
fixture that does not exist in the sandbox. It was collapsed to this pointer so the
grounded runbook (`demo.md`) is the one source of truth.
