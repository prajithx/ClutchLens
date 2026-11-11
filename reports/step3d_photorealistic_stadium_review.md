# Step 3D Photorealistic Stadium Review

## Asset audit

The supplied files were initially found one level too deep at
`dashboard/static/images/stadium/stadium/`. They were moved into the exact
required directory. The nested directory was removed after it became empty.

Required local assets are still missing:

| Required slot | Expected path | Status | Licence/source |
|---|---|---|---|
| Wide stadium night | `dashboard/static/images/stadium/stadium-wide-night.jpg` | Integrated | AI-generated illustrative asset; no external licence metadata supplied |
| Stands and floodlights | `dashboard/static/images/stadium/stadium-stands-night.jpg` | Integrated | AI-generated illustrative asset; no external licence metadata supplied |
| Cricket pitch close-up | `dashboard/static/images/stadium/cricket-pitch-closeup.jpg` | Integrated | AI-generated illustrative asset; no external licence metadata supplied |
| Optional atmosphere video | `dashboard/static/images/stadium/stadium-atmosphere.mp4` | Missing | Not applicable; user must provide or approve a licensed source |

No external assets were downloaded or hotlinked. The supplied files are
AI-generated illustrative visuals, not photographs of a verified Rajasthan
Royals venue or a specifically identified real stadium.

## Integrated image metadata

| Asset | Dimensions | File size |
|---|---:|---:|
| `stadium-wide-night.jpg` | 1672 × 941 | 527,227 bytes |
| `stadium-stands-night.jpg` | 1672 × 941 | 477,722 bytes |
| `cricket-pitch-closeup.jpg` | 1672 × 941 | 456,457 bytes |

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

The result uses the supplied AI-generated illustrative image assets. It is not
claimed to depict a real venue or real match.

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

- Exact file paths exist and each file opens as a valid JPEG.
- Flask route smoke tests returned HTTP 200 for `/`, `/analytics`, `/players`,
  and `/ground`.
- Flask static asset requests returned HTTP 200 for all three image paths.
- Desktop and mobile browser checks confirmed the image layers load without
  broken-image icons or horizontal overflow.
- Scroll checks confirmed progress changes from wide stadium to stands to pitch.
- Reduced-motion checks confirmed the scroll camera remains static.

## Step 3D.1 integration notes

- Desktop uses centered wide/stands crops and a lower-centered pitch crop;
  the three 1672 × 941 assets crossfade and scale through the 300vh journey.
- Mobile uses `56%` wide, `50%` stands, and `52%` pitch horizontal positions
  so the field and pitch remain in frame. A mobile normal-motion scroll test
  loaded all three images and reported no horizontal overflow.
- Reduced-motion mode keeps the wide photographic asset stable and disables
  the camera transform and scroll listener.
- The exact command `python -m flask --app dashboard run` is supported by the
  dashboard package export.

Run the app with:

```powershell
python -m flask --app dashboard.app run
```
