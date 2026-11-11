# Step 3C Stadium Experience Review

## Scope

Step 3C rebuilds only the ClutchLens homepage. Raw datasets, processed
analysis outputs, analytics calculations, player data, and Ground Explorer
venue filtering were not changed.

## Implemented scroll stages

1. **Wide stadium reveal** — the first viewport presents an original inline SVG
   cricket stadium at night with a wide oval bowl, repeated crowd texture,
   roof and concourse rings, four floodlight towers and beams, a green oval,
   boundary rope, pitch, wickets, and a restrained ClutchLens screen.
2. **Descent through the stands** — the `.stadium-journey` section holds the
   stadium scene in a sticky viewport. `animations.js` maps scroll progress to
   a camera scale and shifts the visible depth layers without hijacking wheel
   or touch scrolling.
3. **Pitch arrival** — the camera settles on the pitch, crease and wickets.
   A restrained ball trajectory and bat-impact detail become visible near the
   end of the journey. The screen says `EVIDENCE / NOT A SCOREBOARD`; no match
   statistics are fabricated.
4. **Content emergence** — Analytics, Player Intelligence, Ground Explorer,
   and Methodology panels appear after the stadium section, followed by a
   transparency statement linking the visible claims to the supplied data.

## Responsive and accessibility behaviour

- Desktop uses a full-width stadium composition and a 310vh scroll journey.
- Tablet uses a shorter 260vh journey and a reduced camera scale.
- Mobile uses a 220vh journey, a wider cropped SVG composition, and simplified
  camera movement while retaining the recognisable bowl and pitch.
- The SVG has an accessible title and description.
- Existing keyboard focus styles remain active.
- `prefers-reduced-motion: reduce` disables scroll listeners and continuous
  animation, presents a static pitch-forward composition, and removes the
  nonessential CTA motion.
- The homepage scene is explicitly illustrative and is not presented as a
  supplied real venue.

## Validation

The following Flask routes were smoke-tested and returned HTTP 200:

- `/`
- `/analytics`
- `/players`
- `/ground`

The homepage source was checked for:

- four functional feature links;
- no fake scoreboard statistics;
- no player rankings, pressure ratings, Top 10 lists, economy rates, or shot
  coordinates;
- no changes to raw or existing analysis outputs.

## Run command

```powershell
python -m flask --app dashboard.app run
```
