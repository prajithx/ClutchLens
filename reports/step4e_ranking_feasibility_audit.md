# Step 4E Ranking Feasibility Audit

## Executive decision
- **Batter Top 10 performance ranking: NOT DEFENSIBLE from the supplied evidence without additional semantic and comparability safeguards.** Descriptive conditional comparisons are partially feasible.
- **Bowler Top 10 performance ranking: NOT DEFENSIBLE.** Legal-ball, conservative dot, and candidate dismissal-event evidence is available descriptively, but conceded runs/economy and official wickets are blocked.
- The Step 4B lists remain candidate-context shortlists ordered by evidence coverage, not performance rankings. They are not relabelled here.

## Verified source facts
- Raw delivery rows: 200,999; match IDs in delivery context: 867; reconstructed innings: 1,724.
- Strict batter rows: 175,062; legal-ball bowler rows: 178,297.
- Step 4B contexts: 2 readiness decisions; source candidate files contain 10 batter and 10 bowler contexts.
- Step 4C classifications: {'EXTERNAL_HISTORICAL_CANDIDATE': 17, 'RR_REFERENCE_SEASON_PARTICIPANT': 3}.
- Identity evidence supports `(comp_id, team_id, player_id)` as the safest contextual join key; global `player_id` joins can multiply rows.

## Metric feasibility matrix
The matrix records source lineage, transformations, eligibility, coverage, ranking safety, and caveats. “No” in the ranking column is intentional: a descriptive metric can exist without being safe as a final ranking component.
```text
  role                             metric                                                       business_meaning                                                                source_lineage                                                    calculation                                                             eligibility_exclusions                                                                   sample_coverage             feasibility safe_to_contribute_to_ranking confidence                                                                              caveats
batter          conditional observed runs                           Runs recorded on eligible striker deliveries            delivery_context.csv: runs, striker_id, extras_type, extras_2_runs                                        sum(runs) by striker_id        strict_batter: null extras_type, extras_2_runs == 0, valid ordinary innings      175,062 deliveries; 886 player IDs; 151 pass Step 4B primary sample scenario DESCRIPTIVE_CONDITIONAL                            NO     MEDIUM       runs resembles batter runs but is not explicitly labelled official batter runs
batter                eligible deliveries                   Conditional delivery denominator for batter evidence                  delivery_context.csv: striker_id, extras_type, extras_2_runs                             count strict eligible striker rows                          same strict policy; incomplete scorecard semantics remain      175,062 deliveries; 886 player IDs; 151 pass Step 4B primary sample scenario DESCRIPTIVE_CONDITIONAL                            NO     MEDIUM                                                  not a complete scorecard ball count
batter               conditional run rate                                    Observed runs per eligible delivery            delivery_context.csv: runs, striker_id, extras_type, extras_2_runs          100 * conditional observed runs / eligible deliveries                                                                 same strict policy      175,062 deliveries; 886 player IDs; 151 pass Step 4B primary sample scenario EXPLORATORY_COMPARATIVE                            NO        LOW not a complete scorecard strike rate; denominator and runs semantics are conditional
batter             source boundary counts                                             Descriptive four/six flags                                   delivery_context.csv: is_four, is_six, runs                                     sum source flags by player                                   strict eligible rows; flags checked against runs      175,062 deliveries; 886 player IDs; 151 pass Step 4B primary sample scenario DESCRIPTIVE_CONDITIONAL                            NO     MEDIUM                     does not establish complete innings or tournament boundary rates
batter                    batting average                                     Runs per dismissal/not-out innings                    delivery_context.csv: runs, is_wicket, dismissed_player_id would require reliable innings dismissal and not-out semantics                                                                       not computed                                                            No defensible coverage                 BLOCKED                            NO     MEDIUM              source dismissal/survival semantics and score totals are not sufficient
batter                dot-ball percentage                       Share of batter deliveries with zero batter runs                        delivery_context.csv: runs, extras_type, extras_2_runs            would require verified batter-run and dot semantics                                                   not computed as a ranking metric                                                                    Not defensible                 BLOCKED                            NO        LOW                           ambiguous extras prevent a verified batter-dot denominator
batter          cross-innings consistency              Variation of conditional delivery evidence across innings                     delivery_context.csv: match_id, innings, striker_id, runs                  could summarize per-innings conditional rates             minimum innings/match threshold required; no validated score semantics                                     1,561 eligible innings; candidate contexts 10        EXPLORATORY_ONLY                            NO        LOW                sample size and context comparability are not enough for a final rank
batter           chase-context comparison        Conditional evidence in inferred chase contexts versus baseline                      delivery_context.csv: pressure fields plus batter fields           compare declared strict aggregates under chase_proxy                         chase_proxy rows only; target/score reconstruction caveats                                              17,990 pressure rows; 609 player IDs        EXPLORATORY_ONLY                            NO        LOW                               chase_baseline is not validated psychological pressure
bowler                        legal balls              Deliveries counted as legal after wide/Overstep exclusion                                   delivery_context.csv: legal_ball, bowler_id                                count legal_ball rows by bowler                                            valid ordinary innings; legal_ball true 178,297 legal-ball rows; 639 player IDs; 141 pass Step 4B primary sample scenario DESCRIPTIVE_CONDITIONAL                            NO     MEDIUM                                            other-extra legal status remains a caveat
bowler                    safe dot events                                Conservative zero-run legal-ball events delivery_context.csv: legal_ball, runs, extras_type, extras_2_runs, bowler_id        count legal rows satisfying strict_batter and runs == 0                                               legal ball plus strict batter policy                                                       63,052 rows; 626 player IDs DESCRIPTIVE_CONDITIONAL                            NO     MEDIUM                                    not an official dot-ball rate or scorecard metric
bowler candidate dismissal events by type                  Filtered potential bowler-attributed dismissal events                    delivery_context.csv: is_wicket, dismissal_type, bowler_id  count candidate types: Caught, Bowled, LBW, Stump, Hit Wicket legal ball; is_wicket true; excluded RunOut, Retire Out, obstruction-related types                                                      9,618 events; 549 player IDs DESCRIPTIVE_CONDITIONAL                            NO     MEDIUM                                            candidate events are not official wickets
bowler      candidate dismissal frequency                           Candidate dismissal events per match/context         delivery_context.csv: candidate dismissal fields, match_id, bowler_id               event count and match count by contextual player                                               same filtered candidate-event policy                           141 pass primary sample scenario; 10 displayed contexts        EXPLORATORY_ONLY                            NO     MEDIUM                   raw event totals favour volume and are not a validated wicket rate
bowler                dot-ball percentage                                 Safe dot events divided by legal balls                          delivery_context.csv: safe dot and legal-ball fields                                  safe dot events / legal balls                                                           same conservative policy 178,297 legal-ball rows; 639 player IDs; 141 pass Step 4B primary sample scenario        EXPLORATORY_ONLY                            NO        LOW         safe dot semantics are conditional and may not be comparable across contexts
bowler              runs conceded/economy                                        Runs charged to bowler per over                  No verified bowler-charge field; extras semantics unresolved                                                 not calculated                                                                            blocked                                                                        0 computed                 BLOCKED                            NO       NONE           cannot reliably attribute batter runs, wides, no-balls, byes, and leg-byes
bowler      pace/spin/delivery categories                                  Source delivery-category distribution              delivery_context.csv: pace_or_spin, bowling_type, delivery_style                                    descriptive category counts                                     category values only; no performance inference                                                 200,999 non-null pace/spin values        DESCRIPTIVE_ONLY                            NO     MEDIUM                                     categories are not player quality or role scores
bowler           chase-context comparison Conservative event evidence in inferred chase contexts versus baseline                     delivery_context.csv: pressure fields plus bowling fields                   compare event counts/rates under chase_proxy                                    chase_proxy remains inferred; legal-ball policy                                              18,390 pressure rows; 383 player IDs        EXPLORATORY_ONLY                            NO        LOW                              event coverage does not validate psychological pressure
```

