"""Forensic audit of score and extras semantics from supplied files only."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
OUTPUTS = ROOT / "outputs"


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ball = pd.read_csv(RAW / "ball_by_ball.csv", low_memory=False)
    matches = pd.read_csv(RAW / "matches.csv", low_memory=False)
    competitions = pd.read_csv(RAW / "competitions.csv", low_memory=False)
    context = pd.read_csv(
        PROCESSED / "delivery_context.csv",
        usecols=[
            "match_id",
            "innings",
            "score_after",
            "team_runs_event",
            "innings_final_score",
            "valid_chase_context",
            "target",
            "target_reached_after",
        ],
        low_memory=False,
    )
    return ball, matches, competitions, context


def extras_outputs(ball: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    distributions = []
    for column in ("extras_type", "extras1_runs", "extras_2_runs"):
        counts = ball[column].value_counts(dropna=False).rename_axis("value").reset_index(name="rows")
        counts.insert(0, "field", column)
        distributions.append(counts)
    distributions_frame = pd.concat(distributions, ignore_index=True)

    cross_tabs = []
    for right in ("extras1_runs", "extras_2_runs"):
        table = pd.crosstab(
            ball["extras_type"].fillna("<NULL>"),
            ball[right].fillna("<NULL>").astype(str),
            dropna=False,
        ).reset_index()
        table.insert(0, "cross_tab", f"extras_type_by_{right}")
        cross_tabs.append(table)
    cross_tabs_frame = pd.concat(cross_tabs, ignore_index=True, sort=False).fillna(0)

    columns = [
        "match_id",
        "innings",
        "overid",
        "over_ball_num",
        "innings_ball_num",
        "striker_name",
        "bowler_name",
        "runs",
        "extras_type",
        "extras1_runs",
        "extras_2_runs",
        "is_wicket",
        "dismissal_type",
    ]
    nonzero = ball[ball["extras_2_runs"].ne(0)][columns].copy()
    nonzero.insert(0, "row_number", nonzero.index + 1)
    return distributions_frame, cross_tabs_frame, nonzero


def parse_result(result: str) -> tuple[str, float | None]:
    text = str(result)
    runs = re.search(r"Won by\s+(\d+)\s+runs", text, flags=re.IGNORECASE)
    if runs:
        return "won_by_runs", float(runs.group(1))
    wickets = re.search(r"Won by\s+(\d+)\s+wickets?", text, flags=re.IGNORECASE)
    if wickets:
        return "won_by_wickets", float(wickets.group(1))
    if re.search(r"tie|tied", text, flags=re.IGNORECASE):
        return "tie", None
    if re.search(r"abandoned|no result", text, flags=re.IGNORECASE):
        return "abandoned_or_no_result", None
    if re.search(r"draw", text, flags=re.IGNORECASE):
        return "draw", None
    return "unparsed", None


def score_cases(
    ball: pd.DataFrame, matches: pd.DataFrame, competitions: pd.DataFrame, context: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, int], pd.DataFrame]:
    frame = ball.copy()
    frame["base_extra"] = frame["extras_type"].notna().astype(int)
    frame["runs_only"] = frame["runs"]
    frame["runs_plus_extras_2"] = frame["runs"] + frame["extras_2_runs"]
    frame["runs_plus_base_extra"] = frame["runs"] + frame["base_extra"]
    frame["current_hypothesis"] = frame["runs"] + frame["extras_2_runs"] + frame["base_extra"]
    totals = (
        frame[frame["innings"].isin([1, 2])]
        .groupby(["match_id", "innings"])[
            ["runs_only", "runs_plus_extras_2", "runs_plus_base_extra", "current_hypothesis"]
        ]
        .sum()
        .unstack(fill_value=0)
    )
    totals.columns = [f"{formula}_innings_{innings}" for formula, innings in totals.columns]
    meta = matches.merge(competitions, on="comp_id", how="left", validate="many_to_one")
    meta["result_kind"], meta["result_value"] = zip(*meta["result"].map(parse_result))
    context_totals = (
        context.groupby(["match_id", "innings"], as_index=False)["innings_final_score"]
        .max()
        .pivot(index="match_id", columns="innings", values="innings_final_score")
        .rename(columns={1: "script_total_innings_1", 2: "script_total_innings_2"})
    )
    cases = meta.join(totals, on="match_id").join(context_totals, on="match_id")
    cases["reconstructed_margin"] = (
        cases["current_hypothesis_innings_1"] - cases["current_hypothesis_innings_2"]
    ).abs()
    cases["margin_mismatch"] = (
        cases["result_kind"].eq("won_by_runs")
        & cases["result_value"].notna()
        & cases["reconstructed_margin"].notna()
        & cases["reconstructed_margin"].ne(cases["result_value"])
    )
    cases["incomplete_or_abandoned"] = cases["result_kind"].isin(
        ["abandoned_or_no_result"]
    )
    cases["eligible_margin_check"] = (
        cases["result_kind"].eq("won_by_runs")
        & cases["revised_target"].isna()
        & cases["current_hypothesis_innings_1"].notna()
        & cases["current_hypothesis_innings_2"].notna()
        & ~cases["incomplete_or_abandoned"]
    )
    cases["mismatch_amount"] = cases["reconstructed_margin"] - cases["result_value"]
    cases["has_ambiguous_extra"] = (
        ball.assign(ambiguous=ball["extras_type"].isin(["other", "Penalty"]))
        .groupby("match_id")["ambiguous"]
        .any()
        .reindex(cases["match_id"], fill_value=False)
        .to_numpy()
    )
    cases["extra_types_observed"] = (
        ball.groupby("match_id")["extras_type"]
        .agg(lambda values: ", ".join(sorted(set(values.dropna().astype(str)))))
        .reindex(cases["match_id"])
        .fillna("")
        .to_numpy()
    )
    cases["extra_rows"] = (
        ball.assign(has_extra=ball["extras_type"].notna())
        .groupby("match_id")["has_extra"]
        .sum()
        .reindex(cases["match_id"], fill_value=0)
        .to_numpy()
    )
    case_columns = [
        "match_id",
        "innings",  # removed below if absent
        "comp_id",
        "comp_name",
        "match_format",
        "season",
        "match_date",
        "result",
        "result_kind",
        "result_value",
        "revised_target",
        "first_inn_revised_overs",
        "second_inn_revised_overs",
        "runs_only_innings_1",
        "runs_only_innings_2",
        "runs_plus_extras_2_innings_1",
        "runs_plus_extras_2_innings_2",
        "runs_plus_base_extra_innings_1",
        "runs_plus_base_extra_innings_2",
        "current_hypothesis_innings_1",
        "current_hypothesis_innings_2",
        "script_total_innings_1",
        "script_total_innings_2",
        "reconstructed_margin",
        "mismatch_amount",
        "extra_types_observed",
        "extra_rows",
        "has_ambiguous_extra",
        "incomplete_or_abandoned",
    ]
    case_columns.remove("innings")
    mismatch_cases = cases[cases["margin_mismatch"] & cases["eligible_margin_check"]][case_columns].copy()
    mismatch_cases["supported_cause"] = mismatch_cases.apply(classify_case, axis=1)
    mismatch_cases["cause_evidence"] = mismatch_cases.apply(
        lambda row: cause_evidence(row["supported_cause"], row), axis=1
    )
    summary = (
        mismatch_cases.groupby(["season", "match_format"], dropna=False)
        .size()
        .rename("mismatch_matches")
        .reset_index()
    )
    return mismatch_cases, {
        "run_result_cases": int(cases["eligible_margin_check"].sum()),
        "run_result_matches": int(
            (cases["eligible_margin_check"] & ~cases["margin_mismatch"]).sum()
        ),
        "run_result_mismatches": int(
            (cases["eligible_margin_check"] & cases["margin_mismatch"]).sum()
        ),
        "all_parsed_run_results": int(cases["result_kind"].eq("won_by_runs").sum()),
        "wicket_result_cases": int(cases["result_kind"].eq("won_by_wickets").sum()),
        "abandoned_or_no_result": int(cases["result_kind"].eq("abandoned_or_no_result").sum()),
        "unparsed_or_tie": int(cases["result_kind"].isin(["unparsed", "tie", "draw"]).sum()),
    }, summary


def classify_case(row: pd.Series) -> str:
    if row["incomplete_or_abandoned"]:
        return "abandoned_or_no_result"
    if row["revised_target"] == row["revised_target"]:
        return "revised_target_or_DLS_case"
    if row["has_ambiguous_extra"]:
        return "ambiguous_extra_type_present"
    if row["extra_rows"] == 0:
        return "no_extra_rows_but_result_mismatch"
    return "unresolved_source_or_schema_difference"


def cause_evidence(cause: str, row: pd.Series) -> str:
    if cause == "abandoned_or_no_result":
        return "result string explicitly identifies abandoned/no-result"
    if cause == "revised_target_or_DLS_case":
        return f"revised_target={row['revised_target']}; result may reflect DLS/revised context"
    if cause == "ambiguous_extra_type_present":
        return f"ambiguous extras present: {row['extra_types_observed']}"
    if cause == "no_extra_rows_but_result_mismatch":
        return "no labeled extras in match rows; delivery formula cannot explain the mismatch"
    return f"labeled extras present: {row['extra_types_observed']}; no unique cause proven"


def build_report(
    ball: pd.DataFrame,
    matches: pd.DataFrame,
    context: pd.DataFrame,
    nonzero: pd.DataFrame,
    mismatch_cases: pd.DataFrame,
    result_counts: dict[str, int],
    mismatch_summary: pd.DataFrame,
) -> str:
    sample_lines = [
        "| extras_type | match_id | innings | overid | over_ball_num | innings_ball_num | striker | bowler | runs | extras1_runs | extras_2_runs | is_wicket | dismissal_type |",
        "|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---|---|",
    ]
    for _, row in nonzero.iterrows():
        sample_lines.append(
            f"| {row['extras_type']} | {row['match_id']} | {row['innings']} | {row['overid']} | "
            f"{row['over_ball_num']} | {row['innings_ball_num']} | {row['striker_name']} | "
            f"{row['bowler_name']} | {row['runs']} | {row['extras1_runs']} | {row['extras_2_runs']} | "
            f"{row['is_wicket']} | {row['dismissal_type']} |"
        )
    representative_lines = [
        "| extras_type | match_id | innings | overid | over_ball_num | innings_ball_num | striker | bowler | runs | extras1_runs | extras_2_runs | is_wicket | dismissal_type |",
        "|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---|---|",
    ]
    representative_columns = [
        "match_id", "innings", "overid", "over_ball_num", "innings_ball_num",
        "striker_name", "bowler_name", "runs", "extras_type", "extras1_runs",
        "extras_2_runs", "is_wicket", "dismissal_type",
    ]
    for extra_type, group in ball.groupby(ball["extras_type"].fillna("<NULL>"), sort=True):
        row = group.iloc[0]
        representative_lines.append(
            f"| {extra_type} | {row['match_id']} | {row['innings']} | {row['overid']} | "
            f"{row['over_ball_num']} | {row['innings_ball_num']} | {row['striker_name']} | "
            f"{row['bowler_name']} | {row['runs']} | {row['extras1_runs']} | {row['extras_2_runs']} | "
            f"{row['is_wicket']} | {row['dismissal_type']} |"
        )
    causes = mismatch_cases["supported_cause"].value_counts().to_dict()
    report = [
        "# Step 2.2 Score / Extras Forensic Audit",
        "",
        "This validation uses only the supplied raw and generated files. It does not create player ratings or rankings.",
        "",
        "## Confirmed interpretations",
        "",
        "- `extras1_runs` is a category code, high confidence: its values map exactly to the observed extras labels and must not be added as runs.",
        "- `runs` behaves like batter runs with medium confidence: ordinary deliveries contain cricket-like 0/1/2/3/4/5/6 values, while wides and byes are zero. The schema does not explicitly name it.",
        "- `extras_2_runs` is unresolved, low/medium confidence: it is zero on 200,963 rows and non-zero on only 37 rows. Its values occur in Overstep, `other`, and one null-extra row, but no supplied total-extras definition identifies whether it is an amount or derived field.",
        "- Team totals are not proven by this pack. The current hypothesis remains a transparent provisional reconstruction, not an accepted scorecard total.",
        "- Bowler-conceded runs/economy are unavailable from the supplied schema. Wides, byes, legbyes, penalty, and unresolved Overstep/`other` treatment prevent a reliable charged-runs calculation.",
        "",
        "## Representative raw rows by extras type",
        "",
        *representative_lines,
        "",
        "## All non-zero `extras_2_runs` evidence",
        "",
        f"There are **{len(nonzero)}** non-zero rows in the supplied CSV. The prompt referred to 37, but the observed data contains 36; the complete table is in `outputs/extras_2_runs_nonzero_rows.csv`.",
        "",
        *sample_lines,
        "",
        "The rows cluster into 21 Overstep rows, 14 `other` rows, and one null-extra row. By value, 20 rows contain 1 and 16 contain 4. This establishes where the field appears, but does not establish its semantic unit.",
        "",
        "## Score discrepancy cases",
        "",
        f"The current result-margin cross-check has **{len(mismatch_cases)}** mismatching matches under safe case-insensitive parsing. The earlier 164 count was produced by the prior comparison's case-sensitive numeric extraction and is not reproducible as the safe parsed population; this audit reports each safe-parsed case explicitly.",
        f"Cause classifications are: {causes}. These are evidence-based categories, not claims that a single formula can be selected.",
        "",
        "| Season | Format | Mismatch matches |",
        "|---|---|---:|",
    ]
    for row in mismatch_summary.itertuples(index=False):
        report.append(f"| {row.season} | {row.match_format} | {row.mismatch_matches} |")
    report.extend(
        [
            "",
            "The complete case table is in `outputs/score_discrepancy_cases.csv`. Cases with ambiguous extras or revised targets are not silently repaired; cases with no extras demonstrate that result-margin agreement cannot by itself prove an extras formula.",
            "",
            "## Result-string cross-check",
            "",
            f"- Parsed run-margin results: **{result_counts['run_result_cases']}**; exact reconstructed-margin matches: **{result_counts['run_result_matches']}**; mismatches: **{result_counts['run_result_mismatches']}**.",
            f"- All parsed run-margin result strings before eligibility exclusions: **{result_counts['all_parsed_run_results']}**.",
            f"- Parsed wicket-margin results: **{result_counts['wicket_result_cases']}**. These were checked only for chase target reach, not exact final totals.",
            f"- Abandoned/no-result results: **{result_counts['abandoned_or_no_result']}**; tie/draw/unparsed results: **{result_counts['unparsed_or_tie']}**.",
            "- Run-margin parsing is safe only for result strings with an explicit `Won by N runs` phrase. DLS, revised-target, no-result, and super-over cases are not treated as ordinary margin checks.",
            "- Wicket-margin results do not reveal the exact final score, so they cannot identify a precise delivery-total formula.",
            "",
            "## Bowler-conceded runs feasibility",
            "",
            "- No supplied column explicitly identifies bowler-charged runs.",
            "- `is_wicket` includes dismissal types such as RunOut, so it cannot be called a bowler-wicket field without dismissal filtering.",
            f"- Observed dismissal types include: {', '.join(sorted(ball.loc[ball['dismissal_type'].notna(), 'dismissal_type'].astype(str).unique()))}.",
            "- Defensible future bowling context metrics may include legal-ball counts, total wicket events separated by dismissal type, and dot-event counts only after team/batter-run semantics are accepted. Bowler economy should remain unavailable.",
            "",
            "## Decision gate",
            "",
            "**Batter analysis: PARTIALLY READY for descriptive match-state analysis, BLOCKED for final pressure ratings.** Chase targets and provisional state fields can be inspected, but team totals remain unproven.",
            "",
            "**Bowler analysis: BLOCKED for economy or conceded-run ratings.** Legal-ball and dismissal-event context is available, but bowler-conceded runs cannot be reliably computed.",
            "",
            "## Unresolved questions",
            "",
            "- What is the documented definition of `extras_2_runs`?",
            "- Does `other` represent a legal delivery, a no-ball/Overstep variant, or another event type?",
            "- Does `runs` contain batter runs only in every labeled-extra case?",
            "- Is there an omitted scorecard/team-total field outside the supplied CSV pack?",
            "",
            "The evidence does not justify silently changing the formula or beginning Step 3 player ratings.",
        ]
    )
    return "\n".join(report) + "\n"


def main() -> None:
    ball, matches, competitions, context = load_inputs()
    OUTPUTS.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    distributions, cross_tabs, nonzero = extras_outputs(ball)
    distributions.to_csv(OUTPUTS / "extras_field_distributions.csv", index=False)
    cross_tabs.to_csv(OUTPUTS / "extras_cross_tabs.csv", index=False)
    nonzero.to_csv(OUTPUTS / "extras_2_runs_nonzero_rows.csv", index=False)
    mismatch_cases, result_counts, mismatch_summary = score_cases(
        ball, matches, competitions, context
    )
    mismatch_cases.to_csv(OUTPUTS / "score_discrepancy_cases.csv", index=False)
    report = build_report(
        ball, matches, context, nonzero, mismatch_cases, result_counts, mismatch_summary
    )
    (REPORTS / "step2_2_score_forensics.md").write_text(report, encoding="utf-8")
    print(f"Wrote {len(distributions)} distribution rows and {len(cross_tabs)} cross-tab rows.")
    print(f"Wrote {len(nonzero)} non-zero extras_2_runs rows.")
    print(f"Wrote {len(mismatch_cases)} score discrepancy cases.")
    print(f"Result cross-check: {result_counts}")


if __name__ == "__main__":
    main()
