"""Split a recording into stems with Demucs (free, open source).

    python separate.py "song.mp3" --out work/ [--model htdemucs_6s]

Writes work/stems/<stem>.wav (vocals, drums, bass, guitar, piano, other for
the 6-stem model) and work/source.txt naming the file it came from.
Use only on a copy of the song you own; the stems are for your own use.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="htdemucs_6s",
                    help="htdemucs_6s = 6 stems incl. guitar+piano; htdemucs_ft = 4 cleaner stems")
    a = ap.parse_args()

    src = Path(a.audio)
    if not src.is_file():
        sys.exit(f"No such file: {src}")
    out = Path(a.out)
    raw = out / "_demucs"
    raw.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, "-m", "demucs", "-n", a.model, "-o", str(raw), str(src)]
    print("Separating (a few minutes on a CPU)...", flush=True)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(f"Demucs failed (exit {r.returncode}). Is it installed in this Python? pip install demucs")

    made = raw / a.model / src.stem
    wavs = sorted(made.glob("*.wav"))
    if not wavs:
        sys.exit(f"Demucs finished but wrote no stems under {made}")
    stems = out / "stems"
    stems.mkdir(parents=True, exist_ok=True)
    for w in wavs:
        shutil.move(str(w), stems / w.name)
    shutil.rmtree(raw)
    (out / "source.txt").write_text(str(src.resolve()) + "\n")
    print("Stems:", ", ".join(p.stem for p in sorted(stems.glob("*.wav"))))
    print(f"In {stems}")


if __name__ == "__main__":
    main()
