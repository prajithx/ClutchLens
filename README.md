# SupeRR Selector Season 2 — Step 1 Data Audit

This project extracts the supplied data-pack ZIP and audits every CSV without
changing the source data. It reports observed schemas, missing values,
duplicates, distributions, and key relationships. It does not calculate
pressure scores or player rankings.

## Folder structure

- `data/raw/` — files extracted from the data-pack ZIP.
- `data/processed/` — reserved for later derived data; Step 1 does not alter source files.
- `reports/data_audit_report.md` — readable audit report.
- `reports/problem_statement.txt` — text extracted from the supplied PDF.
- `outputs/data_inventory.csv` — one inventory row per input CSV.
- `src/data_audit.py` — reproducible audit script.
- `src/build_match_context.py` — delivery/innings reconstruction and provisional pressure flags.
- `data/processed/delivery_context.csv` — delivery-level match state.
- `data/processed/innings_summary.csv` — reconstructed innings totals and validation status.
- `reports/pressure_definition_options.md` — candidate definitions and sensitivity comparison.
- `outputs/pressure_coverage_summary.csv` — coverage counts for each threshold variant.
- `reports/ground_data_capability_audit.md` — verified venue and spatial-field limitations.
- `outputs/venue_match_coverage.csv` — exact source venue IDs with match/date/format coverage.
- `outputs/ground_visualisation_field_inventory.csv` — field-level availability inventory.
- `dashboard/` — local Flask UI for analytics, player intelligence, and Ground Explorer.
- `/recruitment` — Step 4D RR recruitment intelligence view built from verified Step 4B/4C outputs.
- `reports/step3c_stadium_experience_review.md` — homepage stadium scroll implementation and validation notes.
- `reports/step3d_photorealistic_stadium_review.md` — photographic asset audit and homepage asset readiness.
- `dashboard/static/images/stadium/` — reserved for approved local stadium and pitch photography.

## Setup and run

From the project folder in PowerShell:

```powershell
python -m pip install -r requirements.txt
python src\data_audit.py
python src\build_match_context.py
python src\validate_match_context.py
python src\audit_score_semantics.py
python src\test_metric_feasibility.py
python src\audit_ground_capability.py
python src\audit_player_methodology.py
python src\build_step4b_candidate_analysis.py
python src\build_step4c_rr_recruitment_audit.py
python src\validate_step4d_recruitment_dashboard.py
```

The script automatically selects the first `.zip` file in the project folder,
extracts it into `data/raw/`, and writes the report and inventory outputs. It
does not delete or modify the original ZIP.

The context builder reads the extracted CSVs and writes only derived files to
`data/processed/`, `reports/`, and `outputs/`. Its pressure flags are
provisional hypotheses for review; it does not calculate player rankings.

The Step 2.1 validation command independently checks innings completeness,
extras semantics, score formulas, legal-ball behavior, targets, and pressure
flag exclusions:

```powershell
python src\validate_match_context.py
```

The Step 2.2 forensic audit creates field distributions, raw non-zero
`extras_2_runs` cases, score-discrepancy cases, and the forensic report:

```powershell
python src\audit_score_semantics.py
```

The Step 2.3 feasibility test evaluates defensible batter and bowler event
metrics, exclusion policies, pressure coverage, and sample-size scenarios
without producing ratings or rankings:

```powershell
python src\test_metric_feasibility.py
```

The Step 4A player methodology audit creates metric feasibility, join quality,
pressure-context coverage, and sample-threshold outputs without ranking
players:

```powershell
python src\audit_player_methodology.py
```

Launch the local UI with:

```powershell
python -m flask --app dashboard.app run
```

The Recruitment Intelligence page is available at `/recruitment`. It displays
the latest supplied RR reference-season evidence and Step 4B candidate
classifications. Historical team context is not treated as proof of 2027
auction availability; roles, retention/release status, auction pool, budget,
and squad needs remain unavailable unless supplied by an official source.

Ground Explorer selections use the exact supplied `venue_id` and display
`venue_country` only as source metadata. The supplied data has no stadium
names, coordinates, dimensions, or shot landing locations, so its ground
diagram is illustrative and not to scale.

The homepage uses an original inline SVG stadium scene and a scroll-driven
camera journey. It does not represent a particular supplied venue:

```powershell
python -m flask --app dashboard.app run
```

If no ZIP is present, copy the downloaded data-pack ZIP into this folder and
rerun the command. The expected pack contains `ball_by_ball.csv`,
`playing_eleven.csv`, `matches.csv`, `competition_team_player_mapping.csv`,
`teams.csv`, `competitions.csv`, and a PDF problem statement.
