# Step 2.3 Metric Feasibility

This is a feasibility and methodology-design audit. It does not create player ratings, rankings, or top-10 lists.

## Trusted batting-runs subsets

- Strict policy: **175062** deliveries and **886** batters.
- Moderate policy: **175806** deliveries and **886** batters.
- Excluded abandoned/incomplete/extra-innings rows: **15054**.
- Second-innings rows excluded for target/reconstruction uncertainty: **12232**.
- Ambiguous `other`/Penalty rows: **265**.
- Strict pressure-eligible batting rows under existing baseline flags: **23628**.

Strict policy uses only null `extras_type` rows in valid ordinary innings. Moderate policy additionally admits `Overstep` and `other` rows only when `extras_2_runs == 0`; this is an explicit sensitivity assumption, not a proven semantic correction. Wides, byes, legbyes, and Penalty rows are excluded because batter/team attribution is unresolved.

## Candidate batter metrics

- Runs per eligible delivery and strike rate are feasible only as conditional descriptive metrics on the strict subset; they must not be presented as complete scorecard strike rates.
- Boundary rate is conditionally feasible because `is_four`/`is_six` can be checked against `runs`; these flags are consistent on 99.99% of all rows.
- Dismissal analysis is partially feasible: `dismissed_player_id` is present for dismissal rows, but attribution requires filtering dismissal types and should not infer all `is_wicket` events as batter dismissals.
- Pressure-vs-baseline batting is **PARTIALLY READY** only for strict eligible rows and provisional match-state flags; it is not ready as a final rating because team totals and target semantics remain unresolved.

## Bowling feasibility

- Legal-ball counts are available using the validated exclusion of `wide` and `Overstep`; `other` remains a caveat.
- Dismissal events must remain separated. Candidate bowler-wicket types are limited to Bowled, Caught, LBW, Stump, and Hit Wicket; RunOut, Retire Out, and obstruction dismissals are not bowler wickets.
- Dot-event counts are only proposed on strict null-extra rows with `runs == 0`; this avoids claiming unresolved extras are batter dots.
- Economy, runs conceded, and any bowler ranking are unavailable because bowler-charged runs are not encoded reliably.

## Sample-size policies

The threshold output tests three policies: 10 pressure events/3 matches/30 baseline events, 20/5/60, and 30/8/90. These are reliability scenarios, not selected ranking cutoffs. The CSV reports counts only and contains no rank order.

## Readiness decisions

**Batter descriptive analysis: PARTIALLY READY.** Strict conditional delivery runs, boundaries, and carefully filtered dismissal events have substantial coverage, but they are not complete scorecard statistics.

**Batter pressure-vs-baseline analysis: PARTIALLY READY for exploratory coverage; BLOCKED for final ratings.** Pressure state is available provisionally, while team totals and revised-target semantics remain unresolved.

**Bowler descriptive analysis: PARTIALLY READY.** Legal deliveries, separated dismissal events, and conservative dot-event counts can be described. Economy and conceded runs are unavailable.

**Bowler pressure-vs-baseline analysis: BLOCKED for performance ratings.** Only event-coverage tables are defensible until bowler run attribution and pressure-state validity are resolved.

No robust Top 10 should be produced from this dataset at this stage. The strongest honest alternative is a coverage and methodology report, followed by player-level exploratory tables only after the user accepts these restrictions.

## Output references

- `outputs/batter_metric_coverage.csv` contains policy and pressure-definition coverage.
- `outputs/bowler_metric_coverage.csv` contains legal-ball, dot-event, and dismissal-event coverage without economy.
- `outputs/player_sample_thresholds.csv` contains threshold counts without rank order.
