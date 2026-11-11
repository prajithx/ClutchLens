"""Test which player-level metrics are supportable without ranking players."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
OUTPUTS = ROOT / "outputs"


def load_context() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "delivery_context.csv", low_memory=False)


def pressure_flags(frame: pd.DataFrame) -> dict[str, pd.Series]:
    eligible = frame["innings_valid_for_pressure"]
    chase = frame["valid_chase_context"] & ~frame["target_reached_before"]
    chase_variants = {
        "chase_baseline": chase
        & (frame["balls_remaining_before"] <= 48)
        & (
            (frame["required_run_rate"] >= 10)
            | ((frame["rrr_minus_crr"] >= 3) & (frame["wickets_in_hand_before"] <= 6))
        ),
        "chase_stricter": chase
        & (frame["balls_remaining_before"] <= 30)
        & (
            (frame["required_run_rate"] >= 12)
            | ((frame["rrr_minus_crr"] >= 4) & (frame["wickets_in_hand_before"] <= 6))
        ),
        "chase_looser": chase
        & (frame["balls_remaining_before"] <= 60)
        & (
            (frame["required_run_rate"] >= 8)
            | ((frame["rrr_minus_crr"] >= 2) & (frame["wickets_in_hand_before"] <= 6))
        ),
    }
    general_variants = {
        "general_baseline": eligible
        & ~frame["target_reached_before"]
        & (frame["balls_remaining_before"] <= 36)
        & (
            (frame["wickets_in_hand_before"] <= 6)
            | (frame["valid_chase_context"] & (frame["runs_required_before"] <= 36))
        ),
        "general_stricter": eligible
        & ~frame["target_reached_before"]
        & (frame["balls_remaining_before"] <= 24)
        & (
            (frame["wickets_in_hand_before"] <= 6)
            | (frame["valid_chase_context"] & (frame["runs_required_before"] <= 24))
        ),
        "general_looser": eligible
        & ~frame["target_reached_before"]
        & (frame["balls_remaining_before"] <= 48)
        & (
            (frame["wickets_in_hand_before"] <= 6)
            | (frame["valid_chase_context"] & (frame["runs_required_before"] <= 48))
        ),
    }
    return {**chase_variants, **general_variants}


def add_eligibility(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["excluded_incomplete_or_abandoned"] = (
        ~output["innings_valid_for_pressure"]
        | output["abandoned_or_no_result"]
        | ~output["ordinary_innings"]
    )
    output["excluded_target_reconstruction_uncertainty"] = (
        output["innings"].eq(2) & ~output["valid_chase_context"]
    )
    output["ambiguous_extra_row"] = output["extras_type"].isin(["other", "Penalty"])
    output["strict_batter_row"] = (
        output["extras_type"].isna()
        & output["extras_2_runs"].eq(0)
        & ~output["excluded_incomplete_or_abandoned"]
    )
    output["moderate_batter_row"] = (
        (
            output["extras_type"].isna()
            & output["extras_2_runs"].eq(0)
        )
        | (
            output["extras_type"].isin(["Overstep", "other"])
            & output["extras_2_runs"].eq(0)
        )
    ) & ~output["excluded_incomplete_or_abandoned"]
    output["boundary_consistent"] = (
        ((output["is_four"]) == (output["runs"].eq(4)))
        & ((output["is_six"]) == (output["runs"].eq(6)))
    )
    output["dismissed_striker"] = output["dismissed_player_id"].eq(output["striker_id"])
    output["bowler_credit_candidate"] = output["dismissal_type"].isin(
        ["Bowled", "Caught", "LBW", "Stump", "Hit Wicket"]
    )
    output["safe_bowling_dot_event"] = (
        output["strict_batter_row"] & output["runs"].eq(0) & output["legal_ball"]
    )
    return output


def coverage_rows(frame: pd.DataFrame, flags: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for policy, policy_column in (
        ("strict", "strict_batter_row"),
        ("moderate", "moderate_batter_row"),
    ):
        base = frame[frame[policy_column]]
        for definition, pressure in [("baseline", pd.Series(True, index=frame.index))] + list(flags.items()):
            pressure_rows = base.index.intersection(frame.index[pressure])
            pressured = frame.loc[pressure_rows]
            rows.append(
                {
                    "policy": policy,
                    "pressure_definition": definition,
                    "eligible_deliveries": len(base),
                    "pressure_deliveries": len(pressured),
                    "eligible_batters": base["striker_id"].nunique(),
                    "pressure_batters": pressured["striker_id"].nunique(),
                    "eligible_matches": base["match_id"].nunique(),
                    "pressure_matches": pressured["match_id"].nunique(),
                    "eligible_innings": base[["match_id", "innings"]].drop_duplicates().shape[0],
                    "pressure_innings": pressured[["match_id", "innings"]].drop_duplicates().shape[0],
                    "runs_observed": base["runs"].sum(),
                    "four_flags": int(base["is_four"].sum()),
                    "six_flags": int(base["is_six"].sum()),
                    "boundary_consistent_rows": int(base["boundary_consistent"].sum()),
                    "notes": (
                        "strict: null extras only"
                        if policy == "strict"
                        else "moderate: null extras plus Overstep/other rows with extras_2_runs=0"
                    ),
                }
            )
    return pd.DataFrame(rows)


def bowler_coverage(frame: pd.DataFrame, flags: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for definition, pressure in [("baseline", pd.Series(True, index=frame.index))] + list(flags.items()):
        eligible = frame["innings_valid_for_pressure"] & frame["ordinary_innings"] & ~frame["abandoned_or_no_result"]
        selected = frame[eligible & pressure]
        strict_selected = selected[selected["strict_batter_row"]]
        rows.append(
            {
                "pressure_definition": definition,
                "eligible_legal_deliveries": int(selected["legal_ball"].sum()),
                "strict_dot_events": int(strict_selected["safe_bowling_dot_event"].sum()),
                "all_dismissal_events": int(selected["is_wicket"].sum()),
                "candidate_bowler_wickets": int(selected["bowler_credit_candidate"].sum()),
                "run_out_events": int(selected["dismissal_type"].eq("RunOut").sum()),
                "other_non_bowler_dismissal_events": int(
                    selected["dismissal_type"].isin(
                        ["Retire Out", "Obstracting the field", "Obstructing the field"]
                    ).sum()
                ),
                "bowlers": selected["bowler_id"].nunique(),
                "matches": selected["match_id"].nunique(),
                "note": "No economy or conceded-run metric; runs charged to bowler are unresolved.",
            }
        )
    return pd.DataFrame(rows)


def sample_thresholds(frame: pd.DataFrame, flags: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    policies = {"strict": "strict_batter_row", "moderate": "moderate_batter_row"}
    for category, player_column, event_column, policy_map in [
        ("batter", "striker_id", "strict_batter_row", policies),
        ("bowler", "bowler_id", "legal_ball", {"available": "legal_ball"}),
    ]:
        for policy, policy_column in policy_map.items():
            for definition, pressure in [("baseline", pd.Series(True, index=frame.index))] + list(flags.items()):
                subset = frame[frame[policy_column] & pressure]
                grouped = subset.groupby(player_column).agg(
                    pressure_events=("match_id", "size"),
                    pressure_matches=("match_id", "nunique"),
                )
                if category == "batter":
                    baseline_subset = frame[frame[policy_column]]
                    baseline = baseline_subset.groupby(player_column).size().rename("baseline_events")
                    grouped = grouped.join(baseline, how="left").fillna(0)
                else:
                    grouped["baseline_events"] = frame[frame[policy_column]].groupby(player_column).size()
                    grouped = grouped.fillna(0)
                for min_pressure, min_matches, min_baseline in (
                    (10, 3, 30),
                    (20, 5, 60),
                    (30, 8, 90),
                ):
                    qualifying = grouped[
                        (grouped["pressure_events"] >= min_pressure)
                        & (grouped["pressure_matches"] >= min_matches)
                        & (grouped["baseline_events"] >= min_baseline)
                    ]
                    rows.append(
                        {
                            "category": category,
                            "policy": policy,
                            "pressure_definition": definition,
                            "minimum_pressure_events": min_pressure,
                            "minimum_pressure_matches": min_matches,
                            "minimum_baseline_events": min_baseline,
                            "qualifying_players": len(qualifying),
                            "observed_players": len(grouped),
                        }
                    )
    return pd.DataFrame(rows)


def report(
    frame: pd.DataFrame,
    batter: pd.DataFrame,
    bowler: pd.DataFrame,
    thresholds: pd.DataFrame,
) -> str:
    strict = frame["strict_batter_row"]
    moderate = frame["moderate_batter_row"]
    pressure = frame["pressure_chase_candidate"] | frame["pressure_general_candidate"]
    lines = [
        "# Step 2.3 Metric Feasibility",
        "",
        "This is a feasibility and methodology-design audit. It does not create player ratings, rankings, or top-10 lists.",
        "",
        "## Trusted batting-runs subsets",
        "",
        f"- Strict policy: **{strict.sum()}** deliveries and **{frame.loc[strict, 'striker_id'].nunique()}** batters.",
        f"- Moderate policy: **{moderate.sum()}** deliveries and **{frame.loc[moderate, 'striker_id'].nunique()}** batters.",
        f"- Excluded abandoned/incomplete/extra-innings rows: **{frame['excluded_incomplete_or_abandoned'].sum()}**.",
        f"- Second-innings rows excluded for target/reconstruction uncertainty: **{frame['excluded_target_reconstruction_uncertainty'].sum()}**.",
        f"- Ambiguous `other`/Penalty rows: **{frame['ambiguous_extra_row'].sum()}**.",
        f"- Strict pressure-eligible batting rows under existing baseline flags: **{frame.loc[strict & pressure].shape[0]}**.",
        "",
        "Strict policy uses only null `extras_type` rows in valid ordinary innings. Moderate policy additionally admits `Overstep` and `other` rows only when `extras_2_runs == 0`; this is an explicit sensitivity assumption, not a proven semantic correction. Wides, byes, legbyes, and Penalty rows are excluded because batter/team attribution is unresolved.",
        "",
        "## Candidate batter metrics",
        "",
        "- Runs per eligible delivery and strike rate are feasible only as conditional descriptive metrics on the strict subset; they must not be presented as complete scorecard strike rates.",
        "- Boundary rate is conditionally feasible because `is_four`/`is_six` can be checked against `runs`; these flags are consistent on "
        f"{frame['boundary_consistent'].mean():.2%} of all rows.",
        "- Dismissal analysis is partially feasible: `dismissed_player_id` is present for dismissal rows, but attribution requires filtering dismissal types and should not infer all `is_wicket` events as batter dismissals.",
        "- Pressure-vs-baseline batting is **PARTIALLY READY** only for strict eligible rows and provisional match-state flags; it is not ready as a final rating because team totals and target semantics remain unresolved.",
        "",
        "## Bowling feasibility",
        "",
        "- Legal-ball counts are available using the validated exclusion of `wide` and `Overstep`; `other` remains a caveat.",
        "- Dismissal events must remain separated. Candidate bowler-wicket types are limited to Bowled, Caught, LBW, Stump, and Hit Wicket; RunOut, Retire Out, and obstruction dismissals are not bowler wickets.",
        "- Dot-event counts are only proposed on strict null-extra rows with `runs == 0`; this avoids claiming unresolved extras are batter dots.",
        "- Economy, runs conceded, and any bowler ranking are unavailable because bowler-charged runs are not encoded reliably.",
        "",
        "## Sample-size policies",
        "",
        "The threshold output tests three policies: 10 pressure events/3 matches/30 baseline events, 20/5/60, and 30/8/90. These are reliability scenarios, not selected ranking cutoffs. The CSV reports counts only and contains no rank order.",
        "",
        "## Readiness decisions",
        "",
        "**Batter descriptive analysis: PARTIALLY READY.** Strict conditional delivery runs, boundaries, and carefully filtered dismissal events have substantial coverage, but they are not complete scorecard statistics.",
        "",
        "**Batter pressure-vs-baseline analysis: PARTIALLY READY for exploratory coverage; BLOCKED for final ratings.** Pressure state is available provisionally, while team totals and revised-target semantics remain unresolved.",
        "",
        "**Bowler descriptive analysis: PARTIALLY READY.** Legal deliveries, separated dismissal events, and conservative dot-event counts can be described. Economy and conceded runs are unavailable.",
        "",
        "**Bowler pressure-vs-baseline analysis: BLOCKED for performance ratings.** Only event-coverage tables are defensible until bowler run attribution and pressure-state validity are resolved.",
        "",
        "No robust Top 10 should be produced from this dataset at this stage. The strongest honest alternative is a coverage and methodology report, followed by player-level exploratory tables only after the user accepts these restrictions.",
        "",
        "## Output references",
        "",
        "- `outputs/batter_metric_coverage.csv` contains policy and pressure-definition coverage.",
        "- `outputs/bowler_metric_coverage.csv` contains legal-ball, dot-event, and dismissal-event coverage without economy.",
        "- `outputs/player_sample_thresholds.csv` contains threshold counts without rank order.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    frame = add_eligibility(load_context())
    flags = pressure_flags(frame)
    for name, flag in flags.items():
        frame[name] = flag
    batter = coverage_rows(frame, flags)
    bowler = bowler_coverage(frame, flags)
    thresholds = sample_thresholds(frame, flags)
    OUTPUTS.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    batter.to_csv(OUTPUTS / "batter_metric_coverage.csv", index=False)
    bowler.to_csv(OUTPUTS / "bowler_metric_coverage.csv", index=False)
    thresholds.to_csv(OUTPUTS / "player_sample_thresholds.csv", index=False)
    (REPORTS / "step2_3_metric_feasibility.md").write_text(
        report(frame, batter, bowler, thresholds), encoding="utf-8"
    )
    print(f"Written batter coverage rows: {len(batter)}")
    print(f"Written bowler coverage rows: {len(bowler)}")
    print(f"Written sample-threshold rows: {len(thresholds)}")
    print(f"Strict/moderate batter deliveries: {frame['strict_batter_row'].sum()}/{frame['moderate_batter_row'].sum()}")


if __name__ == "__main__":
    main()
