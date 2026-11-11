# SupeRR Selector Season 2 Data Audit

- **Source ZIP:** `6af3166e7b922_data_pack.zip`
- **Extracted files:** 7
- **CSV files read successfully:** 6

## Dataset inventory

| File | Rows | Columns | Size (bytes) |
|---|---:|---:|---:|
| `ball_by_ball.csv` | 200999 | 33 | 41071609 |
| `competition_team_player_mapping.csv` | 6413 | 6 | 462969 |
| `competitions.csv` | 141 | 4 | 7624 |
| `matches.csv` | 883 | 22 | 123864 |
| `playing_eleven.csv` | 28381 | 9 | 966287 |
| `teams.csv` | 353 | 3 | 6922 |

Expected CSVs missing or unreadable: none.

## Schema and data dictionary

### `ball_by_ball.csv`

- Rows: **200999**; columns: **33**

| Column | Observed type | Missing | Missing % | Unique non-null |
|---|---|---:|---:|---:|
| `match_id` | `int64` | 0 | 0.0% | 867 |
| `innings` | `int64` | 0 | 0.0% | 4 |
| `overid` | `int64` | 0 | 0.0% | 20 |
| `over_ball_num` | `int64` | 0 | 0.0% | 13 |
| `innings_ball_num` | `int64` | 0 | 0.0% | 136 |
| `batting_team_id` | `int64` | 0 | 0.0% | 38 |
| `bowling_team_id` | `int64` | 0 | 0.0% | 38 |
| `striker_id` | `int64` | 0 | 0.0% | 888 |
| `striker_name` | `object` | 0 | 0.0% | 885 |
| `non_striker_id` | `int64` | 0 | 0.0% | 867 |
| `non_striker_name` | `object` | 0 | 0.0% | 864 |
| `bowler_id` | `int64` | 0 | 0.0% | 647 |
| `bowler_name` | `object` | 0 | 0.0% | 646 |
| `batting_type` | `object` | 0 | 0.0% | 2 |
| `bowling_type` | `object` | 0 | 0.0% | 12 |
| `batting_order` | `int64` | 0 | 0.0% | 13 |
| `runs` | `int64` | 0 | 0.0% | 7 |
| `is_four` | `bool` | 0 | 0.0% | 2 |
| `is_six` | `bool` | 0 | 0.0% | 2 |
| `is_wicket` | `bool` | 0 | 0.0% | 2 |
| `dismissal_type_id` | `float64` | 190118 | 94.59% | 8 |
| `dismissal_type` | `object` | 190118 | 94.59% | 9 |
| `dismissed_player_id` | `float64` | 190107 | 94.58% | 814 |
| `extras_type` | `object` | 189167 | 94.11% | 6 |
| `extras1_runs` | `int64` | 0 | 0.0% | 7 |
| `extras_2_runs` | `int64` | 0 | 0.0% | 3 |
| `pace_or_spin` | `object` | 0 | 0.0% | 2 |
| `bowl_speed` | `float64` | 0 | 0.0% | 1033 |
| `stroke` | `object` | 6158 | 3.06% | 30 |
| `delivery_style` | `object` | 391 | 0.19% | 34 |
| `over_or_around` | `object` | 407 | 0.2% | 2 |
| `on_or_off` | `object` | 0 | 0.0% | 2 |
| `delivery_ist_time` | `object` | 0 | 0.0% | 200826 |

Sample records (maximum 5):

