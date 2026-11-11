"""Read-only Step 4G data-readiness and evidence-gap audit."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
REPORTS = ROOT / "reports"

NEW_FILES = {
    "src/audit_step4g_data_readiness.py",
    "reports/step4g_data_inventory.md",
    "outputs/step4g_metric_feasibility.csv",
    "outputs/step4g_pressure_data_readiness.csv",
    "outputs/step4g_rr_squad_evidence_gaps.csv",
    "outputs/step4g_external_source_requirements.csv",
    "reports/step4g_submission_traceability.md",
    "reports/step4g_next_phase_recommendation.md",
}


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required file missing: {path}")
    return pd.read_csv(path, low_memory=False)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def protected_hashes() -> dict[str, str]:
    result = {}
    for folder in (RAW, PROCESSED, OUTPUTS, REPORTS, ROOT / "src"):
        for path in folder.iterdir():
            if path.is_file():
                relative = str(path.relative_to(ROOT)).replace("\\", "/")
                if relative not in NEW_FILES:
                    result[relative] = digest(path)
    return result


def null_blank_counts(frame: pd.DataFrame) -> tuple[int, int]:
    nulls = int(frame.isna().sum().sum())
    blanks = int(
        frame.select_dtypes(include=["object"]).apply(
            lambda column: column.astype(str).str.strip().eq("").sum()
        ).sum()
    )
    return nulls, blanks


def inventory_table() -> pd.DataFrame:
    rows = []
    for folder, kind in ((RAW, "raw"), (PROCESSED, "derived"), (OUTPUTS, "derived"), (REPORTS, "derived"), (ROOT / "src", "audit_script")):
        for path in sorted(folder.iterdir()):
            if not path.is_file():
                continue
            relative = str(path.relative_to(ROOT)).replace("\\", "/")
            if path.suffix.lower() != ".csv":
                rows.append({
                    "path": relative, "kind": kind, "format": path.suffix.lstrip("."),
                    "size_bytes": path.stat().st_size, "rows": "not_applicable",
                    "columns": "not_applicable", "null_cells": "not_applicable",
                    "blank_cells": "not_applicable", "duplicate_rows": "not_applicable",
                    "declared_grain": "document/report", "safe_use": "read-only reference",
                })
                continue
            frame = read_csv(path)
            nulls, blanks = null_blank_counts(frame)
            rows.append({
                "path": relative, "kind": kind, "format": "csv",
                "size_bytes": path.stat().st_size, "rows": len(frame),
                "columns": len(frame.columns), "null_cells": nulls,
                "blank_cells": blanks, "duplicate_rows": int(frame.duplicated().sum()),
                "declared_grain": "delivery/match/context/output row; see source schema",
                "safe_use": "source or derived evidence; semantics audited before use",
            })
    return pd.DataFrame(rows)


def metric_rows(context: pd.DataFrame, raw_ball: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    strict = context["extras_type"].isna() & context["extras_2_runs"].eq(0)
    ordinary = context["ordinary_innings"] & ~context["abandoned_or_no_result"]
    legal = context["legal_ball"] & ordinary
    rows = []

    def add(domain, metric, definition, required, available, method, missing, status, upgrade, caveat):
        rows.append({
            "domain": domain, "metric": metric, "definition": definition,
            "required_fields": required, "available_fields": available,
            "calculation_or_policy": method, "missing_or_unresolved_semantics": missing,
            "feasibility": status, "evidence_needed_to_upgrade": upgrade,
            "exclusions_caveats": caveat,
        })

    add("batter", "conditional observed runs", "Runs recorded on strict eligible striker rows",
        "runs, striker_id, extras semantics, innings validity", "runs, striker_id, extras_type, extras_2_runs, innings validity",
        "sum runs after null-extra and zero-secondary-field policy", "runs is not formally labelled official batter runs",
        "SUPPORTED_WITH_CAVEATS", "authoritative field dictionary and scorecard reconciliation",
        "Conditional evidence only; not official scorecard runs.")
    add("batter", "balls faced", "Verified legal deliveries faced by batter",
        "legal delivery and batter-run semantics", "legal_ball, striker_id, extras fields",
        "strict eligible delivery count used as conditional proxy", "other-extra and score semantics remain unresolved",
        "EXPLORATORY", "validated legal-ball/scorecard contract",
        "Do not call this official balls faced.")
    add("batter", "boundaries", "Four/six events attributable to striker",
        "validated boundary flags and batter-run semantics", "is_four, is_six, runs, striker_id",
        "source flag counts under strict policy", "completeness and official run semantics not established",
        "SUPPORTED_WITH_CAVEATS", "authoritative boundary definition",
        "Descriptive source flags only.")
    add("batter", "batting average", "Runs divided by dismissals/not-out innings",
        "official runs, dismissal and not-out innings", "is_wicket, dismissed_player_id; conditional runs",
        "not calculated", "not-out and innings dismissal semantics insufficient",
        "BLOCKED", "validated innings scorecards and dismissal semantics",
        "Cannot infer survival from delivery rows.")
    add("batter", "strike rate", "Runs per official ball faced × 100",
        "official batter runs and balls faced", "conditional runs and proxy denominator only",
        "not calculated as official rate", "numerator/denominator semantics unresolved",
        "BLOCKED", "authoritative scorecard fields",
        "Conditional run rate is not official strike rate.")
    add("batter", "dot-ball percentage", "Zero batter-run deliveries divided by verified balls faced",
        "batter runs, extras and verified denominator", "runs, extras fields",
        "not calculated", "extras and batter-run attribution unresolved",
        "BLOCKED", "verified delivery event contract",
        "Do not convert missing semantics to zero.")
    add("batter", "phase-wise performance", "Performance by powerplay/middle/death phase",
        "verified over/phase rules and valid metrics", "overid, innings, delivery context",
        "phase can be labelled descriptively but not with blocked metrics", "metric semantics and format-specific phase rules",
        "EXPLORATORY", "approved phase definitions and valid score metrics",
        "T20 phase rules may not transfer across formats.")
    add("bowler", "legal balls", "Legal deliveries bowled after documented exclusions",
        "legal-ball and extra semantics", "legal_ball, extras_type, bowler_id",
        "count legal_ball under ordinary-innings policy", "other-extra legal caveat",
        "SUPPORTED_WITH_CAVEATS", "validated extras dictionary",
        "Not an official over count.")
    add("bowler", "runs conceded", "Runs charged to bowler including applicable extras",
        "team total, batter runs, wides/no-balls/byes/leg-byes attribution", "runs and extras codes only",
        "not calculated", "extras1_runs is category code; extras_2_runs unresolved",
        "BLOCKED", "authoritative bowler-charge fields or scorecards",
        "Core bowling efficiency field unavailable.")
    add("bowler", "wides and no-balls", "Extra deliveries and charged runs",
        "verified extra type and quantity", "extras_type, extras1_runs, extras_2_runs",
        "category descriptions only", "quantity semantics are not reliable",
        "BLOCKED", "validated extras contract",
        "Do not infer charged runs from category codes.")
    add("bowler", "candidate dismissals", "Filtered potential bowler-attributed dismissal events",
        "dismissal type and attribution rules", "is_wicket, dismissal_type, bowler_id",
        "filter Bowled/Caught/LBW/Stump/Hit Wicket", "candidate events are not official wickets",
        "SUPPORTED_WITH_CAVEATS", "official wicket/attribution field",
        "RunOut and other non-bowler events excluded.")
    add("bowler", "official wickets", "Official bowler wicket total",
        "validated wicket attribution", "candidate dismissal fields",
        "not calculated", "dismissal semantics not complete",
        "BLOCKED", "official scorecards or validated wickets",
        "Candidate event count must not be relabelled wickets.")
    add("bowler", "economy/average/strike rate", "Official bowling rate metrics",
        "runs conceded, wickets, legal balls", "legal balls only; no reliable conceded runs/wickets",
        "not calculated", "required numerator and/or wicket denominator blocked",
        "BLOCKED", "official scorecard fields",
        "No fair bowling efficiency comparison.")
    add("bowler", "dot-ball percentage", "Verified zero-run legal balls divided by legal balls",
        "charged runs and legal balls", "conservative safe-dot proxy fields",
        "descriptive safe-dot events only", "conservative proxy not official dot semantics",
        "EXPLORATORY", "verified charged-run event data",
        "Cross-context comparability limited.")
    add("bowler", "phase-wise performance", "Bowling outcomes by phase",
        "phase rules and valid bowling outcomes", "overid and delivery categories",
        "phase labels descriptive only", "outcome metrics blocked",
        "EXPLORATORY", "approved phases and valid outcomes",
        "No economy or wicket claim.")
    add("match", "match result", "Recorded winner/result",
        "match metadata", "win_team_id, result",
        "read source result", "abandoned/no-result interpretation requires care",
        "SUPPORTED_WITH_CAVEATS", "authoritative result status",
        "Do not infer player causality.")
    add("pressure-context", "chase state", "Innings with a target and unfinished chase",
        "target, innings order, score state", "valid_chase_context, revised_target, score fields",
        "use reconstructed context flags", "target/score semantics audited as provisional",
        "EXPLORATORY", "validated target and score contract",
        "Match-state proxy, not psychology.")
    add("pressure-context", "required runs/balls/wickets", "State variables before an event",
        "score, target, legal balls, wickets", "reconstructed fields in delivery_context",
        "descriptive state fields", "score and wicket semantics have caveats",
        "EXPLORATORY", "validated innings scorecard fields",
        "Do not produce pressure scores.")
    add("pressure-context", "pressure-event coverage", "Events meeting declared chase proxy",
        "reproducible state thresholds", "pressure flags and match context",
        f"{int((strict & ordinary).sum()):,} strict ordinary rows available; exact scenario coverage in pressure CSV",
        "proxy threshold is analyst-defined and not psychologically validated",
        "EXPLORATORY", "pre-registered definition and sensitivity protocol",
        "Report event/match/player counts, not reliability claims.")
    add("venue", "venue identity/match counts", "Supplied venue IDs and match coverage",
        "venue_id, venue_country, match_id", "matches.csv fields",
        "group match counts by venue_id/country", "no stable venue alias/name field",
        "SUPPORTED_WITH_CAVEATS", "venue alias dictionary",
        "Venue ID is source identity, not stadium name.")
    add("venue", "pitch/boundary geometry", "Verified dimensions and geometry",
        "coordinates/dimensions", "none found in source inventory",
        "not calculated", "no supplied geometry",
        "BLOCKED", "official venue geometry or measured data",
        "Illustrative UI artwork is not evidence.")
    add("venue", "shot landing/field placement", "Spatial shot and fielder locations",
        "landing coordinates, wagon wheel, field positions", "stroke/on_or_off categories only",
        "not calculated", "no coordinates",
        "BLOCKED", "licensed spatial event feed",
        "Categorical direction is not spatial location.")
    add("venue", "surface/weather", "Pitch report and environmental context",
        "surface, weather, humidity, wind", "none found in source inventory",
        "not calculated", "no environmental fields",
        "BLOCKED", "official reports or licensed weather archive",
        "Cannot infer conditions from venue country.")
    add("squad/recruitment", "RR reference participants", "Played RR participants in supplied reference season",
        "playing_eleven, match/team/season joins", "playing_eleven, matches, competitions",
        "existing Step 4C reference-season evidence", "reference season is supplied-data cutoff only",
        "SUPPORTED_WITH_CAVEATS", "official current roster source",
        "Not current squad or auction list.")
    add("squad/recruitment", "auction availability", "Official registration/availability for auction",
        "official auction list/status", "none supplied",
        "not calculated", "no official roster/auction fields",
        "BLOCKED", "official auction registration and release documents",
        "External historical status is not availability.")
    add("squad/recruitment", "role certainty", "Verified player role/skills",
        "authoritative role labels", "role fields are unknown/not inferred in Step 4C",
        "not inferred", "source does not establish recruitment roles",
        "BLOCKED", "official squad/role profile",
        "Do not infer from batting/bowling appearances.")
    add("squad/recruitment", "squad gaps/budget/slots", "Evidence-based RR fit constraints",
        "official roster, purse, overseas slots, needs", "none supplied",
        "not calculated", "required planning inputs absent",
        "BLOCKED", "official RR/league documents",
        "No squad-fit conclusion is supportable.")
    return pd.DataFrame(rows)


def pressure_rows(context: pd.DataFrame) -> pd.DataFrame:
    coverage = read_csv(OUTPUTS / "pressure_context_coverage.csv").set_index(
        "pressure_definition"
    )
    scenarios = [
        ("chase_baseline", "valid_chase_context; balls_remaining_before <= 48; RRR >= 10 OR (RRR-CRR >= 3 and wickets_in_hand_before <= 6)", "chase fields, target_reached_before, required_run_rate, rrr_minus_crr, wickets_in_hand_before", "chase_baseline", "inferred chase proxy; not validated psychological pressure"),
        ("chase_strict", "valid chase plus tighter required-rate/wicket threshold from existing pressure definitions", "same reconstructed chase-state fields", "chase_strict", "sensitivity scenario only; no mental-strength inference"),
        ("chase_loose", "valid chase with looser required-rate threshold from existing pressure definitions", "same reconstructed chase-state fields", "chase_loose", "sensitivity scenario only; coverage may be volume-biased"),
        ("general_baseline", "general match-state pressure proxy from existing audit definition", "reconstructed score/wicket/ball fields", "general_baseline", "not necessarily a chase and not psychological pressure"),
        ("general_strict", "strict general pressure scenario from existing audit definition", "reconstructed score/wicket/ball fields", "general_strict", "threshold sensitivity only"),
        ("baseline", "ordinary eligible baseline rows outside pressure scenario", "innings validity and eligibility fields", "baseline", "baseline is not a neutral ability measure"),
    ]
    rows = []
    for s, definition, fields, coverage_key, caveat in scenarios:
        if coverage_key == "baseline":
            row = coverage.loc[coverage_key]
            events, matches, players, innings = (
                int(row["eligible_deliveries"]), int(row["eligible_matches"]),
                int(row["unique_batters"]), int(row["eligible_innings"]),
            )
        else:
            row = coverage.loc[coverage_key]
            events, matches, players, innings = (
                int(row["eligible_deliveries"]), int(row["eligible_matches"]),
                int(row["unique_batters"]), int(row["eligible_innings"]),
            )
        rows.append({
            "scenario": s, "operational_definition": definition,
            "required_fields": fields, "fields_trustworthy": "PARTIAL_ONLY",
            "eligible_event_count": events, "distinct_player_count": players,
            "distinct_match_count": matches, "distinct_innings_count": innings,
            "minimum_sample_limitations": "Step 4B used 20 pressure events, 5 pressure matches, 60 baseline events; these are coverage gates, not validity proof.",
            "sensitivity_checks": "Compare chase_baseline, chase_strict, chase_loose, general_baseline, general_strict and report event/match/player coverage.",
            "confounders": caveat + "; format, season, team, role and workload confounding remain.",
            "readiness": "EXPLORATORY_NOT_PSYCHOLOGICAL",
        })
    return pd.DataFrame(rows)


def squad_gaps() -> pd.DataFrame:
    facts = [
        ("RR reference-season participants", "20 played participants in supplied IPL 2026 reference-season evidence", "outputs/step4c_rr_squad_evidence.csv", "SUPPORTED_WITH_CAVEATS", "Does not prove current 2027 squad membership", "official 2027 RR roster"),
        ("RR reference-season match coverage", "16 RR matches represented in supplied IPL 2026 reference evidence", "matches.csv + competitions.csv + Step 4C", "SUPPORTED_WITH_CAVEATS", "Supplied cutoff only", "official season roster and schedule"),
        ("historical external candidates", "16 unique external player-role rows in Step 4C pool", "outputs/step4c_external_candidate_pool.csv", "SUPPORTED_WITH_CAVEATS", "Historical context is not availability", "official auction registration/release list"),
        ("unresolved candidate contexts", "0 unresolved Step 4C candidate rows in existing audit", "outputs/step4c_unresolved_status.csv", "SUPPORTED_WITH_CAVEATS", "No unresolved row does not establish completeness", "authoritative identity master"),
        ("current official squad", "Not supplied", "No official current-roster file", "BLOCKED", "Historical participation cannot substitute", "official RR announcement/league roster"),
        ("retained players", "Not supplied", "No retention list", "BLOCKED", "Cannot infer from reference participation", "official retention announcement"),
        ("released players", "Not supplied", "No release list", "BLOCKED", "Cannot infer from external classification", "official release/auction document"),
        ("registered auction candidates", "Not supplied", "No auction registration list", "BLOCKED", "External pool is not auction pool", "official auction registration list"),
        ("player roles", "Step 4C records roles as unknown/not inferred where unsupported", "step4c classification outputs", "BLOCKED", "Do not infer role from event presence", "official squad profiles or role feed"),
        ("overseas status/slots", "Not supplied", "No nationality/slot fields", "BLOCKED", "Cannot infer slot constraints", "official league regulations and roster"),
        ("budget/purse", "Not supplied", "No budget field", "BLOCKED", "No financial fit analysis", "official auction purse/team statement"),
        ("squad gaps/needs", "Not supplied", "No requirement brief", "BLOCKED", "No role-gap recommendation", "RR recruitment brief or authorised analyst input"),
    ]
    return pd.DataFrame(facts, columns=["evidence_item", "verified_fact", "repository_evidence", "status", "limitation", "authoritative_verification_needed"])


def source_requirements() -> pd.DataFrame:
    rows = [
        ("official score/ball data dictionary", "runs, batter runs, extras quantities, legal ball, team totals", "Unlock official batter/bowler rates", "IPL/BCCI or licensed score provider documentation", "manual verification required", "scorecard/CSV/API; provider terms unverified", "all seasons used; freshness per match", "(match_id, innings, delivery, player/team IDs)", "confirm license, attribution, redistribution", "reconcile totals, extras and innings"),
        ("official innings scorecards", "runs, balls, dismissals, not-outs, wickets, conceded runs", "Validate average, strike rate, economy, official wickets", "official league/team scorecards or licensed provider", "public or licensed; verify", "HTML/PDF/API unknown", "season and match complete", "(match_id, player_id, team_id)", "terms and archival rights", "cross-check delivery totals"),
        ("auction registration/release document", "registered players, release/retention, auction status", "Establish 2027 availability", "official IPL/BCCI/auction announcement", "likely public document; verify", "PDF/official webpage; no endpoint assumed", "current auction cycle", "(player identity plus official status)", "official-use and attribution review", "date/version and player identity checks"),
        ("RR official roster", "current squad, retained/released players, roles, nationality", "Establish squad baseline and roles", "official RR/league roster announcement", "likely public; verify", "web/PDF; no endpoint assumed", "current 2027 planning date", "(player ID/name plus season)", "terms and citation", "compare to league roster"),
        ("RR authorised recruitment brief", "role gaps, squad priorities, budget constraints", "Support squad-fit analysis", "internal authorised brief", "private/internal; access approval required", "document/table", "current planning cycle", "(role/slot/team constraints)", "confidentiality and access controls", "owner approval and versioning"),
        ("league regulations", "overseas limits, squad rules, auction rules", "Model roster constraints", "official IPL/BCCI regulations", "public document; verify", "PDF/document", "applicable 2027 rules", "team/season/rule version", "citation and version check", "rule interpretation review"),
        ("venue geometry dataset", "pitch dimensions, boundary coordinates, venue aliases", "Enable factual spatial ground analysis", "venue operator/official measured source or licensed provider", "availability/licensing unknown", "GIS/CSV/API unknown", "venues in analysis", "(venue_id plus geometry version)", "license and attribution", "coordinate/reference-system checks"),
        ("spatial event feed", "shot landing, wagon wheel, field placement", "Enable spatial shot/field analytics", "licensed tracking provider or official feed", "likely licensed; verify", "API/schema unknown", "matches analysed", "(match_id, delivery, coordinates)", "redistribution and derived-use checks", "coordinate completeness and plausibility"),
        ("weather/surface reports", "pitch, weather, humidity, wind, surface", "Contextualise venue/match conditions", "official match report or reputable archived weather provider", "public/licensed status unverified", "PDF/API unknown", "match dates and venues", "(venue/date/match_id)", "provider terms and citation", "time-zone and station validation"),
        ("identity master/alias table", "stable player/team/competition IDs and aliases", "Prevent contextual join errors", "official provider/team roster plus audited mapping", "requires source approval", "CSV/database", "all seasons", "(provider player ID, team ID, comp ID)", "license and provenance", "collision and one-to-many tests"),
    ]
    return pd.DataFrame(rows, columns=["source_requirement", "required_fields", "why_needed", "preferred_source_or_document_type", "availability_assessment", "expected_format_or_api", "freshness_and_coverage", "identity_keys", "licensing_terms_check", "pre_integration_validation"])


def inventory_report(inventory: pd.DataFrame, raw: dict[str, pd.DataFrame], context: pd.DataFrame) -> str:
    schema_lines = []
    for label, frame in raw.items():
        schema_lines.append(
            f"- `{label}`: " + ", ".join(
                f"{column} ({dtype})" for column, dtype in frame.dtypes.astype(str).items()
            )
        )
    schema_lines.append(
        "- `delivery_context`: " + ", ".join(
            f"{column} ({dtype})" for column, dtype in context.dtypes.astype(str).items()
        )
    )
    lines = [
        "# Step 4G Data Inventory",
        "",
        "## Scope",
        "Read-only inventory of the current ClutchLens repository and supplied data. No raw or prior audit artifact was changed.",
        "",
        "## Verified counts",
        f"- Raw deliveries: {len(raw['ball']):,}; raw matches: {len(raw['matches']):,}; competitions: {len(raw['competitions']):,}; teams: {len(raw['teams']):,}.",
        f"- Playing-XI rows: {len(raw['playing']):,}; contextual mappings: {len(raw['mapping']):,}.",
        f"- Processed delivery context: {len(context):,} rows; reconstructed innings: {context[['match_id','innings']].drop_duplicates().shape[0]:,}.",
        f"- Distinct venue IDs in matches: {raw['matches']['venue_id'].nunique():,}.",
        "",
        "## Source and artifact inventory",
        "The following table is generated from every CSV and document under data/raw, data/processed, outputs, and reports. CSV row counts, null/blank cells, duplicate rows, file size, and safety notes are recorded.",
        "```text\n" + inventory.to_string(index=False) + "\n```",
        "",
        "## Key source schemas",
        *schema_lines,
        "",
        "## Important source semantics",
        "- `extras1_runs` is an extras category code, not a verified extras-run total.",
        "- `extras_2_runs` has sparse non-zero values with unresolved semantics.",
        "- `runs` is usable only as conditional observed evidence; it is not formally verified as official batter runs.",
        "- `legal_ball` excludes documented wide/Overstep cases but retains other-extra caveats.",
        "- `is_wicket` includes events that are not necessarily bowler-attributed wickets.",
        "- The safest contextual identity key remains `(comp_id, team_id, player_id)`.",
        "",
        "## Dashboard dependency audit",
        "- Existing routes are `/`, `/analytics`, `/players`, `/ground`, `/api/players`, and `/recruitment`.",
        "- Recruitment consumes Step 4B candidate outputs and Step 4C classification/squad/external/unresolved outputs through `dashboard/data_service.py`.",
        "- Step 4F shortlist state is browser-local and must not be treated as repository evidence.",
    ]
    return "\n".join(lines) + "\n"


def traceability_report() -> str:
    rows = [
        ("A. Methodology explanation", "Step 4A-4E reports; Step 4F implementation report", "Pressure definitions, exclusions, contextual keys and caveats documented", "Conditional semantics and pressure proxy remain limited", "No current critical missing methodology description; data dictionary still needed", "Step 4G data-contract review"),
        ("B. Most reliable players under pressure", "Step 4B/4F candidate contexts and UI evidence profiles", "Candidate contexts and sample gates are visible", "Step 4E says no defensible Top 10 or reliability ranking; pressure is exploratory", "No claim can be made from current evidence", "Authoritative score/extras contract plus pre-registered pressure study"),
        ("C. How players strengthen RR squad", "Step 4C/4F RR versus external classification and shortlist", "Historical context and human shortlist workflow supported", "No roles, squad gaps, auction status, budget, or slots", "Official RR roster, needs and auction documents required", "Recruitment evidence integration after verification"),
        ("D. Player-level supporting evidence", "Step 4B outputs, Step 4F profiles/comparison", "Contextual samples, conditional evidence and candidate events shown", "Not official average/strike rate/economy/wickets; player contexts remain distinct", "Validated scorecard semantics and identity master needed", "Metric-contract upgrade"),
        ("E. Usable dashboard link", "`/recruitment` and existing Flask routes", "Local dashboard route is functional and browser-tested", "No hosted/public submission link exists in repository", "Deployment/hosting approval and stable URL required", "Packaging/deployment phase"),
        ("F. Honest limitations and sources", "Step 4E reports, Step 4F reports, current UI disclosures", "Limitations and supplied-data provenance are prominently documented", "External authoritative verification has not been integrated", "Citations and source licensing checks required", "Submission evidence pack review"),
    ]
    df = pd.DataFrame(rows, columns=["requirement", "current_location", "evidence_available", "quality_and_limitations", "missing_work_or_source", "recommended_future_phase"])
    return "# Step 4G Submission Traceability\n\n" + "```text\n" + df.to_string(index=False) + "\n```\n\n" + (
        "## Readiness conclusion\n\n"
        "The current repository supports an honest methodology and evidence-review dashboard, "
        "but does not support the submission's requested claims about the most reliable players "
        "under pressure or how each player would strengthen RR for IPL 2027. Those claims require "
        "validated performance semantics and authoritative squad/auction evidence.\n"
    )


def main() -> None:
    before = protected_hashes()
    raw = {
        "ball": read_csv(RAW / "ball_by_ball.csv"),
        "matches": read_csv(RAW / "matches.csv"),
        "competitions": read_csv(RAW / "competitions.csv"),
        "teams": read_csv(RAW / "teams.csv"),
        "playing": read_csv(RAW / "playing_eleven.csv"),
        "mapping": read_csv(RAW / "competition_team_player_mapping.csv"),
    }
    context = read_csv(PROCESSED / "delivery_context.csv")
    inventory = inventory_table()
    metrics = metric_rows(context, raw["ball"], raw["matches"])
    pressure = pressure_rows(context)
    squad = squad_gaps()
    sources = source_requirements()
    (OUTPUTS / "step4g_metric_feasibility.csv").write_text(metrics.to_csv(index=False), encoding="utf-8")
    (OUTPUTS / "step4g_pressure_data_readiness.csv").write_text(pressure.to_csv(index=False), encoding="utf-8")
    (OUTPUTS / "step4g_rr_squad_evidence_gaps.csv").write_text(squad.to_csv(index=False), encoding="utf-8")
    (OUTPUTS / "step4g_external_source_requirements.csv").write_text(sources.to_csv(index=False), encoding="utf-8")
    (REPORTS / "step4g_data_inventory.md").write_text(inventory_report(inventory, raw, context), encoding="utf-8")
    (REPORTS / "step4g_submission_traceability.md").write_text(traceability_report(), encoding="utf-8")
    recommendation = """# Step 4G Next-Phase Recommendation

