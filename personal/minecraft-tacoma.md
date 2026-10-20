# Minecraft Tacoma build (personal, 20 Oct 2026)

Brian's own black double-cab Tacoma, as a layer-by-layer Minecraft build plan.
He plays **Bedrock on PS5**, which cannot import structure files (.mcstructure)
or add-ons, so the plan is for building by hand. The only way to paste it in
would be via a PC/phone world uploaded to a Realm.

## Where it lives

- **Live page:** the claude.ai artifact *Lifted Tacoma Build*
  (https://claude.ai/artifact/N4rh1NmfzCT9GgScmvENtT, private to Brian).
- **Source:** `virtual-board-games` repo, `client/public/minecraft/tacoma.html`
  (merged to `main` 20 Oct). That repo is not deployed, so the artifact is the
  page to open. Edit the repo copy and republish the artifact together.

## Decided

- **Full blocks only.** No stairs, slabs or panes (Brian asked for simplicity);
  glass is full stained-glass blocks.
- **Build scale: 1 block = 2 inches** -> 102 long x 36 wide x 41 tall, about
  19,100 blocks hollow (~9,700 Black Concrete). Plotz-style Length/Width/Height
  sliders (40-222 long) rebuild everything; "Keep proportions" is on by default.
  For reference: 1 block = 1 inch is 204 x 72 x 83, about 94,000 blocks.
- **Matches his truck** (from his photos): chrome tube bull bar hoop with an LED
  light bar, **no front plate, no skid plate**; black mesh grille, no logo; black
  8-spoke rims with silver lip ring and chrome center cap; round silver tube
  steps; **hard** bed cover; TRD Sport decal on the bed side; hood scoop;
  flared fenders; lift.
- Hollow by default ("Skip hidden blocks"): the body is a 1-2 block shell.

## How the page works

The truck is one function, `classify(x, y, z)`, in units of about 14 cm
(37 x 15 x 13 units), sampled at whatever size the sliders give. Wall thickness
grows at small sizes so there are no holes. Grid: columns run front to back,
row 1 = passenger side. A "row by row" list writes each row as runs
("cols 14-26 B x13") for building off a TV. 3D view is three.js 0.128 from
jsDelivr with InstancedMesh.

## Next

Brian is building it at 2 inches per block. Changes he asks for are edits to
`classify()`.
