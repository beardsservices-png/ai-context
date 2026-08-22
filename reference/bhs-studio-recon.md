# BHS Studio — Recon & Architecture Report

**Repos read:** `beardsservices-png/Rhythm-Maker` @ `09c81b0` (2026-08-02) · `beardsservices-png/musicinspiration` @ `46b29c3` (2026-04-23)
**Both verified current against `origin/main`.** Every file in both repos was read in full. No code was written or changed.

---

## Headline findings

1. **Rhythm-Maker is a synthesizer, not a sampler.** There are zero audio files in either repo. Every sound is generated live from oscillators and filtered noise. This is the biggest divergence from your spec, and I think the existing choice is mostly *right* — see §5.1.
2. **The hardest correctness detail in your whole spec is already done, correctly.** `createScheduler` (`audio-engine.js:354-396`) is a textbook lookahead scheduler. Don't rebuild it. Build a transport *around* it.
3. **But the UI is wired to that scheduler wrongly**, in a way that will not survive a 128-bar timeline. This is the most important thing in this report that your spec doesn't mention (§5.3).
4. **Your looper spec cannot work as literally written.** "Hit record late, it snaps back to the bar" requires capturing audio from *before* the button press. That one fact drives the whole recording design (§5.4).
5. **No transport, no mixer, no arrangement, no recording, no export.** Roughly **25-30%** of your target architecture exists — but it's a well-chosen 25-30%.
6. **musicinspiration is thin.** ~1,000 lines of which maybe 120 are reusable. Harvest it; don't build on it.
7. **One repo, based on Rhythm-Maker.** (§6)

**Honest usefulness verdict:** Rhythm-Maker is a genuinely good foundation — better than its 1,680 lines suggest, because the ~40 lines that are hardest to get right are correct and the file structure is already clean. musicinspiration is a prototype: a good prompt, a good visual language, and one genuinely valuable 120-line chord parser, wrapped in a single 1,054-line HTML file with the API key in the browser.

---

# Part 1 — What actually exists

## 1.1 Rhythm-Maker ("Rhythm Shop")

**1,680 LOC · 16 files · all text · zero binary assets · zero npm dependencies · no build step.**

```
Rhythm-Maker/
├── server.js                    222  Node http server: static + 2 JSON APIs
├── package.json                  12  name/start only — NO dependencies block
├── railway.json                  11  NIXPACKS, `node server.js`, restart ON_FAILURE ×5
├── .gitignore                     3  node_modules/, data/, *.log
├── README.md                     48
└── public/
    ├── index.html                46  mode picker landing page
    ├── freeplay.html             53
    ├── roundrobin.html           50
    ├── css/
    │   ├── base.css              88  design tokens + shared components
    │   ├── freeplay.css          23
    │   └── roundrobin.css        14
    └── js/
        ├── audio-engine.js      407  ★ synthesis + catalog + scheduler
        ├── roundrobin.js        318  layered turn-based mode
        ├── freeplay.js          228  single-instrument 32-step mode
        ├── storage-client.js     86  server API + localStorage fallback
        ├── assist-panel.js       46  shared "Ask Claude" UI
        └── assist-client.js      25  fetch wrapper for /api/assist
```

**Structure:** properly separated — not a single HTML file. Two independent mode pages share four JS modules.

**Loading:** five plain `<script>` tags per page (`freeplay.html:47-51`). **No ES modules** — no `type="module"`, no `import`/`export`. Load order is the dependency graph.

**State management:** no framework, no store, no reactive layer. Each file is an IIFE. Exactly **four globals** are exposed: `RhythmAudio`, `RhythmStorage`, `RhythmAssist`, `initAssistPanel`.

State lives in module-scope `let` bindings (`freeplay.js:3-8`, `roundrobin.js:6-14`) and is canonical; the DOM is rebuilt wholesale from it (`innerHTML = ''` then re-append — `freeplay.js:56`, `roundrobin.js:103`). So it's *not* "globals and DOM" in the bad sense — state is single-source — but the render strategy is full-teardown, which matters later (§5.3, §8.2).

**Server (`server.js`):** zero-dependency `http` server. Static file serving with a `startsWith(ROOT)` traversal guard (`:206`), plus two APIs:
- `POST /api/assist` — Anthropic proxy, key from **env**, never sent to the browser
- `GET/POST/DELETE /api/patterns/:mode/:name` — JSON CRUD to disk

**Env config:** `PORT`, `DATA_DIR`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` (defaults `claude-sonnet-5`).

**Deployment:** Railway-ready and already deployed at `<the Railway URL>`. Degrades gracefully — without `ANTHROPIC_API_KEY` everything works except the assist panel, which returns a friendly 503 (`server.js:50-54`).

The live service config is a clean superset of the repo's `railway.json` — same builder, same start command, same restart policy, plus dashboard settings:

```json
{ "build":  { "builder": "NIXPACKS", "buildEnvironment": "V3" },
  "deploy": { "runtime": "V2", "numReplicas": 1,
              "startCommand": "node server.js",
              "sleepApplication": false,
              "multiRegionConfig": { "us-west2": { "numReplicas": 1 } },
              "restartPolicyType": "ON_FAILURE", "restartPolicyMaxRetries": 5 } }
