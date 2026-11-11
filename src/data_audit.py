"""Extract the supplied data pack and produce a reproducible data audit.

The script deliberately reports observations from the data instead of assigning
meaning to columns that are not present or cannot be validated.
"""

from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
REPORT_DIR = ROOT / "reports"
OUTPUT_DIR = ROOT / "outputs"
EXPECTED_CSVS = {
    "ball_by_ball.csv",
    "playing_eleven.csv",
    "matches.csv",
    "competition_team_player_mapping.csv",
    "teams.csv",
    "competitions.csv",
}


def clean_name(name: str) -> str:
    return Path(name).name


def find_zip() -> Path:
    zips = sorted(ROOT.glob("*.zip"))
    if not zips:
        raise FileNotFoundError(
            f"No ZIP file found in {ROOT}. Copy the downloaded data-pack ZIP into this folder."
        )
    return zips[0]


def extract_pack(zip_path: Path) -> list[str]:
    extracted: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            name = clean_name(member.filename)
            destination = RAW_DIR / name
            destination.write_bytes(archive.read(member))
            extracted.append(name)
    return extracted


def read_csv(path: Path) -> tuple[pd.DataFrame | None, str | None]:
    errors: list[str] = []
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False), None
        except (UnicodeDecodeError, pd.errors.ParserError, OSError) as exc:
            errors.append(f"{encoding}: {exc}")
    return None, " | ".join(errors)


def fmt(value: Any) -> str:
    if pd.isna(value):
        return "null"
    return str(value)


def short_value_counts(series: pd.Series, limit: int = 12) -> str:
    counts = series.value_counts(dropna=False).head(limit)
    values = [f"{fmt(index)} ({count})" for index, count in counts.items()]
    if len(series.value_counts(dropna=False)) > limit:
        values.append("...")
    return ", ".join(values) if values else "no values"


def column_profile(frame: pd.DataFrame) -> list[dict[str, Any]]:
    profile = []
    for column in frame.columns:
        missing = int(frame[column].isna().sum())
        profile.append(
            {
                "column": column,
                "dtype": str(frame[column].dtype),
                "missing": missing,
                "missing_pct": round(missing / len(frame) * 100, 2) if len(frame) else 0,
                "unique": int(frame[column].nunique(dropna=True)),
            }
        )
    return profile


def find_column(frame: pd.DataFrame, *names: str) -> str | None:
    lowered = {str(column).lower(): str(column) for column in frame.columns}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def id_columns(frame: pd.DataFrame) -> list[str]:
    return [
        str(column)
        for column in frame.columns
        if re.search(r"(^|_)(id|key)$|(^|_).*_id$", str(column), flags=re.IGNORECASE)
    ]


def values_for(frame: pd.DataFrame | None, column: str | None) -> set[Any]:
    if frame is None or column is None or column not in frame:
        return set()
    return set(frame[column].dropna().tolist())


def relationship_check(
    report: list[str],
    label: str,
    child: pd.DataFrame | None,
    child_column: str | None,
    parent: pd.DataFrame | None,
    parent_column: str | None,
) -> None:
    if child is None or parent is None or child_column is None or parent_column is None:
        report.append(f"- **{label}:** Could not evaluate because the relevant columns/files were not found.")
        return
    child_values = values_for(child, child_column)
    parent_values = values_for(parent, parent_column)
    missing = child_values - parent_values
    report.append(
        f"- **{label}:** {len(child_values) - len(missing)}/{len(child_values)} distinct "
        f"values matched; unmatched distinct values: {len(missing)}"
        + (f" (examples: {list(missing)[:5]})" if missing else "")
        + "."
    )


