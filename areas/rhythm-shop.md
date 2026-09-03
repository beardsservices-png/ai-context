# Rhythm Shop

Static site + zero-framework Node server, on Railway with a mounted data volume
($DATA_DIR). Repo: https://github.com/beardsservices-png/Rhythm-Maker.git

Two surfaces:
- **Practice Mode** — learn a real instrument. Flute and piano so far: each note
  of a beginner song lights up with its fingering / key, you play it into the
  mic, it turns green when held in tune. Pitch detection is McLeod Pitch Method
  in `public/js/practice/pitch-detector.js` (DOM-free, reusable by the DAW).
  Built to add instruments — one module in `instruments/` + a line in
  `registry.js`. Flute fingering chart is unverified against a method book (mic
  scores the sound, not the picture) — flagged in-repo.
- **BHS Studio** — a small DAW: playable 808 bass, drum lanes, mic loop
  recording, section arrangement, mixer with shared reverb/delay, auto-master,
  offline WAV export. "Ask Claude" edits the song via tool use
  (`/api/studio-assist`, needs ANTHROPIC_API_KEY).

Retired: **Freeplay** and **Round Robin** (the original 32-step pattern games) —
removed when Practice Mode landed. `audio-engine.js` stays because Studio uses it.

Next: verify/adjust flute fingerings to a real method book; optional camera
layers (piano silent-practice hand tracking; flute posture helper) — deferred,
mic path is the priority.