## Readiness decision

Do not begin Step 4H, implement rankings, calculate pressure scores, or make
IPL 2027 squad-fit conclusions. The current evidence supports a transparent
recruitment evidence workspace, not the submission's requested “most reliable
under pressure” or squad-strengthening claims.

## Required sequence before analytical expansion

1. Approve an authoritative data contract for runs, extras, legal balls,
   innings totals, dismissals, not-outs, wickets, and bowler-charge runs.
2. Obtain and version official RR roster, retention/release, auction
   registration, role, overseas-slot, purse, and squad-needs evidence.
3. Define a pre-registered pressure study with objective match-state rules,
   minimum samples, sensitivity checks, and no psychological interpretation.
4. Re-run identity and join validation using stable provider IDs plus the
   contextual `(comp_id, team_id, player_id)` key.
5. Only after those inputs pass review should a human-approved next phase
   consider player-intelligence analytics or submission packaging.

The existing Step 4F dashboard and human working shortlist can remain as
evidence-review tooling. A shortlist is not availability confirmation,
recommendation, ranking, or squad-fit proof.
"""
    (REPORTS / "step4g_next_phase_recommendation.md").write_text(recommendation, encoding="utf-8")
    after = protected_hashes()
    if before != after:
        changed = sorted(set(before) | set(after))
        raise RuntimeError(f"Protected files changed during read-only audit: {changed}")
    for path in [OUTPUTS / "step4g_metric_feasibility.csv", OUTPUTS / "step4g_pressure_data_readiness.csv", OUTPUTS / "step4g_rr_squad_evidence_gaps.csv", OUTPUTS / "step4g_external_source_requirements.csv"]:
        check = pd.read_csv(path)
        if check.empty or check.isna().any().any() or check.duplicated().any():
            raise RuntimeError(f"Invalid Step 4G CSV output: {path.name}")
    print(f"Created Step 4G artifacts: {len(metrics)} metrics, {len(pressure)} pressure scenarios, {len(squad)} squad gaps, {len(sources)} source requirements.")


if __name__ == "__main__":
    main()
