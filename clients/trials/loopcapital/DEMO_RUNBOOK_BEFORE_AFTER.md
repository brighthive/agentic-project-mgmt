# BrightAgent Demo Runbook — Build a Database from a Schema, Load It, Query It, Compare It

**Audience:** GTM / sales team running a live BrightAgent demo on a customer or lab SQL Server.  
**Time:** ~15–20 minutes.  
**Difficulty:** No SQL required — you drive BrightAgent in plain English and check the results.

---

## What this demo shows
In one short session, BrightAgent takes a schema file (.xsd) and stands up a working database from it, loads real data from XML files already sitting on the server, answers business questions about that data, and then compares the new table to a similar table already on the server to prove the load is correct. It does the build-and-load work through dbt, so the customer sees a repeatable, version-controlled pipeline rather than hand-run scripts.

**The story for the customer:**  
*"Hand the agent a schema and some files, and it delivers a queryable, validated database — using the same tooling your data team already trusts."*

---

## Before you start
Confirm these are in place (your SE will have set most of this up):
* [ ] A SQL Server instance is up and connected to BrightAgent (agent IP whitelisted, connection verified).
* [ ] BrightAgent has dbt configured against that SQL Server.
* [ ] You have the demo asset `MarketData.PriceStaging.xsd` on hand.
* [ ] The XML data files are on the server, e.g. `C:\LoopDemo\xml\` (a couple of `eod_prices_*.xml` files — see [Appendix A](#appendix-a--sample-xml-file) for a sample).
* [ ] There is a similar existing table on the server to compare against, e.g. `MarketData_Ref.dbo.PriceStaging` (a known-good copy — see [Appendix B](#appendix-b--the-similar-existing-table-to-compare-against)).

*If any box is unchecked, ping your SE before the demo.*

---

## Run the demo
Each step gives you what to do, what to say to BrightAgent (paste the prompt), and what success looks like.

### 1. Confirm the server connection
* **Do:** Open BrightAgent.
* **Say:** `"Which SQL Server are you connected to, and can you confirm the connection is healthy?"`
* **Success:** Agent names the server and reports the connection is live.

### 2. Create a new project
* **Do:** Start a fresh project/workspace for this demo.
* **Say:** `"Create a new project called LoopCapital-PriceDemo."`
* **Success:** Agent confirms the new project is created and active.

### 3. Add the schema file to the project
* **Do:** Attach or point the agent at `MarketData.PriceStaging.xsd`.
* **Say:** `"Read the PriceStaging.xsd file and tell me what table and columns it describes."`
* **Success:** Agent reports a `PriceStaging` table with `Ticker`, `PriceDate`, `ClosePrice`, `Currency`, including the types and widths (e.g., `Currency` is `char(3)`).

### 4. Create the database and table from the schema via dbt
* **Say:** `"Using dbt, create a MarketData database with a PriceStaging table that matches this .xsd exactly — same columns, types, widths, and nullability."`
* **Success:** Agent runs a dbt build and confirms `MarketData.dbo.PriceStaging` now exists with the columns from the schema. Ask it to show the resulting table definition and check it lines up with the XSD.

### 5. Load the data from the XML files via dbt
* **Say:** `"Populate PriceStaging from the XML files in C:\LoopDemo\xml\, using dbt. Tell me how many rows loaded and flag any rows the schema rejected."`
* **Success:** Agent loads the files and reports a row count. If any value breaks the schema (e.g., a `Currency` longer than 3 characters), it should call that out rather than silently dropping it.

### 6. Ask business questions
* **Do:** Ask a few of the questions below and sanity-check the answers.
* **Say (pick a few):**
  * `"How many rows and how many distinct tickers did we load?"`
  * `"What's the most recent ClosePrice for AAPL?"`
  * `"What date range do the prices cover?"`
  * `"Which tickers are missing a ClosePrice?"`
  * `"List the currencies present and the row count for each."`
* **Success:** Answers are consistent with each other (e.g., distinct tickers ≤ total rows) and match the sample data.

### 7. Compare against the existing table
* **Say:** `"Compare MarketData.dbo.PriceStaging (the one we just built) to MarketData_Ref.dbo.PriceStaging that's already on the server. Tell me if the schemas match, if the row counts match, and list any tickers or price differences between them."`
* **Success:** Agent produces a clear side-by-side: schema match (yes/no), row-count match, and a short list of any differences (rows in one but not the other, or ClosePrice mismatches). For a clean demo this comes back as "schemas match, N rows each, no differences" — or a tidy list of the handful of expected differences if you seeded some.

---

## Pass / fail checklist
Tick each as you go. The demo passes if all are ticked.
* [ ] **Step 3** — Agent correctly read the table + 4 columns from the `.xsd`.
* [ ] **Step 4** — Database and table created via dbt, matching the schema.
* [ ] **Step 5** — Data loaded from the XML files with a row count reported.
* [ ] **Step 6** — Business questions answered correctly and consistently.
* [ ] **Step 7** — New table compared to the existing table with a clear match/difference result.

---

## If something goes wrong
* **"I can't reach the server."** Connection or NSG issue — hand back to your SE; don't try to fix live.
* **Load reports 0 rows.** Check the XML path is correct and the files are actually on the server, not your laptop.
* **Agent flags rejected rows.** That's usually correct behaviour (the data broke the schema) — turn it into a selling point: *"notice it caught the bad values instead of loading garbage."*
* **Comparison shows unexpected differences.** Ask the agent to explain each one; it should tell you whether it's a schema, row-count, or value difference.

---

## Appendix A — sample XML file
Save as `C:\LoopDemo\xml\eod_prices_20260728.xml` on the server. It matches the schema's rowset shape (a `PriceStaging` root with repeating `Row` elements).

```xml
<?xml version="1.0" encoding="utf-8"?>
<PriceStaging xmlns="http://brighthive.net/loopcapital/MarketData/PriceStaging">
  <Row><Ticker>AAPL</Ticker><PriceDate>2026-07-28</PriceDate><ClosePrice>212.500000</ClosePrice><Currency>USD</Currency></Row>
  <Row><Ticker>MSFT</Ticker><PriceDate>2026-07-28</PriceDate><ClosePrice>451.200000</ClosePrice><Currency>USD</Currency></Row>
  <Row><Ticker>SAP</Ticker><PriceDate>2026-07-28</PriceDate><ClosePrice>198.750000</ClosePrice><Currency>EUR</Currency></Row>
  <Row><Ticker>TSM</Ticker><PriceDate>2026-07-28</PriceDate><ClosePrice>184.300000</ClosePrice><Currency>USD</Currency></Row>
  <Row><Ticker>SHEL</Ticker><PriceDate>2026-07-28</PriceDate><Currency>GBP</Currency></Row>
</PriceStaging>
```
*(The last row has no ClosePrice on purpose, so the "which tickers are missing a price" question returns something.)*

---

## Appendix B — the "similar existing table" to compare against
Ask your SE to pre-load a reference copy on the server, e.g. `MarketData_Ref.dbo.PriceStaging`, with the same four columns and the same rows as the sample above. For a more interesting comparison, seed one small difference (e.g., a slightly different `ClosePrice` for one ticker, or one extra ticker) so Step 7 has something concrete to surface.

---
*Companion assets: MarketData.PriceStaging.xsd (the schema used here) and the wider SSIS test packages / test suite from the same demo kit.*
