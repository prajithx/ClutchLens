"""Close the specific Step 4A.1 methodology gaps without selecting players."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
OUTPUTS = ROOT / "outputs"


def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    context = pd.read_csv(PROCESSED / "delivery_context.csv", low_memory=False)
    mapping = pd.read_csv(RAW / "competition_team_player_mapping.csv", low_memory=False)
    ball = pd.read_csv(RAW / "ball_by_ball.csv", low_memory=False)
    required = {
        "match_id", "innings", "striker_id", "striker_name", "bowler_id",
        "extras_type", "extras_2_runs", "legal_ball", "ordinary_innings",
        "abandoned_or_no_result", "innings_valid_for_pressure",
        "valid_chase_context", "target_reached_before", "balls_remaining_before",
        "required_run_rate", "rrr_minus_crr", "wickets_in_hand_before",
        "runs_required_before", "is_wicket", "dismissal_type",
    }
    missing = sorted(required.difference(context.columns))
    if missing:
        raise ValueError(f"delivery_context.csv missing columns: {', '.join(missing)}")
    return context, mapping, ball


def pressure_definitions(context: pd.DataFrame) -> dict[str, pd.Series]:
    eligible = context["innings_valid_for_pressure"] & context["ordinary_innings"] & ~context["abandoned_or_no_result"]
    return {
        "baseline": eligible,
        "chase_baseline": context["valid_chase_context"] & ~context["target_reached_before"] & (context["balls_remaining_before"] <= 48) & ((context["required_run_rate"] >= 10) | ((context["rrr_minus_crr"] >= 3) & (context["wickets_in_hand_before"] <= 6))),
        "general_baseline": eligible & ~context["target_reached_before"] & (context["balls_remaining_before"] <= 36) & ((context["wickets_in_hand_before"] <= 6) | (context["valid_chase_context"] & (context["runs_required_before"] <= 36))),
        "chase_strict": context["valid_chase_context"] & ~context["target_reached_before"] & (context["balls_remaining_before"] <= 30) & ((context["required_run_rate"] >= 12) | ((context["rrr_minus_crr"] >= 4) & (context["wickets_in_hand_before"] <= 6))),
        "general_strict": eligible & ~context["target_reached_before"] & (context["balls_remaining_before"] <= 24) & ((context["wickets_in_hand_before"] <= 6) | (context["valid_chase_context"] & (context["runs_required_before"] <= 24))),
        "chase_loose": context["valid_chase_context"] & ~context["target_reached_before"] & (context["balls_remaining_before"] <= 60) & ((context["required_run_rate"] >= 8) | ((context["rrr_minus_crr"] >= 2) & (context["wickets_in_hand_before"] <= 6))),
    }


def add_policies(context: pd.DataFrame) -> pd.DataFrame:
    frame = context.copy()
    excluded = ~frame["innings_valid_for_pressure"] | frame["abandoned_or_no_result"] | ~frame["ordinary_innings"]
    frame["strict_batter"] = frame["extras_type"].isna() & frame["extras_2_runs"].eq(0) & ~excluded
    frame["moderate_batter"] = ((frame["extras_type"].isna() & frame["extras_2_runs"].eq(0)) | (frame["extras_type"].isin(["Overstep", "other"]) & frame["extras_2_runs"].eq(0))) & ~excluded
    frame["eligible_bowling"] = frame["legal_ball"] & ~excluded
    frame["candidate_bowler_wicket"] = frame["is_wicket"] & frame["dismissal_type"].isin(["Bowled", "Caught", "LBW", "Stump", "Hit Wicket"])
    return frame


def reconcile_batter_counts(frame: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    valid = frame["innings_valid_for_pressure"] & frame["ordinary_innings"] & ~frame["abandoned_or_no_result"]
    strict = frame["strict_batter"]
    baseline_ids = set(frame.loc[valid, "striker_id"].dropna().astype(int))
    strict_ids = set(frame.loc[strict, "striker_id"].dropna().astype(int))
    rows = []
    for player_id in sorted(baseline_ids - strict_ids):
        events = frame[valid & frame["striker_id"].eq(player_id)]
        for (comp_id, team_id), group in events.groupby(["comp_id", "batting_team_id"], dropna=False):
            mapped = mapping[(mapping["player_id"].eq(player_id)) & mapping["comp_id"].eq(comp_id) & mapping["team_id"].eq(team_id)]
            rows.append({
                "player_id": player_id,
                "source_player_name": group["striker_name"].dropna().iloc[0] if group["striker_name"].notna().any() else "",
                "comp_id": comp_id,
                "team_id": team_id,
                "mapping_rows_for_context": len(mapped),
                "valid_baseline_events": len(group),
                "strict_eligible_events": int(group["strict_batter"].sum()),
                "extras_types": ", ".join(sorted(group["extras_type"].dropna().astype(str).unique())),
                "reason": "Baseline identity has valid context events, but all events are excluded by strict extras policy.",
            })
    return pd.DataFrame(rows, columns=["player_id", "source_player_name", "comp_id", "team_id", "mapping_rows_for_context", "valid_baseline_events", "strict_eligible_events", "extras_types", "reason"])


def threshold_rows(frame: pd.DataFrame, definitions: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    scenarios = [(10, 3, 30), (20, 5, 60), (30, 8, 90)]
    for role, player_column, base_column, policy in [
        ("batter", "striker_id", "strict_batter", "strict"),
        ("batter", "striker_id", "moderate_batter", "moderate"),
        ("bowler", "bowler_id", "eligible_bowling", "legal_ball"),
    ]:
        base = frame[frame[base_column] & frame[player_column].notna()]
        baseline = base.groupby(player_column).agg(baseline_events=("match_id", "size"), baseline_matches=("match_id", "nunique"))
        for definition, pressure_flag in definitions.items():
            pressure = frame[pressure_flag & frame[base_column] & frame[player_column].notna()]
            grouped = pressure.groupby(player_column).agg(pressure_events=("match_id", "size"), pressure_matches=("match_id", "nunique"))
            joined = baseline.join(grouped, how="left").fillna(0)
            for min_pressure, min_matches, min_baseline in scenarios:
                qualifying = joined[(joined["pressure_events"] >= min_pressure) & (joined["pressure_matches"] >= min_matches) & (joined["baseline_events"] >= min_baseline)]
                rows.append({
                    "role": role, "policy": policy, "pressure_definition": definition,
                    "minimum_pressure_events": min_pressure, "minimum_pressure_matches": min_matches,
                    "minimum_baseline_events": min_baseline, "threshold_event_scope": "pressure events; baseline_events is a separate minimum",
                    "qualifying_players": len(qualifying), "observed_players": len(joined),
                    "insufficient_evidence_players": len(joined) - len(qualifying),
                    "pressure_events_total": len(pressure), "baseline_events_total": len(base),
                    "caveat": "Contextual counts only; no player ordering or selection.",
                })
    return pd.DataFrame(rows)


def dismissal_thresholds(frame: pd.DataFrame) -> pd.DataFrame:
    candidate = frame[frame["eligible_bowling"] & frame["candidate_bowler_wicket"] & frame["bowler_id"].notna()]
    types = ["Caught", "Bowled", "LBW", "Stump", "Hit Wicket", "COMBINED_CANDIDATE_TYPES"]
    rows = []
    for dismissal_type in types:
        selected = candidate if dismissal_type == "COMBINED_CANDIDATE_TYPES" else candidate[candidate["dismissal_type"].eq(dismissal_type)]
        grouped = selected.groupby("bowler_id").agg(dismissal_events=("match_id", "size"), dismissal_matches=("match_id", "nunique"))
        for minimum_events, minimum_matches in [(1, 1), (2, 2), (3, 3), (5, 3)]:
            qualifying = grouped[(grouped["dismissal_events"] >= minimum_events) & (grouped["dismissal_matches"] >= minimum_matches)]
            rows.append({
                "dismissal_type_scope": dismissal_type,
                "minimum_dismissal_events": minimum_events,
                "minimum_matches": minimum_matches,
                "candidate_events_total": len(selected),
                "candidate_bowlers_observed": len(grouped),
                "qualifying_bowlers": len(qualifying),
                "insufficient_evidence_bowlers": len(grouped) - len(qualifying),
                "excluded_types": "RunOut, Retire Out, obstruction-related dismissals",
                "caveat": "Candidate bowler-attributed event count, not verified official wicket total.",
            })
    return pd.DataFrame(rows)


def identity_audit(mapping: pd.DataFrame) -> pd.DataFrame:
    specs = [
        ("player_id", ["player_id"], "Not safe globally: same player ID appears in multiple competition/team contexts."),
        ("comp_id_plus_player_id", ["comp_id", "player_id"], "Unique in mapping; appropriate competition-scoped identity where team context is not needed."),
        ("team_id_plus_player_id", ["team_id", "player_id"], "Not unique: a player/team context appears across competitions."),
        ("comp_id_plus_team_id_plus_player_id", ["comp_id", "team_id", "player_id"], "Unique and preserves competition plus team context; safest mapping join key for delivery context."),
    ]
    rows = []
    for name, columns, interpretation in specs:
        groups = mapping.groupby(columns, dropna=False).size()
        rows.append({
            "identity_key": name,
            "columns": "+".join(columns),
            "mapping_rows": len(mapping),
            "distinct_keys": len(groups),
            "duplicate_key_groups": int(groups.gt(1).sum()),
            "duplicate_rows_beyond_first": int((groups - 1).clip(lower=0).sum()),
            "unique_key": bool(groups.le(1).all()),
            "row_multiplication_safe": bool(groups.le(1).all()),
            "interpretation": interpretation,
        })
    return pd.DataFrame(rows)


def main() -> None:
    context, mapping, ball = load()
    frame = add_policies(context)
    definitions = pressure_definitions(frame)
    reconciliation = reconcile_batter_counts(frame, mapping)
    thresholds = threshold_rows(frame, definitions)
    dismissal = dismissal_thresholds(frame)
    identity = identity_audit(mapping)
    assert len(reconciliation) == 1
    assert len(thresholds) == 54
    assert len(dismissal) == 24
    assert len(identity) == 4
    assert thresholds.duplicated(["role", "policy", "pressure_definition", "minimum_pressure_events", "minimum_pressure_matches", "minimum_baseline_events"]).sum() == 0
    assert dismissal.duplicated(["dismissal_type_scope", "minimum_dismissal_events", "minimum_matches"]).sum() == 0
    OUTPUTS.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    reconciliation.to_csv(OUTPUTS / "batter_identity_count_reconciliation.csv", index=False)
    thresholds.to_csv(OUTPUTS / "player_sample_thresholds_extended.csv", index=False)
    dismissal.to_csv(OUTPUTS / "bowler_dismissal_thresholds.csv", index=False)
    identity.to_csv(OUTPUTS / "player_identity_key_audit.csv", index=False)
    report = f"""# Step 4A.2 Methodology Gap Closure

