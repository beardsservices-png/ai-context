---
name: song-to-studio
description: Split a song into its separate instruments and load it into Brian's BHS Studio (the Rhythm Maker / Rhythm Shop groovebox) — one track per instrument, notes you can see and edit. Two routes: a public-domain score (Bach, Mozart, hymns, folk tunes — note-perfect, the way the Bach templates were made) or a recording Brian owns (an MP3/WAV of an 80s song — AI stem separation, then audio-to-MIDI transcription). USE WHEN Brian says "separate the instruments", "split this song", "get the stems", "pull the bass line out", "make a template of <song>", "put <song> in the studio / rhythm maker / beatbox", "like we did the Bach songs", or uploads a song file and asks for its parts.
---

# Song to Studio

Brian asks in plain words; this skill picks the route. Do not ask him which tool or format.

## The words (so he knows how to ask)

| Say this | It means |
|---|---|
| **Stems** / **stem separation** (also "source separation", "demixing") | Splitting a *recording* into separate audio files: vocals, drums, bass, guitar, piano, other. Tool: Demucs (free, open source). |
| **Transcription** / **audio-to-MIDI** | Turning a recording (or one stem) into *notes*. Tool: Basic Pitch (free, open source). Good, not perfect. |
| **MIDI** | Notes as data (pitch, start, length) rather than sound. What the Studio's piano roll edits. |
| **Score** / **MusicXML** | Sheet music as a file. Exact notes, no guessing. |
| **OMR** (optical music recognition) | Reading printed / PDF sheet music into a MusicXML file. Tool: Audiveris (free). |
| **Arrangement** | One version of a song written for certain instruments, e.g. "piano/vocal/guitar". Not the same as the band's parts. |
| **Public domain** | Nobody owns it any more (composer dead 70+ years, e.g. Bach). Free to use and publish. |
| **Multitrack** | The studio's own separate recordings of each instrument. Sometimes released officially; the cleanest stems there are. |

So: *"Get the stems of this MP3 and transcribe them into the Studio"* = recording route. *"Make a Studio template of Bach's Minuet in G from the public-domain score"* = score route.

## Pick the route

