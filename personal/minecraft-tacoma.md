# Minecraft tools (personal, 20 Oct 2026)

Brian's own black double-cab Tacoma, as a layer-by-layer Minecraft build plan.
He plays **Bedrock on PS5**, which cannot import structure files (.mcstructure)
or add-ons, so the plan is for building by hand. The only way to paste it in
would be via a PC/phone world uploaded to a Realm.

## Where it lives (moved 20 Oct)

All of Brian's Minecraft tools are together in the **`vrlike`** repo, `tools/`:

- `tools/mc-track-plotter/`: MC Track Plotter (rail/coaster planner with `/setblock`
  output), built in an earlier session. **Check here before building a new Minecraft tool.**
- `tools/mc-builder/`: this build planner. Live copy: claude.ai artifact
  *Lifted Tacoma Build* (https://claude.ai/artifact/N4rh1NmfzCT9GgScmvENtT).
- `tools/mc-commands/`: Bedrock Command Guide for PS5 (syntax, copyable examples,
  command-block recipes, command-only blocks). Live copy: claude.ai artifact
  *Bedrock Command Guide* (https://claude.ai/artifact/Jg2ZK9nHkyVzkv5LFSoe5V).

Edit the repo copy and republish the artifact together (the repo copy has its own
`<!doctype>`/`<head>`; the artifact file does not). It used to live in
`virtual-board-games`; that copy was removed.

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

## Added 20 Oct (Brian plays creative, so block counts are folded away)

- **TV build mode:** one row at a time, full screen, big blocks and run list,
  Done / Back / Skip; finished rows are remembered per build and size.
- **Starting block:** col 1, row 1, layer 1 (truck: front, passenger-side
  corner on the ground), shown as a red post in 3D and a red square on layer 1.
  Enter its in-game X/Y/Z and which way columns and rows run; every row then
  shows game coordinates.
- **My builds:** the Tacoma plus pictures turned into builds ("From a
  picture": upright wall or flat, width up to 256, 1-8 thick, palettes concrete
  / concrete+wool / all color blocks). Pictures are saved in that browser only
  (localStorage), not on GitHub. Brian wants more models later: new 3D models
  are another `classify`-style function added as a built-in build.

## How the page works

The truck is one function, `classify(x, y, z)`, in units of about 14 cm
(37 x 15 x 13 units), sampled at whatever size the sliders give. Wall thickness
grows at small sizes so there are no holes. Grid: columns run front to back,
row 1 = passenger side. A "row by row" list writes each row as runs
("cols 14-26 B x13") for building off a TV. 3D view is three.js 0.128 from
jsDelivr with InstancedMesh.

## Draft Studio -> Minecraft (20 Oct)

The builder reads Draft Studio's **STL/OBJ** export (millimeters, z up; walls are
open-bottomed boxes, which is fine). Pick a scale (1 block = 1, 2, 3, 4, 6 in,
1 ft or 1 m) and one block type; it voxelizes the surface, then flood-fills the
outside air from the sides and top (not below), so anything enclosed comes out
solid and "Skip hidden blocks" turns it back into a shell. Max 400 per side /
6 million cells. CAD x -> column, CAD y -> row, CAD z -> layer. PNG export also
works, as flat pixel art. One block type per model for now (STL has no colours).

## Built-in examples (20 Oct)

- **Frozen Caldera** (Brian's idea): 128 x 128, up to 56 tall. A ring of icy peaks
  (snow caps, packed-ice cliffs, bare stone on steep faces, deepslate base) around
  a sunken crater with a blue-ice lake and a small snowy island. Generated from
  seeded value noise (`genCaldera`), so it is the same every time.
- **Caldera Watchtower** (Claude's pick): 17 x 17 x 44 round stone-brick tower,
  plank floors every 8 layers, glass windows, battlement, glowstone beacon under
  a spruce roof (`genTower`). Sized for the caldera island's center at layer 13.
- **Wicked Ice Dragon** (Brian's request, then made 3x): 120 wide x 126 deep x 198 tall
  (designed in 40 x 42 x 66 units, sampled at 3 blocks each; about 75,000 blocks hollow,
  ~9 s to generate). 3x added ringed eyes, brow spikes, ridged horns, rows of teeth on dark
  gums, a frill, chin spikes, wing finger bones and scale rows. Perched
  statue, no legs (fused into a deepslate/stone base Brian blends into his mountain),
  wings folded, tail curled round the front. The head is drawn 1.5x so the face reads
  from the ground: Shroomlight eyes with black slit pupils, Polished Deepslate brows,
  horns, cheek spikes and spines, Quartz fangs, Sea Lantern throat, Packed/Blue Ice
  scales, Snow Block belly plates. Faces row 1. For one of the two open sides of
  Brian's caldera world (spire on one side, open palm with beams opposite); the
  watchtower/caldera examples were not needed, he has his own.
- New built-ins go in the `BUILTIN` table in the page: name, generator, notes.

## Commands

Brian plays creative with cheats available and didn't know commands could place
blocks (he had been placing stone under his feet while running, which is what led
to the plotter). With the starting block filled in, the builder's TV mode shows a
ready `/fill` command (or `/setblock` for one block) for every run.

## Next

Brian is building it at 2 inches per block. Changes he asks for are edits to
`classify()`.
