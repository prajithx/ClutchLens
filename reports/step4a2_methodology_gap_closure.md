# Step 4A.2 Methodology Gap Closure

This correction step closes the specific review-gate gaps without selecting
players or producing rankings, ratings, pressure scores, recommendations, or
Top 10 lists.

## 887 vs 886 batter reconciliation

The baseline valid-context set contains 887 striker IDs; the strict batter
set contains 886. The exception output has 1 row:

```text
 player_id source_player_name  comp_id  team_id  mapping_rows_for_context  valid_baseline_events  strict_eligible_events extras_types                                                                                           reason
       286    Kane Richardson     1611       20                         1                      1                       0      legbyes Baseline identity has valid context events, but all events are excluded by strict extras policy.
```

The difference is not a missing mapping or join multiplication. Player 286
has one valid ordinary event in competition 1611/team 20, but its
`extras_type` is `legbyes`, so it fails the strict null-extra policy. The
mapping contains one matching `(comp_id, team_id, player_id)` context.

## Extended threshold testing

`player_sample_thresholds_extended.csv` contains 54 data-derived
rows: 3 roles/policies x 6 pressure definitions x 3 threshold scenarios.
The pressure threshold applies to pressure events; `minimum_baseline_events`
is a separate baseline minimum. Counts are grouped by player ID within the
delivery context and do not join the mapping table.