```text
 match_id  innings  overid  over_ball_num  innings_ball_num  batting_team_id  bowling_team_id  striker_id striker_name  non_striker_id non_striker_name  bowler_id      bowler_name batting_type         bowling_type  batting_order  runs  is_four  is_six  is_wicket  dismissal_type_id dismissal_type  dismissed_player_id extras_type  extras1_runs  extras_2_runs pace_or_spin  bowl_speed             stroke delivery_style over_or_around on_or_off       delivery_ist_time
    13511        1       1              1                 1               22               28        1187    Jason Roy            6273       Tom Banton       1772 Sheldon Cottrell          RHB Left-arm fast-medium              1     0    False   False      False                NaN            NaN                  NaN         NaN             6              0         Pace         0.0        Cover Drive        Inswing           Over  Off-side 2022-01-23 00:00:00 UTC
    13511        1       1              2                 2               22               28        1187    Jason Roy            6273       Tom Banton       1772 Sheldon Cottrell          RHB Left-arm fast-medium              1     0    False   False      False                NaN            NaN                  NaN         NaN             6              0         Pace         0.0              Flick        Inswing           Over   On-side 2022-01-23 00:00:00 UTC
    13511        1       1              3                 3               22               28        1187    Jason Roy            6273       Tom Banton       1772 Sheldon Cottrell          RHB Left-arm fast-medium              1     0    False   False      False                NaN            NaN                  NaN         NaN             6              0         Pace         0.0         Square Cut        Inswing           Over  Off-side 2022-01-23 00:00:00 UTC
    13511        1       1              4                 4               22               28        1187    Jason Roy            6273       Tom Banton       1772 Sheldon Cottrell          RHB Left-arm fast-medium              1     0    False   False      False                NaN            NaN                  NaN         NaN             6              0         Pace         0.0 Backfoot defensive        Inswing           Over   On-side 2022-01-23 00:00:00 UTC
    13511        1       1              5                 5               22               28        1187    Jason Roy            6273       Tom Banton       1772 Sheldon Cottrell          RHB Left-arm fast-medium              1     6    False    True      False                NaN            NaN                  NaN         NaN             6              0         Pace         0.0          Pull shot      Seamed In           Over   On-side 2022-01-23 00:00:00 UTC
```

- Duplicate full rows: **0**.
- ID column `match_id`: 867 unique non-null; 0 null.
- ID column `batting_team_id`: 38 unique non-null; 0 null.
- ID column `bowling_team_id`: 38 unique non-null; 0 null.
- ID column `striker_id`: 888 unique non-null; 0 null.
- ID column `non_striker_id`: 867 unique non-null; 0 null.
- ID column `bowler_id`: 647 unique non-null; 0 null.
- ID column `dismissal_type_id`: 8 unique non-null; 190118 null.
- ID column `dismissed_player_id`: 814 unique non-null; 190107 null.

Selected value distributions:
- `innings`: 1 (105727), 2 (95234), 3 (25), 4 (13)
- `overid`: 1 (10818), 2 (10788), 3 (10645), 4 (10638), 5 (10615), 6 (10542), 8 (10476), 7 (10441), 9 (10415), 10 (10396), 11 (10319), 12 (10254), ...
- `over_ball_num`: 1 (32350), 2 (32257), 3 (32169), 4 (32066), 5 (31937), 6 (31791), 7 (6710), 8 (1364), 9 (279), 10 (57), 11 (15), 12 (2), ...
- `batting_type`: RHB (131006), LHB (69993)
- `bowling_type`: Right-arm Leg-Break (28027), Right-arm medium-fast (27014), Right-arm Fast (26637), Right-arm medium (23919), Slow left-arm orthodox (23582), Right-arm offbreak (20948), Right-arm fast-medium (15380), Left-arm medium-fast (12492), Left-arm fast-medium (7780), Left-arm medium (6082), Left-arm Chinaman (4685), Left-arm Fast (4453)
- `batting_order`: 2 (34488), 1 (34126), 3 (31065), 4 (30068), 5 (24125), 6 (18297), 7 (13091), 8 (7578), 9 (4448), 10 (2554), 11 (1133), 12 (17), ...
- `runs`: 0 (79387), 1 (72267), 4 (23303), 6 (12814), 2 (12547), 3 (656), 5 (25)
- `is_four`: False (177716), True (23283)
- `is_six`: False (188188), True (12811)
- `is_wicket`: False (190118), True (10881)
- `dismissal_type_id`: null (190118), 2.0 (7557), 1.0 (1775), 3.0 (709), 4.0 (600), 5.0 (214), 6.0 (17), 9.0 (6), 10.0 (3)
- `dismissal_type`: null (190118), Caught (7557), Bowled (1775), LBW (709), RunOut (600), Stump (214), Hit Wicket (17), Retire Out (6), Obstracting the field (2), Obstructing the field (1)
- `dismissed_player_id`: null (190107), 6281.0 (130), 1699.0 (119), 4117.0 (116), 2258.0 (110), 813.0 (107), 6288.0 (100), 3125.0 (96), 3330.0 (90), 7897.0 (90), 126.0 (86), 6819.0 (83), ...
- `extras_type`: null (189167), wide (7714), legbyes (2748), Overstep (576), byes (529), other (264), Penalty (1)
- `extras1_runs`: 6 (189167), 2 (7714), 3 (2748), 1 (576), 4 (529), 5 (264), 7 (1)
- `extras_2_runs`: 0 (200963), 1 (20), 4 (16)
- `pace_or_spin`: Pace (123886), Spin (77113)
- `over_or_around`: Over (154670), Around (45922), null (407)
- `on_or_off`: Off-side (104875), On-side (96124)

