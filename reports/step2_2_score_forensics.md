# Step 2.2 Score / Extras Forensic Audit

This validation uses only the supplied raw and generated files. It does not create player ratings or rankings.

## Confirmed interpretations

- `extras1_runs` is a category code, high confidence: its values map exactly to the observed extras labels and must not be added as runs.
- `runs` behaves like batter runs with medium confidence: ordinary deliveries contain cricket-like 0/1/2/3/4/5/6 values, while wides and byes are zero. The schema does not explicitly name it.
- `extras_2_runs` is unresolved, low/medium confidence: it is zero on 200,963 rows and non-zero on only 37 rows. Its values occur in Overstep, `other`, and one null-extra row, but no supplied total-extras definition identifies whether it is an amount or derived field.
- Team totals are not proven by this pack. The current hypothesis remains a transparent provisional reconstruction, not an accepted scorecard total.
- Bowler-conceded runs/economy are unavailable from the supplied schema. Wides, byes, legbyes, penalty, and unresolved Overstep/`other` treatment prevent a reliable charged-runs calculation.

## Representative raw rows by extras type

| extras_type | match_id | innings | overid | over_ball_num | innings_ball_num | striker | bowler | runs | extras1_runs | extras_2_runs | is_wicket | dismissal_type |
|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---|---|
| <NULL> | 13511 | 1 | 1 | 1 | 1 | Jason Roy | Sheldon Cottrell | 0 | 6 | 0 | False | nan |
| Overstep | 13513 | 1 | 4 | 2 | 20 | Nicholas Pooran | George Garton | 0 | 1 | 0 | False | nan |
| Penalty | 16753 | 2 | 6 | 4 | 34 | Harry Tector | Fareed Malik | 0 | 7 | 0 | False | nan |
| byes | 13512 | 2 | 11 | 2 | 63 | Romario Shepherd | Adil Rashid | 0 | 4 | 0 | False | nan |
| legbyes | 13511 | 2 | 4 | 5 | 23 | Brandon King | Adil Rashid | 0 | 3 | 0 | False | nan |
| other | 13513 | 1 | 10 | 1 | 57 | Rovman Powell | Tymal Mills | 0 | 5 | 0 | False | nan |
| wide | 13511 | 1 | 7 | 4 | 40 | Eoin Morgan | Akeal Hosein | 0 | 2 | 0 | False | nan |

## All non-zero `extras_2_runs` evidence

There are **36** non-zero rows in the supplied CSV. The prompt referred to 37, but the observed data contains 36; the complete table is in `outputs/extras_2_runs_nonzero_rows.csv`.