```

Two things worth reading off it:

- **`sleepApplication: false`** — no cold starts. Right call for something you open and immediately press Play on.
- **`numReplicas: 1`** — and it must stay 1. A Railway volume attaches to a single instance; scaling to 2 would give you two containers with divergent copies of `/data`. Not a problem now, just don't reach for the replica slider later.

> ⚠️ **Go check one thing.** Volumes are configured in the Railway dashboard, not in `railway.json`, so this config can't tell me whether one is actually mounted. If no volume is attached, `DATA_DIR` falls back to `path.join(__dirname,'data')` (`server.js:11`) — **container-local disk that is wiped on every redeploy.** The README flags this as setup step 3. Save a pattern, redeploy, and see if it's still there. Everything in §5.8 assumes a real volume underneath.

## 1.2 musicinspiration ("Song Idea Explorer")

**1,186 LOC · 4 files · zero dependencies.**

```
musicinspiration/
├── song_explorer.html   1054  the entire app (313 lines CSS + ~500 lines JS, all inline)
├── server.js              98  static serve + Anthropic proxy
├── README.md              29
└── start.bat               5  Windows launcher
```

**Structure:** single self-contained HTML file. Everything inline.

**No `package.json`. No `railway.json`. No deploy config of any kind.** Hardcoded `PORT = 3333` (`server.js:7`) and it shells out to auto-open a browser on boot (`server.js:17-24, 94-98`) — a desktop affordance that would be actively wrong on Railway.

**External dependency:** Google Fonts CDN (Playfair Display, DM Sans, DM Mono — `song_explorer.html:7-9`). The only external resource in either repo.

**State:** three module-level globals (`sessionKey`, `currentIdeas`, `favorites` — `:503-505`) plus inline `onclick=` handlers written into generated HTML strings (`:669`, `:704`, `:711`). This one genuinely *is* globals-and-DOM.

**Security posture (deployment blocker):** the user types their Anthropic key into a browser field (`:336`); it's held in a JS variable and sent as an `x-api-key` header to the proxy, which forwards it (`server.js:50-64`). The proxy sets `Access-Control-Allow-Origin: *` (`:11-15`). Deployed publicly that is an **open relay to the Anthropic API**. Rhythm-Maker's server-side-key approach is strictly better and should win the merge.

*(Small mercy: the key is only in a JS variable — no `localStorage`/`sessionStorage` anywhere — so it isn't persisted. But it must be retyped every page load.)*

---

# Part 2 — How the audio actually works

## 2.1 Rhythm-Maker

**Web Audio API throughout.** No `<audio>` elements anywhere.

**Synthesis, not samples.** The only `createBufferSource` in either repo is `noiseSource()` (`audio-engine.js:67-71`), and what it plays is 1 second of `Math.random()` white noise generated at context creation (`buildNoiseBuffer`, `:47-53`). There is no `decodeAudioData`, no sample fetch, no audio asset. Verified by grep across both repos.

The design intent is stated in the file header (`:2-3`):

> *"No sample libraries, no external deps. Layered oscillators + noise + a shared reverb send so instruments sit together instead of sounding thin/chiptune."*

and advertised on the landing page (`index.html:43`): *"Web Audio synthesis only — no samples, no external libraries."*

**This matters: the existing code identified the exact same problem your spec names ("must not sound like cheap chiptune") and attacked it with a different solution.**

### The node graph — there is a real one

```
                  ┌────────────────────────────────────────────┐
  voice chain ────┤ dryBus (gain 0.85) ──────────┐              │
   (osc/noise     │                              ├─► compressor ├─► destination
    → filters     │ send gain ──► wetSend (0.16) │   (bus glue) │
    → env gain)   │              └─► convolver ──┘              │
                  └────────────────────────────────────────────┘
```

Built once in `ensureContext()` (`:17-45`):
- **Master compressor** (`:24-30`): threshold −14 dB, knee 18, ratio 3, attack 3 ms, release 150 ms
- **Dry bus** gain 0.85 (`:32-34`)
- **Reverb send** gain 0.16 → `ConvolverNode` (`:36-41`)
- **Impulse response is *generated*, not loaded** — `buildImpulse()` (`:55-65`): exponentially decaying stereo white noise, 1.4 s, decay exponent 2.2

So: **yes, there is gain staging.** Nothing connects straight to `destination` except the compressor. This is better than the spec assumes.

**`connectOut(ac, node, sendAmount)` (`:73-81`) is the single choke point** where every voice reaches the bus. One function to change for a mixer.

**A useful accident:** every synth function takes `out` as its third argument and **every one ignores it**, calling `connectOut` which hardcodes `dryBus`/`wetSend`. `playVoice` dutifully passes `dryBus` (`:351`). The seam for per-track routing is already cut — just not used.

Per-voice reverb sends are hand-tuned: kick 0.06, snare 0.18, hat 0.10, clap 0.20, tom 0.15, bass 0.08, lead 0.20, pad 0.30, bell 0.35. That's a deliberate mix decision, not a default.

`makeSaturator()` (`:83-94`) builds a `tanh` WaveShaper curve at 2× oversampling, used on bass, lead and cowbell.

### Timing — a correct lookahead scheduler

`createScheduler` (`:354-396`) is exactly the pattern your spec demands:

```js
const lookahead = 0.1;   // 100 ms
const interval  = 25;    // 25 ms tick
while (nextStepTime < ac.currentTime + lookahead) {
  onStep(currentStep, nextStepTime);          // schedules at an ABSOLUTE audio-clock time
  nextStepTime += stepDuration();
  currentStep = (currentStep + 1) % stepsPerLoop;
}
timerId = setInterval(scheduleAhead, interval);
```

Every note is scheduled against `audioContext.currentTime`, never the JS clock. **This is right and it should survive verbatim into BHS Studio.**

`stepDuration()` (`:362-366`) = `(60/bpm) / (subdivision/4)`. Both pages pass `subdivision: 8`, so **one step = one 8th note**, and 32 steps = 4 bars of 4/4. BPM is read fresh per step, so tempo changes take effect on the next step — correct behaviour.

### Pitch today: not exposed at all

`playVoice(voiceId, t)` (`:346-352`) takes **no pitch, velocity or gain argument.** Pitch is baked into each catalog entry.

### What the "3 tone variants" actually are

They are **not** three pitch shifts. They are three different *synthesis parameter presets* per family. From `CATALOG` (`:296-298`):

| Voice | Params |
|---|---|
| `kick_deep` | 140 Hz → 42 Hz over 0.36 s |
| `kick_punchy` | 180 Hz → 55 Hz over 0.22 s, + noise click |
| `kick_sub` | 90 Hz → 35 Hz over 0.45 s, no click |

**26 voices across 10 families**, 2-3 variants each: kick, snare, hihat, clap, tom, bass, lead, pad, bell, perc (`:295-331`).

Crucially, the underlying synth functions **already accept continuous frequency parameters** — `synthKick({start, end, decay})`, `synthBass({freq})`, `synthLead({freq})`, `synthBell({base})`, `synthHat({tone})`. The pitch capability is one plumbing layer away. It's the *catalog* that hardcodes them, not the synthesis.

**No velocity.** Every hit fires at full level.

## 2.2 musicinspiration

A second, much simpler engine (`:847-1030`) with its own `AudioContext` singleton (`:853-859`).

**Chord text → sound:** `parseChordTokens` (`:937`) → `chordToFreqs` (`:902`) → `playChordNow` (`:948`).

`playChordNow` stacks three layers per note — octave-down triangle (vol 0.20), root sine (0.24), octave-up sine (0.07) — with an ADSR built from gain ramps, into a per-playback master gain of 0.45 → `destination`. No reverb, no compression, no bus.

**Timing is the naive pattern your spec warns about.** `togglePlay` (`:992-1030`):

```js
function tick() {
  ...
  if (freqs.length) playChordNow(freqs, ctx, master, ctx.currentTime, secPerChord);
  playbackTimer = setTimeout(tick, secPerChord * 1000);
}
```

Each chord is scheduled at `ctx.currentTime` *at the moment the `setTimeout` fires* (`:1025-1027`). **It drifts.** This is the exact anti-pattern Rhythm-Maker avoided — the two repos disagree with each other on the single most important timing question.

Also `activeOscs` (`:973`) is appended per note per layer and only cleared on stop (`:981`) — it grows unbounded during playback (9 oscillator refs per chord held alive).

---

# Part 3 — Data structures

## 3.1 A pattern (Freeplay) — the only thing that serializes

Written at `freeplay.js:181`:

```json
{ "pattern": [true, false, false, true, "…32 booleans"],
  "voiceId": "kick_deep",
  "bpm": 110 }
