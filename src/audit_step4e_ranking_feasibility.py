"""Audit Step 4E ranking and comparison feasibility without ranking players."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
REPORTS = ROOT / "reports"

RAW_FILES = [
    "ball_by_ball.csv",
    "matches.csv",
    "competitions.csv",
    "teams.csv",
    "playing_eleven.csv",
    "competition_team_player_mapping.csv",
]
EXISTING_ARTIFACTS = [
    "outputs/player_metric_feasibility.csv",
    "outputs/player_sample_thresholds_extended.csv",
    "outputs/bowler_dismissal_thresholds.csv",
    "outputs/step4b_batter_candidates.csv",
    "outputs/step4b_bowler_candidates.csv",
    "outputs/step4c_batter_classification.csv",
    "outputs/step4c_bowler_classification.csv",
    "outputs/step4c_external_candidate_pool.csv",
]


def read_required(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required file is missing: {path}")
    return pd.read_csv(path, low_memory=False)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {', '.join(missing)}")


def add_policies(context: pd.DataFrame) -> pd.DataFrame:
    frame = context.copy()
    excluded = (
        ~frame["innings_valid_for_pressure"]
        | frame["abandoned_or_no_result"]
        | ~frame["ordinary_innings"]
    )
    frame["strict_batter"] = (
        frame["extras_type"].isna()
        & frame["extras_2_runs"].eq(0)
        & ~excluded
    )
    frame["eligible_bowling"] = frame["legal_ball"] & ~excluded
    frame["safe_bowler_dot"] = (
        frame["eligible_bowling"]
        & frame["strict_batter"]
        & frame["runs"].eq(0)
    )
    frame["candidate_dismissal"] = (
        frame["eligible_bowling"]
        & frame["is_wicket"]
        & frame["dismissal_type"].isin(
            ["Caught", "Bowled", "LBW", "Stump", "Hit Wicket"]
        )
    )
    frame["chase_proxy"] = (
        frame["valid_chase_context"]
        & ~frame["target_reached_before"]
        & (frame["balls_remaining_before"] <= 48)
        & (
            (frame["required_run_rate"] >= 10)
            | (
                (frame["rrr_minus_crr"] >= 3)
                & (frame["wickets_in_hand_before"] <= 6)
            )
        )
    )
    return frame


def metric_row(
    role: str,
    metric: str,
    meaning: str,
    source: str,
    calculation: str,
    eligibility: str,
    coverage: str,
    status: str,
    ranking: str,
    confidence: str,
    caveat: str,
) -> dict[str, str]:
    return {
        "role": role,
        "metric": metric,
        "business_meaning": meaning,
        "source_lineage": source,
        "calculation": calculation,
        "eligibility_exclusions": eligibility,
        "sample_coverage": coverage,
        "feasibility": status,
        "safe_to_contribute_to_ranking": ranking,
        "confidence": confidence,
        "caveats": caveat,
    }


def build_metric_matrix(
    frame: pd.DataFrame,
    batter_candidates: pd.DataFrame,
    bowler_candidates: pd.DataFrame,
    thresholds: pd.DataFrame,
) -> pd.DataFrame:
    batter = frame[frame["strict_batter"]]
    bowler = frame[frame["eligible_bowling"]]
    pressure_batter = batter[batter["chase_proxy"]]
    pressure_bowler = bowler[bowler["chase_proxy"]]
    batter_primary = thresholds[
        thresholds["role"].eq("batter")
        & thresholds["policy"].eq("strict")
        & thresholds["pressure_definition"].eq("chase_baseline")
        & thresholds["minimum_pressure_events"].eq(20)
        & thresholds["minimum_pressure_matches"].eq(5)
        & thresholds["minimum_baseline_events"].eq(60)
    ].iloc[0]
    bowler_primary = thresholds[
        thresholds["role"].eq("bowler")
        & thresholds["policy"].eq("legal_ball")
        & thresholds["pressure_definition"].eq("chase_baseline")
        & thresholds["minimum_pressure_events"].eq(20)
        & thresholds["minimum_pressure_matches"].eq(5)
        & thresholds["minimum_baseline_events"].eq(60)
    ].iloc[0]
    batter_cov = (
        f"{len(batter):,} deliveries; {batter.striker_id.nunique():,} player IDs; "
        f"{int(batter_primary.qualifying_players):,} pass Step 4B primary sample scenario"
    )
    bowler_cov = (
        f"{len(bowler):,} legal-ball rows; {bowler.bowler_id.nunique():,} player IDs; "
        f"{int(bowler_primary.qualifying_players):,} pass Step 4B primary sample scenario"
    )
    rows = [
        metric_row("batter", "conditional observed runs", "Runs recorded on eligible striker deliveries", "delivery_context.csv: runs, striker_id, extras_type, extras_2_runs", "sum(runs) by striker_id", "strict_batter: null extras_type, extras_2_runs == 0, valid ordinary innings", batter_cov, "DESCRIPTIVE_CONDITIONAL", "NO", "MEDIUM", "runs resembles batter runs but is not explicitly labelled official batter runs"),
        metric_row("batter", "eligible deliveries", "Conditional delivery denominator for batter evidence", "delivery_context.csv: striker_id, extras_type, extras_2_runs", "count strict eligible striker rows", "same strict policy; incomplete scorecard semantics remain", batter_cov, "DESCRIPTIVE_CONDITIONAL", "NO", "MEDIUM", "not a complete scorecard ball count"),
        metric_row("batter", "conditional run rate", "Observed runs per eligible delivery", "delivery_context.csv: runs, striker_id, extras_type, extras_2_runs", "100 * conditional observed runs / eligible deliveries", "same strict policy", batter_cov, "EXPLORATORY_COMPARATIVE", "NO", "LOW", "not a complete scorecard strike rate; denominator and runs semantics are conditional"),
        metric_row("batter", "source boundary counts", "Descriptive four/six flags", "delivery_context.csv: is_four, is_six, runs", "sum source flags by player", "strict eligible rows; flags checked against runs", batter_cov, "DESCRIPTIVE_CONDITIONAL", "NO", "MEDIUM", "does not establish complete innings or tournament boundary rates"),
        metric_row("batter", "batting average", "Runs per dismissal/not-out innings", "delivery_context.csv: runs, is_wicket, dismissed_player_id", "would require reliable innings dismissal and not-out semantics", "not computed", "No defensible coverage", "BLOCKED", "NO", "MEDIUM", "source dismissal/survival semantics and score totals are not sufficient"),
        metric_row("batter", "dot-ball percentage", "Share of batter deliveries with zero batter runs", "delivery_context.csv: runs, extras_type, extras_2_runs", "would require verified batter-run and dot semantics", "not computed as a ranking metric", "Not defensible", "BLOCKED", "NO", "LOW", "ambiguous extras prevent a verified batter-dot denominator"),
        metric_row("batter", "cross-innings consistency", "Variation of conditional delivery evidence across innings", "delivery_context.csv: match_id, innings, striker_id, runs", "could summarize per-innings conditional rates", "minimum innings/match threshold required; no validated score semantics", f"{batter[['match_id','innings']].drop_duplicates().shape[0]:,} eligible innings; candidate contexts {len(batter_candidates):,}", "EXPLORATORY_ONLY", "NO", "LOW", "sample size and context comparability are not enough for a final rank"),
        metric_row("batter", "chase-context comparison", "Conditional evidence in inferred chase contexts versus baseline", "delivery_context.csv: pressure fields plus batter fields", "compare declared strict aggregates under chase_proxy", f"chase_proxy rows only; target/score reconstruction caveats", f"{len(pressure_batter):,} pressure rows; {pressure_batter.striker_id.nunique():,} player IDs", "EXPLORATORY_ONLY", "NO", "LOW", "chase_baseline is not validated psychological pressure"),
        metric_row("bowler", "legal balls", "Deliveries counted as legal after wide/Overstep exclusion", "delivery_context.csv: legal_ball, bowler_id", "count legal_ball rows by bowler", "valid ordinary innings; legal_ball true", bowler_cov, "DESCRIPTIVE_CONDITIONAL", "NO", "MEDIUM", "other-extra legal status remains a caveat"),
        metric_row("bowler", "safe dot events", "Conservative zero-run legal-ball events", "delivery_context.csv: legal_ball, runs, extras_type, extras_2_runs, bowler_id", "count legal rows satisfying strict_batter and runs == 0", "legal ball plus strict batter policy", f"{int((bowler.safe_bowler_dot).sum()):,} rows; {bowler.loc[bowler.safe_bowler_dot,'bowler_id'].nunique():,} player IDs", "DESCRIPTIVE_CONDITIONAL", "NO", "MEDIUM", "not an official dot-ball rate or scorecard metric"),
        metric_row("bowler", "candidate dismissal events by type", "Filtered potential bowler-attributed dismissal events", "delivery_context.csv: is_wicket, dismissal_type, bowler_id", "count candidate types: Caught, Bowled, LBW, Stump, Hit Wicket", "legal ball; is_wicket true; excluded RunOut, Retire Out, obstruction-related types", f"{int(frame.candidate_dismissal.sum()):,} events; {frame.loc[frame.candidate_dismissal,'bowler_id'].nunique():,} player IDs", "DESCRIPTIVE_CONDITIONAL", "NO", "MEDIUM", "candidate events are not official wickets"),
        metric_row("bowler", "candidate dismissal frequency", "Candidate dismissal events per match/context", "delivery_context.csv: candidate dismissal fields, match_id, bowler_id", "event count and match count by contextual player", "same filtered candidate-event policy", f"{int(bowler_primary.qualifying_players):,} pass primary sample scenario; {len(bowler_candidates):,} displayed contexts", "EXPLORATORY_ONLY", "NO", "MEDIUM", "raw event totals favour volume and are not a validated wicket rate"),
        metric_row("bowler", "dot-ball percentage", "Safe dot events divided by legal balls", "delivery_context.csv: safe dot and legal-ball fields", "safe dot events / legal balls", "same conservative policy", bowler_cov, "EXPLORATORY_ONLY", "NO", "LOW", "safe dot semantics are conditional and may not be comparable across contexts"),
        metric_row("bowler", "runs conceded/economy", "Runs charged to bowler per over", "No verified bowler-charge field; extras semantics unresolved", "not calculated", "blocked", "0 computed", "BLOCKED", "NO", "NONE", "cannot reliably attribute batter runs, wides, no-balls, byes, and leg-byes"),
        metric_row("bowler", "pace/spin/delivery categories", "Source delivery-category distribution", "delivery_context.csv: pace_or_spin, bowling_type, delivery_style", "descriptive category counts", "category values only; no performance inference", f"{frame.pace_or_spin.notna().sum():,} non-null pace/spin values", "DESCRIPTIVE_ONLY", "NO", "MEDIUM", "categories are not player quality or role scores"),
        metric_row("bowler", "chase-context comparison", "Conservative event evidence in inferred chase contexts versus baseline", "delivery_context.csv: pressure fields plus bowling fields", "compare event counts/rates under chase_proxy", "chase_proxy remains inferred; legal-ball policy", f"{len(pressure_bowler):,} pressure rows; {pressure_bowler.bowler_id.nunique():,} player IDs", "EXPLORATORY_ONLY", "NO", "LOW", "event coverage does not validate psychological pressure"),
    ]
    return pd.DataFrame(rows)


def build_readiness(
    matrix: pd.DataFrame,
    batter_candidates: pd.DataFrame,
    bowler_candidates: pd.DataFrame,
    classifications: pd.DataFrame,
) -> pd.DataFrame:
    external = classifications["classification"].value_counts().to_dict()
    common = {
        "ranking_population": "Step 4B contextual shortlist rows; not unique global player IDs",
        "identity_key": "(comp_id, team_id, player_id)",
        "pressure_definition": "chase_baseline inferred chase-context proxy",
        "auction_status": "NOT_VERIFIED_FROM_SUPPLIED_DATA",
        "external_candidate_contexts": str(
            external.get("EXTERNAL_HISTORICAL_CANDIDATE", 0)
        ),
    }
    return pd.DataFrame(
        [
            {
                **common,
                "role": "batter",
                "decision": "PARTIALLY_FEASIBLE_FOR_DESCRIPTIVE_COMPARISON_ONLY",
                "supported_metrics": "conditional observed runs, eligible deliveries, source boundary flags, declared sample counts",
                "blocked_or_unsafe_metrics": "batting average, official strike rate, verified dot percentage, psychological pressure score, composite ranking",
                "evidence": f"{len(batter_candidates):,} Step 4B contexts; strict conditional fields are medium/low confidence; contexts span different seasons and teams",
                "top10_performance_ranking": "NOT_DEFENSIBLE",
                "reason": "No single semantically complete, comparable and validated metric set supports a fair performance ranking.",
            },
            {
                **common,
                "role": "bowler",
                "decision": "BLOCKED_FOR_PERFORMANCE_RANKING; DESCRIPTIVE_EVENTS_AVAILABLE",
                "supported_metrics": "legal balls, conservative dot events, candidate dismissal events by type, sample counts",
                "blocked_or_unsafe_metrics": "runs conceded, economy, average, official wickets, validated dot percentage, psychological pressure score, composite ranking",
                "evidence": f"{len(bowler_candidates):,} Step 4B contexts; bowler charge runs are not reconstructable",
                "top10_performance_ranking": "NOT_DEFENSIBLE",
                "reason": "The most decision-relevant bowling efficiency metric is blocked and candidate dismissal events are not official wickets.",
            },
        ]
    )


def report(
    matrix: pd.DataFrame,
    readiness: pd.DataFrame,
    context: pd.DataFrame,
    batter: pd.DataFrame,
    bowler: pd.DataFrame,
    classifications: pd.DataFrame,
    ground: pd.DataFrame,
    hashes: dict[str, str],
    existing_hashes: dict[str, str],
) -> str:
    lines = [
        "# Step 4E Ranking Feasibility Audit",
        "",
        "## Executive decision",
        "- **Batter Top 10 performance ranking: NOT DEFENSIBLE from the supplied evidence without additional semantic and comparability safeguards.** Descriptive conditional comparisons are partially feasible.",
        "- **Bowler Top 10 performance ranking: NOT DEFENSIBLE.** Legal-ball, conservative dot, and candidate dismissal-event evidence is available descriptively, but conceded runs/economy and official wickets are blocked.",
        "- The Step 4B lists remain candidate-context shortlists ordered by evidence coverage, not performance rankings. They are not relabelled here.",
        "",
        "## Verified source facts",
        f"- Raw delivery rows: {len(context):,}; match IDs in delivery context: {context.match_id.nunique():,}; reconstructed innings: {context[['match_id','innings']].drop_duplicates().shape[0]:,}.",
        f"- Strict batter rows: {int(batter.shape[0]):,}; legal-ball bowler rows: {int(bowler.shape[0]):,}.",
        f"- Step 4B contexts: {len(readiness):,} readiness decisions; source candidate files contain 10 batter and 10 bowler contexts.",
        f"- Step 4C classifications: {classifications['classification'].value_counts().to_dict()}.",
        "- Identity evidence supports `(comp_id, team_id, player_id)` as the safest contextual join key; global `player_id` joins can multiply rows.",
        "",
        "## Metric feasibility matrix",
        "The matrix records source lineage, transformations, eligibility, coverage, ranking safety, and caveats. “No” in the ranking column is intentional: a descriptive metric can exist without being safe as a final ranking component.",
        "```text\n" + matrix.to_string(index=False) + "\n```",
        "",
        "## Fair comparison and Top 10 feasibility",
        "### Batters",
        "- Raw totals are volume-sensitive, while conditional rates depend on a delivery subset whose score/extras semantics are not fully resolved.",
        "- Contexts span different IPL seasons and teams; the supplied pack also contains T20I data, so combining all formats as one ranking population would be unjustified.",
        "- Pressure comparison is exploratory because `chase_baseline` is an inferred match-state proxy, not validated psychological pressure.",
        "- A transparent ranking would require a validated common metric set, stable innings/dismissal semantics, explicitly comparable populations, missing-data policy, and independently justified weights or normalization.",
        "### Bowlers",
        "- Legal balls and conservative event counts are available, but raw event volume rewards workload.",
        "- Candidate dismissal events exclude non-bowler-attributed types but remain candidate events, not official wickets.",
        "- Runs conceded/economy cannot be reconstructed reliably because extras and bowler-charge attribution are unresolved.",
        "- Without economy or another validated outcome metric, a performance ranking would be materially incomplete and potentially misleading.",
        "",
        "## RR recruitment relevance",
        "- Step 4C distinguishes 2026 RR reference-season participants from external historical candidates; absence from that season does not prove auction availability.",
        "- Auction pool, retention/release, current contracts, budget, overseas slots, and 2027 squad requirements are not supplied.",
        "- The system can support analyst review through evidence profiles, contextual history, sample gates, and explicit blockers; it cannot replace official roster/auction verification or final judgement.",
        "",
        "## Ground Explorer capability check",
        "```text\n" + ground.to_string(index=False) + "\n```",
        "- Factual venue summaries and categorical stroke/pace-spin distributions are supported.",
        "- The current pitch artwork is illustrative and not real venue geometry.",
        "- Actual shot landing coordinates, pitch dimensions, boundary geometry, wagon-wheel plots, and field-placement plots are unavailable.",
        "",
        "## Risks, unresolved questions, and exact additional data needed",
        "1. Verify the semantics of `runs`, `extras_2_runs`, team totals, and bowler-charge runs from an authoritative source or corrected data dictionary.",
        "2. Supply validated innings dismissal/not-out semantics if batting average or survival rates are required.",
        "3. Supply official auction-pool, retention/release, contract, budget, overseas-slot, and 2027 squad-need data before recruitment availability or gap decisions.",
        "4. Supply role/skill labels if role-based squad-gap analysis is required.",
        "5. Supply verified spatial venue and shot-location fields before spatial ground analytics.",
        "",
        "## Read-only integrity and validation",
        "- Raw hashes were recorded before and after the audit.",
        "- Existing Step 4A–4D artifact hashes were recorded before and after and were unchanged.",
        "- No dashboard files, routes, CSS, JavaScript, raw data, or existing reports were modified by Step 4E.",
        "",
        "## Reproduction",
        "```powershell",
        "python src\\audit_step4e_ranking_feasibility.py",
        "python -m py_compile src\\audit_step4e_ranking_feasibility.py",
        "```",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    raw_before = {name: sha256(RAW / name) for name in RAW_FILES}
    existing_before = {name: sha256(ROOT / name) for name in EXISTING_ARTIFACTS}
    context = read_required(PROCESSED / "delivery_context.csv")
    thresholds = read_required(OUTPUTS / "player_sample_thresholds_extended.csv")
    batter_candidates = read_required(OUTPUTS / "step4b_batter_candidates.csv")
    bowler_candidates = read_required(OUTPUTS / "step4b_bowler_candidates.csv")
    batter_class = read_required(OUTPUTS / "step4c_batter_classification.csv")
    bowler_class = read_required(OUTPUTS / "step4c_bowler_classification.csv")
    validate(context, {"match_id", "innings", "striker_id", "bowler_id", "runs", "is_four", "is_six", "is_wicket", "dismissal_type", "dismissed_player_id", "extras_type", "extras_2_runs", "legal_ball", "ordinary_innings", "abandoned_or_no_result", "innings_valid_for_pressure", "valid_chase_context", "target_reached_before", "balls_remaining_before", "required_run_rate", "rrr_minus_crr", "wickets_in_hand_before", "pace_or_spin"}, "delivery_context.csv")
    validate(thresholds, {"role", "policy", "pressure_definition", "minimum_pressure_events", "minimum_pressure_matches", "minimum_baseline_events", "qualifying_players"}, "player_sample_thresholds_extended.csv")
    frame = add_policies(context)
    batter = frame[frame["strict_batter"]]
    bowler = frame[frame["eligible_bowling"]]
    classifications = pd.concat([batter_class, bowler_class], ignore_index=True)
    matrix = build_metric_matrix(frame, batter_candidates, bowler_candidates, thresholds)
    readiness = build_readiness(matrix, batter_candidates, bowler_candidates, classifications)
    ground = pd.DataFrame(
        [
            {"capability": "venue identity and match counts", "status": "SUPPORTED_DESCRIPTIVE", "evidence": "matches.csv: venue_id, venue_country, match_id; 98 venue IDs across 883 matches", "limitation": "No stadium name field"},
            {"capability": "stroke and delivery categories", "status": "SUPPORTED_DESCRIPTIVE", "evidence": "ball_by_ball.csv: stroke, delivery_style, pace_or_spin, on_or_off, over_or_around", "limitation": "Category counts are not locations"},
            {"capability": "shot landing coordinates", "status": "BLOCKED", "evidence": "No supplied coordinate field", "limitation": "No heatmap or wagon-wheel plot"},
            {"capability": "pitch/boundary geometry", "status": "BLOCKED", "evidence": "No dimensions or geometry fields", "limitation": "Pitch artwork is illustrative only"},
            {"capability": "field-placement analytics", "status": "BLOCKED", "evidence": "No verified landing or field-position coordinates", "limitation": "Cannot create factual field maps"},
        ]
    )
    metric_path = OUTPUTS / "step4e_metric_feasibility.csv"
    readiness_path = OUTPUTS / "step4e_ranking_readiness.csv"
    report_path = REPORTS / "step4e_ranking_feasibility_audit.md"
    matrix.to_csv(metric_path, index=False)
    readiness.to_csv(readiness_path, index=False)
    raw_after = {name: sha256(RAW / name) for name in RAW_FILES}
    existing_after = {name: sha256(ROOT / name) for name in EXISTING_ARTIFACTS}
    if raw_before != raw_after:
        raise RuntimeError("Raw CSV hashes changed during Step 4E audit.")
    if existing_before != existing_after:
        raise RuntimeError("Existing Step 4A–4D artifact hashes changed during Step 4E audit.")
    report_path.write_text(report(matrix, readiness, context, batter, bowler, classifications, ground, raw_before, existing_before), encoding="utf-8")
    next_report = """# Step 4E Next-Phase Recommendation

