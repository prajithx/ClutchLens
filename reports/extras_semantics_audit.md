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
1       576
2      7714
3      2748
4       529
5       264
6    189167
7         1
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
        NaN             6              0     1 72043
        NaN             6              0     0 68028
        NaN             6              0     4 23180
        NaN             6              0     6 12741
        NaN             6              0     2 12496
       wide             2              0     0  7714
    legbyes             3              0     0  2747
        NaN             6              0     3   653
       byes             4              0     0   529
   Overstep             1              0     0   218
   Overstep             1              0     1   174
      other             5              0     0   114
   Overstep             1              0     4    81
      other             5              0     1    49
   Overstep             1              0     6    47
      other             5              0     4    42
   Overstep             1              0     2    33
      other             5              0     6    26
        NaN             6              0     5    25
      other             5              0     2    18
   Overstep             1              1     0    12
   Overstep             1              4     0     9
      other             5              1     0     7
      other             5              4     0     7
   Overstep             1              0     3     2
    legbyes             3              0     1     1
    Penalty             7              0     0     1
      other             5              0     3     1
        NaN             6              1     0     1
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

- **`extras1_runs`: category/code only — high confidence.** Its values map exactly to observed labels: null=6, Overstep=1, wide=2, legbyes=3, byes=4, other=5, Penalty=7. It must not be added to a score.
- **`runs`: likely batter runs — medium confidence.** On null-extra deliveries it takes cricket-like batter-run values 0, 1, 2, 3, 4, 5, and 6; on wide and byes it is always 0; on Overstep/`other` it can be 0, 1, 2, 3, 4, or 6. The supplied files do not label it explicitly as batter runs.
- **`extras_2_runs`: likely an additional numeric extra component — low/medium confidence.** It is 0 on 200,963 of 200,999 rows, with 36 non-zero rows: 21 Overstep rows, 14 `other` rows, and one null-extra row. The files do not define whether it is total extra runs, a second code, or a derived component.
- **Total team runs: unresolved from supplied files alone.** `runs + extras_2_runs + one base run for every non-null extra` is a plausible hypothesis, but it does not reproduce every result margin and cannot be proven from a score-total column.
- **Bowler-conceded runs: unresolved.** Byes, legbyes, penalty, and the unclear Overstep/`other` encoding prevent a reliable bowler-runs definition from this pack alone.

Representative rows were sampled by `extras_type` in the independent calculations. The full raw CSV remains unchanged.