```

Missing: velocity, per-step pitch, step count (32 is implied), subdivision, time signature, a name (the name is the store key), any version field.

Legacy tolerance at `freeplay.js:163` — `data.voiceId || data.instrument || 'kick_deep'` — evidence of an earlier schema that already broke once.

## 3.2 A song (Round Robin) — richer, and **not serialized at all**

There is no save button on `roundrobin.html`. In memory (`roundrobin.js:6-14`):

```js
layers = [ { voiceId, steps, cells: bool[] } ]   // max 6
sectionB = /* same shape */ | null
bpm, currentSection: 'A'|'B', songForm: bool, formIndex
const FORM = ['A','A','B','A'];
const DENSITY_STEPS = [32,16,8,4,2,1];           // layer N gets DENSITY_STEPS[N]
```

**The mode with the better data model is the one that can't be saved.** Multi-lane, A/B sections, and a song form list — that's the closest thing to an arrangement in either repo, and it's ephemeral.

Note the lanes are **variable-resolution**: layer 0 has 32 cells, layer 1 has 16, etc., and playback strides across them (`onStep`, `:191-193`: `stride = TOTAL_STEPS / layer.steps`). That's an unusual and rather elegant model — but it's a game mechanic, not a DAW model.

## 3.3 An instrument (`CATALOG` entry)

```js
{ id: 'kick_deep', family: 'kick', familyLabel: 'Kick',
  variant: 'Deep', color: 'var(--red)',
  play: (ac, t, out) => synthKick(ac, t, out, { start:140, end:42, decay:0.36 }) }
```

**`play` is a function, so the catalog is not serializable.** You cannot put an instrument definition into a project file or send it to the server. For BHS Studio this must become data-driven:

```js
{ id:'kick_deep', family:'kick', variant:'Deep', engine:'kick',
  params:{ start:140, end:42, decay:0.36 } }
```

That refactor is a prerequisite for per-instrument pitch (§5.2) *and* for saving projects that reference instruments.

## 3.4 Server storage shape

One JSON file per mode, an object keyed by pattern name (`server.js:112-128`):

```
DATA_DIR/freeplay.json   →  { "my beat": {pattern, voiceId, bpm}, "other": {…} }
```

The whole file is read, mutated and rewritten on every save (`:160-174`). Fine for 32 booleans. Not fine later (§5.8).

## 3.5 An idea (musicinspiration)

```json
{ "type":"Indie Folk", "name":"…", "chords":"Am - F - C - G",
  "key":"G major", "bpm":92, "capo":"Capo 2",
  "description":"…", "tip":"…" }
```

Never persisted. `favorites` is a JS array that vanishes on reload; the only export is clipboard text (`exportFavs`, `:825`).

**Verdict: replace the schemas, but steal two things** — the family/variant taxonomy (§4.2) and the store-per-mode server API (§4.9).

---

# Part 4 — Mapping to the target architecture

| # | Engine | Status | Rough % |
|---|---|---|---|
| 1 | Transport / clock | **Partial** — core right, abstraction absent | ~40% |
| 2 | Instrument engine | **Partial (different thing)** — synth not sampler | ~50%* |
| 3 | Pattern sequencer | **Mostly exists** | ~60% |
| 4 | Live looper | **Does not exist** | 0% |
| 5 | Arrangement / timeline | **Does not exist** | ~5% |
| 6 | Mixer | **Partial** — master only, no tracks | ~25% |
| 7 | Effects | **Partial** — primitives proven, no architecture | ~20% |
| 8 | AI ideas panel | **Exists twice, in two different forms** | ~55% |
| 9 | Persistence / export | **Persistence yes, export no** | ~60% / 0% |

\* *of a synth engine, which is not the thing you spec'd.*

### 1. Transport / clock — partial

**Have:** correct lookahead scheduling, BPM, start/stop, a step callback, tempo changes applied per-step.

**Missing:** bar/beat position model · time signature · pause distinct from stop (`stop()` resets `currentStep = 0`, `:388-393`) · loop region · subscribe/emit (a single `onStep` callback, one consumer) · `timeAtNextBar()` / `timeAtNextBeat()` · cancellation of already-scheduled notes on stop · a shared clock (two `createScheduler` instances would free-run independently).

**Evidence there's no position model:** `updateMississippi` (`freeplay.js:102-106`) computes `beat = Math.floor(step/8) % 4 + 1`. But at `subdivision: 8`, **8 steps is one bar**, not one beat. The one place in the codebase that tries to derive musical position from the step index conflates bars with beats. Nothing depends on it — but it's a clean demonstration that the only position concept is a flat step index.

### 2. Instrument / sample engine — partial, of a different thing

**Have:** 26-voice synth catalog · family + tone-variant taxonomy **exactly as your spec describes** (your spec's example "Kick → Deep / Punchy / Sub" literally matches `audio-engine.js:296-298`) · per-voice reverb sends · saturation · a real bus · noise buffer cached and reused.

**Missing:** sample loading / decode / cache (nothing) · pitch parameter (nothing) · velocity (nothing) · serializable voice definitions · per-note gain.

### 3. Pattern / step sequencer — mostly exists

**Have:** 32-step grid · click + keyboard toggle with ARIA (`freeplay.js:60-72`) · multi-lane (Round Robin) · **playback driven by the transport, not its own timer** ✓ · randomize with musical weighting (`:77-85` — downbeats 85%, offbeats 8%) · density shift · A/B section variation · save/load.

**Missing:** 16/64 step options (`const STEPS = 32` is hardcoded, `freeplay.js:3`) · per-step velocity · per-step pitch · pattern as a **named referenceable clip object** · duplicate.

### 4. Live looper — does not exist

**Zero percent.** Verified by grep across both repos: no `getUserMedia`, no `MediaRecorder`, no `AudioWorklet`, no `MediaStream`, no recording of any kind. This is the largest single build in the project.

### 5. Arrangement / timeline — does not exist

**Direct answer to your question: no, there is no arrangement concept above the pattern. Patterns are the top-level unit.**

The single gesture toward song structure is the `FORM = ['A','A','B','A']` auto-advance (`roundrobin.js:201-206`), which flips section on the last step of the loop. No timeline, no clips, no bar ruler, no drag, no copy/paste, no multi-select.

### 6. Mixer — partial

**Have:** a master bus with real gain staging, a bus compressor, and a global reverb send with per-voice send amounts.

**Missing:** everything per-track. No track objects, no per-track gain, no mute, no solo, **no `StereoPannerNode` anywhere**. All 26 voices share one `dryBus`.

**But the seam is cut:** `connectOut` (`:73-81`) is the one function every voice passes through, and every synth already accepts (and ignores) an `out` destination parameter.

### 7. Effects — partial

**Have, as fixed internal voice components:** `BiquadFilterNode` used extensively (highpass, bandpass, lowpass with Q and envelopes — `:110-111, 124, 146-148, 198-201, 218-219`) · a working `ConvolverNode` reverb with a **procedurally generated IR** · `DynamicsCompressorNode` on the master · a `tanh` WaveShaper saturator.

**Missing as user-facing insert effects:** all of it. No EQ UI, no per-track chain, **no `DelayNode` anywhere**, no bypass, no wet/dry.

**Direct answer to your IR question: no, an IR asset does not need sourcing.** `buildImpulse()` (`:55-65`) already generates one, and it's parameterisable (duration, decay). Keep it.

### 8. AI ideas panel — exists twice, and the less obvious one is more useful

**musicinspiration** — generates the *content*: 12 idea cards with `{type, name, chords, key, bpm, capo, description, tip}`. Display-only. Key in the browser. Model hardcoded client-side as `claude-sonnet-4-20250514` (`:623`) — stale.

**Rhythm-Maker** — has the right *transport for AI output*. `/api/assist` (`server.js:49-110`): key server-side from env, model env-configurable (default `claude-sonnet-5`), and critically the model returns **a constrained action list that the client applies to live state**:

```json
{ "explanation": "…",
  "actions": [ { "type":"adjust_density", "target":"hihat", "direction":"more", "amount":0.25 },
               { "type":"set_bpm", "bpm": 96 } ] }