### `competition_team_player_mapping.csv`

- Rows: **6413**; columns: **6**

| Column | Observed type | Missing | Missing % | Unique non-null |
|---|---|---:|---:|---:|
| `comp_id` | `int64` | 0 | 0.0% | 140 |
| `comp_name` | `object` | 0 | 0.0% | 140 |
| `team_id` | `int64` | 0 | 0.0% | 38 |
| `team_name` | `object` | 0 | 0.0% | 38 |
| `player_id` | `int64` | 0 | 0.0% | 1217 |
| `player_name` | `object` | 0 | 0.0% | 1210 |

Sample records (maximum 5):

```text
 comp_id                               comp_name  team_id team_name  player_id  player_name
    1331 England in West Indies T20I Series 2022       22   England        478  Eoin Morgan
    1331 England in West Indies T20I Series 2022       22   England        479  Adil Rashid
    1331 England in West Indies T20I Series 2022       22   England        722  Liam Dawson
    1331 England in West Indies T20I Series 2022       22   England        786 Chris Jordan
    1331 England in West Indies T20I Series 2022       22   England       1187    Jason Roy
```

- Duplicate full rows: **0**.
- ID column `comp_id`: 140 unique non-null; 0 null.
- ID column `team_id`: 38 unique non-null; 0 null.
- ID column `player_id`: 1217 unique non-null; 0 null.

Selected value distributions:

### `competitions.csv`

- Rows: **141**; columns: **4**

| Column | Observed type | Missing | Missing % | Unique non-null |
|---|---|---:|---:|---:|
| `comp_id` | `int64` | 0 | 0.0% | 141 |
| `comp_name` | `object` | 0 | 0.0% | 141 |
| `match_format` | `object` | 0 | 0.0% | 2 |
| `season` | `object` | 0 | 0.0% | 8 |

Sample records (maximum 5):

```text
 comp_id                                    comp_name match_format season
    3395 South Africa in New Zealand T20I Series 2026         T20I   2026
    3405     Afghanistan v Sri Lanka T20I Series 2026         T20I   2026
    3465           India in Zimbabwe T20I Series 2026         T20I   2026
    3568      Bangladesh in Zimbabwe T20I Series 2026         T20I   2026
    3482     Australia in Bangladesh T20I Series 2026         T20I   2026
```

- Duplicate full rows: **0**.
- ID column `comp_id`: 141 unique non-null; 0 null.

Selected value distributions:
- `match_format`: T20I (134), T20 (7)
- `season`: 2024 (33), 2025 (33), 2022 (25), 2026 (25), 2023 (20), 2022/23 (3), 2023/24 (1), 2024/25 (1)

### `matches.csv`

- Rows: **883**; columns: **22**

| Column | Observed type | Missing | Missing % | Unique non-null |
|---|---|---:|---:|---:|
| `match_id` | `int64` | 0 | 0.0% | 883 |
| `comp_id` | `int64` | 0 | 0.0% | 138 |
| `match_number` | `int64` | 0 | 0.0% | 75 |
| `match_date` | `object` | 0 | 0.0% | 686 |
| `stage` | `object` | 0 | 0.0% | 7 |
| `venue_id` | `int64` | 0 | 0.0% | 98 |
| `venue_country` | `object` | 0 | 0.0% | 17 |
| `home_team_id` | `int64` | 0 | 0.0% | 36 |
| `home_team` | `object` | 0 | 0.0% | 36 |
| `away_team_id` | `int64` | 0 | 0.0% | 36 |
| `away_team` | `object` | 0 | 0.0% | 36 |
| `home_team_captain_id` | `float64` | 44 | 4.98% | 89 |
| `away_team_captain_id` | `float64` | 45 | 5.1% | 98 |
| `toss_win_team_id` | `float64` | 15 | 1.7% | 37 |
| `toss_opted` | `object` | 15 | 1.7% | 2 |
| `man_of_the_match` | `int64` | 0 | 0.0% | 293 |
| `first_inn_revised_overs` | `float64` | 858 | 97.17% | 13 |
| `second_inn_revised_overs` | `float64` | 858 | 97.17% | 12 |
| `revised_target` | `float64` | 860 | 97.4% | 23 |
| `knock_out` | `int64` | 0 | 0.0% | 2 |
| `win_team_id` | `float64` | 41 | 4.64% | 36 |
| `result` | `object` | 0 | 0.0% | 670 |

