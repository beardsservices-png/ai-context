# Draft Studio (CAD app)

Browser drafting tool for drawing jobs to real-world scale — plan, elevation and a
3D preview from one model. Brian uses it to lay out real jobs before building them.

- **Repo:** `beardsservices-png/CAD-` (**public** — customer names are fine in drawings
  committed there, never addresses or phone numbers)
- **Live:** `cad-production-1828.up.railway.app` (Railway, auto-deploys on push to `main`)
- **Stack:** plain ES modules, no build step. `server.js` is a zero-dependency Node
  server that serves the app plus a small JSON storage API. Saved drawings ("Cloud
  Save" / Projects) live on a Railway volume (`DATA_DIR`).
- **Units:** world units are inches.

## Checking a deploy from a cloud session

**Update 2026-10-12: the live site now answers from a cloud session**, and the storage API
works too. `POST /api/drawings` with `{"name": ..., "doc": <the drawing JSON>}` saves a drawing
straight into Brian's **Projects** list (done for the Collins fence, plan and back run), so a
cloud session no longer has to leave it as an Example for him to Cloud Save. Examples are
still the way to ship a drawing with the code. The old note here, that the proxy 403s
Railway hosts, was wrong by this date.

Railway also posts its build result to GitHub as a commit status:

```bash
curl -sS "https://api.github.com/repos/beardsservices-png/CAD-/commits/<sha>/status"
```

`pending` → building, `success` → live. A commit pushed while an earlier build is still
running can stay `pending` forever — Railway skips it and builds the newer one, which
already includes it. Check the latest commit, not the stuck one.

## Examples (how drawings get delivered)

`src/examples.js` lists prebuilt drawings; each is a JSON file in `examples/` in the
same format as a saved project. They appear under the **Examples** button. Adding a
drawing = add the JSON + one entry in `EXAMPLES`.

Current examples:
- `covered-patio-plan` — 24 ft covered patio, 2/12 shed roof, full takeoff (worked tutorial).
- `collins-picket-fence-plan` / `collins-picket-fence-back` — **Collins back-yard picket fence**
  (3 ft tall), re-drawn 17 Oct to the current width: 38 ft across the back (same as the deck), 24 ft
  down each side, one 4 ft gate in the middle of the back, hand framed on 4x4 posts on driven anchors.
  Sides 4 bays of 72 in with 9 pickets; back 3 bays of 67 in each side of the gate with 8 pickets;
  gate leaf 47.5 in with 7. Pickets are 6 ft pickets cut in half, 3.5-4 in gaps (127 of 3 ft = 64 six-footers, buy 68).
  The take-off rule: pickets in a clear span L = n x 3.5 + (n+1) x gap, solved for a gap between 3.5 and 4.
- `l-shaped-porch-windows` — **Giles porch (Jesse & Doree Giles, job 112 = BHS20260627D, Phase 3; 111 is the paid Phase 2 — Porch
  Enclosure).** Plan of an L-shaped porch enclosure on a 37" stone wall:
  open 58" × 91" walkway at a wall corner, **two** front windows (stock 30×54, 29½" × 53½" actual) split by a
  single 2×4 divider between 3½" cedar posts (changed from one wide window 2026-10-04),
  **three** stock 28×54 windows (27½" × 53½" actual) on the 90" long side split by two single 2×4
  dividers (changed from two 2026-10-10, resized to stock sizes 2026-10-10),
  every opening framed
  in 2×4 (flat on the cap, flat under the beam, jack each side). Windows ½" under the
  framed opening.
- `l-shaped-porch-long-side` — Giles porch, elevation of that long side, including the triangle
  between the beam and the rafter framed in 2×4 and glazed with **one layer of ¼" clear
  plexiglass** (not tempered glass — settled 09/28; single layer from 10/15) in three pieces,
  a 2×4 mullion over each window mullion,
  its mullion aligned with the window mullion below.

## Drawing-file format notes (learned the hard way)

- Shape = `{id, type, layer, pts:[{x,y}], ...}`. Useful props: `label` (drives the
  materials list), `step` (build-step playback), `existing: true` + `locked: true`
  (ghosted reference geometry, excluded from takeoff), `material`, `fill`, `dash`.
- 3D comes from `height` (extrusion) and `elevation` (base height) on every shape.
- **Polygons need `closed: true`** or they are treated as open polylines and do not
  extrude in 3D (the sloped pieces silently vanished until this was set).
- `viewMode: "elevation"` → canvas Y is height, and **up is negative Y**
  (`z = -y` in `view3d.js`). Plan drawings: +Y is toward the viewer / front.
- `text` shapes scale with the world, so size ~5–7 reads well at porch scale; larger
  runs off the page.
- Previewing locally: `PORT=8099 node server.js`, then Playwright against
  `localhost:8099` (Chromium at `/opt/pw-browsers/chromium`) — click **Examples**,
  open the card, screenshot, then **3D View**.

## Customer-facing plan sheets

When a drawing needs to go to a customer, the pattern that worked: render clean SVG
sheets in HTML (BHS brand header, "Prepared for", no prices, notes in plain language,
"Dimensions govern — drawing not to scale" title block, sheet n of N) and print to PDF
with Chromium, landscape letter. Embed the Google Fonts as base64 — headless Chromium
did not load them from the CDN. Keep framing and glass-cut sizes off the customer copy;
those belong in Brian's own notes.

Customer contact details (address, phone) and job paperwork go in Brian's Google Drive,
never in this repo. Giles lives in the Drive folder `Giles — BHS20260627 (Jesse & Doree
Giles)`: **`Giles — Job Record (START HERE)`** is the source of truth (phases, billing,
which file is current), and `Giles_Phase3_Porch_Enclosure_Design_Notes` beside it holds
measurements, window and glass sizes and open items. If a drawing disagrees with the job
record, the drawing is wrong. The 58" opening is a **walkway, no door** — the labels say
so because a stale estimate once brought the door back.

## Customer "what to get" sheet

When the homeowner buys the materials, a one-page sheet works better than a plan set: the
elevation with each item lettered (A, B, C), and beside it what to buy, in store terms
(unit size, rough opening if asked, sheet size). Built with `plansheet.py` like the plan
set; no prices, no cut sizes — buy plexiglass as a full sheet and cut on site. Giles got one
on 2026-10-04 (5 double-hung windows — 2 front, 3 long side — one 4×8 sheet of ¼" acrylic). Send the PNG by text —
they read everything by text.

## Giles long side — how it is built (updated 2026-10-15)

- **Siding stays on (Brian, 10/15).** No siding is cut or removed. The house-end jack and the
  triangle's vertical 2×4 are shimmed and screwed **through the vinyl** into the house's corner
  framing (5" structural screws, oversized hole in the vinyl so it still slides, not crushed).
  The exterior cedar **butts in just behind the vinyl outside corner** — no J-channel, no caulk
  to the vinyl. (Supersedes "siding comes off at the house end" of 10/13.)
- **Plexiglass is one layer** of ¼" clear acrylic in cedar stops (inside stop fixed, outside
  stop nailed, glazing tape both faces, neutral-cure silicone only, setting blocks). All three
  pieces come out of one 36×72 sheet. (Supersedes two layers with an air space.)
- Single 2×4 between the long-side windows: trim both nail fins to 1" so they share the stud.
- Brian's 8-sheet build set (sill/head/jamb sections, flashing order, glazing, Home Depot list
  with SKUs and quantities) is generated per job and kept out of this repo.

## Couch drawings (14 Oct 2026) — a personal build, not a customer job

Two drawings were saved straight into **Projects** with `POST /api/drawings` (no repo change):
a side view and a plan. **Re-drawn the same day in bed orientation** (75 in head to toe) and
saved over the same two entries with `PUT /api/drawings/<id>` {name, doc}, so the Projects
list never gained duplicates. Names now read *Couch side view / plan view (bed-style, head to
toe)*. The build itself is in `areas/couch-build.md`. Lesson: when a build is described by a
sketch or a photo, confirm which dimension is head-to-toe before drawing.

What the drawing work taught about the app:

- **A tilted part can be shown in 3D.** Draw its side profile as a closed polygon in
  `viewMode: "elevation"` and set `height` to the width it spans; `elevation` shifts it
  across the width. A back leaning at 105 degrees extrudes correctly. The old note that
  only vertical extrusions work does not apply to elevation drawings.
- **Draw a mechanism to scale before recommending numbers.** The first prop design looked
  right on paper; drawn out, its tip went below the floor. A 20-line Python script that
  computes the geometry at each angle caught what the sketch did not.
- **Reference-only geometry** (`existing: true, locked: true`, `dash: "dashed"`) works well
  for "other positions" of a moving part: ghosted, never counted in the takeoff.
- **Cloud session access:** attaching this repo with *push* access was refused by the
  session's permission classifier. The repo is public, so a read-only `git clone` plus
  `POST /api/drawings` to the live site did the whole job. Adding a built-in Example
  needs a push, so ask Brian to approve push access first if it is wanted.
- **Previewing locally:** `PORT=8099 DATA_DIR=<tmp> node server.js`. In Playwright, an
  example card is opened with the button inside it:
  `.example-card:has(.p-name:text-is("<name>")) button` (clicking the title does nothing
  reliable), then **Fit**, then **3D View**.

## Open threads

- (Resolved 2026-10-12: a cloud session can POST a drawing into Projects, see above.)
- The cedar trim (ripped/beveled sill, casing, stops) on the porch example is noted,
  not drawn piece by piece.
- **BHS app link-up.** A BHS app job (`jobs` table) holds only a free-text `notes`
  field and one `photos_album_url` link — nothing for drawings, plan PDFs or design
  notes. The natural fix is a "Plans & documents" list on the job (links to the CAD
  drawing, the Drive notes doc, the PDF sent to the customer). Not built yet. Until then
  Giles Phase 3 (job 112) points nowhere in the app; its record is the Drive job record above.

## Phone layout (16 Oct 2026)

Brian draws on a phone held sideways, which is about 350 px tall. The top bar is one row that
scrolls sideways (Materials, 3D View, Fit, Panel first); the drawing's name and Undo/Redo sit in
the bottom bar; under 520 px tall the tools are two columns and the side panel starts closed and
opens over the drawing. Check any layout change at 740x360, 844x390 and 915x412 as well as desktop.
