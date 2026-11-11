"""Validate Step 4D evidence integration and route availability."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"


def main() -> None:
    batter = pd.read_csv(OUTPUTS / "step4c_batter_classification.csv")
    bowler = pd.read_csv(OUTPUTS / "step4c_bowler_classification.csv")
    squad = pd.read_csv(OUTPUTS / "step4c_rr_squad_evidence.csv")
    external = pd.read_csv(OUTPUTS / "step4c_external_candidate_pool.csv")
    unresolved = pd.read_csv(OUTPUTS / "step4c_unresolved_status.csv")
    assert len(batter) == 10 and len(bowler) == 10
    assert len(squad) == 20 and len(external) == 16 and len(unresolved) == 0
    assert batter["classification"].value_counts().to_dict() == {
        "EXTERNAL_HISTORICAL_CANDIDATE": 8,
        "RR_REFERENCE_SEASON_PARTICIPANT": 2,
    }
    assert bowler["classification"].value_counts().to_dict() == {
        "EXTERNAL_HISTORICAL_CANDIDATE": 9,
        "RR_REFERENCE_SEASON_PARTICIPANT": 1,
    }
    assert external["player_id"].nunique() == 16
    chahal = external[external["player_id"].eq(1612)]
    assert len(chahal) == 1 and "1358:3:1612;1715:3:1612" in chahal["historical_contexts"].iloc[0]
    for frame in [batter, bowler, squad, external]:
        assert not frame.isna().any().any()
    print("Step 4D evidence validation passed.")
    print("Displayed counts: 20 squad participants, 10 batter contexts, 10 bowler contexts, 16 external player-role rows, 0 unresolved.")


if __name__ == "__main__":
    main()
