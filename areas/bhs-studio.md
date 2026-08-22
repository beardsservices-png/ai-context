# BHS Studio

Planned single-page browser DAW — Web Audio, no paid libraries, no native builds. Deploys to Railway from GitHub with a `/data` volume.

Built on top of **Rhythm Shop** (`Rhythm-Maker`) rather than from scratch, absorbing **musicinspiration** as an ideas panel.

- Foundation repo: https://github.com/beardsservices-png/Rhythm-Maker (auto-deploys on push to `main`)
- Absorbing: https://github.com/beardsservices-png/musicinspiration
- **Full recon & architecture report: [`reference/bhs-studio-recon.md`](../reference/bhs-studio-recon.md)**

## Decisions made

- **One repo, based on Rhythm-Maker.** Not a rename, not a fork — it's the repo already wired to Railway auto-deploy, and that hook isn't worth risking for a cosmetic name change.
- **Synthesis, not samples.** Rhythm Shop generates every sound from oscillators + filtered noise; there are no audio files. Brian confirmed by ear that this sounds good enough and that realism isn't wanted. No sampler is planned.
- **Keep the existing lookahead scheduler.** 25 ms tick / 100 ms lookahead against `audioContext.currentTime` — the hardest correctness detail is already right.
- **Live looper uses AudioWorklet, not MediaRecorder.** MediaRecorder's encoded output can't be sliced to a sample-accurate bar boundary.
- **`main` is production.** DAW work happens on a long-lived branch, merging at milestones, because every push to `main` redeploys the live app.

## Build order

`0` de-singletonise engine → `{1` transport `, 2` playable pitched voices `}` → `3` mixer → `4` looper → `5` timeline → `{6` effects `, 7` export `, 8` AI ideas `}`

Steps 1 and 2 depend only on step 0, not on each other. **Step 0 → 2 is ~3 days to a playable 808** and is the fastest route to something enjoyable.

## Shipped (2026-08-22)

Merged to `main` and deployed. Order: the Rhythm Shop hardening branch first
(Round Robin save/load, `/health` + `healthcheckPath`, favicon, disabled-play
guard), then BHS Studio on top.

- **Playable 808** at `/studio.html` — three-octave keyboard, mouse/QWERTY,
  slide, seven voice knobs.
- **Transport clock** — bars/beats, play/pause/stop, loop, `timeAtNextBar()`
  (the thing the looper is blocked on), and a visual clock separated from the
  audio scheduler.
- **Bassline sequencer** — 16-step mono piano roll driven by the transport,
  with per-step slide.

Volume confirmed mounted at `/data` with `DATA_DIR=/data` set.

## Open threads

- **Crash fix worth remembering:** `new URL(req.url, ...)` threw on a request
  target like `//`, and an uncaught throw in the request handler kills the Node
  process. Now answers 400. Any future route handling needs the same care —
  there is no framework catching these.
- **No auth on `/api/*`.** Unauthenticated read/write/delete on saved patterns, and an unauthenticated LLM proxy that spends the account's budget. Needs a gate before the app is meaningfully public.
- **Latency compensation for the looper** is unsolved and is the project's main technical risk.
- **Web MIDI is Chrome/Edge only** (no Safari) — the virtual on-screen keyboard is the one to build first.
