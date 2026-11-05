"""Build a BHS Studio template (the format in Rhythm-Maker's templates.js).

Recording route (after separate.py + transcribe.py):
    python to_studio.py work/ --label "Song (practice)" --out work/template.json
Score route (public domain, note-perfect):
    python to_studio.py --score bach/bwv846 --label "Bach: Prelude in C" --out bach.json
    (--score takes a music21 corpus path, a MusicXML file or a MIDI file)

Options: --shift-beats N (move the grid), --half-time (tempo read double),
--instrument "Name=real-cello" (repeatable), --id, --blurb.
"""
import argparse
import json
import re
import sys
from pathlib import Path

PAT_BARS = 4            # bars per pattern (a track holds A-D)
SEC_BARS = 16           # bars per section, a multiple of PAT_BARS
STEPS_BAR = 16
PAT_STEPS = PAT_BARS * STEPS_BAR
LETTERS = "ABCD"

STEM_INSTRUMENT = {
    "bass": ("Bass", "real-ebass"),
    "piano": ("Piano", "real-piano"),
    "guitar": ("Guitar", "gm-electric-guitar-clean"),
    "vocals": ("Vocal melody", "real-sax"),
    "other": ("Keys & synths", "real-strings"),
}
# Score route: first keyword found in a part's name picks the sound.
NAME_INSTRUMENT = [
    ("soprano", "gm-choir-aahs"), ("alto", "gm-choir-aahs"), ("tenor", "gm-church-organ"),
    ("organ", "gm-church-organ"), ("violoncello", "real-cello"), ("cello", "real-cello"),
    ("viola", "real-strings"), ("violin", "real-violin"), ("contrabass", "real-upright"),
    ("bass", "real-cello"), ("flute", "real-flute"), ("trumpet", "real-trumpet"),
    ("horn", "real-horn"), ("trombone", "real-trombone"), ("sax", "real-sax"),
    ("harp", "real-harp"), ("guitar", "real-guitar"), ("piano", "real-piano"),
    ("keyboard", "real-piano"), ("voice", "gm-choir-aahs"), ("choir", "gm-choir-aahs"),
]
PITCH_CLASS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