1. **The piece is public domain** (classical, hymns, traditional) -> **Score route.** Look for it in the music21 corpus first (`python -c "from music21 import corpus; print(corpus.search('mozart'))"`), else a public-domain MusicXML/MIDI (IMSLP, Mutopia). Note-perfect. May become a built-in template in the app.
2. **Anything recorded after ~1930 is under copyright** (e.g. *Can't Fight This Feeling*, REO Speedwagon, 1984) -> **Recording route**, from a copy Brian owns (bought MP3, ripped CD). Never download the song or a "free MIDI" of it from the web for him. Results are **for his own practice only**: never added to the app's built-in templates, the public repo, or anything shared or sold (the Rhythm Maker repo is public, so a template there is publishing it).

## Recording route (his own copy of a song)

Needs Python 3.10+, ffmpeg, ~3 GB disk. One-time install:

```bash
python3 -m venv ~/song-venv && . ~/song-venv/bin/activate
pip install --index-url https://download.pytorch.org/whl/cpu torch torchaudio
pip install demucs librosa soundfile music21 onnxruntime pretty_midi mir_eval resampy
pip install --no-deps basic-pitch   # its pinned numpy will not build on new Python; it runs fine on the ONNX model
```

Then, with the scripts in this skill's `scripts/` folder:

```bash
python scripts/separate.py "Cant Fight This Feeling.mp3" --out work/
#   -> work/stems/{vocals,drums,bass,guitar,piano,other}.wav   (~1-3 min per song on a laptop CPU)
python scripts/transcribe.py work/
#   -> work/midi/<stem>.mid, work/drums.json, work/grid.json (tempo + beat grid)
python scripts/to_studio.py work/ --label "Can't Fight This Feeling (practice)" --out work/template.json
#   -> one Studio template: a track per instrument, 4-bar patterns, sections of 16 bars
```

What he gets, and what to tell him:
- **The stems (WAV)** are the best part: real sound, one instrument each. In the Studio, **upload each stem as an audio track** (Rec / upload) and mute or solo them — e.g. mute the piano and play it himself. Works today, no code change.
- **The MIDI / template** is the notes, guessed by a model. Expect: bass and piano good, vocals as a melody line, guitar and 80s synth pads rough, drums as kick / snare / hi-hat only. Say this plainly; he edits from there in the piano roll.
- `--model htdemucs_6s` (default) gives 6 stems incl. guitar and piano; `--model htdemucs_ft` gives 4 cleaner ones (vocals, drums, bass, other).
- Beat 1 is found automatically (kick on 1 and 3, snare on 2 and 4). If a song is the other way round and notes land a beat off, rerun `to_studio.py` with `--shift-beats 1` (2, 3). If the tempo reads double, `--half-time`; to set it yourself, `--bpm 120`.

## Score route (public domain)

```bash
python scripts/to_studio.py --score "bach/bwv846" --label "Bach: Prelude in C" --out bach.json
python scripts/to_studio.py --score minuet.musicxml --label "Minuet in G" --out minuet.json
```
`--score` takes a music21 corpus path, a MusicXML file or a MIDI file. Each part becomes a track (instrument picked from the part name; override with `--instrument "Part name=real-cello"`).

## Sheet-music route (a printed or PDF score of a modern song)

Better than the recording route when it exists: exact notes, no guessing. But:
- **Copyright is the same.** The sheet music of a 1984 song is owned just like the recording. Use a copy Brian bought; the result is his practice copy only, never a built-in template.
- **It is an arrangement, not the band.** Store-bought pop sheet music is usually "piano / vocal / guitar": a piano part, the vocal melody and chord symbols. It gives Piano + Vocal tracks, not the drummer or bass player. For a band's parts, look for a "full band transcription", "guitar tab" or "drum transcription" book.
- **File types:** MusicXML (.mxl / .musicxml) or MIDI go straight in: `python scripts/to_studio.py --score song.mxl --label "..." --out song.json`. A **PDF or photo** needs **optical music recognition (OMR)** first, which reads the printed notes into MusicXML. Free tool: Audiveris (`audiveris -batch -export -output out/ song.pdf`), or open the PDF in MuseScore and export MusicXML. OMR makes mistakes on busy pages: check the bar count and the first few bars against the paper. (This step is untested in the skill so far.)
- Chord symbols are not turned into notes yet; the piano part already plays them.

## Getting it into the Studio

The Studio has no "open a file" button yet. Two ways in:
- **Public-domain piece** -> paste the JSON into `LIST` in `public/js/engine/templates.js` (Rhythm-Maker repo) like the Bach entries, with a comment saying where it came from and that it is public domain. Test on the start screen, push.
- **Copyrighted song** -> do NOT add it to templates.js. Use the stems as audio tracks; for the notes, hand Brian `template.json` and the per-instrument `.mid` files for his own use. (If he wants this often, the right build is an "Open a song file" button in the Studio that loads a template JSON from his own computer, stored only in his browser. Offer it; it is a Rhythm-Maker change.)

## Format facts the converter follows (from templates.js)

- A track holds 4 patterns (A-D) of up to 4 bars, so 16 unique bars per track. Longer parts spill onto numbered tracks ("Piano 1", "Piano 2"), like the Bach prelude. Repeated 4-bar chunks (a chorus) reuse one pattern.
- Melodic pattern = `[step, midi, length]`, steps are sixteenths from the pattern start. Drum pattern = string, one char per sixteenth: `.` off, `x` hit, `X` accent, `o` soft.
- Section `play` = one letter per bar, `-` silent. Sections are 16 bars so every pattern starts on a 4-bar boundary.
- Instrument ids: `real-piano`, `real-epiano`, `real-ebass`, `real-upright`, `real-strings`, `real-guitar`, `real-sax`, `real-flute`, `real-cello`, `real-violin`, `real-trumpet`, ... and General MIDI `gm-*` (`gm-electric-guitar-clean`, `gm-distortion-guitar`, `gm-choir-aahs`, `gm-church-organ`, `gm-drawbar-organ`, ...). Drum roles: kick, snare, clap, hat, openhat, rim, shaker, snap, perc.

## Checks before telling Brian it's done

- Listen-check by numbers: `to_studio.py` prints bars, tracks, notes per track and BPM. A track with 0 notes or a BPM under 50 / over 200 means the grid or a stem failed; say so, don't hand it over silently.
- Score route: total bars should match the sheet music.
