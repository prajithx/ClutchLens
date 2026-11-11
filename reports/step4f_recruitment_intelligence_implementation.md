# Step 4F Recruitment Intelligence Implementation

## Scope and decision boundaries

Step 4F improves the existing `/recruitment` page into a transparent,
human-reviewed scouting workspace. It does not create rankings, scores,
recommendations, auction picks, or auction-availability claims. Step 4E
limitations remain binding.

## Files changed

- `dashboard/data_service.py`
  - Added explicit contextual-key validation for recruitment source files.
  - Rejects null/blank required fields and duplicate `context_key` values.
  - Preserves one-to-one Step 4B-to-Step 4C joins.
  - Adds traceable context identity, source lineage, role status, gate summary,
    supported metrics, unavailable metrics, and player-context counts.
  - Adds comparison metric definitions and dynamic overview counts.
- `dashboard/templates/recruitment.html`
  - Reworked the existing page into discovery, detail, comparison, and
    working-shortlist sections.
- `dashboard/static/js/main.js`
  - Added combined search/filter behavior, detail rendering, same-role
    comparison, browser-local shortlist handling, CSV export, print action,
    stale-ID filtering, and clear confirmation.
- `dashboard/static/css/style.css`
  - Added workspace controls, evidence tables, detail/comparison/shortlist
    styling, print rules, and responsive overflow protections.
- `README.md`
  - Added the Step 4F validation command and documented workspace behavior.
- `src/validate_step4f_recruitment_intelligence.py`
  - Added reproducible data-contract, join, page-content, route, and
    client-behavior wiring checks.

## Data sources and exact keys

The page reads only existing supplied outputs and source files:

- `outputs/step4b_batter_candidates.csv`
- `outputs/step4b_bowler_candidates.csv`
- `outputs/step4c_batter_classification.csv`
- `outputs/step4c_bowler_classification.csv`
- `outputs/step4c_rr_squad_evidence.csv`
- `outputs/step4c_external_candidate_pool.csv`
- `outputs/step4c_unresolved_status.csv`
- `data/raw/matches.csv`
- `data/raw/competitions.csv`

Candidate evidence and classification are joined by `context_key` with
`validate="one_to_one"`. The contextual identity is preserved as the exact
`(comp_id, team_id, player_id)` key. The UI also exposes the generated
`candidate_key`, which is `role:context_key`, so batter and bowler contexts
cannot collide.

## Features implemented

### Discovery

- Supplied-name search.
- Classification filter for RR reference-season participant, external
  historical candidate, and unresolved.
- Role filter for batter, bowler, and unknown/not inferred.
- Evidence-status filter using the actual Step 4B label.
- Reset filters action and useful empty state.
- Dynamic counts sourced from the loaded data, distinguishing contextual rows
  from unique supplied player IDs.

### Evidence detail

Each detail profile preserves the competition/team/player/season context and
shows:

- role status and role basis;
- RR classification and evidence confidence;
- Step 4B evidence gate summary;
- supported descriptive metrics with units, source basis, and caveats;
- unavailable metrics with the specific Step 4E limitation;
- all historical contexts for the same supplied player ID;
- explicit `NOT_VERIFIED_FROM_SUPPLIED_DATA` auction status.

No player photo, team branding, score, rank, rating, or recommendation was
added.

### Comparison

- Users can select two or more candidate contexts.
- Batter and bowler contexts cannot be compared together.
- Same-role comparisons use only fixed Step 4B descriptive fields whose
  definitions are supplied in the data-service contract.
- Each displayed field includes unit, source basis, sample context, and caveat.
- Competition/format/season differences are disclosed.
- No sorting, winner, normalized rate, hidden score, or recommendation is
  produced.

### Human-reviewed working shortlist

- Users can add and remove exact candidate contexts.
- Duplicate additions are prevented by `candidate_key`.
- Counts are shown for selected contexts; context identity is retained.
- Clearing requires confirmation.
- Persistence is browser-local in `localStorage` under
  `clutchlens:working-shortlist:v1`.
- Stored IDs are checked against the current candidate set; stale IDs are
  discarded safely. No sensitive data is stored.
- CSV export contains only visible verified source fields and caveat/status
  labels. Print uses the browser print dialog and hides discovery-only
  sections.

## Supported and unavailable metrics

Supported descriptively:

- Batter conditional observed runs, eligible deliveries, source boundary
  events, and sample coverage.
- Bowler legal balls, conservative dot events, candidate dismissal events by
  type, and sample coverage.
- Competition/team/season context, RR classification, and evidence-gate
  fields.

Unavailable or unsafe for ranking:

- batting average;
- official strike rate;
- verified dot-ball percentage;
- validated psychological pressure performance;
- bowler-conceded runs and economy;
- official wicket totals;
- auction availability, retention/release, contract, budget, overseas-slot,
  squad-gap, or 2027 eligibility fields.

## Candidate-context versus player-level handling

The primary discovery population is 20 contextual candidate rows: 10 batter
and 10 bowler contexts. A player-level count is displayed separately for
orientation only. Historical contexts for a repeated player remain separate
in detail view and shortlist storage. The UI does not calculate player-level
totals across contexts or use player name as an identifier.

## Validation performed

Commands run:

```powershell
python src\validate_step4f_recruitment_intelligence.py
python -m py_compile dashboard\data_service.py dashboard\app.py src\validate_step4f_recruitment_intelligence.py
```

Actual result:

```text
Step 4F data contract, joins, page content, and route checks PASS
candidate_contexts=20
routes={'/': 200, '/analytics': 200, '/players': 200, '/ground': 200, '/recruitment': 200}
python syntax=PASS
```

Browser checks against a fresh local Flask server on port 5010:

- 20 candidate cards rendered and all workspace controls were present.
- Combined bowler + external + `chahal` search returned 2 contextual rows.
- Opening a Yuzvendra Chahal context displayed 2 preserved historical contexts.
- Mixed batter/bowler comparison displayed the explicit “Not comparable”
  limitation.
- Shortlist add/remove behavior changed counts from 2 to 1 and persisted the
  exact contextual key in browser-local storage.
- Clear confirmation removed the stored shortlist.
- Desktop viewport had no horizontal overflow.
- Mobile viewport at 390px CSS width had `scrollWidth == clientWidth` after
  responsive fixes.
- CSV export and print controls were present and wired to verified-field
  actions.

Protected-state checks:

- Raw data files were not edited.
- Step 4E reports and outputs were not edited.
- No ranking or auction-availability claim was introduced.

## Remaining issues and risks

- Browser-local shortlist persistence is intentionally device/browser scoped;
  it is not shared across analysts or accounts.
- CSV export is a client-side download and is not a server-side audit record.
- Comparison remains descriptive because cross-season, cross-format and
  conditional metric semantics remain limited.
- Official recruitment decisions still require authoritative auction,
  contract, role, squad-need, and availability data.

## Recommendation

Human-review the Step 4F workspace and data contract before any next-phase
analytics or player-intelligence redesign. Do not implement Top 10 rankings or
auction recommendations until the unresolved data contracts identified in
Step 4E are supplied and approved.
