# Step 3D Photorealistic Stadium Review

## Asset audit

No files were found under `dashboard/static/images/` before this step. The
asset directory now exists at `dashboard/static/images/stadium/` with a
placeholder `.gitkeep` only.

Required local assets are still missing:

| Required slot | Expected path | Status | Licence/source |
|---|---|---|---|
| Wide stadium night | `dashboard/static/images/stadium/stadium-wide-night.jpg` | Missing | Not applicable; user must provide or approve a licensed source |
| Stands and floodlights | `dashboard/static/images/stadium/stadium-stands-night.jpg` | Missing | Not applicable; user must provide or approve a licensed source |
| Cricket pitch close-up | `dashboard/static/images/stadium/cricket-pitch-closeup.jpg` | Missing | Not applicable; user must provide or approve a licensed source |
| Optional atmosphere video | `dashboard/static/images/stadium/stadium-atmosphere.mp4` | Missing | Not applicable; user must provide or approve a licensed source |

No external assets were downloaded, hotlinked, or represented as licensed.

## Implementation status

The homepage is now asset-ready rather than vector-based:

- The previous inline SVG stadium has been removed from the homepage.
- The scene references the three named local photographic slots with eager
  loading for the hero and lazy loading for the below-fold layers.
- Missing images are hidden on load failure and reveal a deliberate dark
  fallback rather than a CSS/SVG imitation of a photograph.
- A disclosure states that the experience is illustrative and not a
  particular supplied venue.
- The scroll journey retains wide, stands, and pitch layers. When images are
  provided, opacity, crop, scale, and camera translation are tied to the
  existing scroll progress.
- No video is enabled because no licensed local video exists.

The result is **not yet genuinely photographic** until the required assets are
provided or approved. Per the Step 3D stop point, no claim of photorealistic
completion is made.

## Preserved behaviour

- `/analytics`, `/players`, and `/ground` remain unchanged.
- Existing feature links remain functional.
- No raw data, processed analysis output, rankings, pressure ratings, or
  cricket statistics were changed.
- Reduced-motion mode disables the scroll camera and displays a static fallback
  or hero photograph if supplied.
- The layout uses responsive object positioning and does not require external
  animation libraries.

## Validation

Python route smoke tests and syntax checks should be run after assets are
provided. The local asset absence is the intentional blocker for visual
photorealism.

Run the app with:

```powershell
python -m flask --app dashboard.app run
```

Please provide the three required licensed image files (and optionally the
video) or approve a specific licensed source before the visual can be
completed.
