# Step 4F UI Correction: Shortlist Visibility

## Correction made

The original shortlist was functional but positioned below the full candidate
grid, making it difficult to discover. Candidate profiles also lacked a direct
shortlist action. The existing recruitment workspace was corrected without
changing source data or prior audit outputs.

## Visible changes

- Added a prominent, sticky **Shortlisted Players** command bar immediately
  below the recruitment evidence overview.
- Added live selected, batter, and bowler counts to the command bar.
- Added a visible **View shortlist** action that scrolls directly to the
  shortlist workspace.
- Renamed and strengthened the lower workspace as **Shortlisted Players /
  Human-reviewed working shortlist**.
- Grouped selected records into **Batters**, **Bowlers**, and
  **Unknown / not inferred** sections.
- Added team, competition, season, role, classification, and evidence-gate
  context to each shortlisted record.
- Added **Open profile** and **Remove** actions within the shortlist.
- Added **Add to shortlist / Remove from shortlist** directly inside the
  candidate detail profile.
- Preserved exact contextual candidate keys and browser-local persistence.

## Actual browser validation

Tested against a fresh Flask server at `http://127.0.0.1:5010/recruitment`.

- Recruitment page visibly rendered the new shortlist command bar.
- Initial shortlist count was zero.
- Added one batter and one bowler:
  - dock count: `2`
  - batter count: `1`
  - bowler count: `1`
  - visible shortlist rows: `2`
  - groups: `Batters 1`, `Bowlers 1`
- Refreshed the page and restored both exact localStorage contextual keys.
- Clicking an already shortlisted candidate changed it to the remove state
  without creating a duplicate record.
- Removed one candidate and observed the count/list update.
- Cancelled the clear confirmation and verified both records remained.
- Accepted the clear confirmation and verified the count returned to zero.
- Opened a candidate profile and used its direct shortlist action; the detail
  button changed from `Add to shortlist` to `Remove from shortlist` and the
  dock count updated immediately.
- The existing combined filter/search and comparison interactions remained
  wired.
- Mobile viewport at 390px CSS width: `scrollWidth == clientWidth`; no
  horizontal overflow.

## Automated validation

```powershell
python src\validate_step4f_recruitment_intelligence.py
python -m py_compile dashboard\data_service.py dashboard\app.py src\validate_step4f_recruitment_intelligence.py
```

Results:

```text
Step 4F data contract, joins, page content, and route checks PASS
candidate_contexts=20
routes={'/': 200, '/analytics': 200, '/players': 200, '/ground': 200, '/recruitment': 200}
python syntax=PASS
```

## Integrity and limitations

- Raw datasets were not modified.
- Step 4A–4E artifacts were not modified.
- Shortlist state is local to the current browser and is not shared across
  users or devices.
- The shortlist is a human review workspace, not a recommendation, ranking,
  auction list, or availability confirmation.
