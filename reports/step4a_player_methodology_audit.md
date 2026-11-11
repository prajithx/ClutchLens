# Step 4A Player Analysis Methodology & Evidence Audit

This audit establishes reproducible metric feasibility only. It creates no player rankings, Top 10 list, composite rating, pressure score, recommendation, or auction value.

## Executive summary
- Supplied raw files include 200,999 delivery rows, 883 match rows, and 6,413 mapping rows.
- `extras1_runs` remains a category code; `extras_2_runs` has 36 non-zero rows and is not semantically resolved.
- Batter runs, conditional balls, source boundary flags, and filtered dismissal events are partially supportable on strict/moderate subsets.
- Legal balls and conservative bowler dismissal/dot events are descriptively supportable; conceded runs and economy remain BLOCKED.
- Pressure contexts are observed/provisional coverage definitions, not validated player pressure ratings.

## Dataset and identity audit
- Ball-by-ball IDs: 867 matches, 888 strikers, 647 bowlers.
- Mapping contains 1,217 distinct player IDs and 6,413 distinct competition/team/player contexts.
- Exact duplicate mapping rows: 0. They must not be used to multiply delivery rows.
- Player identity is treated as contextual through competition/team/player mapping; no external identity enrichment is used.

## Pressure-context candidates
Chase and general contexts use the reconstructed fields in `delivery_context.csv`; they exclude abandoned/no-result, invalid ordinary innings, and target-completed states. Late-over status alone is not called pressure.
```text
pressure_definition                                                                                           formula  eligible_deliveries  eligible_innings  eligible_matches  unique_batters  unique_bowlers  excluded_target_or_incomplete_rows                                                                caveat
           baseline                                             ordinary valid innings, excluding abandoned/no-result               185945              1561               838             887             639                               15054 Observed context only; score and target semantics remain provisional.
     chase_baseline      valid chase, target not reached, <=48 balls, RRR>=10 or (RRR-CRR>=3 and <=6 wickets in hand)                19447               516               516             611             384                              181552 Observed context only; score and target semantics remain provisional.
   general_baseline valid innings, target not reached, <=36 balls, <=6 wickets in hand or <=36 runs required in chase                19155               676               676             627             433                              181844 Observed context only; score and target semantics remain provisional.
       chase_strict                                          chase baseline with <=30 balls and RRR>=12 or RRR-CRR>=4                10564               452               452             537             328                              190435 Observed context only; score and target semantics remain provisional.
     general_strict                          general baseline with <=24 balls and <=24 runs required for chase branch                12166               626               626             573             377                              188833 Observed context only; score and target semantics remain provisional.
        chase_loose                                           chase baseline with <=60 balls and RRR>=8 or RRR-CRR>=2                29571               582               582             670             431                              171428 Observed context only; score and target semantics remain provisional.
```

## Batter metric feasibility
```text
  role                    metric                                                       formula                                       source_fields  confidence  eligible_deliveries_or_events  eligible_innings  eligible_matches  unique_players                                                                  limitation
batter                      runs                     sum(runs) on strict eligible striker rows                    runs, extras_type, extras_2_runs      MEDIUM                         175062              1561               838             886 runs resembles batter runs but is not explicitly labelled; conditional only
batter      eligible balls faced                            count strict eligible striker rows              striker_id, extras_type, extras_2_runs      MEDIUM                         175062              1561               838             886                                         not a complete scorecard ball count
batter            boundary flags             sum(is_four), sum(is_six) after consistency audit                               is_four, is_six, runs      MEDIUM                         175062              1561               838             886                       source flags are descriptive and checked against runs
batter               strike rate         100 * sum(runs) / count(strict eligible striker rows)        runs, striker_id, extras_type, extras_2_runs         LOW                         175062              1561               838             886             conditional delivery rate, not a complete scorecard strike rate
batter dismissal/survival events             dismissed_player_id plus filtered dismissal types      is_wicket, dismissed_player_id, dismissal_type      MEDIUM                          10606              1708               865             805       dismissal types and non-striker/run-out handling must remain explicit
batter      pressure vs baseline compare strict metric aggregates under declared context flags delivery_context pressure fields plus batter fields EXPLORATORY                          17990               515               515             609               pressure context and target reconstruction remain provisional
```

## Bowler metric feasibility
```text
  role                   metric                                            formula                            source_fields confidence  eligible_deliveries_or_events  eligible_innings  eligible_matches  unique_players                                             limitation
bowler              legal balls count legal_ball after excluding wide and Overstep       extras_type, legal_ball, bowler_id     MEDIUM                         178297              1561               838             639              other extra legal status remains a caveat
bowler  conservative dot events          strict eligible legal rows with runs == 0 legal_ball, runs, extras_type, bowler_id     MEDIUM                          63052              1561               838             626       does not claim unresolved extras are batter dots
bowler candidate bowler wickets      count Bowled/Caught/LBW/Stump/Hit Wicket only     dismissal_type, is_wicket, bowler_id     MEDIUM                           9618              1553               838             549    RunOut, Retire Out, and obstruction events excluded
bowler    runs conceded/economy                                     not calculated          no verified bowler-charge field    BLOCKED                              0                 0                 0               0 cannot reliably attribute batter runs/extras to bowler
```
- Verified candidate bowler dismissal-type counts in the audited context: {'Caught': 7557, 'Bowled': 1775, 'LBW': 709, 'Stump': 214, 'Hit Wicket': 17}. RunOut and Retire Out are not included.

