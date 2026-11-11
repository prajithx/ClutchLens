"""Validate the Step 4F recruitment workspace data contract and routes."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dashboard.app import app
from dashboard.data_service import (
    RECRUITMENT_CONTEXT_KEY,
    RECRUITMENT_FILES,
    RECRUITMENT_REQUIRED_COLUMNS,
    _read_recruitment_csv,
    get_recruitment_data,
)


def main() -> None:
    evidence = {}
    for key in RECRUITMENT_FILES:
        frame = _read_recruitment_csv(key)
        evidence[key] = frame
        missing = RECRUITMENT_REQUIRED_COLUMNS[key].difference(frame.columns)
        assert not missing, f"{key} missing columns: {missing}"
        if key in {"batter_candidates", "bowler_candidates", "batter_classification", "bowler_classification"}:
            assert not frame[RECRUITMENT_CONTEXT_KEY].isna().any().any()
            assert not frame["context_key"].duplicated().any()

    recruitment = get_recruitment_data()
    candidates = pd.DataFrame(recruitment["candidates"])
    assert len(candidates) == 20
    assert not candidates["candidate_key"].duplicated().any()
    assert candidates["context_key"].nunique() == len(candidates)
    assert candidates["classification"].notna().all()
    assert candidates["player_id"].notna().all()
    assert len(evidence["batter_candidates"]) == len(evidence["batter_classification"]) == 10
    assert len(evidence["bowler_candidates"]) == len(evidence["bowler_classification"]) == 10

    client = app.test_client()
    expected_routes = ["/", "/analytics", "/players", "/ground", "/recruitment"]
    statuses = {route: client.get(route).status_code for route in expected_routes}
    assert all(status == 200 for status in statuses.values()), statuses
    page = client.get("/recruitment").get_data(as_text=True)
    for required_text in [
        "Evidence-led scouting workspace",
        "Shortlisted Players",
        "NOT_VERIFIED_FROM_SUPPLIED_DATA",
        "recruitment-data",
    ]:
        assert required_text in page, required_text

    script = (Path(__file__).resolve().parents[1] / "dashboard" / "static" / "js" / "main.js").read_text(encoding="utf-8")
    for required_behavior in [
        "localStorage",
        "renderComparison",
        "exportShortlist",
        "shortlist-clear",
        "Not comparable",
    ]:
        assert required_behavior in script, required_behavior
    print("Step 4F data contract, joins, page content, and route checks PASS")
    print(f"candidate_contexts={len(candidates)}")
    print(f"routes={statuses}")


if __name__ == "__main__":
    main()