Sample records (maximum 5):

```text
 match_id  comp_id  match_number match_date  stage  venue_id venue_country  home_team_id   home_team  away_team_id away_team  home_team_captain_id  away_team_captain_id  toss_win_team_id toss_opted  man_of_the_match  first_inn_revised_overs  second_inn_revised_overs  revised_target  knock_out  win_team_id                       result
    13511     1331             1 2022-01-22 League        54   West Indies            28 West Indies            22   England                   NaN                   NaN              28.0   Fielding                 0                      NaN                       NaN             NaN          0         28.0 West Indies Won by 9 Wickets
    13512     1331             2 2022-01-23 League        54   West Indies            28 West Indies            22   England                 494.0                 478.0              28.0   Fielding                 0                      NaN                       NaN             NaN          0         22.0         England Won by 1 Run
    13513     1331             3 2022-01-26 League        54   West Indies            28 West Indies            22   England                 494.0                1596.0              22.0   Fielding              4986                      NaN                       NaN             NaN          0         28.0   West Indies Won by 20 runs
    13514     1331             4 2022-01-29 League        54   West Indies            28 West Indies            22   England                 494.0                1596.0              28.0   Fielding                 0                      NaN                       NaN             NaN          0         22.0       England Won by 34 runs
    13515     1331             5 2022-01-30 League        54   West Indies            28 West Indies            22   England                 494.0                   NaN              28.0    Batting                 0                      NaN                       NaN             NaN          0         28.0   West Indies Won by 17 runs
```

- Duplicate full rows: **0**.
- ID column `match_id`: 883 unique non-null; 0 null.
- ID column `comp_id`: 138 unique non-null; 0 null.
- ID column `venue_id`: 98 unique non-null; 0 null.
- ID column `home_team_id`: 36 unique non-null; 0 null.
- ID column `away_team_id`: 36 unique non-null; 0 null.
- ID column `home_team_captain_id`: 89 unique non-null; 44 null.
- ID column `away_team_captain_id`: 98 unique non-null; 45 null.
- ID column `toss_win_team_id`: 37 unique non-null; 15 null.
- ID column `win_team_id`: 36 unique non-null; 41 null.

Selected value distributions:
- `stage`: League (620), Others (226), Final (12), Qualifier (10), Super 4 (6), Eliminator (5), Semi Final (4)
- `venue_country`: India (425), United Arab Emirates (69), New Zealand (52), United Kingdom (49), West Indies (44), Zimbabwe (38), Pakistan (36), Bangladesh (34), Sri Lanka (26), Australia (24), Oman (21), South Africa (18), ...
- `toss_opted`: Fielding (639), Batting (229), null (15)
- `first_inn_revised_overs`: null (858), 54.0 (4), 66.0 (3), 84.0 (3), 102.0 (2), 114.0 (2), 108.0 (2), 30.0 (2), 90.0 (2), 48.0 (1), 72.0 (1), 42.0 (1), ...
- `second_inn_revised_overs`: null (858), 90.0 (5), 114.0 (3), 48.0 (3), 42.0 (2), 54.0 (2), 102.0 (2), 60.0 (2), 30.0 (2), 72.0 (1), 78.0 (1), 84.0 (1), ...
- `knock_out`: 0 (852), 1 (31)
- `result`: No Result (21), Match Abandoned (19), India Won by 7 wickets (8), Delhi Capitals Won by 6 wickets (7), Kolkata Knight Riders Won by 8 wickets (6), India Won by 6 Wickets (5), Gujarat Titans Won by 7 wickets (5), Punjab Kings Won by 5 wickets (5), New Zealand Won by 8 wickets (4), Mumbai Indians Won by 6 wickets (4), Rajasthan Royals Won by 6 wickets (4), Punjab Kings Won by 7 wickets (4), ...

### `playing_eleven.csv`

