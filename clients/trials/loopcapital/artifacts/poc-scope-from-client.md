# Loop Capital — POC Scope, Verbatim From Source Messages

> Captured 2026-07-12 from Slack/meeting notes shared in conversation. Kept verbatim where
> possible so nothing is lost in paraphrase — this is the raw input the engineering response
> (`../overview.md`, the handover spec) was built against.

## POC Scope — Technical Deep Dive (7/9 meeting, planned scope)

> Our Approach: One agent that focused on legacy architecture that completes full analysis
> and diagnosis of the SSIS/SSRS environment.
>
> "Legacy Analyst Analyzer Agent" - has three skills: SSIS, SSRS, Storage Optimization
>
> Part 1: Show me how BA is able to run SSIS to find out analysis and diagnosing to find out
> bottlenecks. To dos: Create synthetic SSIS file set agnatically using Claude — give the
> template to format to Claude and ask it to create 5 tables (micro synthetic set), 5 tables -
> representation of Loop data model — Asset Management.
>
> Issue Analysis: Create a Claude skill to our data quality agent — create it as a sub agent to
> focus on SSIS only. Provide it with a skill to look for specific things: Processing time —
> look at a SSIS file and identify the processes that are running which make the processing
> time prolonged, suggest improvements to speed. Being able to take a downstream issue and
> identify what is going on with the SSIS package.
>
> Build the Data Quality agent skill: two skills — Identify and Propose Changes to the SSIS
> file; Rewrite this in dbt to make it more efficient.
>
> Part 2: Analyze the SSRS report to find out where is the bottleneck and improve the
> reporting.
>
> Part 3: Analyze the storage for optimization (diagnosis, recommend, implement).
>
> Provide a resource costing to show what the cost will be (cost management).
>
> Timeline Plan: By Thursday July 2nd — @matt Kick off in Brighthive Studio. To get started,
> need: SSIS - Data assets (Matt will provide a link to assets); Acceptance criteria and
> blueprint for what to look for and diagnose (created in Brighthive Studio).
>
> Need to do: @Kuri Chinca — Model changes — need to be running on Bedrock.

**Resolution**: fully shipped, verified against BH-860 epic + 14 tickets, all Done. See
`../overview.md` Track A.

## Post-Demo Feedback (Suzanne, Slack, following the 7/9 demo)

> I pressed him to give us one more [week]. I promised him that we see the future world the
> same way and what we're building is for that future. I launched the platform and showed
> some of those new pages, he is smart and said "but your screen says this is not live"

> Next meeting is 7/17 — pushing us another week before we can begin to close this deal into a
> sale. We need to really manage the engineering readiness at each sales gate. Here is what I
> included: "Thanks for the time Frank. We will demo
>
> 1. The engineering agent and how it proactively monitors, detects and resolves issues with
>    the ability to alert the user on what it finds.
> 2. The ability/how the MCP will connect to the SQL server when the server does not have an
>    MCP. This is important for such tasks as monitoring the disk space and alerting when
>    "it's at 20% capacity left" so we avoid problems.
> 3. The ability to build skills that help "surface the fixes the agent applied when they are
>    not abided by so we can avoid the recurrence of the same kind of issue"
>
> Essentially, we will go deeper and wider in the core Brighthive capabilities of the
> engineering agent and the nightshift, with a focus on how they power proactivity in the end
> to end data engineering workflow as you would expect from a human data engineer. Our
> platform has all the infrastructure, tooling and skills for these use cases and we did not
> show them fully yesterday."

**Resolution**: in progress. See `../overview.md` Track B and the handover spec
(`../../../docs/specs/proactive-pipeline-ingestion-monitoring.md`).

## Frank's own words (direct quotes worth preserving)

> "But your screen says this is not live" — reacting to a page shown in the demo that wasn't
> backed by real data/infrastructure. Root cause of the sales-gate distrust; directly informs
> why the engineering response insists on real-behavior testing (real SQL Server, real dbt
> Cloud job) rather than mocked demos.

> "I don't think that you're there because I did not see how your digital engineers are going
> to do the level of proactivity that I'm imagining to make it impactful for the human
> engineers." — his core skepticism: not that the vision is wrong, but that BrightHive hasn't
> yet SHOWN the proactivity depth he believes is coming.

> On Matt's MCP-to-SQL-server claim: "I don't think this will be successful if the SQL server
> does not have any MCP or any other service to actually connect. So how are you going to
> actually connect and extract or monitor the SQL jobs. I don't believe what he shared with me
> will work." — the specific technical objection Track B's SQL-Server workstream directly
> answers.
