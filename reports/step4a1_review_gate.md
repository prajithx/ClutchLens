# Step 4A.1 Player Methodology Review Gate

## Review scope

This is a read-only review of the Step 4A report and its four required CSV
outputs. No raw data, dashboard code, analysis script, or existing output was
changed by this review. No player names, ranking, Top 10 list, rating,
pressure score, recommendation, or auction value is produced.

## 1. Step 4A report: exact headline results

The full report states:

- 200,999 delivery rows, 883 match rows, and 6,413 mapping rows.
- `extras_2_runs` has 36 non-zero rows and remains semantically unresolved.
- Ball data contains 867 distinct matches, 888 strikers, and 647 bowlers.
- Mapping contains 1,217 distinct player IDs and 6,413 distinct
  competition/team/player contexts.
- Exact duplicate mapping rows: 0.
- Strict batter rows: 175,062 deliveries, 1,561 innings, 838 matches, and
  886 players.
- Moderate batter rows are not recorded in `player_metric_feasibility.csv`,
  but the threshold output uses a moderate baseline of 175,806 events.
- Candidate bowler dismissal counts are Caught 7,557, Bowled 1,775, LBW
  709, Stump 214, and Hit Wicket 17. RunOut and Retire Out are excluded.
- Bowler conceded runs/economy are explicitly BLOCKED.

## 2. CSV structure and integrity review

All four files were read directly.

### `outputs/player_metric_feasibility.csv`

- Row count: **10**
- Columns: `role`, `metric`, `formula`, `source_fields`, `confidence`,
  `eligible_deliveries_or_events`, `eligible_innings`, `eligible_matches`,
  `unique_players`, `limitation`
- Blank/null fields: **none**
- Duplicate rows: **0**
- Metrics:
  - Batter: runs, eligible balls faced, boundary flags, strike rate,
    dismissal/survival events, pressure vs baseline
  - Bowler: legal balls, conservative dot events, candidate bowler wickets,
    runs conceded/economy
- Exact key counts:
  - Batter runs, balls, boundaries, and strike rate: **175,062 deliveries,
    1,561 innings, 838 matches, 886 players**
  - Batter dismissal/survival events: **10,606 events, 1,708 innings, 865
    matches, 805 players**
  - Batter pressure vs baseline: **17,990 events, 515 innings, 515 matches,
    609 players**
  - Bowler legal balls: **178,297 events, 1,561 innings, 838 matches, 639
    players**
  - Bowler conservative dots: **63,052 events, 1,561 innings, 838 matches,
    626 players**
  - Candidate bowler wickets: **9,618 events, 1,553 innings, 838 matches,
    549 players**
  - Bowler runs conceded/economy: **0 events, 0 innings, 0 matches, 0
    players; BLOCKED**

### `outputs/player_sample_thresholds.csv`

- Row count: **18**
- Columns: `scenario`, `role`, `policy`, `pressure_definition`,
  `minimum_pressure_events`, `minimum_pressure_matches`,
  `minimum_baseline_events`, `qualifying_players`, `observed_players`,
  `pressure_events_total`, `baseline_events_total`, `caveat`
- Blank/null fields: **none**
- Duplicate full rows: **0**
- Roles/policies:
  - Batter / strict: 6 rows
  - Batter / moderate: 6 rows
  - Bowler / legal_ball: 6 rows
- Pressure definitions present: `chase_baseline`, `general_baseline`
- Threshold scenarios present:
  - 10 pressure events / 3 matches / 30 baseline events
  - 20 pressure events / 5 matches / 60 baseline events
  - 30 pressure events / 8 matches / 90 baseline events
- Exact qualifying counts and derived insufficient-evidence counts:

