# Rhythm Shop

Two browser rhythm/pattern games, deployed and live on Railway:
- **Freeplay** — single-instrument randomized 32-step pattern generator.
- **Round Robin** — turn-based layered rhythm builder; each new layer halves in step density (32nd → whole). Includes a "Generate Section B" variation and A·A·B·A song-form auto-arrangement.

Both share an "Ask Claude" assist panel that nudges density/swing/tempo but never generates a whole beat.

- Repo: https://github.com/beardsservices-png/Rhythm-Maker (auto-deploys to Railway on push to `main`)
- Stack: zero-dependency Node static server + vanilla JS. No framework, no build step, no npm install.
- Audio: **pure Web Audio synthesis — no sample files at all.** 26 voices across 10 families, layered oscillators + filtered noise through a shared reverb send and bus compressor.
- Persistence: pattern JSON to `DATA_DIR` (Railway volume), with a localStorage fallback.

**Status: the original plan is done** — separated HTML/CSS/JS, save/load patterns, deployed to Railway with a data volume.

**What's next:** this repo is now the foundation for **BHS Studio** (see `areas/bhs-studio.md`). Rhythm Shop's two modes stay as routes. Note they both call `RhythmAudio.playVoice()` and `createScheduler()` directly, so engine changes for the DAW can break the games silently — there are no tests. Re-check both modes after any engine work.
