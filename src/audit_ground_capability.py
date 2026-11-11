"""Audit venue and ground-visualisation capability from the supplied data."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
OUTPUTS = ROOT / "outputs"


def main() -> None:
    matches = pd.read_csv(RAW / "matches.csv", low_memory=False)
    competitions = pd.read_csv(RAW / "competitions.csv", low_memory=False)
    ball = pd.read_csv(RAW / "ball_by_ball.csv", low_memory=False)
    merged = matches.merge(
        competitions[["comp_id", "comp_name", "match_format", "season"]],
        on="comp_id",
        how="left",
        validate="many_to_one",
    )
    coverage = (
        merged.groupby(["venue_id", "venue_country"], dropna=False)
        .agg(
            match_count=("match_id", "nunique"),
            first_match_date=("match_date", "min"),
            last_match_date=("match_date", "max"),
            seasons=("season", lambda values: ", ".join(sorted(set(map(str, values))))),
            formats=("match_format", lambda values: ", ".join(sorted(set(map(str, values))))),
        )
        .reset_index()
        .sort_values(["venue_country", "venue_id"])
    )
    coverage.to_csv(OUTPUTS / "venue_match_coverage.csv", index=False)
    fields = []
    for source, frame in (
        ("matches.csv", matches),
        ("ball_by_ball.csv", ball),
        ("competitions.csv", competitions),
    ):
        for column in frame.columns:
            fields.append(
                {
                    "source_file": source,
                    "field": column,
                    "dtype": str(frame[column].dtype),
                    "null_count": int(frame[column].isna().sum()),
                    "null_pct": round(frame[column].isna().mean() * 100, 3),
                    "unique_non_null": int(frame[column].nunique(dropna=True)),
                    "ground_relevance": (
                        "venue identifier"
                        if column == "venue_id"
                        else "venue country label"
                        if column == "venue_country"
                        else "categorical shot/delivery field"
                        if column in {"stroke", "delivery_style", "on_or_off", "over_or_around", "pace_or_spin", "is_four", "is_six"}
                        else "not a ground geometry field"
                    ),
                }
            )
    pd.DataFrame(fields).to_csv(OUTPUTS / "ground_visualisation_field_inventory.csv", index=False)
    geometry = [
        column for column in ball.columns
        if column.lower().startswith(("lat", "lon"))
        or "coord" in column.lower()
        or column.lower() in {"x", "y", "shot_x", "shot_y", "latitude", "longitude"}
    ]
    report = [
        "# Ground Data Capability Audit",
        "",
        "## Verified venue fields",
        "",
        f"- `matches.csv` contains `venue_id` with **{matches['venue_id'].nunique()}** distinct IDs across **{len(matches):,}** match rows.",
        f"- `matches.csv` contains `venue_country` with **{matches['venue_country'].nunique()}** distinct country labels.",
        "- No stadium/ground name field is present. The UI therefore displays the exact supplied venue ID and country label, never an invented stadium name.",
        "- `venue_match_coverage.csv` lists every venue ID/country combination, match count, date range, seasons, and formats.",
        "",
        "## Spatial capability",
        "",
        f"- Candidate geometry/location fields found by schema audit: {', '.join(geometry) if geometry else 'none'}.",
        "- No supplied field contains venue coordinates, boundary dimensions, pitch dimensions, or shot landing coordinates.",
        "- Ground diagrams are illustrative layouts only and are explicitly labelled not to scale.",
        "",
        "## Categorical shot and delivery fields",
        "",
        f"- `stroke`: {ball['stroke'].nunique(dropna=True)} non-null categories; {int(ball['stroke'].isna().sum()):,} missing values.",
        f"- `delivery_style`: {ball['delivery_style'].nunique(dropna=True)} non-null categories; {int(ball['delivery_style'].isna().sum()):,} missing values.",
        f"- `on_or_off`: {ball['on_or_off'].nunique(dropna=True)} categories; `over_or_around`: {ball['over_or_around'].nunique(dropna=True)} categories.",
        "- `is_four` and `is_six` are source flags suitable for descriptive counts, but they do not provide spatial locations.",
        "",
        "## Limitations",
        "",
        "- Venue selection is exact supplied `venue_id` plus `venue_country`, not a real stadium-name or map lookup.",
        "- Venue-specific stroke and pace/spin distributions are descriptive row counts only.",
        "- No shot markers, heatmap positions, stadium maps, boundary sizes, or geographic claims are generated.",
    ]
    (REPORTS / "ground_data_capability_audit.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {len(coverage)} venue coverage rows.")
    print(f"Wrote {len(fields)} field inventory rows.")


if __name__ == "__main__":
    main()