| extras_type | match_id | innings | overid | over_ball_num | innings_ball_num | striker | bowler | runs | extras1_runs | extras_2_runs | is_wicket | dismissal_type |
|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---|---|
| Overstep | 13523 | 1 | 1 | 4 | 4 | Ishan Kishan | Akeal Hosein | 0 | 1 | 4 | False | nan |
| other | 13614 | 1 | 18 | 5 | 111 | Dasun Shanaka | Mitchell Starc | 0 | 5 | 4 | False | nan |
| Overstep | 14112 | 1 | 11 | 5 | 66 | David Warner | Varun Chakravarthy | 0 | 1 | 4 | False | nan |
| other | 14127 | 2 | 9 | 3 | 52 | Prithvi Shaw | Obed McCoy | 0 | 5 | 4 | False | nan |
| other | 14159 | 2 | 9 | 1 | 51 | Ishan Kishan | Umran Malik | 0 | 5 | 1 | False | nan |
| Overstep | 15796 | 2 | 14 | 4 | 88 | Lorcan Tucker | Umran Malik | 0 | 1 | 1 | False | nan |
| Overstep | 16424 | 2 | 6 | 1 | 33 | Anamul Haque | Tanaka Chivanga | 0 | 1 | 4 | False | nan |
| nan | 17555 | 1 | 5 | 4 | 29 | Dawid Malan | Haris Rauf | 0 | 6 | 1 | False | nan |
| Overstep | 20186 | 2 | 20 | 2 | 130 | Krishnappa Gowtham | Tushar Deshpande | 0 | 1 | 1 | False | nan |
| other | 20188 | 1 | 19 | 4 | 117 | M Shahrukh Khan | KM Asif | 0 | 5 | 1 | False | nan |
| Overstep | 20199 | 2 | 10 | 4 | 59 | Nitish Rana | Marco Jansen | 0 | 1 | 1 | False | nan |
| Overstep | 20201 | 1 | 11 | 5 | 66 | Krunal Pandya | Sikandar Raza | 0 | 1 | 4 | False | nan |
| Overstep | 20218 | 1 | 16 | 5 | 101 | Marcus Stoinis | Kagiso Rabada | 0 | 1 | 1 | False | nan |
| other | 20234 | 2 | 13 | 3 | 80 | Nehal Wadhera | Harshal Patel | 0 | 5 | 4 | False | nan |
| other | 20243 | 2 | 19 | 4 | 121 | Tim David | Naveen ul Haq | 0 | 5 | 4 | False | nan |
| other | 21583 | 1 | 20 | 4 | 119 | Moeen Ali | Mohammed Shami | 0 | 5 | 1 | False | nan |
| Overstep | 30068 | 1 | 6 | 2 | 32 | David Warner | Mustafizur Rahman | 0 | 1 | 1 | False | nan |
| Overstep | 30071 | 2 | 15 | 3 | 91 | Tristan Stubbs | Varun Chakravarthy | 0 | 1 | 4 | False | nan |
| Overstep | 30076 | 2 | 5 | 5 | 30 | Sai Sudharsan | Manimaran Siddharth | 0 | 1 | 1 | False | nan |
| Overstep | 30341 | 1 | 20 | 3 | 123 | Sadeera Samarawickrama | Mustafizur Rahman | 0 | 1 | 4 | False | nan |
| Overstep | 31254 | 1 | 17 | 3 | 101 | Andre Russell | Yash Dayal | 0 | 1 | 4 | False | nan |
| Overstep | 31265 | 2 | 1 | 3 | 3 | Sunil Narine | Lizaad Williams | 0 | 1 | 1 | False | nan |
| Overstep | 31278 | 2 | 3 | 2 | 14 | Rohit Sharma | Vaibhav Arora | 0 | 1 | 4 | False | nan |
| other | 36200 | 2 | 18 | 1 | 110 | William Jacks | Alzarri Joseph | 0 | 5 | 4 | False | nan |
| other | 37093 | 2 | 19 | 3 | 111 | Yasim Murtaza | Abdul Rahmani | 0 | 5 | 1 | False | nan |
| other | 37278 | 1 | 12 | 1 | 69 | Suryakumar Yadav | Taskin Ahmed | 0 | 5 | 4 | False | nan |
| Overstep | 37894 | 1 | 17 | 5 | 106 | Zakary Foulkes | Matheesha Pathirana | 0 | 1 | 4 | False | nan |
| Overstep | 38844 | 1 | 19 | 1 | 111 | Jaker Ali Anik | Romario Shepherd | 0 | 1 | 1 | False | nan |
| Overstep | 39811 | 1 | 6 | 1 | 34 | Finn Allen | Abbas Afridi | 0 | 1 | 1 | False | nan |
| other | 40038 | 1 | 19 | 3 | 114 | Mark Wood | Mohammed Shami | 0 | 5 | 1 | False | nan |
| other | 40695 | 1 | 18 | 1 | 115 | Ishan Kishan | Jofra Archer | 0 | 5 | 4 | False | nan |
| Overstep | 40756 | 1 | 4 | 5 | 23 | Ravichandran Ashwin | Yudhvir Singh | 0 | 1 | 1 | False | nan |
| Overstep | 43057 | 2 | 14 | 6 | 85 | Karun Nair | Marco Jansen | 0 | 1 | 1 | False | nan |
| Overstep | 46740 | 2 | 1 | 3 | 3 | Sahibzada Farhan | Nandre Burger | 0 | 1 | 1 | False | nan |
| other | 48467 | 1 | 20 | 6 | 126 | Curtis Campher | Muhammad Jawadullah | 0 | 5 | 1 | False | nan |
| other | 55078 | 1 | 20 | 4 | 124 | Eshan Malinga | Razaullah Razaullah | 0 | 5 | 1 | False | nan |