## Decision

Do not implement final Top 10 performance rankings yet. The supplied data
supports a transparent evidence-review workflow and conditional comparisons,
but not a scientifically defensible single ordering for either role.

## Can be built now

- Candidate evidence profiles using the existing Step 4B and Step 4C outputs.
- Contextual identity and historical team/competition/season views.
- Fixed sample-gate and sensitivity disclosures.
- Descriptive batter delivery/boundary evidence and conservative bowler
  legal-ball/dismissal-event evidence.
- RR reference-season participation and auction-availability disclaimers.
- Ground venue/category summaries with explicit non-spatial caveats.

## Must wait

- Any Top 10 performance ranking or composite reliability score.
- Batting average, validated strike rate, verified dot percentage, bowler
  economy, conceded runs, official wicket totals, or psychology claims.
- Role-based RR squad-gap conclusions.
- Auction availability, retention/release, budget, overseas-slot, or 2027
  squad recommendations.

## Required next data

Provide an authoritative field dictionary or corrected score data for runs,
extras, team totals, and bowler charge attribution; validated dismissal and
not-out semantics; official auction/contract/retention data; explicit player
role and squad-need data; and verified venue/shot coordinates if spatial
analytics are required.

The next implementation step should therefore be a data-contract and
comparison-methodology review, not ranking UI or final submission packaging.
"""
    (REPORTS / "step4e_next_phase_recommendation.md").write_text(next_report, encoding="utf-8")
    print(f"Created Step 4E audit: {len(matrix)} metrics, {len(readiness)} readiness rows.")


if __name__ == "__main__":
    main()