- Rows: **28381**; columns: **9**

| Column | Observed type | Missing | Missing % | Unique non-null |
|---|---|---:|---:|---:|
| `match_id` | `int64` | 0 | 0.0% | 880 |
| `team_id` | `int64` | 0 | 0.0% | 38 |
| `player_id` | `int64` | 0 | 0.0% | 1082 |
| `batting_order` | `float64` | 8678 | 30.58% | 13 |
| `is_played` | `bool` | 0 | 0.0% | 2 |
| `is_captain` | `object` | 8667 | 30.54% | 2 |
| `is_wk` | `object` | 8667 | 30.54% | 2 |
| `is_impact` | `int64` | 0 | 0.0% | 2 |
| `is_impact_off` | `int64` | 0 | 0.0% | 2 |

Sample records (maximum 5):

```text
 match_id  team_id  player_id  batting_order  is_played is_captain is_wk  is_impact  is_impact_off
    13511       22       1187            1.0       True      False False          0              0
    13511       22       6273            2.0       True      False False          0              0
    13511       22       1210            3.0       True      False False          0              0
    13511       22       1596            4.0       True      False False          0              0
    13511       22        478            5.0       True      False False          0              0
```

- Duplicate full rows: **0**.
- ID column `match_id`: 880 unique non-null; 0 null.
- ID column `team_id`: 38 unique non-null; 0 null.
- ID column `player_id`: 1082 unique non-null; 0 null.

Selected value distributions:
- `batting_order`: null (8678), 3.0 (1744), 2.0 (1743), 1.0 (1743), 4.0 (1742), 5.0 (1741), 6.0 (1741), 8.0 (1736), 11.0 (1736), 9.0 (1736), 10.0 (1735), 7.0 (1735), ...
- `is_played`: True (19714), False (8667)
- `is_captain`: False (18031), null (8667), True (1683)
- `is_wk`: False (18039), null (8667), True (1675)
- `is_impact`: 0 (27823), 1 (558)
- `is_impact_off`: 0 (27823), 1 (558)

### `teams.csv`

- Rows: **353**; columns: **3**

| Column | Observed type | Missing | Missing % | Unique non-null |
|---|---|---:|---:|---:|
| `comp_id` | `int64` | 0 | 0.0% | 141 |
| `team_id` | `int64` | 0 | 0.0% | 38 |
| `team_name` | `object` | 0 | 0.0% | 38 |

Sample records (maximum 5):

```text
 comp_id  team_id   team_name
    1331       22     England
    1331       28 West Indies
    1335       18       India
    1335       28 West Indies
    1345       20   Australia
```

- Duplicate full rows: **0**.
- ID column `comp_id`: 141 unique non-null; 0 null.
- ID column `team_id`: 38 unique non-null; 0 null.

Selected value distributions:

## Ball-by-ball audit

- **Unique matches:** 867 unique values in `match_id`.
- **Innings distribution (`innings`):** 1 (105727), 2 (95234), 3 (25), 4 (13).
- **Over distribution/range:** column not present.
- **Ball-number distribution/range:** column not present.
- **Unique batters:** 888 unique values in `striker_id`.
- **Unique bowlers:** 647 unique values in `bowler_id`.
- **Run-related columns (`runs`):** 0 (79387), 1 (72267), 4 (23303), 6 (12814), 2 (12547), 3 (656), 5 (25).
- **Extras type (`extras_type`):** null (189167), wide (7714), legbyes (2748), Overstep (576), byes (529), other (264), Penalty (1).
- **Wicket flag (`is_wicket`):** False (190118), True (10881).
- **Dismissal type (`dismissal_type`):** null (190118), Caught (7557), Bowled (1775), LBW (709), RunOut (600), Stump (214), Hit Wicket (17), Retire Out (6), Obstracting the field (2), Obstructing the field (1).
- **Pace/spin (`pace_or_spin`):** Pace (123886), Spin (77113).
- **Bowling type (`bowling_type`):** Right-arm Leg-Break (28027), Right-arm medium-fast (27014), Right-arm Fast (26637), Right-arm medium (23919), Slow left-arm orthodox (23582), Right-arm offbreak (20948), Right-arm fast-medium (15380), Left-arm medium-fast (12492), Left-arm fast-medium (7780), Left-arm medium (6082), Left-arm Chinaman (4685), Left-arm Fast (4453).