```

applied via `applyActions` (`freeplay.js:213-226`, `roundrobin.js:280-315`), with **clamping on the way in** (`Math.min(200, Math.max(60, a.bpm))`, `freeplay.js:217`).

**So your "can an idea populate the project?" capability already exists as a pattern — it's just wired to the wrong repo's output.** The merge is: musicinspiration's prompt + Rhythm-Maker's action transport. (§5.9)

### 9. Persistence & export

**Persistence — mostly exists.** JSON save/load to a Railway volume via `DATA_DIR`, **exactly as you spec'd**, with a localStorage fallback that means it never hard-fails offline (`storage-client.js:39-83`). Full list/load/save/delete.

**Missing:** no project-level (vs pattern-level) save · no audio-blob storage · no auth on the endpoints · no locking.

**Export — zero percent.** No `OfflineAudioContext`, no WAV encoder, no export path of any kind, in either repo.

---

# Part 5 — Where the existing approach differs from your spec

*This is the section you asked me to weight most heavily. Where I think you're wrong, I say so.*

## 5.1 Samples vs synthesis — the big one

> ✅ **RESOLVED by Brian, after listening.** He likes how the instruments sound, likes the bass specifically, and explicitly doesn't need realism: *"it is just for us to make music… so it doesn't need symphony quality."* What he wants instead is **an 808 whose pitch he can move**, and **notes that sound good when played from a keyboard.**
>
> That settles this section. **Keep synthesis. Don't build a sampler — not later, probably not ever.** Everything below still explains *why* the choice is sound, but it's no longer an open question. And the thing he actually wants is the thing synthesis is *best* at and a sampler is *worst* at (§5.2).

**Recommendation: keep the synthesis engine. Add samples as a second voice type only if a specific need appears. Do not replace.**

Your spec assumes a sampler ("loads and decodes samples into `AudioBuffer`s… sample quality matters"). Rhythm-Maker went pure synthesis, deliberately, and said so in a code comment and on its landing page.

**Why it was probably built this way:** zero assets means zero licensing, zero hosting, zero egress, instant load, and a deploy that's one Node process with no CDN. Given your own constraint — *"no paid libraries, no licensing"* — samples are the **harder** constraint to satisfy, not the easier one. Cleanly-licensed good drum samples exist, but you must source them, audit the licences, host them and serve them.

**Where synthesis wins outright: pitch.** Your spec flags `playbackRate`'s duration coupling as a known tradeoff you'd have to live with. On a synth voice **that tradeoff doesn't exist** — changing an oscillator's frequency doesn't change its decay time. The problem your spec anticipates simply isn't a problem for the 26 voices that already exist.

**Where synthesis loses:** acoustic realism. You will never get a convincing real drum kit, piano, or acoustic guitar out of oscillators. The current catalog is drum-machine shaped.

**Is your spec naive here?** In one respect, yes: it assumes sound quality is a function of *having samples*. For electronic percussion it's mostly a function of envelope shaping, layering and bus glue — which is precisely what this code invested in. The 808 and 909 are synthesizers; "sounds like cheap chiptune" is not the inevitable result of synthesis, it's the result of bare unfiltered oscillators with no envelopes and no bus. This code has envelopes, filters, saturation, a reverb send and bus compression.

**The architecture that resolves it:**

```js
// Sequencer, transport and mixer stay ignorant of which kind this is.
interface Voice { trigger(ctx, time, { semitones, velocity, destination }) }
SynthVoice   // the existing 26 — params-driven
SampleVoice  // AudioBuffer + playbackRate — added when you want acoustic sounds
```

You get a third implementation free: **looper recordings are just `SampleVoice`s.**

## 5.2 The playable 808 — what Brian actually asked for

This is now the highest-value near-term feature, and it's worth being precise about it, because **"playable from a keyboard" is a bigger change than "a pitch knob per instrument slot"** — and the spec only asked for the knob.

Three specific gaps between what exists and what he described.

### (a) The 808 pitch envelope has to become *relative*, not absolute

A real 808 bass note is a sine wave with a **fast downward pitch sweep into the fundamental** — that sweep is the "thump." Today neither voice does what's needed:

| | Today | Problem |
|---|---|---|
| `synthKick` <span>`:96`</span> | `start: 140` → `end: 42` — **absolute Hz** | Play it at a different note and the sweep doesn't move with it musically |
| `synthBass` <span>`:187`</span> | a single constant `freq`, **no sweep at all** | It's a sine blip, not an 808 |

**The fix is small and it's exactly what he's asking for.** Make the sweep a *ratio above the note*:

```
end   = the note you pressed        (the fundamental — this is the pitch)
start = end × ratio                 (ratio ≈ 3–6 for the classic thump)
glide = 20–50 ms                    (fast; this is the punch)
```

Now the drop is constant in *musical* terms, and the fundamental is whatever key you hit. That's how 808s are actually programmed, and it's maybe a few hours of work. **This one change is the difference between "a kick that got pitched" and "an 808 you can play a bassline on."**

### (b) Notes must sustain while held — this is the real work

Every voice today is **fire-and-forget with a hardcoded decay**: `osc.stop(t + decay)`, and the envelope is a fixed exponential ramp down to 0.001. There is no note-off anywhere in the engine.

A keyboard needs sustain-while-held, which means:
- `trigger()` must return a **handle** with a `.release(time)` method
- the envelope splits into **attack / decay / sustain / release** instead of one ramp to zero
- the oscillator's `stop()` moves from trigger-time to release-time

**Budget 1–2 days, not half a day.** This is the honest correction to the build plan — the original "per-instrument pitch, half a day" estimate assumed one-shot triggers.

### (c) Two things that follow from (b)

- **Decay has to scale.** An 808 sub held for a bar wants 1–2 s; `synthBass` currently decays in 0.22–0.5 s. Low notes also generally want longer decay than high ones.
- **Voice allocation becomes a thing.** Once notes are held, a chord plus fast playing stacks oscillators indefinitely — today they self-terminate, which is why it's never mattered. You'll want a polyphony cap and voice stealing. Not hard, but it's real.

### Keyboard input — build the virtual one first

| Input | Support | Verdict |
|---|---|---|
| **On-screen virtual keyboard** | Everywhere | **Build this first.** Zero compatibility risk |
| **Computer QWERTY as piano** | Everywhere | Nearly free once (a) and (b) exist, and genuinely usable |
| **Physical MIDI keyboard** (Web MIDI API) | Chrome/Edge solid. **Safari does not support it.** Firefox support is more recent and may prompt for permission — verify rather than assume | A bonus, not a foundation |

Since you said *"virtual or not"*: the virtual keyboard is the one to build. Web MIDI is a nice addition in Chrome, but don't let it gate the feature.

### Why this vindicates §5.1

Everything above is cheap **because it's a synth.** On a sampler, pitching an 808 with `playbackRate` also shortens it — a low note would ring longer and a high note would clip short, exactly backwards from what you want — and sustain-while-held is impossible without loop points in the sample. **The feature Brian asked for is the one synthesis does well and sampling does badly.**

## 5.2b Pitch — don't put `playbackRate` in the engine contract

Your spec fixes the implementation as `playbackRate = 2 ** (n/12)`. That's right *for samples only*. Make the contract a **semitone offset** and let each voice type interpret it:

| Voice type | Interpretation | Duration changes? |
|---|---|---|
| Synth, tonal (bass, lead, pad, bell, tom, kick) | `freq * 2**(n/12)` | **No** |
| Synth, noise-based (hat, clap, shaker) | scale filter cutoff: `tone * 2**(n/12)` | **No** |
| Sample | `playbackRate = 2**(n/12)` | Yes — the tradeoff you named |

The noise-voice mapping already has the right knob: `synthHat` takes `tone: 8500` (`:143`), `synthPerc`'s shaker uses a 4 kHz highpass (`:282`). Pitching a hat down 5 semitones is `8500 * 2**(-5/12)`.

**Do the catalog refactor at the same time.** Right now each voice's params are hardcoded inside a closure at the call site (`:296-331`). Converting to `{engine, params}` (§3.3) makes pitch one params transform instead of 26 separate edits — and makes instruments serializable, which you need for project files anyway.

## 5.3 The scheduler is right; the UI wiring is wrong

**This is the most important correction in this report, and your spec doesn't mention it.**

`onStep(step, time)` is doing two incompatible jobs:

```js
function onStep(step, time) {
  document.querySelectorAll('.cell').forEach(c => c.classList.remove('playing')); // NOW
  ...
  if (pattern[step]) RhythmAudio.playVoice(currentVoiceId, time);                 // time = UP TO 100ms FROM NOW
}
```
*(`freeplay.js:108-116`; same shape at `roundrobin.js:183-199`)*

Two consequences:

1. **The playhead runs ahead of the sound** by up to the lookahead window. You see the highlight before you hear the hit.
2. **A full-document `querySelectorAll` runs inside the audio scheduling path**, on every step. At 110 BPM / 8ths that's ~3.7 full-document sweeps per second across a 32-cell grid today. On a 128-bar arrangement with 8 tracks it's a stall — and a stall in the scheduling path is an audio dropout, not just a dropped frame.

**The fix is standard** (it's in the same Chris Wilson "Tale of Two Clocks" article the scheduler came from) and it's about 20 lines:

- Scheduler pushes `{step, time}` onto a queue and schedules audio. Nothing else.
- A separate `requestAnimationFrame` loop pops entries whose `time <= ctx.currentTime` and updates the DOM.

Two clocks, cleanly separated. **Do this while building the transport (step 1), not later** — every UI you build before it inherits the bug.

## 5.4 Quantized punch-in requires retroactive capture

**Your looper spec can't work as literally written**, and this is the single most consequential thing in the build.

> *"Hit record slightly late, it snaps back to the bar line."*

If you start capturing when the button is pressed, the audio between the bar line and the button press **does not exist**. You cannot snap backwards to a moment you weren't recording. You could only snap *forward* (wait for the next bar), which is a completely different feel — and not the one you described.

**So the design must be:**

1. When a slot is **armed**, start capturing continuously into a rolling ring buffer. A few seconds is plenty — 2 bars at 60 BPM is 8 s, so a 10-second ring covers every supported tempo.
2. The recorder **never starts or stops on the beat.** Only the *slicing* is quantized.
3. On punch-out, compute the two bar-boundary times from the transport and **slice the ring buffer** at the corresponding sample offsets.

This is why the recording-API question (§5.5) has a clear answer.

## 5.5 `MediaRecorder` vs `AudioWorklet` — AudioWorklet, and it isn't close

Neither exists today, so there's no sunk cost either way.

**Against `MediaRecorder`:**
- It emits an **encoded container** (WebM/Opus in Chrome; support and defaults differ in Safari and Firefox). To loop it you must `decodeAudioData` it back.
- **Opus has encoder pre-skip / priming delay**, so the decoded buffer's start is offset from what you recorded, and the offset isn't reliably exposed.
- You receive chunks on a timer, not sample indices. **You cannot slice to a sample-accurate bar boundary.**
- It gives you no ring buffer, so §5.4 is impossible with it.

For "bar-accurate loop boundaries" — your stated requirement — that's disqualifying. `MediaRecorder` is the right tool for a voice memo and the wrong tool for a looper.

**For `AudioWorkletNode`:**
- `process()` delivers 128-frame blocks of `Float32`. Copy into a preallocated ring buffer and you know exactly how many frames you've seen, so a bar boundary in seconds converts to a sample index by multiplication.
- Slice → `ctx.createBuffer()` + `copyToChannel()` → done. Sample-accurate.
- **It gives you §5.4's ring buffer for free** — it's the same mechanism.

**Costs, honestly:** the worklet must be a **separate file** loaded by `audioWorklet.addModule()` — it cannot be inlined into an HTML file — served with a JS MIME type. Rhythm-Maker's server already maps `.js` correctly (`server.js:17`). Budget ~100 lines of worklet + ~150 lines of host. You don't need `SharedArrayBuffer`; `port.postMessage` with transferred `ArrayBuffer`s is fine at these rates, and `SharedArrayBuffer` would drag in COOP/COEP headers you don't want.

**Get the capture constraints right — this matters as much as the API choice:**

```js
getUserMedia({ audio: { echoCancellation: false,
                        noiseSuppression: false,
                        autoGainControl:  false } })
