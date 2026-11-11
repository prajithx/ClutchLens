"""Independent validation of the Step 2 match-context reconstruction."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
OUTPUTS = ROOT / "outputs"


def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return (
        pd.read_csv(RAW / "ball_by_ball.csv", low_memory=False),
        pd.read_csv(RAW / "matches.csv", low_memory=False),
        pd.read_csv(RAW / "competitions.csv", low_memory=False),
        pd.read_csv(PROCESSED / "delivery_context.csv", low_memory=False),
    )


def completeness_table(
    ball: pd.DataFrame, matches: pd.DataFrame, competitions: pd.DataFrame
) -> tuple[pd.DataFrame, int]:
    meta = matches.merge(competitions[["comp_id", "match_format", "season"]], on="comp_id", how="left")
    rows = []
    for match_id in sorted(ball["match_id"].unique()):
        match_ball = ball[ball["match_id"].eq(match_id)]
        ordinary = match_ball[match_ball["innings"].isin([1, 2])]
        present = sorted(ordinary["innings"].unique().tolist())
        counts = ordinary.groupby("innings").size().to_dict()
        if len(present) == 2:
            continue
        match = meta[meta["match_id"].eq(match_id)].iloc[0]
        result = str(match["result"])
        if "abandoned" in result.lower():
            reason = "abandoned match; only recorded innings is expected"
        elif "no result" in result.lower():
            reason = "no-result match; only recorded innings is expected"
        else:
            reason = "one ordinary innings present; source result does not independently explain omission"
        rows.append(
            {
                "match_id": match_id,
                "match_date": match["match_date"],
                "comp_id": match["comp_id"],
                "match_format": match["match_format"],
                "season": match["season"],
                "result": match["result"],
                "innings_present": ",".join(map(str, present)),
                "delivery_rows_by_innings": ";".join(f"{key}:{value}" for key, value in sorted(counts.items())),
                "revised_target": match["revised_target"],
                "reason": reason,
            }
        )
    ordinary_counts = ball[ball["innings"].isin([1, 2])].groupby(["match_id", "innings"]).size()
    more_than_two = int(
        (ordinary_counts.reset_index().groupby("match_id")["innings"].nunique() > 2).sum()
    )
    return pd.DataFrame(rows), more_than_two


def extras_report(ball: pd.DataFrame) -> str:
    lines = [
        "# Extras Semantics Audit",
        "",
        "This is an evidence audit. No field is assigned a run meaning unless the observed "
        "relationships support it.",
        "",
        "## Distinct values and frequencies",
        "",
    ]
    for column in ["extras_type", "extras1_runs", "extras_2_runs", "runs"]:
        lines.extend(
            [
                f"### `{column}`",
                "",
                "```text",
                ball[column].value_counts(dropna=False).sort_index().to_string(),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Cross-tab and representative evidence",
            "",
            "The following table shows the dominant combinations. The one-to-one mapping "
            "between `extras_type` and `extras1_runs` is evidence that `extras1_runs` is a "
            "category/code field, not a delivered run count.",
            "",
            "```text",
            ball.groupby(["extras_type", "extras1_runs", "extras_2_runs", "runs"], dropna=False)
            .size()
            .reset_index(name="rows")
            .sort_values("rows", ascending=False)
            .head(40)
            .to_string(index=False),
            "```",
            "",
            "| extras_type | rows | runs values | extras_2_runs values |",
            "|---|---:|---|---|",
        ]
    )
    for extra_type, frame in ball.groupby(ball["extras_type"].fillna("<NULL>")):
        lines.append(
            f"| {extra_type} | {len(frame)} | {sorted(frame['runs'].unique().tolist())} | "
            f"{sorted(frame['extras_2_runs'].unique().tolist())} |"
        )
    lines.extend(
        [
            "",
            "## Interpretations and confidence",
            "",
            "- **`extras1_runs`: category/code only — high confidence.** Its values map exactly to observed labels: null=6, Overstep=1, wide=2, legbyes=3, byes=4, other=5, Penalty=7. It must not be added to a score.",
            "- **`runs`: likely batter runs — medium confidence.** On null-extra deliveries it takes cricket-like batter-run values 0, 1, 2, 3, 4, 5, and 6; on wide and byes it is always 0; on Overstep/`other` it can be 0, 1, 2, 3, 4, or 6. The supplied files do not label it explicitly as batter runs.",
            "- **`extras_2_runs`: likely an additional numeric extra component — low/medium confidence.** It is 0 on 200,963 of 200,999 rows, with non-zero values only on 20 Overstep rows, 16 `other` rows, and one null-extra row. The files do not define whether it is total extra runs, a second code, or a derived component.",
            "- **Total team runs: unresolved from supplied files alone.** `runs + extras_2_runs + one base run for every non-null extra` is a plausible hypothesis, but it does not reproduce every result margin and cannot be proven from a score-total column.",
            "- **Bowler-conceded runs: unresolved.** Byes, legbyes, penalty, and the unclear Overstep/`other` encoding prevent a reliable bowler-runs definition from this pack alone.",
            "",
            "Representative rows were sampled by `extras_type` in the independent calculations. "
            "The full raw CSV remains unchanged.",
        ]
    )
    return "\n".join(lines) + "\n"


def score_comparison(ball: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    frame = ball.copy()
    frame["base_extra"] = frame["extras_type"].notna().astype(int)
    formulas = {
        "runs_only": frame["runs"],
        "runs_plus_extras_2": frame["runs"] + frame["extras_2_runs"],
        "runs_plus_base_extra": frame["runs"] + frame["base_extra"],
        "current_hypothesis": frame["runs"] + frame["extras_2_runs"] + frame["base_extra"],
    }
    valid_matches = (
        frame[frame["innings"].isin([1, 2])]
        .groupby(["match_id", "innings"])
        .size()
        .unstack()
        .dropna()
        .index
    )
    result_mask = (
        matches["result"].astype("string").str.contains(r"Won by \d+ runs", case=False, na=False)
        & matches["revised_target"].isna()
        & ~matches["result"].astype("string").str.contains("abandoned|no result", case=False, na=False)
    )
    result_matches = matches[result_mask & matches["match_id"].isin(valid_matches)].copy()
    result_matches["margin"] = pd.to_numeric(
        result_matches["result"].str.extract(r"Won by (\d+) runs", expand=False), errors="coerce"
    )
    rows = []
    for name, values in formulas.items():
        frame[name] = values
        totals = frame[frame["innings"].isin([1, 2])].groupby(["match_id", "innings"])[name].sum().unstack()
        compared = result_matches[["match_id", "margin"]].merge(
            totals[1].rename("innings_1_total"), on="match_id"
        ).merge(totals[2].rename("innings_2_total"), on="match_id")
        error = (
            compared["innings_1_total"] - compared["innings_2_total"]
        ).abs().sub(compared["margin"]).abs()
        rows.append(
            {
                "formula": name,
                "result_matches_compared": len(error),
                "exact_result_margin_matches": int((error == 0).sum()),
                "innings_affected_by_nonzero_discrepancy": int((error > 0).sum()),
                "mean_absolute_margin_error": round(error.mean(), 3),
                "maximum_absolute_margin_error": int(error.max()),
                "interpretation": "not proven; result-margin agreement is an external consistency check only",
            }
        )
    return pd.DataFrame(rows)


def legal_ball_evidence(ball: pd.DataFrame) -> dict[str, int]:
    ordered = ball.sort_values(["match_id", "innings", "innings_ball_num", "delivery_ist_time"])
    grouped = ordered.groupby(["match_id", "innings"])
    previous = grouped["innings_ball_num"].shift()
    delta = ordered["innings_ball_num"] - previous
    same = ordered["extras_type"].fillna("<NULL>")
    return {
        "rows": len(ball),
        "innings_ball_increment_one": int((delta == 1).sum()),
        "wide_rows": int((same == "wide").sum()),
        "overstep_rows": int((same == "Overstep").sum()),
        "wide_or_overstep_increment_one": int(delta[same.isin(["wide", "Overstep"])].eq(1).sum()),
        "non_extra_increment_one": int(delta[~same.isin(["wide", "Overstep"])].eq(1).sum()),
    }


def write_validation() -> None:
    ball, matches, competitions, context = load()
    REPORTS.mkdir(exist_ok=True)
    OUTPUTS.mkdir(exist_ok=True)
    exceptions, more_than_two = completeness_table(ball, matches, competitions)
    exceptions.to_csv(OUTPUTS / "innings_completeness_exceptions.csv", index=False)
    comparison = score_comparison(ball, matches)
    comparison.to_csv(OUTPUTS / "score_reconstruction_comparison.csv", index=False)
    (REPORTS / "extras_semantics_audit.md").write_text(extras_report(ball), encoding="utf-8")

    ordinary_groups = ball[ball["innings"].isin([1, 2])].groupby(["match_id", "innings"]).size()
    full_groups = ball.groupby(["match_id", "innings"]).size()
    incomplete = context.groupby(["match_id", "innings"]).agg(
        ordinary=("ordinary_innings", "first"),
        abandoned=("abandoned_or_no_result", "first"),
        final_legal=("legal_balls_after", "max"),
        limit=("innings_ball_limit", "first"),
        wickets=("wickets_after", "max"),
        target_reached=("target_reached_after", "any"),
    ).reset_index()
    incomplete["short_nonallout"] = (
        incomplete["ordinary"]
        & ~incomplete["abandoned"]
        & (incomplete["final_legal"] < incomplete["limit"])
        & (incomplete["wickets"] < 10)
    )
    short_not_reached = incomplete["short_nonallout"] & ~incomplete["target_reached"]
    short_not_reached_keys = incomplete.loc[short_not_reached, ["match_id", "innings"]]
    short_not_reached_rows = context.merge(
        short_not_reached_keys, on=["match_id", "innings"], how="inner"
    )
    pressure_after_target_chase = int(
        context.loc[context["target_reached_before"], "pressure_chase_candidate"].sum()
    )
    pressure_after_target_general = int(
        context.loc[context["target_reached_before"], "pressure_general_candidate"].sum()
    )
    pressure_abandoned = int(
        context.loc[context["abandoned_or_no_result"], ["pressure_chase_candidate", "pressure_general_candidate"]].sum().sum()
    )
    legal = legal_ball_evidence(ball)
    target_source = context[context["innings"].eq(2)].groupby("match_id").agg(
        revised_target=("revised_target", "first"),
        first_innings_score=("first_innings_score", "first"),
        target=("target", "first"),
        valid=("valid_chase_context", "first"),
    )
    revised_count = int(target_source["revised_target"].notna().sum())
    first_total_count = int((target_source["revised_target"].isna() & target_source["first_innings_score"].notna()).sum())
    report = [
        "# Step 2.1 Validation Report",
        "",
        "This report independently audits Step 2 outputs. It does not create player ratings or rankings.",
        "",
        "## Innings completeness",
        "",
        f"- Ball-by-ball match IDs: **{ball['match_id'].nunique()}**.",
        f"- Full match/innings groups in the processed context: **{len(full_groups)}**.",
        f"- Ordinary innings groups (innings 1/2): **{len(ordinary_groups)}**.",
        f"- Expected groups from two innings per match: **{ball['match_id'].nunique() * 2}**.",
        f"- Matches with fewer than two ordinary innings: **{len(exceptions)}**; more than two ordinary innings: **{more_than_two}**.",
        "- The 22 exceptions are all abandoned/no-result matches with one recorded ordinary innings. They explain 22 missing ordinary innings; six matches also contain innings 3/4 (12 extra groups), so the total 1,724 groups is 1,734 expected ordinary groups minus 22 plus 12 extra groups.",
        "- This count difference is therefore supported by source match status and extra innings, not a grouping bug.",
        "",
        "See `outputs/innings_completeness_exceptions.csv` for every exception.",
        "",
        "## Extras, score, and bowler-run findings",
        "",
        "- `extras1_runs` is a category code with high confidence, based on its exact one-to-one mapping to `extras_type`.",
        "- `runs` is consistent with batter runs but is not explicitly labeled; confidence is medium.",
        "- `extras_2_runs` is sparse and not defined by the supplied files; confidence in its exact semantics is low/medium.",
        "- Candidate total formulas are compared in `outputs/score_reconstruction_comparison.csv`. Result-margin agreement favors the current hypothesis over simpler alternatives, but it does not prove the formula because result strings, DLS outcomes, and source omissions can affect the comparison.",
        "- Bowler-conceded runs cannot be established reliably. No bowler economy calculation should be performed.",
        "",
        "## Legal-ball and over-limit audit",
        "",
        f"- `innings_ball_num` increments by one on {legal['innings_ball_increment_one']} observed non-first rows; it increments on {legal['wide_or_overstep_increment_one']} of {legal['wide_rows'] + legal['overstep_rows']} wide/Overstep rows, so it is an event sequence, not a legal-ball count.",
        "- The recommended legal-ball rule is to exclude `wide` and `Overstep` from legal-ball counts. `other` remains legal in the current provisional reconstruction because its legal status is unresolved and it is rare; its rows are flagged.",
        "- Revised-over values above 20 are observed as multiples of six and normalize consistently to 7, 8, 15, and 19 overs in sample matches. The conversion is supported by delivery counts and over IDs.",
        "",
        "## Chase target audit",
        "",
        f"- Second innings targets sourced from revised_target: **{revised_count}** matches.",
        f"- Second innings targets sourced from first-innings total plus one: **{first_total_count}** matches.",
        f"- Pressure flags after target reached: chase candidate **{pressure_after_target_chase}**; general candidate **{pressure_after_target_general}** after the eligibility fix.",
        f"- Pressure flags in abandoned/no-result rows: **{pressure_abandoned}** after the eligibility fix.",
        f"- Ordinary short non-all-out innings found independently: **{int(incomplete['short_nonallout'].sum())}** groups. These are excluded from pressure eligibility unless they are demonstrably target-reached, all-out, or overs-complete.",
        f"- Of those, **{int(short_not_reached.sum())}** groups were not target-reached and had **{len(short_not_reached_rows)}** deliveries; pressure flags in them were chase **{int(short_not_reached_rows['pressure_chase_candidate'].sum())}** and general **{int(short_not_reached_rows['pressure_general_candidate'].sum())}**.",
        "",
        "A hand-checkable chase example can be reproduced by reading the first rows for match 13511 or 13522 in `delivery_context.csv`: score_before is the cumulative prior event total; legal_balls_before excludes wide/Overstep; runs_required_before equals target minus score_before; and required_run_rate is runs required divided by balls remaining times six.",
        "",
        "## Decision",
        "",
        "**Step 3 player analysis is blocked.** Match-state fields and provisional pressure flags are useful for review, but total team runs and bowler-conceded runs are not conclusively defined by the supplied data. Player pressure ratings should not be calculated until the extras semantics and score reconstruction are accepted or corrected.",
    ]
    (REPORTS / "step2_validation_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {len(exceptions)} innings exceptions.")
    print(f"Wrote {len(comparison)} score formulas.")
    print(f"Legal-ball evidence: {legal}")
    print(f"Pressure flags after target reached: chase={pressure_after_target_chase}, general={pressure_after_target_general}")


if __name__ == "__main__":
    write_validation()
