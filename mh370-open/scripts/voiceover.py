"""Single-document voice-over workflow for ElevenLabs.

  build   Write video/voiceover_full.txt: the whole narration as plain text (pronunciation fixes
          applied, no markdown), ready to paste into ElevenLabs in one go.
  split   Cut the narrated audio (one file, or several files in order) back into per-scene files
          video/audio/S01.wav ... S17.wav for scripts/video_render.py.

Usage:
  .venv/bin/python -I scripts/voiceover.py build
  .venv/bin/python -I scripts/voiceover.py split path/to/voiceover.mp3 [more.mp3 ...]
  .venv/bin/python -I scripts/voiceover.py split --use-cuts      # re-cut using edited video/audio/cuts.csv

How split finds the scene boundaries:
  1. If faster-whisper is installed (pip install faster-whisper), it transcribes the audio with word
     timestamps and finds where each scene's opening words are spoken. The cut is snapped to the
     pause just before. This is the reliable method.
  2. Otherwise it falls back to picking pauses near the expected boundary times (based on each
     scene's share of the characters). Check the result in cuts.csv.
  Either way it writes video/audio/cuts.csv (start/end seconds per scene + the method used). You can
  edit the times there and re-run with --use-cuts.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import importlib.util
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "video"
AUDIO = VIDEO / "audio"
FULL_TXT = VIDEO / "voiceover_full.txt"
CUTS = AUDIO / "cuts.csv"
SR = 16_000

_spec = importlib.util.spec_from_file_location("video_render", ROOT / "scripts" / "video_render.py")
vr = importlib.util.module_from_spec(_spec)
sys.modules["video_render"] = vr
_spec.loader.exec_module(vr)


def ffmpeg_exe() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def scene_texts():
    scenes, pron = vr.parse_script()
    return [(s.sid, vr.tts_text(s.narration, pron)) for s in scenes]


# --------------------------------------------------------------------------- build
def build():
    items = scene_texts()
    body = "\n\n".join(t.strip() for _, t in items) + "\n"
    FULL_TXT.write_text(body, encoding="utf-8")
    n_chars = len(body)
    n_words = len(body.split())
    print(f"wrote {FULL_TXT.relative_to(ROOT)}: {len(items)} scenes, {n_words} words, {n_chars} characters "
          f"(~{n_words / 150:.1f} min at 150 wpm)")


# --------------------------------------------------------------------------- audio helpers
def decode(paths: list[Path], sr: int = SR) -> np.ndarray:
    """Decode and concatenate input files to mono float32 at sample rate sr."""
    chunks = []
    for p in paths:
        cmd = [ffmpeg_exe(), "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"]
        raw = subprocess.run(cmd, check=True, capture_output=True).stdout
        chunks.append(np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0)
    return np.concatenate(chunks)


def write_wav(path: Path, x: np.ndarray, sr: int = SR):
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def silences(x: np.ndarray, frame_s=0.02, min_len=0.30):
    """Return list of (start, end) silent runs, using an adaptive threshold."""
    n = int(frame_s * SR)
    m = len(x) // n
    rms = np.sqrt(np.mean(x[: m * n].reshape(m, n) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    speech_level = np.percentile(db, 90)
    floor = np.percentile(db, 5)
    thr = max(floor + 6, speech_level - 30)
    quiet = db < thr
    runs, i = [], 0
    while i < m:
        if quiet[i]:
            j = i
            while j < m and quiet[j]:
                j += 1
            if (j - i) * frame_s >= min_len:
                runs.append((i * frame_s, j * frame_s))
            i = j
        else:
            i += 1
    return runs


def _num_to_words(m):
    try:
        from num2words import num2words
    except ImportError:
        return " "
    tok = m.group(0)
    try:
        if re.fullmatch(r"\d+(st|nd|rd|th)", tok):
            return " " + num2words(int(re.sub(r"\D", "", tok)), to="ordinal") + " "
        n = int(tok.replace(",", ""))
        return " " + (num2words(n, to="year") if 1900 <= n <= 2099 else num2words(n)) + " "
    except Exception:
        return " "


def norm_words(text: str) -> list[str]:
    t = re.sub(r"\d[\d,]*(st|nd|rd|th)?", _num_to_words, text.lower())
    return [w for w in re.sub(r"[^a-z\s]", " ", t).split() if w]


# --------------------------------------------------------------------------- boundary finding
def expected_boundaries(items, total):
    lens = np.array([len(t) for _, t in items], float)
    cum = np.concatenate([[0], np.cumsum(lens)]) / lens.sum()
    return cum[1:-1] * total  # boundaries between scenes


def _best_window(toks, target, lo_i, hi_i):
    """Best fuzzy match of the word list `target` in toks[lo_i:hi_i]; returns (ratio, start index)."""
    tgt = " ".join(target)
    best = (0.0, None)
    for i in range(max(0, lo_i), min(len(toks), hi_i)):
        cand = " ".join(w for _, _, w in toks[i:i + len(target)])
        r = difflib.SequenceMatcher(None, tgt, cand).ratio()
        if r > best[0]:
            best = (r, i)
    return best


def align_with_whisper(x16: np.ndarray, items, total, sil):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    print("transcribing with faster-whisper (base.en) for alignment ...")
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(x16.astype(np.float32), word_timestamps=True, vad_filter=False, beam_size=1)
    toks = [(w.start, w.end, nw) for s in segs for w in (s.words or []) for nw in norm_words(w.word)]
    times = np.array([t for t, _, _ in toks])
    exp = expected_boundaries(items, total)
    cuts, info = [], []
    last_i = 0
    for k in range(1, len(items)):
        prev_words = norm_words(items[k - 1][1])[-8:]
        next_words = norm_words(items[k][1])[:10]
        win = max(90.0, 0.12 * total)
        lo = int(np.searchsorted(times, exp[k - 1] - win))
        hi = int(np.searchsorted(times, exp[k - 1] + win))
        r_prev, i_prev = _best_window(toks, prev_words, max(lo, last_i), hi)
        if i_prev is None:
            return None
        # word-level refinement: index of the last transcript word that matches the end of the previous scene
        w0 = max(0, i_prev - 3)
        seg_words = [w for _, _, w in toks[w0:i_prev + len(prev_words) + 4]]
        sm = difflib.SequenceMatcher(None, prev_words, seg_words, autojunk=False)
        blocks = [bl for bl in sm.get_matching_blocks() if bl.size > 0]
        j_prev_end = min(w0 + blocks[-1].b + blocks[-1].size - 1, len(toks) - 1) if blocks else \
            min(i_prev + len(prev_words) - 1, len(toks) - 1)
        r_next, i_next = _best_window(toks, next_words, j_prev_end - 1, j_prev_end + 30)
        if i_next is not None:
            n0 = max(0, i_next - 3)
            seg_words = [w for _, _, w in toks[n0:i_next + len(next_words) + 4]]
            sm = difflib.SequenceMatcher(None, next_words, seg_words, autojunk=False)
            blocks = [bl for bl in sm.get_matching_blocks() if bl.size > 0]
            if blocks:
                i_next = n0 + blocks[0].b - min(blocks[0].a, blocks[0].b)
        if i_next is None or i_next <= j_prev_end:
            i_next = min(j_prev_end + 1, len(toks) - 1)
        t_next = toks[i_next][0]
        t_prev_end = toks[j_prev_end][1]
        g0, g1 = min(t_prev_end, t_next), max(t_prev_end, t_next)
        cand = [sg for sg in sil if sg[1] >= g0 - 0.1 and sg[0] <= g1 + 0.1]  # pauses overlapping the gap
        if cand:
            sg = max(cand, key=lambda z: z[1] - z[0])
            cut = (sg[0] + sg[1]) / 2
        else:
            cut = (g0 + g1) / 2
        cuts.append(cut)
        info.append(("whisper", round(min(r_next, r_prev), 2), items[k][0]))
        last_i = i_next
    return cuts, info


def pick_silences(items, total, sil):
    """Fallback: choose one long pause near each expected boundary, keeping order (dynamic programming)."""
    exp = expected_boundaries(items, total)
    cands = [((a + b) / 2, b - a) for a, b in sil]
    if len(cands) < len(exp):
        raise SystemExit("Not enough pauses found to split the audio; edit cuts.csv by hand.")
    sigma = max(20.0, 0.04 * total)
    K, N = len(exp), len(cands)
    score = np.full((K, N), -np.inf)
    back = np.zeros((K, N), int)
    for j, (t, d) in enumerate(cands):
        score[0, j] = np.log(d) - 0.5 * ((t - exp[0]) / sigma) ** 2
    for k in range(1, K):
        best_prev, arg = -np.inf, -1
        for j, (t, d) in enumerate(cands):
            if j > 0 and score[k - 1, j - 1] > best_prev:
                best_prev, arg = score[k - 1, j - 1], j - 1
            if arg >= 0:
                score[k, j] = best_prev + np.log(d) - 0.5 * ((t - exp[k]) / sigma) ** 2
                back[k, j] = arg
    j = int(np.argmax(score[-1]))
    picks = [j]
    for k in range(K - 1, 0, -1):
        j = back[k, j]
        picks.append(j)
    picks = picks[::-1]
    cuts = [cands[j][0] for j in picks]
    info = [("pause-heuristic", round(cands[j][1], 2), items[k + 1][0]) for k, j in enumerate(picks)]
    return cuts, info


# --------------------------------------------------------------------------- split
def split(paths: list[Path], use_cuts: bool):
    items = scene_texts()
    if use_cuts:
        rows = list(csv.DictReader(open(CUTS)))
        paths = [Path(p) for p in rows[0]["source"].split("|")]
        bounds = [(float(r["start_s"]), float(r["end_s"])) for r in rows]
        methods = [r["method"] for r in rows]
    else:
        x = decode(paths)  # 16 kHz for analysis only
        total = len(x) / SR
        sil = silences(x)
        res = align_with_whisper(x, items, total, sil)
        if res is None:
            print("faster-whisper not available or alignment failed; using the pause heuristic. "
                  "Check video/audio/cuts.csv.")
            res = pick_silences(items, total, sil)
        cuts, info = res
        edges = [0.0] + list(cuts) + [total]
        bounds = list(zip(edges[:-1], edges[1:]))
        methods = ["start"] + [f"{m} ({q})" for m, q, _ in info]
        AUDIO.mkdir(parents=True, exist_ok=True)
        with open(CUTS, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["scene", "start_s", "end_s", "duration_s", "method", "source"])
            for (sid, _), (a, b), m in zip(items, bounds, methods):
                w.writerow([sid, f"{a:.2f}", f"{b:.2f}", f"{b - a:.2f}", m, "|".join(str(p.resolve()) for p in paths)])
    HQ = 44_100
    xq = decode(paths, HQ)  # full-quality audio for the output files
    for (sid, text), (a, b), m in zip(items, bounds, methods):
        seg = xq[int(a * HQ): int(b * HQ)]
        # trim long leading/trailing silence (keep 0.15 s)
        env = np.abs(seg) > 0.01
        if env.any():
            i0 = max(0, np.argmax(env) - int(0.15 * HQ))
            i1 = min(len(seg), len(seg) - np.argmax(env[::-1]) + int(0.15 * HQ))
            seg = seg[i0:i1]
        for old in AUDIO.glob(f"{sid}.*"):
            if old.suffix.lower() in (".mp3", ".m4a", ".flac", ".wav") and old.name != f"{sid}.wav":
                print(f"note: {old.name} also exists; the renderer may prefer it. Remove it if it's stale.")
        write_wav(AUDIO / f"{sid}.wav", seg, HQ)
        first = " ".join(text.split()[:6])
        print(f"{sid}: {a:7.1f}s – {b:7.1f}s  ({(b - a):5.1f}s)  {m:<24}  starts: \"{first} ...\"")
    print(f"wrote {len(items)} scene files to {AUDIO}/ and {CUTS}")
    print("Listen to the start of a few scene files; if a cut is off, edit cuts.csv and run: split --use-cuts")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    sp = sub.add_parser("split")
    sp.add_argument("audio", nargs="*", type=Path)
    sp.add_argument("--use-cuts", action="store_true")
    sp.add_argument("--out-dir", type=Path, help="write scene files + cuts.csv here instead of video/audio")
    a = ap.parse_args()
    global AUDIO, CUTS
    if getattr(a, "out_dir", None):
        AUDIO = a.out_dir.resolve()
        CUTS = AUDIO / "cuts.csv"
    if a.cmd == "build":
        build()
    else:
        if not a.use_cuts and not a.audio:
            sys.exit("give the narrated audio file(s), or --use-cuts")
        split(a.audio, a.use_cuts)


if __name__ == "__main__":
    main()