The rows cluster into 21 Overstep rows, 14 `other` rows, and one null-extra row. By value, 20 rows contain 1 and 16 contain 4. This establishes where the field appears, but does not establish its semantic unit.

## Score discrepancy cases

The current result-margin cross-check has **266** mismatching matches under safe case-insensitive parsing. The earlier 164 count was produced by the prior comparison's case-sensitive numeric extraction and is not reproducible as the safe parsed population; this audit reports each safe-parsed case explicitly.
Cause classifications are: {'unresolved_source_or_schema_difference': 194, 'ambiguous_extra_type_present': 72}. These are evidence-based categories, not claims that a single formula can be selected.

| Season | Format | Mismatch matches |
|---|---|---:|
| 2022 | T20 | 24 |
| 2022 | T20I | 33 |
| 2022/23 | T20I | 4 |
| 2023 | T20 | 31 |
| 2023 | T20I | 15 |
| 2024 | T20 | 27 |
| 2024 | T20I | 39 |
| 2025 | T20 | 27 |
| 2025 | T20I | 36 |
| 2026 | T20 | 12 |
| 2026 | T20I | 18 |

The complete case table is in `outputs/score_discrepancy_cases.csv`. Cases with ambiguous extras or revised targets are not silently repaired; cases with no extras demonstrate that result-margin agreement cannot by itself prove an extras formula.

## Result-string cross-check

- Parsed run-margin results: **391**; exact reconstructed-margin matches: **125**; mismatches: **266**.
- All parsed run-margin result strings before eligibility exclusions: **402**.
- Parsed wicket-margin results: **409**. These were checked only for chase target reach, not exact final totals.
- Abandoned/no-result results: **40**; tie/draw/unparsed results: **32**.
- Run-margin parsing is safe only for result strings with an explicit `Won by N runs` phrase. DLS, revised-target, no-result, and super-over cases are not treated as ordinary margin checks.
- Wicket-margin results do not reveal the exact final score, so they cannot identify a precise delivery-total formula.

## Bowler-conceded runs feasibility

- No supplied column explicitly identifies bowler-charged runs.
- `is_wicket` includes dismissal types such as RunOut, so it cannot be called a bowler-wicket field without dismissal filtering.
- Observed dismissal types include: Bowled, Caught, Hit Wicket, LBW, Obstracting the field, Obstructing the field, Retire Out, RunOut, Stump.
- Defensible future bowling context metrics may include legal-ball counts, total wicket events separated by dismissal type, and dot-event counts only after team/batter-run semantics are accepted. Bowler economy should remain unavailable.

## Decision gate

**Batter analysis: PARTIALLY READY for descriptive match-state analysis, BLOCKED for final pressure ratings.** Chase targets and provisional state fields can be inspected, but team totals remain unproven.

**Bowler analysis: BLOCKED for economy or conceded-run ratings.** Legal-ball and dismissal-event context is available, but bowler-conceded runs cannot be reliably computed.

## Unresolved questions

- What is the documented definition of `extras_2_runs`?
- Does `other` represent a legal delivery, a no-ball/Overstep variant, or another event type?
- Does `runs` contain batter runs only in every labeled-extra case?
- Is there an omitted scorecard/team-total field outside the supplied CSV pack?

The evidence does not justify silently changing the formula or beginning Step 3 player ratings.
