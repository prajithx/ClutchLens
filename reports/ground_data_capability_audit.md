# Ground Data Capability Audit

## Verified venue fields

- `matches.csv` contains `venue_id` with **98** distinct IDs across **883** match rows.
- `matches.csv` contains `venue_country` with **17** distinct country labels.
- No stadium/ground name field is present. The UI therefore displays the exact supplied venue ID and country label, never an invented stadium name.
- `venue_match_coverage.csv` lists every venue ID/country combination, match count, date range, seasons, and formats.

## Spatial capability

- Candidate geometry/location fields found by schema audit: none.
- No supplied field contains venue coordinates, boundary dimensions, pitch dimensions, or shot landing coordinates.
- Ground diagrams are illustrative layouts only and are explicitly labelled not to scale.

## Categorical shot and delivery fields

- `stroke`: 30 non-null categories; 6,158 missing values.
- `delivery_style`: 34 non-null categories; 391 missing values.
- `on_or_off`: 2 categories; `over_or_around`: 2 categories.
- `is_four` and `is_six` are source flags suitable for descriptive counts, but they do not provide spatial locations.

## Limitations

- Venue selection is exact supplied `venue_id` plus `venue_country`, not a real stadium-name or map lookup.
- Venue-specific stroke and pace/spin distributions are descriptive row counts only.
- No shot markers, heatmap positions, stadium maps, boundary sizes, or geographic claims are generated.
