# Step 2.1 Validation Report

This report independently audits Step 2 outputs. It does not create player ratings or rankings.

## Innings completeness

- Ball-by-ball match IDs: **867**.
- Full match/innings groups in the processed context: **1724**.
- Ordinary innings groups (innings 1/2): **1712**.
- Expected groups from two innings per match: **1734**.
- Matches with fewer than two ordinary innings: **22**; more than two ordinary innings: **0**.
- The 22 exceptions are all abandoned/no-result matches with one recorded ordinary innings. They explain 22 missing ordinary innings; six matches also contain innings 3/4 (12 extra groups), so the total 1,724 groups is 1,734 expected ordinary groups minus 22 plus 12 extra groups.
- This count difference is therefore supported by source match status and extra innings, not a grouping bug.

See `outputs/innings_completeness_exceptions.csv` for every exception.

## Extras, score, and bowler-run findings

- `extras1_runs` is a category code with high confidence, based on its exact one-to-one mapping to `extras_type`.
- `runs` is consistent with batter runs but is not explicitly labeled; confidence is medium.
- `extras_2_runs` is sparse and not defined by the supplied files; confidence in its exact semantics is low/medium.
- Candidate total formulas are compared in `outputs/score_reconstruction_comparison.csv`. Result-margin agreement favors the current hypothesis over simpler alternatives, but it does not prove the formula because result strings, DLS outcomes, and source omissions can affect the comparison.
- Bowler-conceded runs cannot be established reliably. No bowler economy calculation should be performed.

## Legal-ball and over-limit audit

- `innings_ball_num` increments by one on 199275 observed non-first rows; it increments on 8186 of 8290 wide/Overstep rows, so it is an event sequence, not a legal-ball count.
- The recommended legal-ball rule is to exclude `wide` and `Overstep` from legal-ball counts. `other` remains legal in the current provisional reconstruction because its legal status is unresolved and it is rare; its rows are flagged.
- Revised-over values above 20 are observed as multiples of six and normalize consistently to 7, 8, 15, and 19 overs in sample matches. The conversion is supported by delivery counts and over IDs.

## Chase target audit

- Second innings targets sourced from revised_target: **23** matches.
- Second innings targets sourced from first-innings total plus one: **822** matches.
- Pressure flags after target reached: chase candidate **0**; general candidate **0** after the eligibility fix.
- Pressure flags in abandoned/no-result rows: **0** after the eligibility fix.
- Ordinary short non-all-out innings found independently: **417** groups. These are excluded from pressure eligibility unless they are demonstrably target-reached, all-out, or overs-complete.
- Of those, **125** groups were not target-reached and had **13263** deliveries; pressure flags in them were chase **0** and general **0**.

A hand-checkable chase example can be reproduced by reading the first rows for match 13511 or 13522 in `delivery_context.csv`: score_before is the cumulative prior event total; legal_balls_before excludes wide/Overstep; runs_required_before equals target minus score_before; and required_run_rate is runs required divided by balls remaining times six.

## Decision

**Step 3 player analysis is blocked.** Match-state fields and provisional pressure flags are useful for review, but total team runs and bowler-conceded runs are not conclusively defined by the supplied data. Player pressure ratings should not be calculated until the extras semantics and score reconstruction are accepted or corrected.
