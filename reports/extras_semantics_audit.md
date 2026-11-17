# Extras Semantics Audit

This is an evidence audit. No field is assigned a run meaning unless the observed relationships support it.

## Distinct values and frequencies

### `extras_type`

```text
extras_type
Overstep       576
Penalty          1
byes           529
legbyes       2748
other          264
wide          7714
NaN         189167
```

### `extras1_runs`

```text
extras1_runs
0    189167
1     10672
2       458
3        47
4       381
5       274
```

### `extras_2_runs`

```text
extras_2_runs
0    200963
1        20
4        16
```

### `runs`

```text
runs
0    79387
1    72267
2    12547
3      656
4    23303
5       25
6    12814
```

## Cross-tab and representative evidence

The following table shows the dominant combinations. The one-to-one mapping between `extras_type` and `extras1_runs` is evidence that `extras1_runs` is a category/code field, not a delivered run count.

```text
extras_type  extras1_runs  extras_2_runs  runs  rows
        NaN             0              0     1 72043
        NaN             0              0     0 68027
        NaN             0              0     4 23180
        NaN             0              0     6 12741
        NaN             0              0     2 12496
       wide             1              0     0  7107
    legbyes             1              0     0  2376
        NaN             0              0     3   653
       byes             1              0     0   348
       wide             2              0     0   296
       wide             5              0     0   270
    legbyes             4              0     0   237
   Overstep             1              0     0   218
   Overstep             1              0     1   174
       byes             4              0     0   142
    legbyes             2              0     0   127
      other             1              0     0   114
   Overstep             1              0     4    81
      other             1              0     1    49
   Overstep             1              0     6    47
      other             1              0     4    42
       wide             3              0     0    39
       byes             2              0     0    35
   Overstep             1              0     2    33
      other             1              0     6    26
        NaN             0              0     5    25
      other             1              0     2    18
   Overstep             1              1     0    12
   Overstep             1              4     0     9
      other             1              4     0     7
      other             1              1     0     7
    legbyes             3              0     0     5
       byes             3              0     0     3
   Overstep             1              0     3     2
    legbyes             5              0     0     2
       wide             4              0     0     2
    Penalty             5              0     0     1
       byes             5              0     0     1
      other             1              0     3     1
    legbyes             0              0     1     1
```

| extras_type | rows | runs values | extras_2_runs values |
|---|---:|---|---|
| <NULL> | 189167 | [0, 1, 2, 3, 4, 5, 6] | [0, 1] |
| Overstep | 576 | [0, 1, 2, 3, 4, 6] | [0, 1, 4] |
| Penalty | 1 | [0] | [0] |
| byes | 529 | [0] | [0] |
| legbyes | 2748 | [0, 1] | [0] |
| other | 264 | [0, 1, 2, 3, 4, 6] | [0, 1, 4] |
| wide | 7714 | [0] | [0] |

## Interpretations and confidence

- **`extras1_runs`: numeric extras evidence — medium confidence.** In the updated file it is 0 on ordinary deliveries and takes positive values on labeled extras, but the schema does not define whether it is a complete extras total. It is not added to score reconstruction.
- **`runs`: likely batter runs — medium confidence.** On null-extra deliveries it takes cricket-like batter-run values 0, 1, 2, 3, 4, 5, and 6; on wide and byes it is always 0; on Overstep/`other` it can be 0, 1, 2, 3, 4, or 6. The supplied files do not label it explicitly as batter runs.
- **`extras_2_runs`: likely an additional numeric extra component — low/medium confidence.** It is 0 on 200,963 of 200,999 rows and non-zero on 36 rows, occurring in Overstep, `other`, and one null-extra row. The files do not define whether it is total extra runs, a second code, or a derived component.
- **Total team runs: unresolved from supplied files alone.** `runs + extras_2_runs + one base run for every non-null extra` is a plausible hypothesis, but it does not reproduce every result margin and cannot be proven from a score-total column.
- **Bowler-conceded runs: unresolved.** Byes, legbyes, penalty, and the unclear Overstep/`other` encoding prevent a reliable bowler-runs definition from this pack alone.

Representative rows were sampled by `extras_type` in the independent calculations. The full raw CSV remains unchanged.