```text
  role     policy pressure_definition  minimum_pressure_events  minimum_pressure_matches  minimum_baseline_events                                  threshold_event_scope  qualifying_players  observed_players  insufficient_evidence_players  pressure_events_total  baseline_events_total                                                   caveat
batter     strict            baseline                       10                         3                       30 pressure events; baseline_events is a separate minimum                 525               886                            361                 175062                 175062 Contextual counts only; no player ordering or selection.
batter     strict            baseline                       20                         5                       60 pressure events; baseline_events is a separate minimum                 388               886                            498                 175062                 175062 Contextual counts only; no player ordering or selection.
batter     strict            baseline                       30                         8                       90 pressure events; baseline_events is a separate minimum                 304               886                            582                 175062                 175062 Contextual counts only; no player ordering or selection.
batter     strict      chase_baseline                       10                         3                       30 pressure events; baseline_events is a separate minimum                 261               886                            625                  17990                 175062 Contextual counts only; no player ordering or selection.
batter     strict      chase_baseline                       20                         5                       60 pressure events; baseline_events is a separate minimum                 151               886                            735                  17990                 175062 Contextual counts only; no player ordering or selection.
batter     strict      chase_baseline                       30                         8                       90 pressure events; baseline_events is a separate minimum                  86               886                            800                  17990                 175062 Contextual counts only; no player ordering or selection.
batter     strict    general_baseline                       10                         3                       30 pressure events; baseline_events is a separate minimum                 266               886                            620                  17725                 175062 Contextual counts only; no player ordering or selection.
batter     strict    general_baseline                       20                         5                       60 pressure events; baseline_events is a separate minimum                 166               886                            720                  17725                 175062 Contextual counts only; no player ordering or selection.
batter     strict    general_baseline                       30                         8                       90 pressure events; baseline_events is a separate minimum                  90               886                            796                  17725                 175062 Contextual counts only; no player ordering or selection.
batter     strict        chase_strict                       10                         3                       30 pressure events; baseline_events is a separate minimum                 180               886                            706                   9661                 175062 Contextual counts only; no player ordering or selection.
batter     strict        chase_strict                       20                         5                       60 pressure events; baseline_events is a separate minimum                  92               886                            794                   9661                 175062 Contextual counts only; no player ordering or selection.
batter     strict        chase_strict                       30                         8                       90 pressure events; baseline_events is a separate minimum                  48               886                            838                   9661                 175062 Contextual counts only; no player ordering or selection.
batter     strict      general_strict                       10                         3                       30 pressure events; baseline_events is a separate minimum                 216               886                            670                  11151                 175062 Contextual counts only; no player ordering or selection.
batter     strict      general_strict                       20                         5                       60 pressure events; baseline_events is a separate minimum                 122               886                            764                  11151                 175062 Contextual counts only; no player ordering or selection.
batter     strict      general_strict                       30                         8                       90 pressure events; baseline_events is a separate minimum                  62               886                            824                  11151                 175062 Contextual counts only; no player ordering or selection.
batter     strict         chase_loose                       10                         3                       30 pressure events; baseline_events is a separate minimum                 306               886                            580                  27548                 175062 Contextual counts only; no player ordering or selection.
batter     strict         chase_loose                       20                         5                       60 pressure events; baseline_events is a separate minimum                 209               886                            677                  27548                 175062 Contextual counts only; no player ordering or selection.
batter     strict         chase_loose                       30                         8                       90 pressure events; baseline_events is a separate minimum                 124               886                            762                  27548                 175062 Contextual counts only; no player ordering or selection.
batter   moderate            baseline                       10                         3                       30 pressure events; baseline_events is a separate minimum                 526               886                            360                 175806                 175806 Contextual counts only; no player ordering or selection.
batter   moderate            baseline                       20                         5                       60 pressure events; baseline_events is a separate minimum                 388               886                            498                 175806                 175806 Contextual counts only; no player ordering or selection.
batter   moderate            baseline                       30                         8                       90 pressure events; baseline_events is a separate minimum                 304               886                            582                 175806                 175806 Contextual counts only; no player ordering or selection.
batter   moderate      chase_baseline                       10                         3                       30 pressure events; baseline_events is a separate minimum                 261               886                            625                  18098                 175806 Contextual counts only; no player ordering or selection.
batter   moderate      chase_baseline                       20                         5                       60 pressure events; baseline_events is a separate minimum                 151               886                            735                  18098                 175806 Contextual counts only; no player ordering or selection.
batter   moderate      chase_baseline                       30                         8                       90 pressure events; baseline_events is a separate minimum                  86               886                            800                  18098                 175806 Contextual counts only; no player ordering or selection.
batter   moderate    general_baseline                       10                         3                       30 pressure events; baseline_events is a separate minimum                 266               886                            620                  17834                 175806 Contextual counts only; no player ordering or selection.
batter   moderate    general_baseline                       20                         5                       60 pressure events; baseline_events is a separate minimum                 166               886                            720                  17834                 175806 Contextual counts only; no player ordering or selection.
batter   moderate    general_baseline                       30                         8                       90 pressure events; baseline_events is a separate minimum                  90               886                            796                  17834                 175806 Contextual counts only; no player ordering or selection.
batter   moderate        chase_strict                       10                         3                       30 pressure events; baseline_events is a separate minimum                 180               886                            706                   9731                 175806 Contextual counts only; no player ordering or selection.
batter   moderate        chase_strict                       20                         5                       60 pressure events; baseline_events is a separate minimum                  92               886                            794                   9731                 175806 Contextual counts only; no player ordering or selection.
batter   moderate        chase_strict                       30                         8                       90 pressure events; baseline_events is a separate minimum                  48               886                            838                   9731                 175806 Contextual counts only; no player ordering or selection.
batter   moderate      general_strict                       10                         3                       30 pressure events; baseline_events is a separate minimum                 216               886                            670                  11239                 175806 Contextual counts only; no player ordering or selection.
batter   moderate      general_strict                       20                         5                       60 pressure events; baseline_events is a separate minimum                 122               886                            764                  11239                 175806 Contextual counts only; no player ordering or selection.
batter   moderate      general_strict                       30                         8                       90 pressure events; baseline_events is a separate minimum                  62               886                            824                  11239                 175806 Contextual counts only; no player ordering or selection.
batter   moderate         chase_loose                       10                         3                       30 pressure events; baseline_events is a separate minimum                 306               886                            580                  27698                 175806 Contextual counts only; no player ordering or selection.
batter   moderate         chase_loose                       20                         5                       60 pressure events; baseline_events is a separate minimum                 209               886                            677                  27698                 175806 Contextual counts only; no player ordering or selection.
batter   moderate         chase_loose                       30                         8                       90 pressure events; baseline_events is a separate minimum                 124               886                            762                  27698                 175806 Contextual counts only; no player ordering or selection.
bowler legal_ball            baseline                       10                         3                       30 pressure events; baseline_events is a separate minimum                 460               639                            179                 178297                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball            baseline                       20                         5                       60 pressure events; baseline_events is a separate minimum                 351               639                            288                 178297                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball            baseline                       30                         8                       90 pressure events; baseline_events is a separate minimum                 281               639                            358                 178297                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball      chase_baseline                       10                         3                       30 pressure events; baseline_events is a separate minimum                 210               639                            429                  18390                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball      chase_baseline                       20                         5                       60 pressure events; baseline_events is a separate minimum                 141               639                            498                  18390                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball      chase_baseline                       30                         8                       90 pressure events; baseline_events is a separate minimum                  92               639                            547                  18390                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball    general_baseline                       10                         3                       30 pressure events; baseline_events is a separate minimum                 224               639                            415                  18110                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball    general_baseline                       20                         5                       60 pressure events; baseline_events is a separate minimum                 164               639                            475                  18110                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball    general_baseline                       30                         8                       90 pressure events; baseline_events is a separate minimum                 102               639                            537                  18110                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball        chase_strict                       10                         3                       30 pressure events; baseline_events is a separate minimum                 151               639                            488                   9918                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball        chase_strict                       20                         5                       60 pressure events; baseline_events is a separate minimum                  98               639                            541                   9918                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball        chase_strict                       30                         8                       90 pressure events; baseline_events is a separate minimum                  64               639                            575                   9918                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball      general_strict                       10                         3                       30 pressure events; baseline_events is a separate minimum                 181               639                            458                  11433                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball      general_strict                       20                         5                       60 pressure events; baseline_events is a separate minimum                 121               639                            518                  11433                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball      general_strict                       30                         8                       90 pressure events; baseline_events is a separate minimum                  78               639                            561                  11433                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball         chase_loose                       10                         3                       30 pressure events; baseline_events is a separate minimum                 238               639                            401                  28092                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball         chase_loose                       20                         5                       60 pressure events; baseline_events is a separate minimum                 174               639                            465                  28092                 178297 Contextual counts only; no player ordering or selection.
bowler legal_ball         chase_loose                       30                         8                       90 pressure events; baseline_events is a separate minimum                 122               639                            517                  28092                 178297 Contextual counts only; no player ordering or selection.
```

