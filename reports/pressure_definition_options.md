# Provisional Pressure Definition Options

This report documents match-state reconstruction and candidate pressure flags only. It does not rank players or calculate player performance indices.

## Match and innings structure

- Delivery rows: **200999**.
- Reconstructed match/innings groups: **1724**.
- Ordinary innings 1/2 rows: **200961**.
- Super-over/extra-innings rows (innings 3/4): **38**, across **6** matches.
- Abandoned/no-result match rows: **24** matches.
- Revised-target matches: **23**.
- Extra-innings/super-over groups excluded from ordinary pressure context: **12**.

## Reconstructed fields

Each delivery includes score and wicket state before and after the event, legal balls, balls remaining, innings target, runs required, current run rate, required run rate, wickets in hand, and a target-reached marker where chase context is valid.

### Explicit data assumptions and limitations

- extras1_runs is categorical: observed values map one-to-one to extra labels, so it was not added to score.
- team_runs_event = runs + extras_2_runs + one base run for every non-null extras_type. This is a transparent reconstruction assumption.
- wide and Overstep are treated as non-legal deliveries. 'other' is treated as legal because its legal-ball meaning is not independently documented; rows are flagged for review.
- All T20 and T20I competitions were assigned a default 20-over limit. Revised-overs values above 20 were observed as multiples of six (for example 42, 48, 90, 114) and normalized to legal-ball limits divided by six.
- Chase pressure excludes innings 3/4, abandoned/no-result matches, and rows without a valid first-innings total.

The source does not expose a direct total-extras or batter-runs field. Therefore the score reconstruction is a documented hypothesis and `review_assumptions` is set on innings containing ambiguous `other` or `Penalty` extras. These outputs must be reviewed before player-level calculations.

## Target and result cross-check

- Among valid revised-target chase contexts, reconstructed second innings reached the target: **10**.
- Among valid revised-target chase contexts, reconstructed second innings did not reach the target: **10**. These include matches ending short, no-result matches, and cases needing scorecard interpretation.
- Revised-target matches excluded from this cross-check because the chase was not valid: **3**.
- Result text is retained for review rather than parsed into a definitive winner/loser model; DLS and abandoned outcomes make automatic result validation ambiguous.

## Candidate definitions

### A. Chase-pressure candidate

Second innings only, with a valid first-innings total or revised target, excluding abandoned/no-result matches and target-already-reached rows. Baseline pressure requires at most 48 legal balls remaining and either required run rate at least 10, or required-minus-current run rate at least 3 while six or fewer wickets remain. This combines chase demand, time, and wicket resources rather than labeling every late ball as pressure.

### B. General high-leverage candidate

Ordinary innings only, excluding abandoned/no-result matches, with at most 36 legal balls remaining and either six or fewer wickets in hand or a chase with at most 36 runs required. This is deliberately broader and does not equate first-innings late overs with chase pressure.

## Sensitivity comparison

The CSV output compares baseline, stricter, and looser variants. Stricter variants reduce coverage by shortening the remaining-ball window and increasing run-rate requirements; looser variants increase coverage but risk labeling routine states as pressure. Counts are descriptive, not evidence that any threshold is correct.

| Definition | Eligible deliveries | Flagged deliveries | Matches | Innings | Batters | Bowlers |
|---|---:|---:|---:|---:|---:|---:|
| chase_baseline | 83002 | 19447 | 516 | 516 | 611 | 384 |
| chase_stricter | 83002 | 10564 | 452 | 452 | 537 | 328 |
| chase_looser | 83002 | 29571 | 582 | 582 | 670 | 431 |
| general_baseline | 185945 | 19155 | 676 | 676 | 627 | 433 |
| general_stricter | 185945 | 12166 | 626 | 626 | 573 | 377 |
| general_looser | 185945 | 25518 | 698 | 698 | 651 | 464 |

## Validation questions before Step 3

- Confirm whether `other` extras represent a no-ball/non-legal delivery or another event type.
- Confirm the intended meaning of the sparse `extras_2_runs` field and whether the one-run base assumption is appropriate for every labeled extra.
- Compare `innings_summary.csv` totals with an authoritative scorecard interpretation before treating reconstructed scores as final.
- These provisional flags should be reviewed before any player pressure-performance calculation.