def audit() -> int:
    for directory in (RAW_DIR, REPORT_DIR, OUTPUT_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    zip_path = find_zip()
    extracted = extract_pack(zip_path)
    csv_paths = sorted(RAW_DIR.glob("*.csv"))
    frames: dict[str, pd.DataFrame] = {}
    read_errors: dict[str, str] = {}
    for path in csv_paths:
        frame, error = read_csv(path)
        if frame is None:
            read_errors[path.name] = error or "unknown read error"
        else:
            frames[path.name] = frame

    inventory = []
    for path in csv_paths:
        frame = frames.get(path.name)
        inventory.append(
            {
                "file_name": path.name,
                "rows": len(frame) if frame is not None else None,
                "columns": len(frame.columns) if frame is not None else None,
                "file_size_bytes": path.stat().st_size,
            }
        )
    pd.DataFrame(inventory).to_csv(OUTPUT_DIR / "data_inventory.csv", index=False)

    report: list[str] = [
        "# SupeRR Selector Season 2 Data Audit",
        "",
        f"- **Source ZIP:** `{zip_path.name}`",
        f"- **Extracted files:** {len(extracted)}",
        f"- **CSV files read successfully:** {len(frames)}",
        "",
        "## Dataset inventory",
        "",
        "| File | Rows | Columns | Size (bytes) |",
        "|---|---:|---:|---:|",
    ]
    for item in inventory:
        report.append(
            f"| `{item['file_name']}` | {item['rows'] if item['rows'] is not None else 'read failed'} | "
            f"{item['columns'] if item['columns'] is not None else 'read failed'} | {item['file_size_bytes']} |"
        )
    missing_expected = sorted(EXPECTED_CSVS - set(frames))
    report.extend(
        [
            "",
            f"Expected CSVs missing or unreadable: {', '.join(missing_expected) if missing_expected else 'none'}.",
            "",
            "## Schema and data dictionary",
            "",
        ]
    )
    for name, frame in frames.items():
        report.extend([f"### `{name}`", "", f"- Rows: **{len(frame)}**; columns: **{len(frame.columns)}**"])
        report.append("")
        report.append("| Column | Observed type | Missing | Missing % | Unique non-null |")
        report.append("|---|---|---:|---:|---:|")
        for item in column_profile(frame):
            report.append(
                f"| `{item['column']}` | `{item['dtype']}` | {item['missing']} | "
                f"{item['missing_pct']}% | {item['unique']} |"
            )
        report.append("")
        report.append("Sample records (maximum 5):")
        report.append("")
        report.append("```text")
        report.append(frame.head(5).to_string(index=False))
        report.extend(["```", ""])

        duplicates = int(frame.duplicated().sum())
        report.append(f"- Duplicate full rows: **{duplicates}**.")
        for column in id_columns(frame):
            report.append(
                f"- ID column `{column}`: {frame[column].nunique(dropna=True)} unique non-null; "
                f"{frame[column].isna().sum()} null."
            )
        report.append("")
        report.append("Selected value distributions:")
        for column in frame.columns:
            if (
                frame[column].nunique(dropna=True) <= 20
                or re.search(r"run|extra|wicket|dismiss|pace|spin|format|season|result|flag", str(column), re.I)
            ):
                report.append(f"- `{column}`: {short_value_counts(frame[column])}")
        report.append("")

    ball = frames.get("ball_by_ball.csv")
    if ball is not None:
        report.extend(["## Ball-by-ball audit", ""])
        for label, candidates in (
            ("Unique matches", ("match_id",)),
            ("Innings distribution", ("innings", "inning")),
            ("Over distribution/range", ("over", "over_number")),
            ("Ball-number distribution/range", ("ball", "ball_number", "ball_no")),
            ("Unique batters", ("batter_id", "batsman_id", "striker_id", "batter")),
            ("Unique bowlers", ("bowler_id", "bowler")),
            ("Run-related columns", ("runs", "total_runs", "batter_runs", "batsman_runs", "extras1_runs", "extras_2_runs")),
            ("Extras type", ("extras_type",)),
            ("Wicket flag", ("is_wicket",)),
            ("Dismissal type", ("dismissal_type",)),
            ("Pace/spin", ("pace_or_spin",)),
            ("Bowling type", ("bowling_type",)),
        ):
            matched = find_column(ball, *candidates)
            if matched is None:
                report.append(f"- **{label}:** column not present.")
            elif label in {"Unique matches", "Unique batters", "Unique bowlers"}:
                report.append(f"- **{label}:** {ball[matched].nunique(dropna=True)} unique values in `{matched}`.")
            else:
                report.append(f"- **{label} (`{matched}`):** {short_value_counts(ball[matched], 20)}.")
        report.append("")

    report.extend(["## Coverage and relationship validation", ""])
    matches = frames.get("matches.csv")
    playing = frames.get("playing_eleven.csv")
    mapping = frames.get("competition_team_player_mapping.csv")
    teams = frames.get("teams.csv")
    competitions = frames.get("competitions.csv")
    if matches is not None and competitions is not None:
        match_comp = find_column(matches, "comp_id", "competition_id")
        competition_comp = find_column(competitions, "comp_id", "competition_id")
        if match_comp and competition_comp:
            coverage = matches.merge(
                competitions[[competition_comp, "season", "match_format"]],
                left_on=match_comp,
                right_on=competition_comp,
                how="left",
                indicator=True,
            )
            report.extend(
                [
                    "### Match coverage by season and format",
                    "",
                    "| Season | Format | Matches |",
                    "|---|---|---:|",
                ]
            )
            for (season, match_format), count in (
                coverage.groupby(["season", "match_format"], dropna=False).size().sort_index().items()
            ):
                report.append(f"| {fmt(season)} | {fmt(match_format)} | {count} |")
            report.append("")
            date_column = find_column(matches, "match_date")
            result_column = find_column(matches, "result")
            if date_column:
                report.append(
                    f"- Match dates: {matches[date_column].min()} through {matches[date_column].max()} "
                    f"({matches[date_column].nunique()} distinct observed values)."
                )
            if result_column:
                report.append(f"- Result categories: {short_value_counts(matches[result_column], 20)}.")
                report.append(
                    f"- Abandoned/no-result results: "
                    f"{matches[result_column].astype('string').str.contains('abandoned|no result', case=False, na=False).sum()}."
                )
            report.append(
                f"- Matches without a competition join: "
                f"{(coverage['_merge'] != 'both').sum()}."
            )
            report.append("")
    if playing is not None:
        report.extend(["### Playing-eleven coverage", ""])
        report.append(
            f"- Unique players: **{playing['player_id'].nunique()}**; matches: **{playing['match_id'].nunique()}**; "
            f"teams: **{playing['team_id'].nunique()}**."
        )
        for column in ("is_played", "is_captain", "is_wk", "is_impact", "is_impact_off"):
            if column in playing:
                report.append(f"- `{column}`: {short_value_counts(playing[column])}.")
        report.append("")
    relationship_check(report, "Ball match IDs to matches", ball, find_column(ball, "match_id") if ball is not None else None, matches, find_column(matches, "match_id") if matches is not None else None)
    relationship_check(report, "Playing-eleven match IDs to matches", playing, find_column(playing, "match_id") if playing is not None else None, matches, find_column(matches, "match_id") if matches is not None else None)
    relationship_check(report, "Matches competition IDs to competitions", matches, find_column(matches, "comp_id", "competition_id"), competitions, find_column(competitions, "comp_id", "competition_id"))
    relationship_check(report, "Playing-eleven team IDs to teams", playing, find_column(playing, "team_id"), teams, find_column(teams, "team_id"))
    if ball is not None and teams is not None:
        for column in ("batting_team_id", "bowling_team_id"):
            relationship_check(report, f"Ball `{column}` to teams", ball, column if column in ball else None, teams, find_column(teams, "team_id"))
    if ball is not None and mapping is not None:
        for column in ("striker_id", "non_striker_id", "bowler_id"):
            relationship_check(report, f"Ball `{column}` to mapping", ball, column if column in ball else None, mapping, find_column(mapping, "player_id"))
    if mapping is not None:
        player_name_columns = [column for column in mapping.columns if re.search(r"player.*name|name", str(column), re.I)]
        if player_name_columns:
            report.append(f"- Mapping player-name columns observed: {', '.join(f'`{c}`' for c in player_name_columns)}.")
            report.append(f"- Duplicate mapping rows: **{mapping.duplicated().sum()}**; duplicate ID rows: **{mapping.duplicated(subset=[find_column(mapping, 'player_id')], keep=False).sum() if find_column(mapping, 'player_id') else 'not evaluated'}**.")
    report.append("")

    report.extend(["## Data quality findings and limitations", ""])
    if read_errors:
        for name, error in read_errors.items():
            report.append(f"- **Read error in `{name}`:** {error}")
    else:
        report.append("- All extracted CSV files were read successfully.")
    if ball is not None:
        for column in (find_column(ball, "innings", "inning"), find_column(ball, "over", "over_number"), find_column(ball, "ball", "ball_number", "ball_no")):
            if column is not None:
                numeric = pd.to_numeric(ball[column], errors="coerce")
                report.append(
                    f"- `{column}` numeric validity: {numeric.notna().sum()}/{len(ball)} parseable; "
                    f"observed range {numeric.min()} to {numeric.max()}."
                )
        innings_column = find_column(ball, "innings", "inning")
        over_column = find_column(ball, "overid", "over", "over_number")
        ball_column = find_column(ball, "over_ball_num", "ball", "ball_number", "ball_no")
        if innings_column and over_column and ball_column:
            innings = pd.to_numeric(ball[innings_column], errors="coerce")
            overs = pd.to_numeric(ball[over_column], errors="coerce")
            balls = pd.to_numeric(ball[ball_column], errors="coerce")
            report.append(
                f"- Suspicious delivery values: innings outside 1-4: {(~innings.between(1, 4)).sum()}; "
                f"over IDs outside 1-20: {(~overs.between(1, 20)).sum()}; "
                f"non-positive ball numbers: {(balls < 1).sum()}."
            )
        for column in ("runs", "extras1_runs", "extras_2_runs"):
            if column in ball:
                numeric = pd.to_numeric(ball[column], errors="coerce")
                report.append(
                    f"- `{column}` suspicious numeric values: negative {(numeric < 0).sum()}; "
                    f"non-numeric {numeric.isna().sum()}."
                )
    report.extend(
        [
            "- Source files were not modified. Different row counts are expected because ball-by-ball data has multiple rows per delivery, playing-eleven data has multiple rows per match/player, and mapping/team/competition tables are reference data.",
            "- Join checks use exact observed column names and values. Competition context, composite keys, and null IDs may require domain confirmation before any correction.",
            "- No player rankings, pressure scores, or inferred meanings for run/extra fields were calculated in this step.",
            "",
            "## Unresolved questions",
            "",
            "- The supplied schema should be reviewed before deciding whether similarly named run or extras columns represent runs, codes, or derived values.",
            "- Any unmatched IDs and duplicate mappings should be investigated with the challenge owner before source data is changed.",
        ]
    )
    (REPORT_DIR / "data_audit_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    pdfs = list(RAW_DIR.glob("*.pdf"))
    problem_path = REPORT_DIR / "problem_statement.txt"
    if pdfs:
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(pdfs[0]))
            text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
            problem_path.write_text(text + "\n", encoding="utf-8")
            pdf_status = f"extracted {len(reader.pages)} pages from {pdfs[0].name}"
        except (ImportError, OSError, ValueError) as exc:
            problem_path.write_text(
                f"PDF text extraction unavailable for {pdfs[0].name}: {exc}\n", encoding="utf-8"
            )
            pdf_status = f"PDF extraction unavailable: {exc}"
    else:
        problem_path.write_text("No PDF was found in the extracted data pack.\n", encoding="utf-8")
        pdf_status = "no PDF found"

    print(f"Extracted {len(extracted)} files from {zip_path.name}.")
    print(f"Read {len(frames)} CSV files; generated {OUTPUT_DIR / 'data_inventory.csv'}.")
    print(f"Generated {REPORT_DIR / 'data_audit_report.md'}.")
    print(f"Problem statement: {pdf_status}.")
    if read_errors:
        print(f"WARNING: CSV read errors: {', '.join(read_errors)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(audit())