# ---------------------------------------------------------------- readers
def read_recording(work: Path, shift_beats: float, half_time: bool):
    import numpy as np
    import pretty_midi

    grid = json.loads((work / "grid.json").read_text())
    beats = np.array(grid["beats"])
    bpm = grid["bpm"]
    if half_time:
        beats, bpm = beats[::2], bpm / 2
    spb = float(np.median(np.diff(beats)))
    # The beat finder often misses the first beat or two: extend the grid back to the start.
    lead = int(beats[0] // spb)
    if lead:
        beats = np.concatenate([beats[0] - spb * np.arange(lead, 0, -1), beats])
    idx = np.arange(len(beats), dtype=float)
    hits_raw = json.loads((work / "drums.json").read_text()) if (work / "drums.json").exists() else []
    if shift_beats is None:
        shift_beats = downbeat_shift(hits_raw, beats, idx)

    def to_step(t):
        if t < beats[0]:
            b = (t - beats[0]) / spb
        elif t > beats[-1]:
            b = idx[-1] + (t - beats[-1]) / spb
        else:
            b = float(np.interp(t, beats, idx))
        return int(round((b + shift_beats) * 4))

    parts = []
    for stem, (name, inst) in STEM_INSTRUMENT.items():
        f = work / "midi" / f"{stem}.mid"
        if not f.exists():
            continue
        pm = pretty_midi.PrettyMIDI(str(f))
        notes = []
        for ins in pm.instruments:
            for n in ins.notes:
                s, e = to_step(n.start), to_step(n.end)
                if s < 0:
                    continue
                notes.append((s, int(n.pitch), max(1, e - s)))
        if stem in ("vocals", "bass"):
            notes = monophonic(notes)
        parts.append({"name": name, "instrument": inst, "notes": sorted(set(notes))})

    drums = []
    df = work / "drums.json"
    if df.exists():
        roles = {"kick": "Kick", "snare": "Snare", "hat": "Hi-hat"}
        hits = hits_raw
        for role, name in roles.items():
            steps = {}
            for h in hits:
                if h["role"] != role:
                    continue
                s = to_step(h["t"])
                if s >= 0:
                    steps[s] = max(steps.get(s, 0), h["v"])
            if steps:
                drums.append({"name": name, "role": role,
                              "hits": {s: ("X" if v >= 0.9 else "o" if v < 0.5 else "x") for s, v in steps.items()}})
    key = guess_key([n for p in parts for n in p["notes"]])
    return parts, drums, round(bpm), key


def downbeat_shift(hits, beats, idx):
    """Which beat is beat 1? Rock and pop put the kick on 1 and 3 and the snare on 2 and 4:
    try each of the four phases and keep the one that fits best."""
    import numpy as np
    if not hits:
        return 0
    best = (-1, 0)
    for k in range(4):
        score = 0
        for h in hits:
            b = float(np.interp(h["t"], beats, idx)) + k
            if abs(b - round(b)) > 0.2:
                continue
            pos = int(round(b)) % 4
            if h["role"] == "kick":
                score += 2 if pos == 0 else 1 if pos == 2 else 0
            elif h["role"] == "snare":
                score += 1 if pos in (1, 3) else 0
        if score > best[0]:
            best = (score, k)
    k = best[1]
    print(f"Downbeat: shifted the grid {k} beat(s) so the kick lands on beat 1")
    return k   # the first k beats become a pickup (rests), so nothing is cut off


def monophonic(notes):
    """One note at a time (a voice or a bass line): keep the loudest-lasting at each step, cut overlaps."""
    by_step = {}
    for s, m, l in notes:
        if s not in by_step or l > by_step[s][2]:
            by_step[s] = (s, m, l)
    out = sorted(by_step.values())
    for i in range(len(out) - 1):
        s, m, l = out[i]
        nxt = out[i + 1][0]
        if s + l > nxt:
            out[i] = (s, m, max(1, nxt - s))
    return out


def guess_key(notes):
    """Krumhansl key profile over the pitch classes, weighted by length."""
    if not notes:
        return None
    major = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    minor = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    hist = [0.0] * 12
    for _, m, l in notes:
        hist[m % 12] += l
    best = None
    for root in range(12):
        for scale, prof in (("major", major), ("minor", minor)):
            score = sum(hist[(root + i) % 12] * prof[i] for i in range(12))
            if best is None or score > best[0]:
                best = (score, root, scale)
    return {"root": best[1], "scale": best[2]}


def read_score(src: str):
    from music21 import converter, corpus, tempo as m21tempo

    p = Path(src)
    score = converter.parse(str(p)) if p.exists() else corpus.parse(src)
    bpm = 90
    marks = score.flatten().getElementsByClass(m21tempo.MetronomeMark)
    if marks and marks[0].number:
        bpm = round(marks[0].getQuarterBPM() or marks[0].number)
    parts = []
    for i, part in enumerate(score.parts):
        label = (part.partName or part.id or f"Part {i + 1}").strip()
        label = re.sub(r"\s+", " ", str(label))[:24]
        notes = []
        measures = part.getElementsByClass("Measure")
        pad = float(measures[0].paddingLeft or 0) if measures else 0.0  # pickup bar: keep barlines true
        for el in part.flatten().notes:
            s = int(round((float(el.offset) + pad) * 4))
            l = max(1, int(round(float(el.quarterLength) * 4)))
            pitches = el.pitches
            for pt in pitches:
                notes.append((s, int(pt.midi), l))
        lower = label.lower()
        inst = next((v for k, v in NAME_INSTRUMENT if k in lower), "real-piano")
        parts.append({"name": label, "instrument": inst, "notes": sorted(set(notes))})
    k = score.analyze("key")
    key = {"root": k.tonic.pitchClass, "scale": "minor" if k.mode == "minor" else "major"}
    return parts, [], bpm, key


# ---------------------------------------------------------------- packing
def chunk_notes(notes, total_chunks):
    chunks = [[] for _ in range(total_chunks)]
    for s, m, l in notes:
        c = s // PAT_STEPS
        if c >= total_chunks:
            continue
        rel = s - c * PAT_STEPS
        chunks[c].append([rel, m, max(1, min(l, PAT_STEPS - rel))])
    return [sorted(c) for c in chunks]


def chunk_drums(hits, total_chunks):
    chunks = [["."] * PAT_STEPS for _ in range(total_chunks)]
    for s, ch in hits.items():
        c = s // PAT_STEPS
        if c < total_chunks:
            chunks[c][s - c * PAT_STEPS] = ch
    return ["".join(c) if set(c) != {"."} else None for c in chunks]


def pack(name, chunks, is_empty):
    """Unique non-empty chunks -> patterns; 4 per track, spilling to 'Name 2', 'Name 3'.
    Returns [(track_name, [pattern...])] and per-chunk (track_index, letter) or None."""
    uniq, where = [], []
    for c in chunks:
        if is_empty(c):
            where.append(None)
            continue
        key = json.dumps(c)
        if key not in [json.dumps(u) for u in uniq]:
            uniq.append(c)
        i = [json.dumps(u) for u in uniq].index(key)
        where.append((i // 4, LETTERS[i % 4]))
    n_tracks = (len(uniq) + 3) // 4
    tracks = []
    for t in range(n_tracks):
        tname = name if n_tracks == 1 else f"{name} {t + 1}"
        tracks.append((tname, uniq[t * 4:(t + 1) * 4]))
    return tracks, where


def build(parts, drums, bpm, key, args):
    last = 0
    for p in parts:
        for s, _, l in p["notes"]:
            last = max(last, s + l)
    for d in drums:
        if d["hits"]:
            last = max(last, max(d["hits"]) + 1)
    if last == 0:
        sys.exit("No notes found in any part: nothing to build.")
    total_bars = -(-last // STEPS_BAR)
    total_chunks = -(-total_bars // PAT_BARS)

    overrides = dict(x.split("=", 1) for x in args.instrument)
    synths, drum_tracks, layout = [], [], []   # layout: (track_name, where-list)
    for d in drums:
        tracks, where = pack(d["name"], chunk_drums(d["hits"], total_chunks), lambda c: c is None)
        for t_i, (tname, pats) in enumerate(tracks):
            tr = {"name": tname, "role": d["role"], "bars": PAT_BARS}
            for L, pat in zip(LETTERS, pats):
                tr[L] = pat
            drum_tracks.append(tr)
            layout.append((tname, [w[1] if w and w[0] == t_i else "-" for w in where]))
    for p in parts:
        inst = overrides.get(p["name"], p["instrument"])
        tracks, where = pack(p["name"], chunk_notes(p["notes"], total_chunks), lambda c: not c)
        for t_i, (tname, pats) in enumerate(tracks):
            tr = {"name": tname, "instrument": inst, "bars": PAT_BARS}
            for L, pat in zip(LETTERS, pats):
                tr[L] = pat
            synths.append(tr)
            layout.append((tname, [w[1] if w and w[0] == t_i else "-" for w in where]))

    sections = []
    for start in range(0, total_bars, SEC_BARS):
        bars = min(SEC_BARS, total_bars - start)
        play = {}
        for tname, per_chunk in layout:
            s = "".join(per_chunk[(start + b) // PAT_BARS] for b in range(bars))
            if set(s) != {"-"}:
                play[tname] = s
        sections.append({"name": f"Bars {start + 1}-{start + bars}", "bars": bars, "play": play})

    tid = args.id or re.sub(r"[^a-z0-9]+", "-", args.label.lower()).strip("-")
    tpl = {
        "id": tid, "label": args.label,
        "blurb": args.blurb or f"{bpm} BPM · {len(synths) + len(drum_tracks)} tracks",
        "bpm": bpm, "kit": "acoustic" if not drums else "studio", "swing": 0, "key": key,
        "drums": drum_tracks, "synths": synths, "sections": sections,
    }
    print(f"{args.label}: {total_bars} bars, {bpm} BPM, key {key}")
    for t in drum_tracks:
        hits = sum(sum(ch != "." for ch in t[L]) for L in LETTERS if L in t)
        print(f"  {t['name']:<16} drums  {hits} hits in {sum(L in t for L in LETTERS)} patterns")
    for t in synths:
        n = sum(len(t[L]) for L in LETTERS if L in t)
        print(f"  {t['name']:<16} {t['instrument']:<26} {n} notes in {sum(L in t for L in LETTERS)} patterns")
    if not 50 <= bpm <= 200:
        print(f"WARNING: {bpm} BPM looks wrong -- try --half-time, or check the beat grid.")
    return tpl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work", nargs="?", help="folder from transcribe.py (recording route)")
    ap.add_argument("--score", help="music21 corpus path, MusicXML or MIDI file (score route)")
    ap.add_argument("--label", required=True)
    ap.add_argument("--id")
    ap.add_argument("--blurb")
    ap.add_argument("--out", required=True)
    ap.add_argument("--shift-beats", type=float, default=None, help="override the automatic downbeat")
    ap.add_argument("--half-time", action="store_true")
    ap.add_argument("--bpm", type=int, help="set the tempo yourself")
    ap.add_argument("--instrument", action="append", default=[], help='"Track name=instrument-id"')
    a = ap.parse_args()
    if bool(a.work) == bool(a.score):
        sys.exit("Give either a work folder (recording) or --score (public-domain score), not both.")
    if a.score:
        parts, drums, bpm, key = read_score(a.score)
    else:
        parts, drums, bpm, key = read_recording(Path(a.work), a.shift_beats, a.half_time)
    tpl = build(parts, drums, a.bpm or bpm, key, a)
    Path(a.out).write_text(json.dumps(tpl, indent=1))
    print(f"Wrote {a.out}")


if __name__ == "__main__":
    main()