## Coverage and relationship validation

### Match coverage by season and format

| Season | Format | Matches |
|---|---|---:|
| 2022 | T20 | 74 |
| 2022 | T20I | 94 |
| 2022/23 | T20I | 12 |
| 2023 | T20 | 74 |
| 2023 | T20I | 63 |
| 2023/24 | T20I | 3 |
| 2024 | T20 | 89 |
| 2024 | T20I | 109 |
| 2024/25 | T20I | 3 |
| 2025 | T20 | 90 |
| 2025 | T20I | 126 |
| 2026 | T20 | 74 |
| 2026 | T20I | 72 |

- Match dates: 2022-01-22 through 2026-11-01 (686 distinct observed values).
- Result categories: No Result (21), Match Abandoned (19), India Won by 7 wickets (8), Delhi Capitals Won by 6 wickets (7), Kolkata Knight Riders Won by 8 wickets (6), India Won by 6 Wickets (5), Gujarat Titans Won by 7 wickets (5), Punjab Kings Won by 5 wickets (5), New Zealand Won by 8 wickets (4), Mumbai Indians Won by 6 wickets (4), Rajasthan Royals Won by 6 wickets (4), Punjab Kings Won by 7 wickets (4), Pakistan Won by 7 wickets (4), Bangladesh Won by 8 wickets (4), West Indies Won by 5 wickets (4), Bangladesh Won by 4 wickets (4), Royal Challengers Bengaluru Won by 6 wickets (4), Australia Won by 3 wickets (4), Gujarat Titans won by 6 wickets (3), Afghanistan Won by 7 wickets (3), ....
- Abandoned/no-result results: 40.
- Matches without a competition join: 0.

### Playing-eleven coverage

- Unique players: **1082**; matches: **880**; teams: **38**.
- `is_played`: True (19714), False (8667).
- `is_captain`: False (18031), null (8667), True (1683).
- `is_wk`: False (18039), null (8667), True (1675).
- `is_impact`: 0 (27823), 1 (558).
- `is_impact_off`: 0 (27823), 1 (558).

- **Ball match IDs to matches:** 867/867 distinct values matched; unmatched distinct values: 0.
- **Playing-eleven match IDs to matches:** 880/880 distinct values matched; unmatched distinct values: 0.
- **Matches competition IDs to competitions:** 138/138 distinct values matched; unmatched distinct values: 0.
- **Playing-eleven team IDs to teams:** 38/38 distinct values matched; unmatched distinct values: 0.
- **Ball `batting_team_id` to teams:** 38/38 distinct values matched; unmatched distinct values: 0.
- **Ball `bowling_team_id` to teams:** 38/38 distinct values matched; unmatched distinct values: 0.
- **Ball `striker_id` to mapping:** 888/888 distinct values matched; unmatched distinct values: 0.
- **Ball `non_striker_id` to mapping:** 867/867 distinct values matched; unmatched distinct values: 0.
- **Ball `bowler_id` to mapping:** 647/647 distinct values matched; unmatched distinct values: 0.
- Mapping player-name columns observed: `comp_name`, `team_name`, `player_name`.
- Duplicate mapping rows: **0**; duplicate ID rows: **6016**.

## Data quality findings and limitations

- All extracted CSV files were read successfully.
- `innings` numeric validity: 200999/200999 parseable; observed range 1 to 4.
- Suspicious delivery values: innings outside 1-4: 0; over IDs outside 1-20: 0; non-positive ball numbers: 0.
- `runs` suspicious numeric values: negative 0; non-numeric 0.
- `extras1_runs` suspicious numeric values: negative 0; non-numeric 0.
- `extras_2_runs` suspicious numeric values: negative 0; non-numeric 0.
- Source files were not modified. Different row counts are expected because ball-by-ball data has multiple rows per delivery, playing-eleven data has multiple rows per match/player, and mapping/team/competition tables are reference data.
- Join checks use exact observed column names and values. Competition context, composite keys, and null IDs may require domain confirmation before any correction.
- No player rankings, pressure scores, or inferred meanings for run/extra fields were calculated in this step.

## Unresolved questions

- The supplied schema should be reviewed before deciding whether similarly named run or extras columns represent runs, codes, or derived values.
- Any unmatched IDs and duplicate mappings should be investigated with the challenge owner before source data is changed.