This correction step closes the specific review-gate gaps without selecting
players or producing rankings, ratings, pressure scores, recommendations, or
Top 10 lists.

## 887 vs 886 batter reconciliation

The baseline valid-context set contains 887 striker IDs; the strict batter
set contains 886. The exception output has {len(reconciliation)} row:

```text
{reconciliation.to_string(index=False)}
```

The difference is not a missing mapping or join multiplication. Player 286
has one valid ordinary event in competition 1611/team 20, but its
`extras_type` is `legbyes`, so it fails the strict null-extra policy. The
mapping contains one matching `(comp_id, team_id, player_id)` context.

## Extended threshold testing

`player_sample_thresholds_extended.csv` contains {len(thresholds)} data-derived
rows: 3 roles/policies x 6 pressure definitions x 3 threshold scenarios.
The pressure threshold applies to pressure events; `minimum_baseline_events`
is a separate baseline minimum. Counts are grouped by player ID within the
delivery context and do not join the mapping table.

```text
{thresholds.to_string(index=False)}
```

## Bowler dismissal-event reliability

`bowler_dismissal_thresholds.csv` contains {len(dismissal)} rows across five
scopes (Caught, Bowled, LBW, Stump, Hit Wicket, and the combined scope is
included in the row count) and four minimum event/match scenarios. Candidate
types exclude RunOut, Retire Out, and obstruction-related dismissals. These
are candidate bowler-attributed events, not verified official wicket totals.

