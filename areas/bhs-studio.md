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
- **Uploaded sample audio is not persisted.** Saving a project stores the clip
  layout and sample names, not the audio, so reloading needs the files re-added
  and re-matched by name. `SampleTimeline.relinkSample` exists for that but
  nothing calls it yet.
- **Recording a MIDI performance into the sequencer grid** is the obvious next
  MIDI step and is not built. Neither is MIDI clock sync.
- **Export can't capture live playing.** `studio-export.js` renders the written
  patterns offline; a performance played by hand isn't a pattern.

## Shipped (2026-08-29) — the rest of the DAW, and MIDI in

Everything below is on `main` and deployed. Summarised rather than itemised;
the commit log is the record.

Between 08-22 and 08-29: per-track **mixer** (volume/pan/mute/subtractive solo),
shared **reverb + tempo-synced delay** as sends, **live looper** (4 slots,
bar-quantised punch via a 30s AudioWorklet ring buffer), **sample timeline**
(4 lanes, 32 bars, drag/trim), **A/B/C/D variations per instrument** plus song
**arrangement** mode, **offline .wav export** with an analysis-driven
**mastering** pass, and **Claude as an editor** — 8 strict tools that change the
song itself rather than describing it (`studio-assist.js`, needs
`ANTHROPIC_API_KEY`, set on Railway).

### MIDI keyboard (this pass)

- `public/js/engine/midi.js` — device layer. Raw bytes → note/control/bend
  events. Knows nothing about instruments.
- `public/js/studio-midi.js` — routing + panel. A `TARGETS` registry where every
  destination is `{ noteOn(midi, velocity), noteOff(midi) }`, so re-assigning the
  keyboard is a dropdown and a fifth instrument is one entry.
- Four targets: **808 bass**, **drum pads**, **sample pads**, **pitched synth
  voices**.
- Nothing plays audio directly. The 808 goes through a `bhs:note-on` event, so
  MIDI inherits voice stealing, the slide and the on-screen key lighting up;
  drums go through `bhs:trigger-drum` onto the same mixer strip a sequenced hit
  uses. Same shape as the existing `bhs:set-drum-mute`.
- **Notes fire at `currentTime`, not scheduled ahead** — the opposite of
  everything else in the studio, on purpose. `MIDIMessageEvent.timeStamp` is in
  the `performance.now()` domain with no exact conversion to the audio clock,
  and a note played by hand has no correct time except now.
- Drum notes honour the **General MIDI map** (36 kick, 38/40 snare, 42/44 closed
  hat, 46 open hat, 39 clap, 70/82 shaker) so a pad controller works with no
  setup, falling back to six contiguous keys from C2 for a plain keyboard.
- `RhythmAudio.renderVoicePitched` — new, additive. `CATALOG` bakes each voice's
  frequency into a closure (bell_glass can only ring at 660Hz), which is right
  for a drum machine and useless for a keyboard. This maps the melodic families
  back to the synth underneath and passes the played note in. `CATALOG`,
  `playVoice` and `renderVoice` are untouched — Freeplay and Round Robin are
  unaffected, and the test asserts it.
- Also: **velocity** on the 808 (curved with a floor so soft playing doesn't
  vanish), **sustain pedal** (CC 64), and a **pitch-bend wheel** via a new
  `setBend` on the note handle — which deliberately does *not* move
  `handle.midi`, so letting the wheel go lands back on the held note.

**Browser reality, and it's worth restating because it's the thing that will
confuse Brian:** Chrome or Edge on a computer. **Safari has no Web MIDI at all,
so iPhone and iPad cannot do this** — Chrome on iOS included, since it's Safari
underneath. Firefox has it behind a permission prompt (untested). And it needs a
secure context: the Railway https URL and localhost work, **a LAN address like
`192.168.1.50:8080` silently does not**. The panel says both in plain English
rather than leaving a dead button.

**Verification:** `tests/midi.test.js` in the Rhythm-Maker repo — headless
Chromium with only `navigator.requestMIDIAccess` faked, so every byte goes
through the real parser and real routing. 30 checks, including pitch measured
off rendered audio (C2 → 65.4Hz, C3 → 130.8Hz, a +2 semitone bend landing at
73.4Hz), note-on-with-velocity-0 treated as note-off, channel filtering, a
keyboard plugged in after page load, and Freeplay/Round Robin still triggering
voices. Playwright is deliberately *not* a project dependency — it would ride
along into the Railway build for no reason.
