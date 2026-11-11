"""Build delivery and innings match-state context from the supplied data pack.

This step intentionally produces context and provisional flags only. It does
not calculate player ratings or rankings.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
OUTPUTS = ROOT / "outputs"


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ball = pd.read_csv(RAW / "ball_by_ball.csv", low_memory=False)
    matches = pd.read_csv(RAW / "matches.csv", low_memory=False)
    competitions = pd.read_csv(RAW / "competitions.csv", low_memory=False)
    return ball, matches, competitions


def extra_base_runs(extra_type: pd.Series) -> pd.Series:
    """Return the standard one-run base for observed extra events.

    The source exposes category labels and a sparse additional-run field, but
    no direct total-extras column. This is an explicit reconstruction assumption
    and is validated against match-level totals where possible.
    """

    return extra_type.notna().astype("int64")


def normalized_limit(value: pd.Series) -> pd.Series:
    """Normalize revised-overs fields stored as six-ball units."""

    numeric = pd.to_numeric(value, errors="coerce")
    return numeric.where((numeric <= 20) | numeric.isna(), numeric / 6)


def build_context() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    ball, matches, competitions = load_inputs()
    match_columns = [
        "match_id",
        "comp_id",
        "match_date",
        "result",
        "first_inn_revised_overs",
        "second_inn_revised_overs",
        "revised_target",
    ]
    context = ball.merge(matches[match_columns], on="match_id", how="left", validate="many_to_one")
    context = context.merge(
        competitions[["comp_id", "match_format", "season"]],
        on="comp_id",
        how="left",
        validate="many_to_one",
    )
    context["ordinary_innings"] = context["innings"].isin([1, 2])
    context["abandoned_or_no_result"] = context["result"].astype("string").str.contains(
        "abandoned|no result", case=False, na=False
    )
    context["is_wide"] = context["extras_type"].eq("wide")
    context["is_overstep"] = context["extras_type"].eq("Overstep")
    context["ambiguous_extra_type"] = context["extras_type"].eq("other") | context["extras_type"].eq("Penalty")
    context["legal_ball"] = ~(context["is_wide"] | context["is_overstep"])
    context["extra_base_runs_assumed"] = extra_base_runs(context["extras_type"])
    context["team_runs_event"] = (
        context["runs"].fillna(0)
        + context["extras_2_runs"].fillna(0)
        + context["extra_base_runs_assumed"]
    )
    context["delivery_sequence"] = context.groupby(["match_id", "innings"], sort=False).cumcount() + 1
    context = context.sort_values(["match_id", "innings", "delivery_sequence"]).reset_index(drop=True)
    group = context.groupby(["match_id", "innings"], sort=False)
    context["score_before"] = group["team_runs_event"].cumsum() - context["team_runs_event"]
    context["score_after"] = group["team_runs_event"].cumsum()
    context["wickets_before"] = group["is_wicket"].cumsum() - context["is_wicket"].astype(int)
    context["wickets_after"] = group["is_wicket"].cumsum()
    context["legal_balls_before"] = group["legal_ball"].cumsum() - context["legal_ball"].astype(int)
    context["legal_balls_after"] = group["legal_ball"].cumsum()
    context["innings_final_score"] = group["score_after"].transform("max")
    context["innings_final_wickets"] = group["wickets_after"].transform("max")
    context["innings_final_legal_balls"] = group["legal_balls_after"].transform("max")

    first_limit = normalized_limit(context["first_inn_revised_overs"])
    second_limit = normalized_limit(context["second_inn_revised_overs"])
    revised_overs = np.where(
        context["innings"].eq(1),
        first_limit,
        second_limit,
    )
    context["innings_overs_limit"] = pd.Series(revised_overs, index=context.index).fillna(20.0)
    context["innings_ball_limit"] = context["innings_overs_limit"] * 6
    context["balls_remaining_before"] = (
        context["innings_ball_limit"] - context["legal_balls_before"]
    ).clip(lower=0)
    context["innings_completion_status"] = np.select(
        [
            context["innings_final_wickets"] >= 10,
            context["innings_final_legal_balls"] >= context["innings_ball_limit"],
            context["innings"].eq(2) & context["abandoned_or_no_result"],
        ],
        ["all_out", "overs_complete", "abandoned_or_no_result"],
        default="completed_or_stopped_early",
    )

    first_totals = (
        context[context["innings"].eq(1)]
        .groupby("match_id")["innings_final_score"]
        .max()
        .rename("first_innings_score")
    )
    context = context.join(first_totals, on="match_id")
    valid_revised = context["revised_target"].notna() & (context["revised_target"] > 0)
    context["target"] = np.where(
        context["innings"].eq(2) & valid_revised,
        context["revised_target"],
        context["first_innings_score"] + 1,
    )
    context["valid_chase_context"] = (
        context["innings"].eq(2)
        & context["ordinary_innings"]
        & ~context["abandoned_or_no_result"]
        & context["first_innings_score"].notna()
        & (context["target"] > 0)
    )
    context["runs_required_before"] = np.where(
        context["valid_chase_context"],
        (context["target"] - context["score_before"]).clip(lower=0),
        np.nan,
    )
    context["wickets_in_hand_before"] = np.where(
        context["valid_chase_context"], 10 - context["wickets_before"], np.nan
    )
    context["current_run_rate"] = np.where(
        context["legal_balls_before"] > 0,
        context["score_before"] / context["legal_balls_before"] * 6,
        np.nan,
    )
    context["required_run_rate"] = np.where(
        context["valid_chase_context"] & (context["balls_remaining_before"] > 0),
        context["runs_required_before"] / context["balls_remaining_before"] * 6,
        np.nan,
    )
    context["rrr_minus_crr"] = context["required_run_rate"] - context["current_run_rate"]
    context["target_reached_before"] = context["valid_chase_context"] & (
        context["runs_required_before"] <= 0
    )
    context["target_reached_after"] = context["valid_chase_context"] & (
        context["target"] <= context["score_after"]
    )
    group = context.groupby(["match_id", "innings"], sort=False)
    innings_target_reached = group["target_reached_after"].transform("any")
    innings_all_out = context["innings_final_wickets"] >= 10
    innings_overs_complete = context["innings_final_legal_balls"] >= context["innings_ball_limit"]
    context["innings_valid_for_pressure"] = (
        context["ordinary_innings"]
        & ~context["abandoned_or_no_result"]
        & (innings_all_out | innings_overs_complete | innings_target_reached)
    )
    context["valid_chase_context"] = context["valid_chase_context"] & context["innings_valid_for_pressure"]

    # Provisional hypotheses, not final pressure labels.
    context["pressure_chase_candidate"] = (
        context["valid_chase_context"]
        & ~context["target_reached_before"]
        & (context["balls_remaining_before"] <= 48)
        & (
            (context["required_run_rate"] >= 10)
            | ((context["rrr_minus_crr"] >= 3) & (context["wickets_in_hand_before"] <= 6))
        )
    )
    context["pressure_general_candidate"] = (
        context["innings_valid_for_pressure"]
        & ~context["target_reached_before"]
        & (context["balls_remaining_before"] <= 36)
        & (
            (context["wickets_in_hand_before"] <= 6)
            | (context["valid_chase_context"] & (context["runs_required_before"] <= 36))
        )
    )
    context["pressure_semantics_warning"] = context["ambiguous_extra_type"]

    summaries = []
    for (match_id, innings), frame in context.groupby(["match_id", "innings"], sort=True):
        first = frame.iloc[0]
        summaries.append(
            {
                "match_id": match_id,
                "innings": innings,
                "batting_team_id": frame["batting_team_id"].iloc[0],
                "bowling_team_id": frame["bowling_team_id"].iloc[0],
                "rows": len(frame),
                "final_score": int(frame["score_after"].iloc[-1]),
                "wickets": int(frame["wickets_after"].iloc[-1]),
                "legal_balls": int(frame["legal_balls_after"].iloc[-1]),
                "innings_overs_limit": first["innings_overs_limit"],
                "completion_status": frame["innings_completion_status"].iloc[-1],
                "ordinary_innings": bool(first["ordinary_innings"]),
                "abandoned_or_no_result": bool(first["abandoned_or_no_result"]),
                "ambiguous_extra_rows": int(frame["ambiguous_extra_type"].sum()),
                "revised_target": first["revised_target"],
                "target_reached": bool(frame["target_reached_after"].any()),
                "validation_status": "review_assumptions" if frame["ambiguous_extra_type"].any() else "reconstructed",
            }
        )
    innings_summary = pd.DataFrame(summaries)

    coverage_rows = []
    variants = [
        ("chase_baseline", "chase", 48, 10, 3),
        ("chase_stricter", "chase", 30, 12, 4),
        ("chase_looser", "chase", 60, 8, 2),
        ("general_baseline", "general", 36, 0, 0),
        ("general_stricter", "general", 24, 0, 0),
        ("general_looser", "general", 48, 0, 0),
    ]
    for name, kind, balls_limit, rrr_limit, gap_limit in variants:
        eligible = context["valid_chase_context"] if kind == "chase" else context["innings_valid_for_pressure"]
        if kind == "chase":
            flag = (
                eligible & ~context["target_reached_before"]
                & (context["balls_remaining_before"] <= balls_limit)
                & ((context["required_run_rate"] >= rrr_limit) | (
                    (context["rrr_minus_crr"] >= gap_limit)
                    & (context["wickets_in_hand_before"] <= 6)
                ))
            )
        else:
            flag = eligible & ~context["target_reached_before"] & (context["balls_remaining_before"] <= balls_limit) & (
                (context["wickets_in_hand_before"] <= 6)
                | (context["valid_chase_context"] & (context["runs_required_before"] <= balls_limit))
            )
        flagged = context[flag]
        coverage_rows.append(
            {
                "definition": name,
                "eligible_deliveries": int(eligible.sum()),
                "flagged_deliveries": int(flag.sum()),
                "matches": int(flagged["match_id"].nunique()),
                "innings": int(flagged[["match_id", "innings"]].drop_duplicates().shape[0]),
                "batters": int(flagged["striker_id"].nunique()),
                "bowlers": int(flagged["bowler_id"].nunique()),
                "thresholds": f"balls_remaining<={balls_limit}; rrr>={rrr_limit}; rrr_minus_crr>={gap_limit}",
            }
        )
    coverage = pd.DataFrame(coverage_rows)
    return context, innings_summary, coverage, [
        "extras1_runs is categorical: observed values map one-to-one to extra labels, so it was not added to score.",
        "team_runs_event = runs + extras_2_runs + one base run for every non-null extras_type. This is a transparent reconstruction assumption.",
        "wide and Overstep are treated as non-legal deliveries. 'other' is treated as legal because its legal-ball meaning is not independently documented; rows are flagged for review.",
        "All T20 and T20I competitions were assigned a default 20-over limit. Revised-overs values above 20 were observed as multiples of six (for example 42, 48, 90, 114) and normalized to legal-ball limits divided by six.",
        "Chase pressure excludes innings 3/4, abandoned/no-result matches, and rows without a valid first-innings total.",
    ]


def write_outputs() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    context, innings_summary, coverage, assumptions = build_context()
    context.to_csv(PROCESSED / "delivery_context.csv", index=False)
    innings_summary.to_csv(PROCESSED / "innings_summary.csv", index=False)
    coverage.to_csv(OUTPUTS / "pressure_coverage_summary.csv", index=False)

    ordinary = context[context["ordinary_innings"]]
    super_rows = context[~context["ordinary_innings"]]
    revised_chase = (
        context[
            context["revised_target"].notna()
            & context["innings"].eq(2)
            & context["valid_chase_context"]
        ]
        .groupby("match_id")["target_reached_after"]
        .any()
    )
    report = [
        "# Provisional Pressure Definition Options",
        "",
        "This report documents match-state reconstruction and candidate pressure flags only. "
        "It does not rank players or calculate player performance indices.",
        "",
        "## Match and innings structure",
        "",
        f"- Delivery rows: **{len(context)}**.",
        f"- Reconstructed match/innings groups: **{context[['match_id', 'innings']].drop_duplicates().shape[0]}**.",
        f"- Ordinary innings 1/2 rows: **{len(ordinary)}**.",
        f"- Super-over/extra-innings rows (innings 3/4): **{len(super_rows)}**, across "
        f"**{super_rows['match_id'].nunique()}** matches.",
        f"- Abandoned/no-result match rows: **{context[context['abandoned_or_no_result']]['match_id'].nunique()}** matches.",
        f"- Revised-target matches: **{context[context['revised_target'].notna()]['match_id'].nunique()}**.",
        f"- Extra-innings/super-over groups excluded from ordinary pressure context: **{context[~context['ordinary_innings']][['match_id', 'innings']].drop_duplicates().shape[0]}**.",
        "",
        "## Reconstructed fields",
        "",
        "Each delivery includes score and wicket state before and after the event, legal balls, "
        "balls remaining, innings target, runs required, current run rate, required run rate, "
        "wickets in hand, and a target-reached marker where chase context is valid.",
        "",
        "### Explicit data assumptions and limitations",
        "",
    ]
    report.extend(f"- {item}" for item in assumptions)
    report.extend(
        [
            "",
            "The source does not expose a direct total-extras or batter-runs field. Therefore "
            "the score reconstruction is a documented hypothesis and `review_assumptions` is "
            "set on innings containing ambiguous `other` or `Penalty` extras. These outputs "
            "must be reviewed before player-level calculations.",
            "",
            "## Target and result cross-check",
            "",
            f"- Among valid revised-target chase contexts, reconstructed second innings reached the target: "
            f"**{int(revised_chase.sum())}**.",
            f"- Among valid revised-target chase contexts, reconstructed second innings did not reach the target: "
            f"**{int((~revised_chase).sum())}**. "
            "These include matches ending short, no-result matches, and cases needing scorecard interpretation.",
            f"- Revised-target matches excluded from this cross-check because the chase was not valid: "
            f"**{int(context[context['revised_target'].notna()]['match_id'].nunique() - len(revised_chase))}**.",
            "- Result text is retained for review rather than parsed into a definitive winner/loser model; DLS and abandoned outcomes make automatic result validation ambiguous.",
            "",
            "## Candidate definitions",
            "",
            "### A. Chase-pressure candidate",
            "",
            "Second innings only, with a valid first-innings total or revised target, excluding "
            "abandoned/no-result matches and target-already-reached rows. Baseline pressure "
            "requires at most 48 legal balls remaining and either required run rate at least "
            "10, or required-minus-current run rate at least 3 while six or fewer wickets "
            "remain. This combines chase demand, time, and wicket resources rather than labeling "
            "every late ball as pressure.",
            "",
            "### B. General high-leverage candidate",
            "",
            "Ordinary innings only, excluding abandoned/no-result matches, with at most 36 legal "
            "balls remaining and either six or fewer wickets in hand or a chase with at most 36 "
            "runs required. This is deliberately broader and does not equate first-innings "
            "late overs with chase pressure.",
            "",
            "## Sensitivity comparison",
            "",
            "The CSV output compares baseline, stricter, and looser variants. Stricter variants "
            "reduce coverage by shortening the remaining-ball window and increasing run-rate "
            "requirements; looser variants increase coverage but risk labeling routine states "
            "as pressure. Counts are descriptive, not evidence that any threshold is correct.",
            "",
            "| Definition | Eligible deliveries | Flagged deliveries | Matches | Innings | Batters | Bowlers |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in coverage.itertuples(index=False):
        report.append(
            f"| {row.definition} | {row.eligible_deliveries} | {row.flagged_deliveries} | "
            f"{row.matches} | {row.innings} | {row.batters} | {row.bowlers} |"
        )
    report.extend(
        [
            "",
            "## Validation questions before Step 3",
            "",
            "- Confirm whether `other` extras represent a no-ball/non-legal delivery or another event type.",
            "- Confirm the intended meaning of the sparse `extras_2_runs` field and whether the one-run base assumption is appropriate for every labeled extra.",
            "- Compare `innings_summary.csv` totals with an authoritative scorecard interpretation before treating reconstructed scores as final.",
            "- These provisional flags should be reviewed before any player pressure-performance calculation.",
        ]
    )
    (REPORTS / "pressure_definition_options.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {len(context)} delivery rows to {PROCESSED / 'delivery_context.csv'}")
    print(f"Wrote {len(innings_summary)} innings rows to {PROCESSED / 'innings_summary.csv'}")
    print(f"Wrote {len(coverage)} coverage variants to {OUTPUTS / 'pressure_coverage_summary.csv'}")
    print(f"Super-over/extra-innings rows: {len(super_rows)}")
    print(f"Ambiguous-extra delivery rows: {int(context['ambiguous_extra_type'].sum())}")


if __name__ == "__main__":
    write_outputs()
