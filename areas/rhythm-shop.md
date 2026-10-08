# Rhythm Shop

Static site + zero-framework Node server, on Railway with a mounted data volume
($DATA_DIR). Repo: https://github.com/beardsservices-png/Rhythm-Maker.git

Installable as a phone/desktop app (PWA: manifest + network-first service worker,
pages open offline; iPhone = Safari → Share → Add to Home Screen).

Two surfaces:
- **Practice Mode** — learn a real instrument. Each note of a beginner song
  lights up with its fingering / key, you play it into the mic, it turns green
  when held in tune. Pitch detection is McLeod Pitch Method in
  `public/js/practice/pitch-detector.js` (DOM-free, reusable by the DAW). Built
  to add instruments — one module in `instruments/` + a line in `registry.js`.
  Modes: flute (mic, octave-agnostic), piano (mic, octave-exact), and
  "watch my hands" (beta — webcam + MediaPipe from a CDN, point at the lit key,
  silent practice). Plus an "ask a music question" helper (needs
  ANTHROPIC_API_KEY). Flute fingering chart is unverified against a method book
  (mic scores the sound, not the picture) — flagged in-repo, wants matching to a
  real method book.
- **BHS Studio** — a one-screen groovebox/DAW (redesigned Oct 2026, modelled on the
  Groovebox / Korg Gadget / FL "one pattern per instrument" workflow). Every
  instrument is a track with four patterns A–D; every drum sound is its own track.
  The **song grid** has sections across and tracks down: per section each track
  picks its letter (or silent), can mute individual bars, and can be soloed for
  that section only. Top bar = transport + Loop parts / Play song. Lower pane =
  drum machine / piano roll / waveform editor, mixer, reverb & delay. A **dock**
  pinned at the bottom holds the keyboard (or drum pads) plus the current sound's
  knobs — so drums and 808 knobs are always on screen together (Brian's main
  complaint about the old page). Instruments: 808, piano, e-piano, organ, bell,
  strings, brass, flute, pad, lead, pluck, synth bass (all synthesised). Kits:
  Trap 808, Boom Bap, House 909, Lo-Fi, Live, Classic. ● Rec records "my playing"
  (keys/pads only), the whole mix (bounce), or the mic — each take becomes an audio
  track with a waveform; uploads too, and they're now saved with the project.
  "Write notes" records keyboard playing into the pattern. Export runs through the
  mixer + effects. "Ask Claude" (`/api/studio-assist`, needs ANTHROPIC_API_KEY,
  Opus 5.5 with server-side fallback) edits tracks, sections, kits and knobs.
  Also: start screen (continue / templates Trap, Boom Bap, Lo-Fi, House, R&B,
  Blank / saved tracks), undo-redo, browser autosave incl. audio, drum accents +
  ghost notes + hi-hat rolls, swing, metronome with 1-bar count-in, key + chord
  helper in the piano roll, per-track sidechain pump.
  Old saved projects convert on open. Notes + research: `docs/studio-redesign.md`
  in the repo; browser tests: `tests/studio.test.js`.

Retired: **Freeplay** and **Round Robin** (the original 32-step pattern games),
and the old Studio page (scenes, 4-slot looper, sample timeline). `audio-engine.js`
is gone.

Next: verify/adjust flute fingerings against a real method book. A flute posture
helper (webcam) was scoped but not built. Studio ideas not built yet:
time-stretching recorded loops on tempo change, a per-track filter sweep.
