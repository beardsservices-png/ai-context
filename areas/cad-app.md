# Draft Studio (CAD app)

Browser drafting tool for drawing jobs to real-world scale — plan, elevation and a
3D preview from one model. Brian uses it to lay out real jobs before building them.

- **Repo:** `beardsservices-png/CAD-` (**public** — no customer names or addresses in
  drawings committed there; use a generic job name)
- **Live:** `cad-production-1828.up.railway.app` (Railway, auto-deploys on push to `main`)
- **Stack:** plain ES modules, no build step. `server.js` is a zero-dependency Node
  server that serves the app plus a small JSON storage API. Saved drawings ("Cloud
  Save" / Projects) live on a Railway volume (`DATA_DIR`).
- **Units:** world units are inches.

## Checking a deploy from a cloud session

Railway hosts are blocked by the cloud-session egress proxy (403), so the live site
and its `/api/drawings` storage **cannot be reached or written from there**. Railway
posts its build result to GitHub as a commit status, which is reachable:

```bash
curl -sS "https://api.github.com/repos/beardsservices-png/CAD-/commits/<sha>/status"
```

`pending` → building, `success` → live. A commit pushed while an earlier build is still
running can stay `pending` forever — Railway skips it and builds the newer one, which
already includes it. Check the latest commit, not the stuck one.

Consequence: a cloud session cannot drop a drawing into Brian's **Projects** list.
It ships drawings as **Examples** instead (below); Brian opens one and taps
*Cloud Save* to keep his own copy.

## Examples (how drawings get delivered)

`src/examples.js` lists prebuilt drawings; each is a JSON file in `examples/` in the
same format as a saved project. They appear under the **Examples** button. Adding a
drawing = add the JSON + one entry in `EXAMPLES`.

Current examples:
- `covered-patio-plan` — 24 ft covered patio, 2/12 shed roof, full takeoff (worked tutorial).
- `l-shaped-porch-windows` — plan of an L-shaped porch enclosure on a 37" stone wall:
  open 58" × 91" walkway at a wall corner, one front window between 3½" cedar posts,
  two windows on the 90" long side split by a double 2×4 mullion, every opening framed
  in 2×4 (flat on the cap, flat under the beam, jack each side). Windows ½" under the
  framed opening.
- `l-shaped-porch-long-side` — elevation of that long side, including the triangle
  between the beam and the rafter framed in 2×4 and glazed in two fixed-glass pieces,
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

Customer-specific details for a job (names, address, which phase, delivered files)
go in that customer's Google Drive folder, never in this repo.

## Open threads

- No way yet to save a drawing into Projects from a cloud session (proxy). A GitHub-
  based import (drawings committed to a private repo and pulled by the app) would fix it.
- The cedar trim (ripped/beveled sill, casing, stops) on the porch example is noted,
  not drawn piece by piece.