```text
{dismissal.to_string(index=False)}
```

## Contextual identity key

```text
{identity.to_string(index=False)}
```

`player_id` alone is unsafe because it has duplicate mapping groups. The
actual mapping shows `(comp_id, player_id)` and
`(comp_id, team_id, player_id)` are unique, while `(team_id, player_id)` is
not. Use `(comp_id, team_id, player_id)` for a delivery-to-mapping join when
team context is available; use `(comp_id, player_id)` only for analyses where
competition-scoped identity is sufficient. The extended calculations avoid
mapping joins for event counts, so delivery rows are not multiplied.

## Remaining blockers

- Score and extras semantics remain unresolved.
- Pressure contexts remain inferred match-state contexts, not validated
  psychological pressure.
- Bowler conceded runs/economy remain blocked.
- Candidate dismissal events remain conservative source-event counts, not
  official wicket totals.
- Step 4B ranking or Top 10 selection is not authorized by this audit.

## Reproduction

```powershell
python src\\audit_methodology_gaps.py
```
"""
    (REPORTS / "step4a2_methodology_gap_closure.md").write_text(report, encoding="utf-8")
    print("Created Step 4A.2 gap-closure artifacts.")
    print(f"Threshold rows: {len(thresholds)}; dismissal rows: {len(dismissal)}; identity rows: {len(identity)}.")


if __name__ == "__main__":
    main()
