"""Turn the stems from separate.py into notes (audio-to-MIDI).

    python transcribe.py work/

Reads work/stems/*.wav. Writes:
  work/midi/<stem>.mid   pitched stems, by Basic Pitch (free, open source)
  work/drums.json        drum hits: kick / snare / hat with times in seconds
  work/grid.json         tempo and beat times, measured on the drums (or the mix)
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import librosa

PITCHED = ["bass", "piano", "guitar", "vocals", "other"]


def beat_grid(stems: Path):
    """Tempo + beat times, measured on the drum stem when there is one."""
    src = stems / "drums.wav"
    if not src.exists():
        files = sorted(stems.glob("*.wav"))
        y = sum(librosa.load(str(f), sr=22050, mono=True)[0] for f in files)
        sr = 22050
    else:
        y, sr = librosa.load(str(src), sr=22050, mono=True)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
    tempo = float(np.atleast_1d(tempo)[0])
    if len(beats) < 8:
        sys.exit("Could not find a steady beat (fewer than 8 beats). The song may be too free-time for a grid.")
    return {"bpm": round(tempo, 1), "beats": [round(float(b), 4) for b in beats]}


def drum_hits(path: Path):
    """Onsets on the drum stem, sorted into kick / snare / hat by where the energy sits."""
    y, sr = librosa.load(str(path), sr=22050, mono=True)
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units="time", backtrack=False)
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    low = freqs < 150
    mid = (freqs >= 150) & (freqs < 4000)
    high = freqs >= 6000
    hits = []
    peak = None
    rows = []
    for t in onsets:
        f = librosa.time_to_frames(t, sr=sr, hop_length=512)
        seg = S[:, f:f + 4]
        if seg.size == 0:
            continue
        e = seg.mean(axis=1)
        rows.append((float(t), e[low].sum(), e[mid].sum(), e[high].sum()))
    if not rows:
        return []
    arr = np.array([r[1:] for r in rows])
    ref = np.percentile(arr, 90, axis=0) + 1e-9   # each band judged against its own loud hits
    for (t, lo, mi, hi), n in zip(rows, arr / ref):
        loud = float(n.max())
        if n[0] >= 0.45 and n[0] >= n[1] * 0.8:
            hits.append({"t": round(t, 4), "role": "kick", "v": loud})
        if n[1] >= 0.5 and n[1] > n[0] * 0.9:
            hits.append({"t": round(t, 4), "role": "snare", "v": loud})
        if n[2] >= 0.35 and n[0] < 0.45 and n[1] < 0.5:
            hits.append({"t": round(t, 4), "role": "hat", "v": loud})
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    a = ap.parse_args()
    work = Path(a.work)
    stems = work / "stems"
    if not stems.is_dir():
        sys.exit(f"No stems folder at {stems}. Run separate.py first.")

    grid = beat_grid(stems)
    (work / "grid.json").write_text(json.dumps(grid))
    print(f"Tempo about {grid['bpm']} BPM, {len(grid['beats'])} beats found")

    from basic_pitch.inference import predict  # imported late: slow to load
    mid_dir = work / "midi"
    mid_dir.mkdir(exist_ok=True)
    for name in PITCHED:
        wav = stems / f"{name}.wav"
        if not wav.exists():
            continue
        y, _ = librosa.load(str(wav), sr=22050, mono=True)
        if float(np.sqrt(np.mean(y ** 2))) < 0.003:
            print(f"  {name}: silent, skipped")
            continue
        kw = {"minimum_note_length": 100}
        if name == "bass":
            kw.update(minimum_frequency=30, maximum_frequency=400)
        if name == "vocals":
            kw.update(minimum_frequency=70, maximum_frequency=1100)
        _, midi, notes = predict(str(wav), **kw)
        midi.write(str(mid_dir / f"{name}.mid"))
        print(f"  {name}: {len(notes)} notes")

    drums = stems / "drums.wav"
    if drums.exists():
        hits = drum_hits(drums)
        (work / "drums.json").write_text(json.dumps(hits))
        counts = {r: sum(1 for h in hits if h["role"] == r) for r in ("kick", "snare", "hat")}
        print("  drums:", ", ".join(f"{k} {v}" for k, v in counts.items()))
    print(f"Done. Next: python to_studio.py {work}")


if __name__ == "__main__":
    main()