```

Leave those on (they default on) and the browser's voice-processing pipeline will duck, gate and smear the music **and** introduce variable latency that makes calibration impossible.

## 5.6 Latency — plan for a calibration control, not a formula

Nothing in either repo touches `baseLatency` or `outputLatency` (verified by grep).

Total round-trip = input hardware + `ctx.baseLatency` + `ctx.outputLatency` + OS buffering. **Only the middle two are readable**, and `outputLatency` is not reliably implemented in Safari — treat it as possibly `undefined` and guard.

**So:** seed an offset from `baseLatency + (outputLatency || 0)`, then expose a millisecond slider **and** a one-time automatic calibration — play a click, record it back through the mic, cross-correlate to find the true offset, store it per device. That is the only approach that actually works across machines. Budget it as a real feature, not a constant.

**And flag the usability trap in the UI:** a looper on speakers records the backing track back into the loop. Headphones aren't optional — say so on screen.

## 5.7 `DynamicsCompressorNode` is not a limiter — don't rely on it for export

Your spec: *"a limiter (`DynamicsCompressorNode` with a high ratio and fast attack) to prevent clipping on export."*

One already exists (`:24-30`) and it's well-tuned for glue. But it has **no lookahead** and will overshoot; it cannot guarantee no clipping. It's a compressor with a knee, not a brickwall limiter.

**For export the exact fix is free:** render with `OfflineAudioContext`, then scan the rendered `Float32Array` channels for the true peak and scale the whole buffer. One pass over the samples, deterministic, guaranteed.

**Go further: bypass the master compressor during offline render.** `DynamicsCompressorNode` is known to behave differently between realtime and offline rendering and across browsers, so leaving it in makes your export not match what you heard — which is worse than either option alone. Keep it in realtime for feel; bypass + peak-normalize on export.

## 5.8 Project JSON alone can't hold a DAW project once the looper exists

Your spec: *"Project save/load as JSON… to a Railway volume at `/data`."* That works today because a pattern is 32 booleans.

Once a project contains recorded loops it doesn't. Loops are megabytes of PCM; base64 in JSON inflates them ~33%, and the current store rewrites the **entire mode file on every save** (`server.js:117-128, 160-174`).

**Recommendation:** project JSON references audio by id; audio lives beside it as real files.

```
/data/projects/<projectId>.json          ← patterns, arrangement, mixer, effects
/data/audio/<projectId>/<clipId>.wav     ← looper takes, direct recordings
```

Save = write changed WAVs, then write the JSON. Export/import a project = a zip of that folder. **Small decision now, expensive migration later.**

**Also, two things to fix before this holds real work:**
- **No auth on `/api/*`.** On a public Railway URL anyone can list, read, overwrite and delete every saved pattern (`server.js:130-187`), and anyone can spend your Anthropic budget through `/api/assist` (`:49`). Put a shared secret or Basic auth in front of `/api/*`.
- **No locking** on the read-modify-write cycle. Two tabs open, and one save silently loses the other.

## 5.9 The AI integration is much closer than it looks — but the halves are in the wrong repos

**Rhythm-Maker has the right transport** (server-side key, constrained action list, `applyActions` into live state, clamped inputs).

**musicinspiration has the right content** — and, crucially, **a working chord-text parser**: `parseChordTokens` (`:937`) → `chordToFreqs` (`:902`) → `getKeyRoot` (`:943`), backed by `QUALITY_INTERVALS` (`:870-887`, 16 chord qualities). That's the piece that turns `"Am - F - C - G"` into semitone sets, and **it already works.**

**So: yes, a generated idea can populate the project, and it's roughly a day's work once a transport and a chord track exist.**
- `bpm` → `transport.setBpm()` — it's already an integer
- `key` → `project.key` — `getKeyRoot` already parses `"G major"` → `"G"`
- `chords` → chord clips — `parseChordTokens` plus a bar assignment; the existing playback already assumes 4 beats per chord (`:1007`)

**Two things to fix on the way:**

**(a) Don't trust the JSON extraction.** `raw.match(/\[[\s\S]*\]/)` (`:636`) is a greedy regex with no schema validation. Acceptable when the output fills a card the user reads; not acceptable when it **mutates project state**. Use tool-use / structured output so the shape is enforced, and validate server-side. Keep Rhythm-Maker's clamping habit.

**(b) The roman-numeral table has a real bug.** `ROMAN` (`:890-895`) uses letter case to mean **key context**, not chord quality:

```js
'I':{s:0,q:''},  'II':{s:2,q:'m'},  'III':{s:4,q:'m'}, …   // major scale
'i':{s:0,q:'m'}, 'ii':{s:2,q:'dim'},'iii':{s:3,q:''},  …   // natural minor scale
'iv':{s:5,q:'m'},'v':{s:7,q:'m'},   'vi':{s:8,q:''},   'vii':{s:10,q:''},
```

That's coherent **only if a progression is uniformly cased.** But standard notation uses case for *quality*, so the single most common progression an LLM will emit — **`I - V - vi - IV`** — resolves `vi` to `s:8, q:''`, a **major chord a minor sixth up** (A♭ in C major) instead of A minor. It will sound wrong and it will not be obvious why.

Worse, your prompt actively invites the ambiguity: it offers both formats as examples (`:596`) — *`"e.g. "Am - F - C - G" or "I - IV - V - I""`*.

**Fix:** have the model return letter-name chords in a machine field — e.g. `"bars":[{"chord":"Am","beats":4}, …]` — and keep roman parsing as a fallback only.

*(Related, lower priority: transposing a roman-numeral progression currently does nothing to playback. `transposeChordString` only rewrites letter-name tokens (`:546-553`), and `togglePlay` re-derives `keyRoot` from the untransposed `idea.key` (`:1005`).)*

## 5.10 Where your spec is right and I'd change nothing

- **Family + tone-variant taxonomy** — already built, and your spec's example matches the code line for line.
- **Lookahead scheduling** — already built, correctly.
- **Railway + `/data` volume + JSON persistence** — already built, with a graceful localStorage fallback.
- **Procedurally generated reverb IR** — already built, and better than sourcing assets.
- **No framework, no build step** — both repos prove it works, deploys stay trivial, and there's no bundler to fight. Don't add React for this.

## 5.11 One over-engineering flag: three pitch systems

"Per-step pitch offset" + "per-instrument pitch" + "chord blocks" is three pitch systems in one spec.

Per-step pitch is what turns a drum sequencer into a melodic one — a real feature — but it doubles both the pattern data model and the grid UI, and you already have a chord track for melodic content. **I'd defer it.**

**But make the data model able to accept it now.** The current `pattern: bool[]` is exactly the thing that would need a migration. Store steps as objects from day one, even if you only use `on`:

```js
steps: [ { on: true, vel: 1.0, pitch: 0 }, … ]
```

Costs nothing today; saves a migration later.

## 5.12 The UI aesthetic — the two repos disagree, and your spec sides with one

Your spec says *"dark, modern, flat — not a skeuomorphic 2005 Windows app."* Neither repo is skeuomorphic, but they're not the same language either:

| | Rhythm-Maker | musicinspiration |
|---|---|---|
| Background | `#191a17` + graph-paper grid | `#111014` flat |
| Type | Courier New + Georgia serif | DM Sans + Playfair + DM Mono |
| Corners | 2-3 px, near-square | 10-16 px |
| Feel | Letterpress / workshop | Modern flat ✓ |

**musicinspiration's shell matches your brief.** But Rhythm-Maker has something worth keeping: a **per-instrument-family colour system** (`CATALOG.color` → `--red`, `--amber`, `--teal`, `--blue`, `--violet`), which in a DAW becomes track identity — genuinely useful once you have 8 tracks on a timeline.

**Recommendation:** take musicinspiration's shell (typography, surfaces, radii, spacing) and keep Rhythm-Maker's instrument palette as the track-colour system.

---

# Part 6 — Repo strategy

## Recommendation: **one repo, based on Rhythm-Maker.**

**Why one repo:**
- **One Railway service, one volume at `/data`.** Two services means two volumes, and the ideas panel then physically cannot write into the project.
- **"Picking an idea sets BPM and drops chord clips" is a function call, not an HTTP call.** Separate repos force an API boundary around what should be `project.applyIdea(idea)`.
- **Merging deletes code.** musicinspiration's 98-line server is a strictly worse version of what Rhythm-Maker's server already does — MI puts the key in the browser and wildcards CORS on a proxy that forwards a user-supplied `x-api-key`. Adopt RM's `/api/assist` pattern; **delete MI's server entirely.**
- **Zero conflicts.** Both have zero dependencies, no build step, no bundler, no test suite.

**Why base it on Rhythm-Maker, not musicinspiration and not a fresh repo:** RM already has the working `railway.json`, the volume wiring, the correct scheduler, and separated files. MI is one 1,054-line HTML file that has to be split apart anyway. Keep RM's git history.

**Practical move — revised, now that I know `Rhythm-Maker` is the repo wired to Railway auto-deploy on push:**

**Don't rename it, and don't fork it. Keep building in `Rhythm-Maker`.** A rename would redirect the git URL fine, but it puts a working production deploy hook at risk for a cosmetic gain. The repo name is not worth a broken deploy pipeline. Rename it later, once BHS Studio is real, if you still care.

Keep Rhythm Shop's two game modes as routes — they're self-contained, they work, and they cost 2 HTML + 2 JS files.

> ⚠️ **The operational consequence you need a plan for: `main` is production.** Every push to `main` redeploys the app people can load right now. Building a DAW directly on `main` means shipping a half-finished DAW over a working Rhythm Shop, repeatedly, for weeks.
>
> **Recommendation:** do BHS Studio work on a long-lived branch and merge to `main` at milestones — after step 1 (transport), after step 4 (looper), after step 5 (timeline). And because the two apps share `audio-engine.js`, each merge is exactly when the coupling warning above bites: re-open Freeplay and Round Robin after every merge and confirm they still play. That's your regression test — there are no others.

> ⚠️ **Coupling warning.** `freeplay.js` and `roundrobin.js` both call `RhythmAudio.playVoice(voiceId, time)` and `RhythmAudio.createScheduler({...})`. Change those signatures and the games break **silently** — there are no tests. Keep `playVoice(voiceId, time)` as a one-line back-compat wrapper over `playVoice(voiceId, time, opts)`. Costs nothing; saves you from choosing between breaking the games and freezing the engine.

## Proposed merged structure

```
bhs-studio/
├── server.js                     ← RM's, extended: /api/ideas added, auth gate added
├── package.json                  ← RM's (still zero dependencies)
├── railway.json                  ← RM's
├── README.md
└── public/
    ├── index.html                ← BHS Studio (the DAW)
    ├── shop/                     ← Rhythm Shop games, kept, frozen against the engine API
    │   ├── freeplay.html
    │   └── roundrobin.html
    ├── css/
    │   ├── tokens.css            ← MI's shell + RM's instrument palette (§5.12)
    │   ├── studio.css
    │   └── shop.css
    └── js/
        ├── engine/
        │   ├── context.js        ← ★ de-singletonised: takes a ctx, doesn't create one (§7.0)
        │   ├── transport.js      ← ★ NEW: bar/beat, subscribe/emit, timeAtNextBar()
        │   ├── voices.js         ← RM's synth fns, params-driven (§3.3)
        │   ├── catalog.js        ← RM's CATALOG as DATA, not closures
        │   ├── sample-voice.js   ← NEW: AudioBuffer + playbackRate
        │   ├── mixer.js          ← NEW: Track{gain,pan,mute,solo} → master
        │   ├── effects.js        ← NEW: EQ / comp / reverb / delay inserts
        │   ├── looper.js         ← NEW: 4 slots, quantized slicing
        │   ├── recorder-worklet.js  ← NEW: served standalone (addModule requires it)
        │   └── export.js         ← NEW: OfflineAudioContext + WAV + peak normalize
        ├── ui/
        │   ├── sequencer.js      ← from freeplay.js/roundrobin.js
        │   ├── timeline.js       ← NEW: the big one
        │   ├── mixer-ui.js
        │   ├── looper-ui.js
        │   └── playhead.js       ← ★ rAF visual clock, separate from scheduling (§5.3)
        ├── ideas/
        │   ├── ideas-panel.js    ← MI's UI, extracted from the HTML
        │   ├── chords.js         ← ★ MI's chord parser — the valuable 120 lines
        │   └── apply-idea.js     ← NEW: idea → transport BPM + key + chord clips
        └── storage-client.js     ← RM's, extended for projects + audio blobs
```

**One loose end:** musicinspiration's Google Fonts CDN link is the only external resource in either repo. Fine on Railway; it's also the only thing that breaks offline. Self-host the three fonts or accept it — your call, low stakes.

---

# Part 7 — Build order

**Your instinct:** looper → pitch → timeline copy/paste → mixer → effects.

**Verdict: right about what matters, wrong about two prerequisites, and the mixer is in the wrong place.** Your ordering correctly puts the differentiating feature ahead of the polish. It's missing about 3-4 days of foundation.

### 0. De-singletonise the engine — *~half a day*
`audio-engine.js` holds `ctx`, `dryBus`, `wetSend`, `convolver`, `compressor` as **module-level singletons** (`:6-11`) created inside `ensureContext()`, and every export closes over them. This blocks two later things: **offline export** (needs a different context) and any second context. Make the engine a factory that takes a context.

Do the catalog → data refactor here too (§3.3) — it's a prerequisite for pitch *and* for serializable projects.

**Cheap now, expensive after the engine grows.**

### 1. Transport — *2-3 days*
Wrap the existing scheduler; **keep its 25 ms / 100 ms core verbatim**. Add: bar/beat/step position, time signature, play/pause/stop/seek, loop region, subscribe/emit, `timeAtNextBar()` / `timeAtNextBeat()`, cancel-scheduled-notes-on-stop. **And split the visual clock onto rAF (§5.3).**

> **Why this must be first:** the looper's punch quantize *is* `timeAtNextBar()`, and phase-correct loop resume needs an absolute song position. Build the looper first and you will invent bar math inside it and tear it out later.

### 2. Playable pitched voices — *2-3 days* — **moved up**
The 808 with a movable pitch, note-on/note-off, and a virtual keyboard (§5.2). Originally step 3 at "half a day"; **both the position and the estimate changed** once Brian confirmed this is what he wants and that it means *playable*, not just a knob.

> **Why it moved ahead of the mixer:** it's a confirmed priority, it depends only on step 0, and it's the first thing in this plan that's genuinely fun to use. Nothing downstream is blocked by doing it now.

> 🎹 **The shortcut worth knowing about:** this doesn't actually need the transport either. **Step 0 → step 2 is about 3 days to an 808 you can play**, and it doesn't conflict with the transport work that follows. If you want something enjoyable in hand before the multi-week grind, that's the path.

### 3. Mixer / routing — *1-2 days*
`Track` objects: `GainNode` + `StereoPannerNode` + mute/solo → master. Change `connectOut` to take a destination — one function — and the `out` parameter every synth already accepts becomes live.

> **Why before the looper, not after:** your own looper spec requires a per-slot volume fader. Without tracks, the four slots have nowhere to go but the shared `dryBus`.

### 4. Live looper — *1-2 weeks. The big one.*
AudioWorklet ring buffer, continuous capture, quantized slicing, phase-correct toggle, latency calibration. See §5.4-5.6. This is where the schedule risk lives.

### 5. Arrangement / timeline — *1-2 weeks*
Clips referencing patterns / audio / chords, bar snapping, and the copy-paste-duplicate-drag-extend you called out as a pain point. Requires transport (bars) and mixer (tracks). **Build the playhead on rAF from day one, and don't render 128 bars of DOM cells** — this is where §5.3 stops being theoretical.

### 6. Effects — *~1 week*
Per-track insert chains. Every primitive is already proven in-repo.

### 7. Export — *2-3 days*
`OfflineAudioContext` + WAV encode + peak normalize (§5.7). **Only possible after step 0.**

### 8. AI ideas integration — *2-3 days*
Port musicinspiration in, key server-side, structured output, wire `applyIdea` → transport + chord track (§5.9).

**Dependency chain that actually matters:** `0 → {1, 2} → 3 → 4 → 5 → {6, 7, 8}`

Steps 1 (transport) and 2 (playable voices) both depend only on step 0 and not on each other — so either can go first, and step 2 is the one that produces something playable soonest.

**Rough total: 6-10 weeks of focused work for a working v1**, with the looper the dominant risk. I don't know your available hours, so treat those durations as **relative weights, not a schedule.**

---

# Part 8 — Risks and hard parts

**1. Looper timing is the whole project's risk.** Everything else is ordinary UI work. Concrete failure mode: loops that sound in time when played solo and flam audibly when stacked. Mitigate with real calibration (§5.6), a headphones-required warning, and a test that records a click track back in and measures the offset.

**2. The render-on-every-step pattern is load-bearing and fragile.** `freeplay.js:109`, `roundrobin.js:184` — full-document `querySelectorAll` inside the audio scheduling callback. Works at 32 cells. Will not work at 128 bars, and a stall there is an audio dropout. **Must be replaced during step 1.**

**3. The singleton `AudioContext` blocks export.** `audio-engine.js:6-11`. Cheap to fix now, expensive later.

**4. iOS / Safari for the looper specifically is doubtful.** The AudioContext-needs-a-gesture rule is already handled (`ensureContext()` is called from click handlers). But iOS routes simultaneous input+output through a voice-processing path that can force a lower sample rate and impose AEC you can't fully disable; the hardware silent switch can mute Web Audio; and `outputLatency` is unreliable in Safari. **Playback, sequencing and arranging on mobile: fine. Live looping on an iPhone: plan for it not working and be pleased if it does.** Target desktop Chrome first.

**5. A timeline DAW on a phone is limited by screen real estate, not by the platform.** Rhythm Shop's grid already needs `overflow-x: auto` at 32 cells on a phone (`freeplay.css:21-23`). 128 bars on a 390 px viewport isn't a problem you can design your way out of. Plan a phone view that's transport + looper slots only, and put the arrangement on desktop.

**6. `stop()` doesn't cancel already-scheduled notes.** `audio-engine.js:388-393` clears the interval but leaves up to ~100 ms of scheduled hits to fire. Inaudible today; with a looper and 8 tracks it's a smear on every stop. Track scheduled sources and stop them.

**7. `DynamicsCompressorNode` renders differently offline than in realtime** — your export won't match what you heard if you leave it in the chain (§5.7).

**8. No auth on `/api/*` plus an Anthropic key in env on a public URL** = anyone who finds the URL spends your money (`server.js:49`). Gate it before it's public.

**9. Read-modify-write with no locking** on the pattern store (`server.js:117-128`). Two tabs, and one save silently loses the other.

**10. The roman-numeral chord bug** (§5.9b) produces wrong chords silently, for the most common progression format there is.

**11. musicinspiration's model string is stale and hardcoded client-side** — `claude-sonnet-4-20250514` (`:623`). Rhythm-Maker's env-configurable approach is right (currently defaulting to `claude-sonnet-5`).

**12. AudioWorklet and getUserMedia both require a secure context.** Railway gives you HTTPS ✓, and `http://localhost` counts as secure ✓ — **but a LAN IP does not.** Given you test the BHS app from your phone over LAN, expect the looper to fail silently in exactly that setup. You'll need HTTPS on the LAN, a tunnel, or to test the looper on the deployed URL.

---

## Where I'm uncertain

- **Sound quality — now answered, not by me.** I still haven't heard this app (egress blocked). But Brian has, and his verdict closed the question: the instruments sound good enough, the bass especially, and realism isn't wanted. That resolves §5.1 and promoted §5.2 to the top of the build order. The remaining sound question is narrower and only answerable by playing it: **does a pitched 808 still sound good two octaves down?** Very low sines get inaudible on phone speakers and very high ones get clicky — you'll likely want to cap the playable range per voice.
- **I could not reach the live deployment** (`<the Railway URL>`) — this session's network egress proxy blocks that domain, so **I have not heard this app.** The provenance question is settled though: you confirmed the repo auto-deploys on push, and I verified the source is current against `origin/main`, so the code in this report is the running app.
- **Duration estimates** are relative weights. I don't know your available hours or how much of the build is yours vs. Claude's.
- **Safari/iOS looper behaviour** is the area where my confidence is lowest — the failure modes are well-known in the field but they shift between iOS releases, and I haven't tested them here.
- **I did not read the deleted branch** `claude/rhythm-shop-railway-deploy-69zr1m` (it no longer exists on the remote). Its session summary describes deploy-skill work, not app changes, and `beardsservices-site`'s `main` contains no Rhythm Shop code — so I'm confident `Rhythm-Maker@09c81b0` is the current app, but I couldn't verify that branch directly.