## Bowler dismissal-event reliability

`bowler_dismissal_thresholds.csv` contains 24 rows across five
scopes (Caught, Bowled, LBW, Stump, Hit Wicket, and the combined scope is
included in the row count) and four minimum event/match scenarios. Candidate
types exclude RunOut, Retire Out, and obstruction-related dismissals. These
are candidate bowler-attributed events, not verified official wicket totals.

```text
    dismissal_type_scope  minimum_dismissal_events  minimum_matches  candidate_events_total  candidate_bowlers_observed  qualifying_bowlers  insufficient_evidence_bowlers                                     excluded_types                                                                       caveat
                  Caught                         1                1                    7090                         532                 532                              0 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                  Caught                         2                2                    7090                         532                 419                            113 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                  Caught                         3                3                    7090                         532                 336                            196 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                  Caught                         5                3                    7090                         532                 291                            241 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                  Bowled                         1                1                    1674                         352                 352                              0 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                  Bowled                         2                2                    1674                         352                 222                            130 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                  Bowled                         3                3                    1674                         352                 164                            188 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                  Bowled                         5                3                    1674                         352                 121                            231 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                     LBW                         1                1                     668                         246                 246                              0 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                     LBW                         2                2                     668                         246                 126                            120 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                     LBW                         3                3                     668                         246                  81                            165 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                     LBW                         5                3                     668                         246                  31                            215 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                   Stump                         1                1                     169                          75                  75                              0 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                   Stump                         2                2                     169                          75                  30                             45 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                   Stump                         3                3                     169                          75                  17                             58 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
                   Stump                         5                3                     169                          75                  11                             64 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
              Hit Wicket                         1                1                      17                          17                  17                              0 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
              Hit Wicket                         2                2                      17                          17                   0                             17 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
              Hit Wicket                         3                3                      17                          17                   0                             17 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
              Hit Wicket                         5                3                      17                          17                   0                             17 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
COMBINED_CANDIDATE_TYPES                         1                1                    9618                         549                 549                              0 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
COMBINED_CANDIDATE_TYPES                         2                2                    9618                         549                 447                            102 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
COMBINED_CANDIDATE_TYPES                         3                3                    9618                         549                 369                            180 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
COMBINED_CANDIDATE_TYPES                         5                3                    9618                         549                 332                            217 RunOut, Retire Out, obstruction-related dismissals Candidate bowler-attributed event count, not verified official wicket total.
```

## Contextual identity key

```text
                       identity_key                   columns  mapping_rows  distinct_keys  duplicate_key_groups  duplicate_rows_beyond_first  unique_key  row_multiplication_safe                                                                                    interpretation
                          player_id                 player_id          6413           1217                   820                         5196       False                    False                  Not safe globally: same player ID appears in multiple competition/team contexts.
             comp_id_plus_player_id         comp_id+player_id          6413           6413                     0                            0        True                     True      Unique in mapping; appropriate competition-scoped identity where team context is not needed.
             team_id_plus_player_id         team_id+player_id          6413           1790                  1003                         4623       False                    False                                    Not unique: a player/team context appears across competitions.
comp_id_plus_team_id_plus_player_id comp_id+team_id+player_id          6413           6413                     0                            0        True                     True Unique and preserves competition plus team context; safest mapping join key for delivery context.
```

`player_id` alone is unsafe because it has duplicate mapping groups. The
actual mapping shows `(comp_id, player_id)` and
`(comp_id, team_id, player_id)` are unique, while `(team_id, player_id)` is
not. Use `(comp_id, team_id, player_id)` for a delivery-to-mapping join when
team context is available; use `(comp_id, player_id)` only for analyses where
competition-scoped identity is sufficient. The extended calculations avoid
mapping joins for event counts, so delivery rows are not multiplied.

## Remaining blockers

- Score and extras semantics remain unresolved.
- Pressure contexts remain inferred match-state contexts, not validated
  psychological pressure.
- Bowler conceded runs/economy remain blocked.
- Candidate dismissal events remain conservative source-event counts, not
  official wicket totals.
- Step 4B ranking or Top 10 selection is not authorized by this audit.

## Reproduction

```powershell
python src\audit_methodology_gaps.py
```
