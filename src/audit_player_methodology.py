"""Reproducible Step 4A player metric and evidence audit.

This script produces feasibility and coverage evidence only. It never ranks
players, computes ratings, or publishes a candidate list.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
OUTPUTS = ROOT / "outputs"

REQUIRED_BALL = {
    "match_id", "innings", "striker_id", "striker_name", "bowler_id",
    "bowler_name", "runs", "is_four", "is_six", "is_wicket",
    "dismissal_type", "dismissed_player_id", "extras_type", "extras_2_runs",
}
REQUIRED_CONTEXT = {
    "match_id", "innings", "legal_ball", "ordinary_innings",
    "abandoned_or_no_result", "innings_valid_for_pressure",
    "valid_chase_context", "target_reached_before", "balls_remaining_before",
    "required_run_rate", "rrr_minus_crr", "wickets_in_hand_before",
    "runs_required_before", "pressure_chase_candidate",
    "pressure_general_candidate",
}


def read_required(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required file is missing: {path}")
    return pd.read_csv(path, low_memory=False)


def validate_schema(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {', '.join(missing)}")


def pressure_definitions(context: pd.DataFrame) -> dict[str, pd.Series]:
    eligible = (
        context["innings_valid_for_pressure"]
        & context["ordinary_innings"]
        & ~context["abandoned_or_no_result"]
    )
    chase = (
        context["valid_chase_context"]
        & ~context["target_reached_before"]
        & (context["balls_remaining_before"] <= 48)
        & (
            (context["required_run_rate"] >= 10)
            | ((context["rrr_minus_crr"] >= 3) & (context["wickets_in_hand_before"] <= 6))
        )
    )
    general = (
        eligible
        & ~context["target_reached_before"]
        & (context["balls_remaining_before"] <= 36)
        & (
            (context["wickets_in_hand_before"] <= 6)
            | (context["valid_chase_context"] & (context["runs_required_before"] <= 36))
        )
    )
    return {
        "baseline": eligible,
        "chase_baseline": chase,
        "general_baseline": general,
        "chase_strict": (
            context["valid_chase_context"] & ~context["target_reached_before"]
            & (context["balls_remaining_before"] <= 30)
            & ((context["required_run_rate"] >= 12)
               | ((context["rrr_minus_crr"] >= 4) & (context["wickets_in_hand_before"] <= 6)))
        ),
        "general_strict": (
            eligible & ~context["target_reached_before"]
            & (context["balls_remaining_before"] <= 24)
            & (
                (context["wickets_in_hand_before"] <= 6)
                | (context["valid_chase_context"] & (context["runs_required_before"] <= 24))
            )
        ),
        "chase_loose": (
            context["valid_chase_context"] & ~context["target_reached_before"]
            & (context["balls_remaining_before"] <= 60)
            & ((context["required_run_rate"] >= 8)
               | ((context["rrr_minus_crr"] >= 2) & (context["wickets_in_hand_before"] <= 6)))
        ),
    }


def add_policies(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    excluded = (
        ~output["innings_valid_for_pressure"]
        | output["abandoned_or_no_result"]
        | ~output["ordinary_innings"]
    )
    output["strict_batter"] = output["extras_type"].isna() & output["extras_2_runs"].eq(0) & ~excluded
    output["moderate_batter"] = (
        output["extras_type"].isna() & output["extras_2_runs"].eq(0)
    ) | (output["extras_type"].isin(["Overstep", "other"]) & output["extras_2_runs"].eq(0))
    output["moderate_batter"] &= ~excluded
    output["boundary_consistent"] = (
        output["is_four"].eq(output["runs"].eq(4))
        & output["is_six"].eq(output["runs"].eq(6))
    )
    output["dismissed_striker"] = output["dismissed_player_id"].eq(output["striker_id"])
    output["candidate_bowler_wicket"] = output["dismissal_type"].isin(
        ["Bowled", "Caught", "LBW", "Stump", "Hit Wicket"]
    )
    output["safe_dot"] = output["strict_batter"] & output["legal_ball"] & output["runs"].eq(0)
    output["eligible_bowling"] = (
        output["legal_ball"] & output["ordinary_innings"]
        & output["innings_valid_for_pressure"] & ~output["abandoned_or_no_result"]
    )
    return output


def unique_events(frame: pd.DataFrame, mask: pd.Series, player: str) -> tuple[int, int, int, int]:
    selected = frame[mask & frame[player].notna()]
    return (
        len(selected),
        selected[["match_id", "innings"]].drop_duplicates().shape[0],
        selected["match_id"].nunique(),
        selected[player].nunique(),
    )


def join_quality(ball: pd.DataFrame, matches: pd.DataFrame, competitions: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    rows = []
    match_ids = set(matches["match_id"].dropna())
    comp_ids = set(competitions["comp_id"].dropna())
    map_ids = set(mapping["player_id"].dropna())
    for name, source_rows, key, target, target_key, matched, duplicate in [
        ("ball_to_matches", len(ball), "match_id", len(matches), "match_id", ball["match_id"].isin(match_ids), matches["match_id"].duplicated().sum()),
        ("matches_to_competitions", len(matches), "comp_id", len(competitions), "comp_id", matches["comp_id"].isin(comp_ids), competitions["comp_id"].duplicated().sum()),
        ("striker_ids_to_mapping", len(ball), "striker_id", len(mapping), "player_id", ball["striker_id"].isin(map_ids), mapping["player_id"].duplicated().sum()),
        ("bowler_ids_to_mapping", len(ball), "bowler_id", len(mapping), "player_id", ball["bowler_id"].isin(map_ids), mapping["player_id"].duplicated().sum()),
    ]:
        rows.append({
            "join_name": name, "source_rows": source_rows, "source_key": key,
            "target_rows": target, "target_key": target_key,
            "matched_source_rows": int(matched.sum()),
            "unmatched_source_rows": int((~matched).sum()),
            "target_duplicate_key_rows": int(duplicate),
            "row_multiplication_risk": "HIGH" if duplicate else "LOW",
            "notes": "Mapping is contextual by competition/team; aggregate distinct contexts before joining.",
        })
    exact_dupes = mapping.duplicated().sum()
    rows.append({
        "join_name": "mapping_exact_duplicate_rows", "source_rows": len(mapping),
        "source_key": "all_columns", "target_rows": len(mapping), "target_key": "all_columns",
        "matched_source_rows": len(mapping) - exact_dupes, "unmatched_source_rows": 0,
        "target_duplicate_key_rows": int(exact_dupes), "row_multiplication_risk": "LOW",
        "notes": "Exact duplicates may be de-duplicated for identity lookup only; valid team/competition contexts are retained.",
    })
    return pd.DataFrame(rows)


def pressure_coverage(frame: pd.DataFrame, definitions: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for name, flag in definitions.items():
        selected = frame[flag]
        rows.append({
            "pressure_definition": name,
            "formula": {
                "baseline": "ordinary valid innings, excluding abandoned/no-result",
                "chase_baseline": "valid chase, target not reached, <=48 balls, RRR>=10 or (RRR-CRR>=3 and <=6 wickets in hand)",
                "general_baseline": "valid innings, target not reached, <=36 balls, <=6 wickets in hand or <=36 runs required in chase",
                "chase_strict": "chase baseline with <=30 balls and RRR>=12 or RRR-CRR>=4",
                "general_strict": "general baseline with <=24 balls and <=24 runs required for chase branch",
                "chase_loose": "chase baseline with <=60 balls and RRR>=8 or RRR-CRR>=2",
            }[name],
            "eligible_deliveries": len(selected),
            "eligible_innings": selected[["match_id", "innings"]].drop_duplicates().shape[0],
            "eligible_matches": selected["match_id"].nunique(),
            "unique_batters": selected["striker_id"].nunique(),
            "unique_bowlers": selected["bowler_id"].nunique(),
            "excluded_target_or_incomplete_rows": int((~flag).sum()),
            "caveat": "Observed context only; score and target semantics remain provisional.",
        })
    return pd.DataFrame(rows)


def metric_rows(frame: pd.DataFrame, definitions: dict[str, pd.Series]) -> pd.DataFrame:
    strict = frame["strict_batter"]
    moderate = frame["moderate_batter"]
    bowling = frame["eligible_bowling"]
    rows = []
    specs = [
        ("batter", "runs", "sum(runs) on strict eligible striker rows", "runs, extras_type, extras_2_runs", "MEDIUM", strict, "runs resembles batter runs but is not explicitly labelled; conditional only"),
        ("batter", "eligible balls faced", "count strict eligible striker rows", "striker_id, extras_type, extras_2_runs", "MEDIUM", strict, "not a complete scorecard ball count"),
        ("batter", "boundary flags", "sum(is_four), sum(is_six) after consistency audit", "is_four, is_six, runs", "MEDIUM", strict, "source flags are descriptive and checked against runs"),
        ("batter", "strike rate", "100 * sum(runs) / count(strict eligible striker rows)", "runs, striker_id, extras_type, extras_2_runs", "LOW", strict, "conditional delivery rate, not a complete scorecard strike rate"),
        ("batter", "dismissal/survival events", "dismissed_player_id plus filtered dismissal types", "is_wicket, dismissed_player_id, dismissal_type", "MEDIUM", frame["dismissed_striker"] & frame["is_wicket"], "dismissal types and non-striker/run-out handling must remain explicit"),
        ("batter", "pressure vs baseline", "compare strict metric aggregates under declared context flags", "delivery_context pressure fields plus batter fields", "EXPLORATORY", strict & definitions["chase_baseline"], "pressure context and target reconstruction remain provisional"),
        ("bowler", "legal balls", "count legal_ball after excluding wide and Overstep", "extras_type, legal_ball, bowler_id", "MEDIUM", bowling, "other extra legal status remains a caveat"),
        ("bowler", "conservative dot events", "strict eligible legal rows with runs == 0", "legal_ball, runs, extras_type, bowler_id", "MEDIUM", frame["safe_dot"], "does not claim unresolved extras are batter dots"),
        ("bowler", "candidate bowler wickets", "count Bowled/Caught/LBW/Stump/Hit Wicket only", "dismissal_type, is_wicket, bowler_id", "MEDIUM", bowling & frame["candidate_bowler_wicket"], "RunOut, Retire Out, and obstruction events excluded"),
        ("bowler", "runs conceded/economy", "not calculated", "no verified bowler-charge field", "BLOCKED", pd.Series(False, index=frame.index), "cannot reliably attribute batter runs/extras to bowler"),
    ]
    for role, metric, formula, fields, confidence, mask, limitation in specs:
        events, innings, matches, players = unique_events(frame, mask, "striker_id" if role == "batter" else "bowler_id")
        rows.append({
            "role": role, "metric": metric, "formula": formula, "source_fields": fields,
            "confidence": confidence, "eligible_deliveries_or_events": events,
            "eligible_innings": innings, "eligible_matches": matches,
            "unique_players": players, "limitation": limitation,
        })
    return pd.DataFrame(rows)


def thresholds(frame: pd.DataFrame, definitions: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    scenarios = [(10, 3, 30), (20, 5, 60), (30, 8, 90)]
    for role, player, base_mask, policy in [
        ("batter", "striker_id", frame["strict_batter"], "strict"),
        ("batter", "striker_id", frame["moderate_batter"], "moderate"),
        ("bowler", "bowler_id", frame["eligible_bowling"], "legal_ball"),
    ]:
        base = frame[base_mask & frame[player].notna()]
        grouped_base = base.groupby(player).agg(baseline_events=("match_id", "size"), baseline_matches=("match_id", "nunique"))
        for definition in ("chase_baseline", "general_baseline"):
            pressure = frame[definitions[definition] & base_mask & frame[player].notna()]
            grouped = pressure.groupby(player).agg(pressure_events=("match_id", "size"), pressure_matches=("match_id", "nunique"))
            joined = grouped_base.join(grouped, how="left").fillna(0)
            for min_events, min_matches, min_base in scenarios:
                qualifies = joined[
                    (joined["pressure_events"] >= min_events)
                    & (joined["pressure_matches"] >= min_matches)
                    & (joined["baseline_events"] >= min_base)
                ]
                rows.append({
                    "scenario": f"{min_events}_pressure_{min_matches}_matches_{min_base}_baseline",
                    "role": role, "policy": policy, "pressure_definition": definition,
                    "minimum_pressure_events": min_events, "minimum_pressure_matches": min_matches,
                    "minimum_baseline_events": min_base, "qualifying_players": len(qualifies),
                    "observed_players": len(joined), "pressure_events_total": len(pressure),
                    "baseline_events_total": len(base),
                    "caveat": "Count only; no ordering or selection is produced.",
                })
    return pd.DataFrame(rows)


def report(ball: pd.DataFrame, matches: pd.DataFrame, mapping: pd.DataFrame, context: pd.DataFrame,
           metrics: pd.DataFrame, coverage: pd.DataFrame, joins: pd.DataFrame, thresholds_frame: pd.DataFrame) -> str:
    nonzero = ball[ball["extras_2_runs"].ne(0)]
    bowler_wickets = context[context["candidate_bowler_wicket"]]["dismissal_type"].value_counts().to_dict()
    lines = [
        "# Step 4A Player Analysis Methodology & Evidence Audit", "",
        "This audit establishes reproducible metric feasibility only. It creates no player rankings, Top 10 list, composite rating, pressure score, recommendation, or auction value.", "",
        "## Executive summary",
        f"- Supplied raw files include {len(ball):,} delivery rows, {len(matches):,} match rows, and {len(mapping):,} mapping rows.",
        f"- `extras1_runs` remains a category code; `extras_2_runs` has {len(nonzero)} non-zero rows and is not semantically resolved.",
        "- Batter runs, conditional balls, source boundary flags, and filtered dismissal events are partially supportable on strict/moderate subsets.",
        "- Legal balls and conservative bowler dismissal/dot events are descriptively supportable; conceded runs and economy remain BLOCKED.",
        "- Pressure contexts are observed/provisional coverage definitions, not validated player pressure ratings.",
        "",
        "## Dataset and identity audit",
        f"- Ball-by-ball IDs: {ball['match_id'].nunique():,} matches, {ball['striker_id'].nunique():,} strikers, {ball['bowler_id'].nunique():,} bowlers.",
        f"- Mapping contains {mapping['player_id'].nunique():,} distinct player IDs and {mapping[['comp_id','team_id','player_id']].drop_duplicates().shape[0]:,} distinct competition/team/player contexts.",
        f"- Exact duplicate mapping rows: {mapping.duplicated().sum():,}. They must not be used to multiply delivery rows.",
        "- Player identity is treated as contextual through competition/team/player mapping; no external identity enrichment is used.",
        "",
        "## Pressure-context candidates",
        "Chase and general contexts use the reconstructed fields in `delivery_context.csv`; they exclude abandoned/no-result, invalid ordinary innings, and target-completed states. Late-over status alone is not called pressure.",
        "```text\n" + coverage.to_string(index=False) + "\n```",
        "",
        "## Batter metric feasibility",
        "```text\n" + metrics[metrics["role"].eq("batter")].to_string(index=False) + "\n```",
        "",
        "## Bowler metric feasibility",
        "```text\n" + metrics[metrics["role"].eq("bowler")].to_string(index=False) + "\n```",
        f"- Verified candidate bowler dismissal-type counts in the audited context: {bowler_wickets}. RunOut and Retire Out are not included.",
        "",
        "## Sample-size policy",
        "The scenarios 10/3/30, 20/5/60, and 30/8/90 mean minimum pressure events / matches / baseline events. They are safeguards for later review, not universal statistical truths and not ranking cutoffs.",
        "```text\n" + thresholds_frame.to_string(index=False) + "\n```",
        "",
        "## Supported / exploratory / blocked register",
        "- **SUPPORTED DESCRIPTIVE, with caveats:** legal balls; strict/moderate conditional batter runs and balls; source boundary flags; filtered dismissal events; conservative dot events.",
        "- **EXPLORATORY:** pressure-context versus baseline comparisons using provisional reconstructed context and declared sensitivity variants.",
        "- **BLOCKED:** bowler conceded runs, economy, final pressure ratings, composite ratings, rankings, Top 10 selection, and recommendations.",
        "",
        "## Future selection framework",
        "A later step may present player-level descriptive tables only after applying a declared policy, minimum event/match thresholds, and uncertainty/sample-size disclosures. Batter comparisons should use conditional runs, conditional balls, boundary flags, and carefully filtered dismissals without calling them complete scorecard statistics. Bowler comparisons may use legal balls, conservative dots, and separated candidate dismissal types, but not economy or conceded runs.",
        "Pressure comparisons should report the exact context formula, baseline, exclusions, and sensitivity variants side by side. Correlated metrics should not be double-counted; no composite score should be proposed until every component is semantically defensible and weights are justified.",
        "",
        "## Reproduction",
        "```powershell\npython src\\audit_player_methodology.py\n```",
        "",
        "## Join audit reference",
        "```text\n" + joins.to_string(index=False) + "\n```",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    ball = read_required(RAW / "ball_by_ball.csv")
    matches = read_required(RAW / "matches.csv")
    competitions = read_required(RAW / "competitions.csv")
    mapping = read_required(RAW / "competition_team_player_mapping.csv")
    context = read_required(PROCESSED / "delivery_context.csv")
    validate_schema(ball, REQUIRED_BALL, "ball_by_ball.csv")
    validate_schema(context, REQUIRED_CONTEXT, "delivery_context.csv")
    frame = add_policies(context)
    definitions = pressure_definitions(frame)
    metrics = metric_rows(frame, definitions)
    coverage = pressure_coverage(frame, definitions)
    threshold_frame = thresholds(frame, definitions)
    joins = join_quality(ball, matches, competitions, mapping)
    assert len(ball) > 0 and len(metrics) == 10 and len(coverage) == 6
    assert (metrics["eligible_deliveries_or_events"] >= 0).all()
    assert not metrics["metric"].str.contains("ranking|top 10|rating", case=False).any()
    OUTPUTS.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    metrics.to_csv(OUTPUTS / "player_metric_feasibility.csv", index=False)
    threshold_frame.to_csv(OUTPUTS / "player_sample_thresholds.csv", index=False)
    joins.to_csv(OUTPUTS / "player_join_quality.csv", index=False)
    coverage.to_csv(OUTPUTS / "pressure_context_coverage.csv", index=False)
    (REPORTS / "step4a_player_methodology_audit.md").write_text(
        report(ball, matches, mapping, frame, metrics, coverage, joins, threshold_frame),
        encoding="utf-8",
    )
    print("Created Step 4A methodology report and four audit outputs.")
    print(f"Metrics: {len(metrics)}; pressure definitions: {len(coverage)}; threshold rows: {len(threshold_frame)}.")


if __name__ == "__main__":
    main()