## Fair comparison and Top 10 feasibility
### Batters
- Raw totals are volume-sensitive, while conditional rates depend on a delivery subset whose score/extras semantics are not fully resolved.
- Contexts span different IPL seasons and teams; the supplied pack also contains T20I data, so combining all formats as one ranking population would be unjustified.
- Pressure comparison is exploratory because `chase_baseline` is an inferred match-state proxy, not validated psychological pressure.
- A transparent ranking would require a validated common metric set, stable innings/dismissal semantics, explicitly comparable populations, missing-data policy, and independently justified weights or normalization.
### Bowlers
- Legal balls and conservative event counts are available, but raw event volume rewards workload.
- Candidate dismissal events exclude non-bowler-attributed types but remain candidate events, not official wickets.
- Runs conceded/economy cannot be reconstructed reliably because extras and bowler-charge attribution are unresolved.
- Without economy or another validated outcome metric, a performance ranking would be materially incomplete and potentially misleading.

## RR recruitment relevance
- Step 4C distinguishes 2026 RR reference-season participants from external historical candidates; absence from that season does not prove auction availability.
- Auction pool, retention/release, current contracts, budget, overseas slots, and 2027 squad requirements are not supplied.
- The system can support analyst review through evidence profiles, contextual history, sample gates, and explicit blockers; it cannot replace official roster/auction verification or final judgement.

## Ground Explorer capability check
```text
                     capability                status                                                                          evidence                         limitation
venue identity and match counts SUPPORTED_DESCRIPTIVE   matches.csv: venue_id, venue_country, match_id; 98 venue IDs across 883 matches              No stadium name field
 stroke and delivery categories SUPPORTED_DESCRIPTIVE ball_by_ball.csv: stroke, delivery_style, pace_or_spin, on_or_off, over_or_around  Category counts are not locations
       shot landing coordinates               BLOCKED                                                      No supplied coordinate field     No heatmap or wagon-wheel plot
        pitch/boundary geometry               BLOCKED                                                  No dimensions or geometry fields Pitch artwork is illustrative only
      field-placement analytics               BLOCKED                                 No verified landing or field-position coordinates   Cannot create factual field maps
```
- Factual venue summaries and categorical stroke/pace-spin distributions are supported.
- The current pitch artwork is illustrative and not real venue geometry.
- Actual shot landing coordinates, pitch dimensions, boundary geometry, wagon-wheel plots, and field-placement plots are unavailable.

## Risks, unresolved questions, and exact additional data needed
1. Verify the semantics of `runs`, `extras_2_runs`, team totals, and bowler-charge runs from an authoritative source or corrected data dictionary.
2. Supply validated innings dismissal/not-out semantics if batting average or survival rates are required.
3. Supply official auction-pool, retention/release, contract, budget, overseas-slot, and 2027 squad-need data before recruitment availability or gap decisions.
4. Supply role/skill labels if role-based squad-gap analysis is required.
5. Supply verified spatial venue and shot-location fields before spatial ground analytics.

## Read-only integrity and validation
- Raw hashes were recorded before and after the audit.
- Existing Step 4A–4D artifact hashes were recorded before and after and were unchanged.
- No dashboard files, routes, CSS, JavaScript, raw data, or existing reports were modified by Step 4E.

## Reproduction
```powershell
python src\audit_step4e_ranking_feasibility.py
python -m py_compile src\audit_step4e_ranking_feasibility.py
```
