"""Day-by-day expectation matrix for the Longaeva trial.

This is the SoT for what's expected on each trial day. The renderer paints a
checkbox for each row and auto-checks it when all linked items reach
Done/Merged. Edit this file to tune what the trial expects to see.

Schema:
    Phase: top-level grouping ("Pre-trial", "Days 1-5", etc.).
    Expectation: one outcome on a given day. Linked items are tickets or PRs
        that, when collectively Done/Merged, mark the row green.

Linked items can be either:
    - "BH-XXX" (a Jira ticket — Done means status_category == "Done")
    - "REPO#NUM" (a PR shorthand — must match keys in pr_states map; merged means MERGED)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Expectation:
    """One expected outcome on a trial day."""

    day: str               # "Day 1" | "Pre-trial" | "Day 14" — free form for grouping
    outcome: str           # human-readable goal
    linked: tuple[str, ...] = ()  # BH-XXX or REPO#NUM tokens

    def is_green(
        self, *, ticket_statuses: dict[str, str], merged_pr_keys: set[str]
    ) -> bool | None:
        """Return True/False if linked items resolve cleanly; None when no links (manual)."""
        if not self.linked:
            return None  # manual outcome, no auto-check
        for item in self.linked:
            if item.startswith("BH-"):
                if ticket_statuses.get(item, "").lower() != "done":
                    return False
            else:
                # PR shorthand: "<repo>#<num>"
                if item not in merged_pr_keys:
                    return False
        return True


@dataclass(frozen=True)
class Phase:
    """Top-level grouping for expectations."""

    title: str
    description: str
    expectations: tuple[Expectation, ...]


# Concrete plan — derived from clients/trials/longaeva/scorecard.md and
# poc-scope-from-client.md. Trial days are *relative* to the agreed start;
# adjust as the schedule firms up.
EXPECTATION_PLAN: tuple[Phase, ...] = (
    Phase(
        title="Pre-trial — Snowflake foundation must be merged",
        description=(
            "All Phase 1 Snowflake integration PRs land before Day 1. Without "
            "these, brightbot can't query Snowflake and the trial can't run §1 "
            "ingestion or §2 semantic-view enrollment."
        ),
        expectations=(
            Expectation(
                day="Pre-trial",
                outcome="brightbot Layer 5 (SnowflakeConnection + dialect + tests) merged",
                linked=("BH-527", "BH-528", "BH-549", "BH-550", "BH-553"),
            ),
            Expectation(
                day="Pre-trial",
                outcome="Atlas semantic-view YAML scaffold tool merged (BH-531)",
                linked=("BH-531",),
            ),
            Expectation(
                day="Pre-trial",
                outcome="OMD ingestion lambda Layer 3 (SnowflakeSourceConfig) merged",
                linked=("BH-551",),
            ),
            Expectation(
                day="Pre-trial",
                outcome="Org-CDK ingestion stack reads workspace_secret_store",
                linked=("BH-554",),
            ),
            Expectation(
                day="Pre-trial",
                outcome="Webapp Snowflake form audit signed off",
                linked=("BH-552",),
            ),
            Expectation(
                day="Pre-trial",
                outcome="dbt agent GitHub Enterprise base_url config merged",
                linked=("BH-529",),
            ),
            Expectation(
                day="Pre-trial",
                outcome="GX output: serialize as YAML to repo branch (not Markdown to S3)",
                linked=("BH-530",),
            ),
            Expectation(
                day="Pre-trial",
                outcome="Quality agent CRUD resolvers + service merged",
                linked=("BH-541",),
            ),
            Expectation(
                day="Pre-trial",
                outcome="Quality → BrightSignals wiring + webapp side-menu live",
                linked=("BH-557", "BH-558"),
            ),
            Expectation(
                day="Pre-trial",
                outcome="Trial start date confirmed with Grant",
                linked=(),  # manual
            ),
            Expectation(
                day="Pre-trial",
                outcome="Trial-user list confirmed (1-2 DEs + 1-2 DSs)",
                linked=(),  # manual
            ),
        ),
    ),
    Phase(
        title="Days 1-5 — Provision + context layer",
        description=(
            "Stack connectivity validated; reference schemas + Atlas YAML spec "
            "loaded into the workspace KG. Joint working session on Day 3."
        ),
        expectations=(
            Expectation(
                day="Day 1",
                outcome="Use cases + success criteria confirmed (joint kickoff)",
                linked=(),
            ),
            Expectation(
                day="Day 2",
                outcome="Longaeva provisions stack access (Snowflake, S3, dbt, Dagster, GHE, MCP)",
                linked=(),
            ),
            Expectation(
                day="Day 3",
                outcome="Workspace provisioned + Snowflake connectivity validated",
                linked=("BH-533",),
            ),
            Expectation(
                day="Day 3",
                outcome="MCP client config to Longaeva's MCP server confirmed",
                linked=("BH-532",),
            ),
            Expectation(
                day="Day 4",
                outcome="Context layer built — reference schemas + Atlas YAML spec in KG",
                linked=("BH-534",),
            ),
            Expectation(
                day="Day 5",
                outcome="Environment mapping validated (joint review)",
                linked=(),
            ),
        ),
    ),
    Phase(
        title="Days 6-10 — Trial executions",
        description=(
            "Run the three ingestion scenarios + semantic-view enrollment + MCP "
            "validation. This is where the platform shows up."
        ),
        expectations=(
            Expectation(
                day="Day 6-8",
                outcome="Ingestion: S3 vendor bucket scenario merge-ready",
                linked=("BH-535",),
            ),
            Expectation(
                day="Day 6-8",
                outcome="Ingestion: REST API scenario merge-ready",
                linked=("BH-535",),
            ),
            Expectation(
                day="Day 6-8",
                outcome="Ingestion: Snowflake Data Share scenario merge-ready",
                linked=("BH-535",),
            ),
            Expectation(
                day="Day 8-10",
                outcome="Semantic view scaffolded for ≥1 Silver table (Atlas YAML)",
                linked=("BH-536",),
            ),
            Expectation(
                day="Day 8-10",
                outcome="Reference-data binding (LEI/FIGI / fiscal calendar / geo) auto-detected",
                linked=("BH-536",),
            ),
            Expectation(
                day="Day 8-10",
                outcome="MCP validation: enrolled view queryable through Longaeva's MCP",
                linked=("BH-536",),
            ),
        ),
    ),
    Phase(
        title="Days 11-14 — Maintenance demo + final evaluation",
        description=(
            "Self-healing PRs, longitudinal anomaly signals, Slack triage. Then "
            "joint scorecard review and commercial next-steps discussion."
        ),
        expectations=(
            Expectation(
                day="Day 11-12",
                outcome="Self-healing: schema drift → surgical fix PR demonstrated",
                linked=(),
            ),
            Expectation(
                day="Day 11-12",
                outcome="Self-healing: missing partition / broken stage / dbt contract fail",
                linked=(),
            ),
            Expectation(
                day="Day 11-12",
                outcome="Longitudinal anomaly: ≥1 of {row-count / cardinality / skew / nulls}",
                linked=(),
            ),
            Expectation(
                day="Day 11-12",
                outcome="Slack alerts: triage-ready (dataset + severity + PR/run link)",
                linked=("BH-557",),
            ),
            Expectation(
                day="Day 11-12",
                outcome="Slack bidirectional: @brightagent answers pipeline-state question",
                linked=(),
            ),
            Expectation(
                day="Day 13",
                outcome="Final scorecard filled (17 success criteria scored)",
                linked=(),
            ),
            Expectation(
                day="Day 14",
                outcome="Commercial next-steps discussion scheduled",
                linked=(),
            ),
        ),
    ),
    Phase(
        title="Post-trial — followups",
        description=(
            "Things tracked but not gated by the 14-day window. Update as the "
            "decision lands."
        ),
        expectations=(
            Expectation(
                day="Post",
                outcome="Decision recorded (Won / Lost / Extended) with rationale",
                linked=(),
            ),
            Expectation(
                day="Post",
                outcome="JWT/key-pair Snowflake auth (Phase 2)",
                linked=(),
            ),
        ),
    ),
)