## Sample-size policy
The scenarios 10/3/30, 20/5/60, and 30/8/90 mean minimum pressure events / matches / baseline events. They are safeguards for later review, not universal statistical truths and not ranking cutoffs.
```text
                         scenario   role     policy pressure_definition  minimum_pressure_events  minimum_pressure_matches  minimum_baseline_events  qualifying_players  observed_players  pressure_events_total  baseline_events_total                                            caveat
10_pressure_3_matches_30_baseline batter     strict      chase_baseline                       10                         3                       30                 261               886                  17990                 175062 Count only; no ordering or selection is produced.
20_pressure_5_matches_60_baseline batter     strict      chase_baseline                       20                         5                       60                 151               886                  17990                 175062 Count only; no ordering or selection is produced.
30_pressure_8_matches_90_baseline batter     strict      chase_baseline                       30                         8                       90                  86               886                  17990                 175062 Count only; no ordering or selection is produced.
10_pressure_3_matches_30_baseline batter     strict    general_baseline                       10                         3                       30                 266               886                  17725                 175062 Count only; no ordering or selection is produced.
20_pressure_5_matches_60_baseline batter     strict    general_baseline                       20                         5                       60                 166               886                  17725                 175062 Count only; no ordering or selection is produced.
30_pressure_8_matches_90_baseline batter     strict    general_baseline                       30                         8                       90                  90               886                  17725                 175062 Count only; no ordering or selection is produced.
10_pressure_3_matches_30_baseline batter   moderate      chase_baseline                       10                         3                       30                 261               886                  18098                 175806 Count only; no ordering or selection is produced.
20_pressure_5_matches_60_baseline batter   moderate      chase_baseline                       20                         5                       60                 151               886                  18098                 175806 Count only; no ordering or selection is produced.
30_pressure_8_matches_90_baseline batter   moderate      chase_baseline                       30                         8                       90                  86               886                  18098                 175806 Count only; no ordering or selection is produced.
10_pressure_3_matches_30_baseline batter   moderate    general_baseline                       10                         3                       30                 266               886                  17834                 175806 Count only; no ordering or selection is produced.
20_pressure_5_matches_60_baseline batter   moderate    general_baseline                       20                         5                       60                 166               886                  17834                 175806 Count only; no ordering or selection is produced.
30_pressure_8_matches_90_baseline batter   moderate    general_baseline                       30                         8                       90                  90               886                  17834                 175806 Count only; no ordering or selection is produced.
10_pressure_3_matches_30_baseline bowler legal_ball      chase_baseline                       10                         3                       30                 210               639                  18390                 178297 Count only; no ordering or selection is produced.
20_pressure_5_matches_60_baseline bowler legal_ball      chase_baseline                       20                         5                       60                 141               639                  18390                 178297 Count only; no ordering or selection is produced.
30_pressure_8_matches_90_baseline bowler legal_ball      chase_baseline                       30                         8                       90                  92               639                  18390                 178297 Count only; no ordering or selection is produced.
10_pressure_3_matches_30_baseline bowler legal_ball    general_baseline                       10                         3                       30                 224               639                  18110                 178297 Count only; no ordering or selection is produced.
20_pressure_5_matches_60_baseline bowler legal_ball    general_baseline                       20                         5                       60                 164               639                  18110                 178297 Count only; no ordering or selection is produced.
30_pressure_8_matches_90_baseline bowler legal_ball    general_baseline                       30                         8                       90                 102               639                  18110                 178297 Count only; no ordering or selection is produced.
```

## Supported / exploratory / blocked register
- **SUPPORTED DESCRIPTIVE, with caveats:** legal balls; strict/moderate conditional batter runs and balls; source boundary flags; filtered dismissal events; conservative dot events.
- **EXPLORATORY:** pressure-context versus baseline comparisons using provisional reconstructed context and declared sensitivity variants.
- **BLOCKED:** bowler conceded runs, economy, final pressure ratings, composite ratings, rankings, Top 10 selection, and recommendations.

## Future selection framework
A later step may present player-level descriptive tables only after applying a declared policy, minimum event/match thresholds, and uncertainty/sample-size disclosures. Batter comparisons should use conditional runs, conditional balls, boundary flags, and carefully filtered dismissals without calling them complete scorecard statistics. Bowler comparisons may use legal balls, conservative dots, and separated candidate dismissal types, but not economy or conceded runs.
Pressure comparisons should report the exact context formula, baseline, exclusions, and sensitivity variants side by side. Correlated metrics should not be double-counted; no composite score should be proposed until every component is semantically defensible and weights are justified.

## Reproduction
```powershell
python src\audit_player_methodology.py
```

## Join audit reference
```text
                   join_name  source_rows  source_key  target_rows  target_key  matched_source_rows  unmatched_source_rows  target_duplicate_key_rows row_multiplication_risk                                                                                                         notes
             ball_to_matches       200999    match_id          883    match_id               200999                      0                          0                     LOW                        Mapping is contextual by competition/team; aggregate distinct contexts before joining.
     matches_to_competitions          883     comp_id          141     comp_id                  883                      0                          0                     LOW                        Mapping is contextual by competition/team; aggregate distinct contexts before joining.
      striker_ids_to_mapping       200999  striker_id         6413   player_id               200999                      0                       5196                    HIGH                        Mapping is contextual by competition/team; aggregate distinct contexts before joining.
       bowler_ids_to_mapping       200999   bowler_id         6413   player_id               200999                      0                       5196                    HIGH                        Mapping is contextual by competition/team; aggregate distinct contexts before joining.
mapping_exact_duplicate_rows         6413 all_columns         6413 all_columns                 6413                      0                          0                     LOW Exact duplicates may be de-duplicated for identity lookup only; valid team/competition contexts are retained.
```
