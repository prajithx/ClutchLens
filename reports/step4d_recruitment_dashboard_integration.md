# Step 4D Recruitment Dashboard Integration

## Delivered surface

Added `/recruitment` to the Flask dashboard and added a shared navigation link
without changing the cinematic homepage, analytics, player intelligence, or
Ground Explorer routes.

The page is an evidence reader, not an auction recommendation engine. It
does not create new rankings, reorder Step 4B candidates, infer roles, or
infer auction availability.

## Source files consumed

The integration reads only existing verified outputs:

- `outputs/step4b_batter_candidates.csv`
- `outputs/step4b_bowler_candidates.csv`
- `outputs/step4c_batter_classification.csv`
- `outputs/step4c_bowler_classification.csv`
- `outputs/step4c_rr_squad_evidence.csv`
- `outputs/step4c_external_candidate_pool.csv`
- `outputs/step4c_unresolved_status.csv`

The service also reads supplied `matches.csv` and `competitions.csv` only to
derive the displayed RR reference-season match count from source metadata.
No raw data is copied into dashboard files.

## Grain and identity decisions

- Candidate cards are one row per Step 4B contextual identity and role:
  `(role, comp_id, team_id, player_id)`, represented by the source
  `context_key`.
- Step 4B evidence is joined to Step 4C classification using `context_key`
  with `validate="one_to_one"`.
- External pool rows are unique by `(role, player_id)` and preserve all
  historical contexts in the `historical_contexts`, `historical_teams`, and
  `historical_competitions` fields.
- Yuzvendra Chahal therefore appears once in the external player-role pool,
  while his two Step 4B historical contexts remain visible in the
  classification evidence.
- RR squad evidence is displayed at its supplied reference-season
  comp/team/player grain.
- Required columns, duplicate rows, empty required files, and missing
  classifications raise explicit errors during loading.

## Exact displayed totals

Validated from the actual CSV outputs:

- RR reference season: IPL 2026
- RR team identifier: `team_id=3`
- RR matches: 16
- RR played participants: 20
- Step 4B batter contexts: 10
  - RR reference-season participants: 2
  - external historical contexts: 8
- Step 4B bowler contexts: 10
  - RR reference-season participants: 1
  - external historical contexts: 9
- External unique player-role rows: 16
- Unresolved contexts: 0

The page labels the RR register as participants in the latest supplied
reference season, not as the 2027 squad.

## Visible evidence and limitations

The page exposes supplied player names, contextual team/competition/season
fields, Step 4B sample evidence, Step 4C classification, confidence labels,
historical contexts, and provenance-oriented caveats.

It explicitly keeps unavailable:

- auction-pool, retention, release, and transfer status;
- 2027 availability, budget, overseas slots, and squad needs;
- validated recruitment roles and role-gap analysis;
- bowler conceded runs, economy, official wicket totals, and unsupported
  composite ratings;
- psychological pressure scores.

`chase_baseline` is shown as an inferred chase-context or match-state proxy,
not measured psychological pressure.

## Validation

Commands completed:

```powershell
python src\validate_step4d_recruitment_dashboard.py
python -m py_compile dashboard\app.py dashboard\data_service.py src\validate_step4d_recruitment_dashboard.py
```

Evidence validation passed with 20 squad rows, 10 batter rows, 10 bowler
rows, 16 external player-role rows, and zero unresolved rows. All validated
frames contain no blank values or duplicate rows at the declared grain.

Flask smoke tests returned HTTP 200 for:

- `/`
- `/analytics`
- `/players`
- `/ground`
- `/recruitment`

Fresh-browser checks on the new `/recruitment` page:

- Desktop page rendered with the shared ClutchLens navigation and evidence
  cards.
- Mobile viewport rendered with zero horizontal overflow.
- Classification filter returned 3 RR reference-season contexts.
- Batter/bowler filter returned 1 RR reference-season bowler context.
- External historical plus bowler filter returned 9 contexts.
- The page displayed IPL 2026, Yuzvendra Chahal, and the auction-availability
  warning.

Raw CSV files and Step 4B/4C source outputs were not modified. No external
data, image URLs, player biographies, or manually entered player facts were
used.