| Role | Policy | Definition | Minimums (pressure/matches/baseline) | Qualifying | Observed | Insufficient evidence |
|---|---|---|---:|---:|---:|---:|
| batter | strict | chase_baseline | 10 / 3 / 30 | 261 | 886 | 625 |
| batter | strict | chase_baseline | 20 / 5 / 60 | 151 | 886 | 735 |
| batter | strict | chase_baseline | 30 / 8 / 90 | 86 | 886 | 800 |
| batter | strict | general_baseline | 10 / 3 / 30 | 266 | 886 | 620 |
| batter | strict | general_baseline | 20 / 5 / 60 | 166 | 886 | 720 |
| batter | strict | general_baseline | 30 / 8 / 90 | 90 | 886 | 796 |
| batter | moderate | chase_baseline | 10 / 3 / 30 | 261 | 886 | 625 |
| batter | moderate | chase_baseline | 20 / 5 / 60 | 151 | 886 | 735 |
| batter | moderate | chase_baseline | 30 / 8 / 90 | 86 | 886 | 800 |
| batter | moderate | general_baseline | 10 / 3 / 30 | 266 | 886 | 620 |
| batter | moderate | general_baseline | 20 / 5 / 60 | 166 | 886 | 720 |
| batter | moderate | general_baseline | 30 / 8 / 90 | 90 | 886 | 796 |
| bowler | legal_ball | chase_baseline | 10 / 3 / 30 | 210 | 639 | 429 |
| bowler | legal_ball | chase_baseline | 20 / 5 / 60 | 141 | 639 | 498 |
| bowler | legal_ball | chase_baseline | 30 / 8 / 90 | 92 | 639 | 547 |
| bowler | legal_ball | general_baseline | 10 / 3 / 30 | 224 | 639 | 415 |
| bowler | legal_ball | general_baseline | 20 / 5 / 60 | 164 | 639 | 475 |
| bowler | legal_ball | general_baseline | 30 / 8 / 90 | 102 | 639 | 537 |

The `qualifying_players` values are computed from groupby event and match
counts in `src/audit_player_methodology.py`; they are not illustrative
constants. The output contains no player order.

### `outputs/player_join_quality.csv`

- Row count: **5**
- Columns: `join_name`, `source_rows`, `source_key`, `target_rows`,
  `target_key`, `matched_source_rows`, `unmatched_source_rows`,
  `target_duplicate_key_rows`, `row_multiplication_risk`, `notes`
- Blank/null fields: **none**
- Duplicate rows: **0**
- `ball_to_matches`: 200,999/200,999 source rows matched; 0 unmatched;
  0 duplicate target keys; risk LOW.
- `matches_to_competitions`: 883/883 matched; 0 unmatched; 0 duplicate
  target keys; risk LOW.
- `striker_ids_to_mapping`: 200,999/200,999 matched; 0 unmatched; 5,196
  duplicate target `player_id` rows; risk HIGH.
- `bowler_ids_to_mapping`: 200,999/200,999 matched; 0 unmatched; 5,196
  duplicate target `player_id` rows; risk HIGH.
- `mapping_exact_duplicate_rows`: 6,413 rows checked; 0 exact duplicates.

### `outputs/pressure_context_coverage.csv`

- Row count: **6**
- Columns: `pressure_definition`, `formula`, `eligible_deliveries`,
  `eligible_innings`, `eligible_matches`, `unique_batters`,
  `unique_bowlers`, `excluded_target_or_incomplete_rows`, `caveat`
- Blank/null fields: **none**
- Duplicate rows: **0**

## 3. Pressure-context review

All counts below are observed coverage, not validated psychological pressure.
The exclusion count is the number of delivery rows outside that definition.

| Definition | Deliveries | Innings | Matches | Batters | Bowlers | Excluded rows |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 185,945 | 1,561 | 838 | 887 | 639 | 15,054 |
| chase_baseline | 19,447 | 516 | 516 | 611 | 384 | 181,552 |
| general_baseline | 19,155 | 676 | 676 | 627 | 433 | 181,844 |
| chase_strict | 10,564 | 452 | 452 | 537 | 328 | 190,435 |
| general_strict | 12,166 | 626 | 626 | 573 | 377 | 188,833 |
| chase_loose | 29,571 | 582 | 582 | 670 | 431 | 171,428 |

Definitions and formulas:

- `baseline`: ordinary valid innings excluding abandoned/no-result.
- `chase_baseline`: valid chase, target not reached, at most 48 balls
  remaining, and RRR at least 10 or `(RRR - CRR) >= 3` with at most six
  wickets in hand.
- `general_baseline`: valid innings, target not reached, at most 36 balls
  remaining, and at most six wickets in hand or at most 36 runs required in a
  chase.
- `chase_strict`: chase context using at most 30 balls and RRR at least 12
  or `(RRR - CRR) >= 4`.
- `general_strict`: general context using at most 24 balls and the stricter
  chase run requirement of 24.
- `chase_loose`: chase context using at most 60 balls and RRR at least 8 or
  `(RRR - CRR) >= 2`.

The most defensible exploratory comparison is **chase_baseline**, because it
uses a recognizable chase situation and combines target proximity, remaining
balls, required run rate, and wickets in hand. It is still only an inferred
match-state context: unresolved extras and reconstructed totals mean it must
not be called a validated psychological pressure measure.

## 4. Threshold review

The thresholds are genuinely computed: the script groups rows by `striker_id`
or `bowler_id`, counts pressure events and pressure matches, joins those
counts to baseline events, and applies the three minimum policies. The
`observed_players - qualifying_players` values above are the players excluded
for failing at least one minimum. The CSV does not identify which minimum
failed, and it does not contain player names; that detail is therefore not
available in current outputs.

The threshold output does **not** include a baseline pressure-definition row,
the `chase_strict`, `general_strict`, or `chase_loose` variants, or a separate
dismissal-event threshold scenario. Those are gaps, not evidence that the
missing scenarios have zero qualifiers.

## 5. Join safety review

`player_id` matches all delivery IDs to at least one mapping row, but it is
not a safe global identity key: the mapping contains 6,413 contextual rows
for 1,217 player IDs and 5,196 duplicate `player_id` rows. The actual
context columns available for a future identity key are `comp_id`, `team_id`,
and `player_id`; a future step should derive and test the composite
`(comp_id, team_id, player_id)` context rather than inventing a global
identity.

The current Step 4A metric calculations avoid mapping joins for event counts,
so they do not multiply delivery rows. The join-quality output explicitly
marks striker and bowler joins on `player_id` alone as HIGH risk. No
unresolved delivery-to-context mismatch was found: all 200,999 ball rows
matched a match and all 883 match rows matched a competition.

## 6. Step 4A decision gate

| Decision | Gate result | Evidence |
|---|---|---|
| Descriptive batter analysis | READY WITH CAVEATS | `player_metric_feasibility.csv`: strict runs/balls/boundaries each 175,062 events across 886 players; formulas explicitly say conditional, not complete scorecard metrics. |
| Exploratory batter pressure comparison | READY FOR EXPLORATORY COVERAGE ONLY | Pressure coverage: `chase_baseline` 19,447 deliveries / 516 innings / 516 matches / 611 batters; metric row reports 17,990 strict pressure events / 609 players; report labels it EXPLORATORY. |
| Descriptive bowler analysis | READY WITH CAVEATS | Legal balls 178,297 events / 639 players; conservative dots 63,052; candidate wickets 9,618; dismissal types are filtered. |
| Exploratory bowler pressure comparison | READY FOR EVENT COVERAGE ONLY; PERFORMANCE COMPARISON NOT READY | Pressure coverage reports bowler event counts, but conceded runs/economy are BLOCKED and reconstructed pressure remains provisional. |
| Bowler economy | BLOCKED | `player_metric_feasibility.csv`: 0 eligible events/players and confidence BLOCKED; limitation says no verified bowler-charge field. |
| Final batter rankings | BLOCKED | Report explicitly blocks final pressure ratings/rankings and says no Top 10 should be produced. |
| Final bowler rankings | BLOCKED | Same report register blocks rankings, and bowler economy/conceded runs are unavailable. |

## 7. Gaps before Step 4B

1. Decide whether Step 4B will use only `chase_baseline` or require all
   sensitivity variants to be thresholded. Current thresholds cover only
   `chase_baseline` and `general_baseline`.
2. Add threshold coverage for dismissal events if dismissal-based selection is
   intended. It is not available in current outputs.
3. Derive and test a future contextual identity key from the actual columns
   `(comp_id, team_id, player_id)` before any mapping-based player table.
4. Reconcile the different observed-player denominators in the outputs:
   baseline pressure coverage has 887 batters, while strict metric and
   threshold baselines observe 886. The difference is not explained in the
   current outputs and should be traced before selection.
5. Preserve the explicit caveat that `runs` and target context are inferred
   or medium-confidence, not verified scorecard semantics.

## Review conclusion

The review gate passes for descriptive feasibility and reproducible threshold
counting, but does **not** authorize Step 4B ranking or Top 10 work. Step 4B
requires explicit approval of the context policy and resolution of the
identity/threshold gaps above.
