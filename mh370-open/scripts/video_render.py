"""Render the explainer video from video/script.md, the stills in video/visuals/ and (optionally)
per-scene voice-over files in video/audio/.

What it does
  1. Parses video/script.md into scenes (id, title, VISUALS, ONSCREEN captions, NARRATION) and the
     pronunciation list at the top of the file.
  2. Writes TTS-ready narration to video/tts/Sxx.txt (pronunciation replacements applied to these
     copies only; script.md is never modified).
  3. Times each scene: duration of video/audio/Sxx.(mp3|wav|m4a) + 0.6 s if present, otherwise
     words / 2.5 + 1.0 s.
  4. Splits each scene's time across its visuals (evenly, or by narration paragraphs / fixed weights
     for a few scenes, see SCENE_WEIGHTS), applies a gentle Ken Burns move (4 % zoom) to each still,
     0.5 s crossfades between consecutive stills, optional burned-in lower-third captions (ONSCREEN).
  5. Renders scenes in parallel to H.264 chunks, concatenates them, muxes the per-scene audio aligned to
     the scene starts (or a silent AAC track), and writes an .srt from the narration.
  6. Writes video/out/timeline.json and updates the chapter block in video/description.md.

Usage (from the project root)
  .venv/bin/python -I scripts/video_render.py                 # uses audio if video/audio/ has any
  .venv/bin/python -I scripts/video_render.py --animatic      # ignore audio -> *_animatic.mp4
  .venv/bin/python -I scripts/video_render.py --scenes S09,S14 --animatic   # quick preview of some scenes
  .venv/bin/python -I scripts/video_render.py --tts-only      # just (re)write video/tts/*.txt
  .venv/bin/python -I scripts/video_render.py --srt-only [--animatic]   # just (re)write the .srt
  options: --no-captions  --workers 8  --crf 20  --frames 6

ffmpeg comes from the imageio-ffmpeg wheel in .venv (no system install needed).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
VID = ROOT / "video"
SCRIPT = VID / "script.md"
VISUALS = VID / "visuals"
AUDIO = VID / "audio"
AUDIO_DIR = [AUDIO]    # overridable with --audio-dir
TTS = VID / "tts"
OUT = VID / "out"

W, H, FPS = 1920, 1080, 30
XFADE = 0.5            # s, crossfade between consecutive stills (centred on the cut)
FADE_EDGE = 0.6        # s, fade from/to black at the very start/end
AUDIO_PAD = 0.6        # s added after each scene's voice-over
WPS = 2.5              # words per second when no audio exists
NO_AUDIO_PAD = 1.0     # s added per scene when no audio exists
ZOOM = 0.04            # Ken Burns zoom amount (<= 6 %)
BG = (14, 26, 43)

# Time split between a scene's stills. Default: even. A list of numbers = fixed relative weights; a list
# of lists = narration paragraph indices covered by each still (weights = their word counts).
SCENE_WEIGHTS = {"S01": [0.3, 0.24, 0.46], "S03": [[0, 1], [2, 3]], "S04": [0.62, 0.38], "S12": [[0, 1], [2, 3, 4]],
                 "S13": [[0, 1], [2, 3]], "S14": [[0, 1, 2], [3], [4], [5], [6, 7]]}
CAPTION_MAX = 8.0      # s, longest time a lower-third stays up
# Narration paragraph (0-based) during which each ONSCREEN caption is shown, in caption order. Captions
# sharing a paragraph split its time. Scenes not listed: captions spread evenly across the scene.
CAPTION_PARAS = {"S01": [0, 1, 2], "S02": [0, 1, 2], "S03": [1, 2, 1], "S04": [1, 2, 3], "S05": [0, 0, 0],
                 "S06": [1, 2], "S07": [1, 1, 1], "S08": [0, 1, 2, 3, 4], "S09": [2, 2, 3, 3], "S10": [1, 2, 3],
                 "S11": [1, 2, 2, 4], "S12": [1, 1, 1, 2], "S13": [1, 1, 2], "S14": [0, 3, 4, 5, 6],
                 "S15": [1, 2, 3, 5], "S16": [0, 0, 0, 0, 0], "S17": [2, 3]}

FONT_TTC = "/System/Library/Fonts/HelveticaNeue.ttc"
FONT_FALLBACK = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
FALLBACK_CHARS = set("→←↑↓⇒")   # glyphs missing from Helvetica Neue


def ffmpeg_exe() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


# ----------------------------------------------------------------------------- script parsing
@dataclass
class Scene:
    sid: str
    title: str
    visuals: list[str]
    captions: list[str]
    narration: str
    paragraphs: list[str] = field(default_factory=list)
    duration: float = 0.0
    speech: float = 0.0
    audio: Path | None = None
    start: float = 0.0


def parse_script(path=SCRIPT):
    text = path.read_text(encoding="utf-8")
    pron = []
    for m in re.finditer(r'^- (.+?) → "(.+?)"\s*$', text, flags=re.M):
        pron.append((m.group(1).strip(), m.group(2).strip()))
    scenes = []
    blocks = re.split(r"^## ", text, flags=re.M)[1:]
    for b in blocks:
        head, _, body = b.partition("\n")
        m = re.match(r"(S\d+)\s*\|\s*(.+)", head.strip())
        if not m:
            continue
        sid, title = m.group(1), m.group(2).strip()
        vis = re.search(r"^VISUALS:\s*(.+)$", body, flags=re.M)
        ons = re.search(r"^ONSCREEN:\s*(.+)$", body, flags=re.M)
        nar = body.split("NARRATION:", 1)[1] if "NARRATION:" in body else ""
        nar = nar.split("\n---", 1)[0].strip()
        paras = [p.strip().replace("\n", " ") for p in re.split(r"\n\s*\n", nar) if p.strip()]
        caps = re.findall(r'"([^"]+)"', ons.group(1)) if ons else []
        scenes.append(Scene(sid, title, [v.strip() for v in vis.group(1).split(",")] if vis else [], caps,
                            "\n\n".join(paras), paras))
    return scenes, pron


def tts_text(text, pron):
    """Apply the pronunciation list (whole words only); capitalise a replacement that starts a sentence."""
    out = text
    for src, dst in pron:
        def rep(m, dst=dst):
            before = m.string[:m.start()].rstrip()
            return dst[:1].upper() + dst[1:] if (not before or before[-1] in ".!?\n") else dst
        out = re.sub(r"(?<![\w-])" + re.escape(src) + r"(?![\w-])", rep, out)
    return out


def write_tts(scenes, pron):
    TTS.mkdir(parents=True, exist_ok=True)
    for s in scenes:
        (TTS / f"{s.sid}.txt").write_text(tts_text(s.narration, pron) + "\n", encoding="utf-8")
    print(f"wrote {len(scenes)} TTS files to {TTS.relative_to(ROOT)}/")


# ----------------------------------------------------------------------------- timing
def media_duration(path: Path) -> float:
    """Duration by decoding (accurate for VBR mp3); falls back to the container header."""
    p = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(path), "-f", "null", "-"],
                       capture_output=True, text=True)
    times = re.findall(r"time=(\d+):(\d+):(\d+\.\d+)", p.stderr)
    if times:
        h, m, s = times[-1]
        return int(h) * 3600 + int(m) * 60 + float(s)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stderr)
    if not m:
        raise RuntimeError(f"cannot read duration of {path}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def find_audio(sid):
    for ext in ("mp3", "wav", "m4a", "aac", "flac"):
        p = AUDIO_DIR[0] / f"{sid}.{ext}"
        if p.exists():
            return p
    return None


def time_scenes(scenes, use_audio=True):
    t = 0.0
    for s in scenes:
        s.audio = find_audio(s.sid) if use_audio else None
        if s.audio:
            s.speech = media_duration(s.audio)
            s.duration = s.speech + AUDIO_PAD
        else:
            words = len(s.narration.split())
            s.speech = words / WPS
            s.duration = s.speech + NO_AUDIO_PAD
        s.start = t
        t += s.duration
    return t


def visual_files(vid: str) -> list[Path]:
    p = VISUALS / f"{vid}.png"
    if p.exists():
        return [p]
    code = re.match(r"(V\d+)", vid).group(1)
    hits = sorted(VISUALS.glob(f"{code}*.png"))
    if not hits:
        raise FileNotFoundError(f"no image for visual {vid} in {VISUALS}")
    return hits


def segments_for(scenes):
    """Global list of (image path, start, end) covering the whole video without gaps."""
    segs = []
    for s in scenes:
        files = [f for v in s.visuals for f in visual_files(v)]
        n = len(files)
        wmode = SCENE_WEIGHTS.get(s.sid)
        wc = [len(p.split()) for p in s.paragraphs]
        if isinstance(wmode, list) and len(wmode) == n and all(isinstance(g, list) for g in wmode) \
                and all(i < len(wc) for g in wmode for i in g):
            weights = [sum(wc[i] for i in g) for g in wmode]
        elif isinstance(wmode, list) and len(wmode) == n and not any(isinstance(g, list) for g in wmode):
            weights = wmode
        else:
            weights = [1.0] * n
        weights = np.asarray(weights, float) / np.sum(weights)
        t = s.start
        for f, w in zip(files, weights):
            segs.append([f, t, t + w * s.duration, s.sid])
            t += w * s.duration
        segs[-1][2] = s.start + s.duration
    return segs


# ----------------------------------------------------------------------------- frame drawing
_IMG_CACHE: dict[str, Image.Image] = {}


def load(path) -> Image.Image:
    k = str(path)
    if k not in _IMG_CACHE:
        im = Image.open(path).convert("RGB")
        if im.size != (W, H):
            im = im.resize((W, H), Image.LANCZOS)
        _IMG_CACHE[k] = im
    return _IMG_CACHE[k]


def ken_burns(im: Image.Image, u: float, idx: int) -> Image.Image:
    """u in [0, 1] across the segment (incl. crossfade overlap). Alternating zoom in / out with a
    small drift; smooth easing."""
    e = 0.5 - 0.5 * math.cos(math.pi * min(max(u, 0.0), 1.0))
    z = 1.0 + ZOOM * (e if idx % 2 == 0 else 1.0 - e)
    dirs = [(1, 0.5), (-1, -0.5), (0.6, -1), (-0.6, 1)]
    dx, dy = dirs[idx % 4]
    # crop window (in source pixels) of size W/z x H/z, drifting within the margin
    cw, ch = W / z, H / z
    mx, my = (W - cw) / 2, (H - ch) / 2
    cx = W / 2 + dx * mx * (e - 0.5) * 0.8
    cy = H / 2 + dy * my * (e - 0.5) * 0.8
    x0, y0 = cx - cw / 2, cy - ch / 2
    a = cw / W
    return im.transform((W, H), Image.AFFINE, (a, 0, x0, 0, a, y0), resample=Image.BILINEAR)


def _runs(text):
    out, cur, fb = [], "", None
    for ch in text:
        f = ch in FALLBACK_CHARS
        if fb is None or f == fb:
            cur += ch
        else:
            out.append((cur, fb))
            cur = ch
        fb = f
    if cur:
        out.append((cur, bool(fb)))
    return out


def _fonts(size):
    try:
        main = ImageFont.truetype(FONT_TTC, size, index=10)   # Helvetica Neue Medium
    except Exception:
        main = ImageFont.load_default()
    try:
        fb = ImageFont.truetype(FONT_FALLBACK, size)
    except Exception:
        fb = main
    return main, fb


def _textlen(draw, text, fonts):
    return sum(draw.textlength(r, font=fonts[1] if f else fonts[0]) for r, f in _runs(text))


def _draw_text(d, x, y, text, fonts, fill):
    for r, f in _runs(text):
        font = fonts[1] if f else fonts[0]
        d.text((x, y), r, font=font, fill=fill)
        x += d.textlength(r, font=font)


def caption_image(text: str) -> Image.Image:
    """RGBA lower-third: semi-transparent navy bar, white sans text, wrapped to <= 2 lines."""
    fonts = _fonts(44)
    draw = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    maxw = 1600
    words, lines, cur = text.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if _textlen(draw, trial, fonts) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    lines.append(cur)
    lh = 56
    tw = max(_textlen(draw, l, fonts) for l in lines)
    bw, bh = int(tw + 64), int(lh * len(lines) + 30)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0 = (W - bw) // 2
    y1 = H - 62
    y0 = y1 - bh
    d.rounded_rectangle([x0, y0, x0 + bw, y1], radius=14, fill=(10, 18, 32, 205))
    d.rectangle([x0, y0 + 14, x0 + 6, y1 - 14], fill=(255, 126, 182, 255))
    for i, l in enumerate(lines):
        lw = _textlen(draw, l, fonts)
        _draw_text(d, (W - lw) / 2 + 3, y0 + 13 + i * lh, l, fonts, (240, 239, 236, 255))
    return img


def paragraph_windows(scene: Scene):
    """(start, end) of each narration paragraph, proportional to its length within the speech time."""
    lens = [len(p) for p in scene.paragraphs] or [1]
    tot = sum(lens)
    out, t = [], scene.start
    for L in lens:
        d = scene.speech * L / tot
        out.append((t, t + d))
        t += d
    return out


def caption_schedule(scene: Scene):
    """ONSCREEN captions, each shown during its narration paragraph (CAPTION_PARAS) or, for scenes not
    configured, spread evenly across the scene. 0.3 s fades; at least ~3 s on screen where room allows."""
    n = len(scene.captions)
    if not n:
        return []
    paras = CAPTION_PARAS.get(scene.sid)
    wins = paragraph_windows(scene)
    slots = []
    if paras and len(paras) == n and max(paras) < len(wins):
        for i, pi in enumerate(paras):
            same = [j for j, q in enumerate(paras) if q == pi]
            k, m = same.index(i), len(same)
            a, b = wins[pi]
            slots.append((a + (b - a) * k / m, a + (b - a) * (k + 1) / m))
    else:
        d = scene.duration / n
        slots = [(scene.start + i * d, scene.start + (i + 1) * d) for i in range(n)]
    order = sorted(range(n), key=lambda i: slots[i][0])
    out = []
    for r, i in enumerate(order):
        a, b = slots[i]
        nxt = slots[order[r + 1]][0] if r + 1 < n else scene.start + scene.duration
        a, b = a + 0.3, max(b - 0.3, min(a + 3.3, nxt - 0.3))
        b = min(b, a + CAPTION_MAX)
        if b - a > 1.0:
            out.append((scene.captions[i], a, b))
    return out


def alpha_over(base: np.ndarray, over: Image.Image, alpha_scale: float, box) -> None:
    x0, y0, x1, y1 = box
    ov = np.asarray(over.crop(box), dtype=np.float32)
    a = ov[..., 3:4] / 255.0 * alpha_scale
    region = base[y0:y1, x0:x1].astype(np.float32)
    base[y0:y1, x0:x1] = (region * (1 - a) + ov[..., :3] * a).astype(np.uint8)


def render_chunk(job):
    """Render frames [f0, f1) to an H.264 file. Runs in a worker process."""
    f0, f1, segs, caps, total, out_path, crf, show_caps = job
    caption_imgs = {}
    cmd = [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-threads", "2", "-g", str(FPS * 2), "-movflags", "+faststart", str(out_path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    half = XFADE / 2
    for fi in range(f0, f1):
        t = (fi + 0.5) / FPS
        active = [(k, s) for k, s in enumerate(segs) if s[1] - half <= t < s[2] + half]
        layers = []
        for k, (path, a, b, _) in active:
            u = (t - (a - half)) / ((b + half) - (a - half))
            # weight: 1 inside, linear ramps across the crossfades at both ends (none at video start/end)
            wgt = 1.0
            if k > 0 and t < a + half:
                wgt = min(wgt, (t - (a - half)) / XFADE)
            if k < len(segs) - 1 and t > b - half:
                wgt = min(wgt, ((b + half) - t) / XFADE)
            wgt = max(0.0, min(1.0, wgt))
            if wgt > 0:
                layers.append((ken_burns(load(path), u, k), wgt))
        if len(layers) == 1:
            frame = np.array(layers[0][0])
        else:
            frame = sum(np.asarray(im_, np.float32) * w_ for im_, w_ in layers)
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        if show_caps:
            for text, a, b in caps:
                if a <= t <= b:
                    if text not in caption_imgs:
                        ci = caption_image(text)
                        caption_imgs[text] = (ci, ci.getbbox())
                    ci, box = caption_imgs[text]
                    al = min(1.0, (t - a) / 0.3, (b - t) / 0.3)
                    alpha_over(frame, ci, al, box)
        edge = min(1.0, t / FADE_EDGE, (total - t) / FADE_EDGE)
        if edge < 1.0:
            frame = (frame.astype(np.float32) * max(edge, 0.0) + np.array(BG, np.float32) * (1 - max(edge, 0.0))).astype(np.uint8)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg failed for chunk {out_path}")
    return str(out_path), f1 - f0


# ----------------------------------------------------------------------------- subtitles
def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def wrap2(text, width=42):
    """Two balanced lines of <= width chars (or one line if it fits)."""
    if len(text) <= width:
        return text
    words = text.split()
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if len(a) <= width and len(b) <= width:
            score = abs(len(a) - len(b))
            if best is None or score < best[0]:
                best = (score, a + "\n" + b)
    return best[1] if best else text


def subtitle_chunks(text, width=42):
    """Greedy chunks that always fit two lines of <= width characters; closes a chunk at a sentence end
    (once it has some length) or at a comma/colon when it is already fairly full."""
    def fits(t):
        return len(t) <= width or "\n" in wrap2(t, width)
    chunks, cur = [], []
    for wd in text.replace("\n", " ").split():
        trial = " ".join(cur + [wd])
        if cur and not fits(trial):
            chunks.append(" ".join(cur))
            cur = [wd]
        else:
            cur.append(wd)
        joined = " ".join(cur)
        if (re.search(r"[.?!][\"”']?$", wd) and len(joined) >= 18) or (wd[-1] in ",;:" and len(joined) >= 58):
            chunks.append(joined)
            cur = []
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def write_srt(scenes, path):
    lines, n = [], 0
    for s in scenes:
        chunks = subtitle_chunks(s.narration)
        tot = sum(len(c) for c in chunks)
        t = s.start + 0.05
        for c in chunks:
            d = max(1.0, s.speech * len(c) / tot)
            n += 1
            lines += [str(n), f"{srt_time(t)} --> {srt_time(min(t + d - 0.04, s.start + s.duration - 0.05))}", wrap2(c), ""]
            t += d
    path.write_text("\n".join(lines), encoding="utf-8")


# ----------------------------------------------------------------------------- audio + mux
def build_audio(scenes, total, out_path):
    ff = ffmpeg_exe()
    inputs, filters, labels = [], [], []
    k = 0
    for s in scenes:
        if s.audio:
            inputs += ["-i", str(s.audio)]
            filters.append(f"[{k}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,apad,"
                           f"atrim=0:{s.duration:.4f},asetpts=PTS-STARTPTS[a{k}]")
            labels.append(f"[a{k}]")
            k += 1
        else:
            filters.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{s.duration:.4f},asetpts=PTS-STARTPTS[n{s.sid}]")
            labels.append(f"[n{s.sid}]")
    filters.append("".join(labels) + f"concat=n={len(labels)}:v=0:a=1[aout]")
    cmd = [ff, "-hide_banner", "-loglevel", "error", "-y"] + inputs + [
        "-filter_complex", ";".join(filters), "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}",
        str(out_path)]
    subprocess.run(cmd, check=True)


def silent_audio(total, out_path):
    subprocess.run([ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                    "anullsrc=r=48000:cl=stereo", "-t", f"{total:.3f}", "-c:a", "aac", "-b:a", "128k", str(out_path)],
                   check=True)


def container_duration(path):
    p = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stderr)
    streams = re.findall(r"Stream #\S+: (Video|Audio): (\w+)[^\n]*", p.stderr)
    info = re.findall(r"Stream #\S+: Video: [^\n]*", p.stderr)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    return dur, streams, info


def fmt_ts(t):
    t = int(t)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


CHAPTER_TITLES = {
    "S01": "Cold open: can a plane's sound find MH370?", "S02": "What happened on 8 March 2014",
    "S03": "The satellite arcs", "S04": "Where people have looked", "S05": "The debris",
    "S06": "The other leads", "S07": "Can you reverse the sound trick?", "S08": "What we did differently",
    "S09": "Finding 1: the satellite data points to the high 30s south, but can't settle it alone",
    "S10": "Finding 2: why the drift studies disagreed",
    "S11": "Finding 3: the sound candidates", "S12": "Finding 4: WSPR's physics problem",
    "S13": "The uncomfortable part: is the model wrong somewhere?", "S14": "Where the probability is now",
    "S15": "How this explains the history",
    "S16": "What could prove us wrong", "S17": "Close",
}


def update_description_chapters(scenes, with_audio):
    p = VID / "description.md"
    if not p.exists():
        return
    lines = [f"{fmt_ts(s.start)} {CHAPTER_TITLES.get(s.sid, s.title)}" for s in scenes]
    note = ("(timestamps from the voiced render)" if with_audio else
            "(timestamps from the silent animatic: they will shift once the voice-over is added; re-run the renderer)")
    block = "<!-- chapters:start -->\n" + note + "\n\n" + "\n".join(lines) + "\n<!-- chapters:end -->"
    txt = p.read_text(encoding="utf-8")
    txt = re.sub(r"<!-- chapters:start -->.*?<!-- chapters:end -->", block, txt, flags=re.S)
    p.write_text(txt, encoding="utf-8")
    print("updated chapters in video/description.md")


# ----------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--animatic", action="store_true", help="ignore audio; write *_animatic.mp4")
    ap.add_argument("--no-captions", action="store_true")
    ap.add_argument("--scenes", default="", help="comma list of scene ids for a quick preview")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--frames", type=int, default=6, help="sample frames to extract into video/out/frames/")
    ap.add_argument("--tts-only", action="store_true")
    ap.add_argument("--srt-only", action="store_true", help="only (re)write the .srt for the current timing")
    ap.add_argument("--audio-dir", default=None, help="folder with Sxx.mp3/.wav (default video/audio)")
    ap.add_argument("--out-name", default=None, help="override the output base name (no extension)")
    a = ap.parse_args(argv)
    if a.audio_dir:
        AUDIO_DIR[0] = Path(a.audio_dir).resolve()

    scenes, pron = parse_script()
    write_tts(scenes, pron)
    if a.tts_only:
        return
    have_audio = any(find_audio(s.sid) for s in scenes) and not a.animatic
    if a.scenes:
        keep = set(a.scenes.split(","))
        scenes = [s for s in scenes if s.sid in keep]
    total = time_scenes(scenes, use_audio=have_audio)
    segs = segments_for(scenes)
    for s in scenes:
        print(f"{s.sid} start {fmt_ts(s.start):>6}  {s.duration:6.1f} s  "
              f"{'audio ' + s.audio.name if s.audio else 'no audio'}  visuals: {', '.join(s.visuals)}")
    print(f"total {total:.1f} s ({fmt_ts(total)}), {len(segs)} stills")

    OUT.mkdir(parents=True, exist_ok=True)
    base = a.out_name or ("mh370_reanalysis" + ("" if have_audio else "_animatic") + ("_preview" if a.scenes else ""))
    out_mp4 = OUT / f"{base}.mp4"
    if a.srt_only:
        write_srt(scenes, out_mp4.with_suffix(".srt"))
        print("wrote", out_mp4.with_suffix(".srt").relative_to(ROOT))
        return
    caps = [c for s in scenes for c in caption_schedule(s)]
    seg_rows = [(str(p), st, en, sid) for p, st, en, sid in segs]
    tmp = Path(tempfile.mkdtemp(prefix="render_", dir=OUT))
    try:
        # fixed-size chunks of the global frame range (independent of scene boundaries) for even load
        ftot = round(total * FPS)
        CH = 240
        jobs = [(f0, min(f0 + CH, ftot), seg_rows, caps, total, tmp / f"chunk_{i:04d}.mp4", a.crf, not a.no_captions)
                for i, f0 in enumerate(range(0, ftot, CH))]
        nframes = 0
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            for i, (path, n) in enumerate(ex.map(render_chunk, jobs)):
                nframes += n
                if i % 10 == 0 or i == len(jobs) - 1:
                    print(f"  rendered chunk {i + 1}/{len(jobs)} ({nframes} frames)", flush=True)
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{j[5]}'\n" for j in jobs))
        silent_v = tmp / "video.mp4"
        subprocess.run([ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                        "-i", str(lst), "-c", "copy", str(silent_v)], check=True)
        aud = tmp / "audio.m4a"
        if have_audio:
            build_audio(scenes, total, aud)
        else:
            silent_audio(total, aud)
        subprocess.run([ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(silent_v), "-i", str(aud),
                        "-map", "0:v", "-map", "1:a", "-c", "copy", "-shortest", "-movflags", "+faststart",
                        str(out_mp4)], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    srt = out_mp4.with_suffix(".srt")
    write_srt(scenes, srt)
    dur, streams, info = container_duration(out_mp4)
    print(f"wrote {out_mp4.relative_to(ROOT)}: {dur:.2f} s (expected {total:.2f} s, {nframes} frames = "
          f"{nframes / FPS:.2f} s); streams {streams}")
    print("  " + (info[0] if info else ""))
    print(f"wrote {srt.relative_to(ROOT)}")
    if abs(dur - total) > 0.5:
        print("WARNING: container duration differs from the scene total by more than 0.5 s")

    timeline = {"file": str(out_mp4.relative_to(ROOT)), "with_audio": have_audio, "total_s": round(total, 3),
                "container_duration_s": round(dur, 3), "fps": FPS,
                "scenes": [{"id": s.sid, "title": s.title, "start_s": round(s.start, 3), "duration_s": round(s.duration, 3),
                            "audio": s.audio.name if s.audio else None, "visuals": s.visuals,
                            "words": len(s.narration.split())} for s in scenes],
                "stills": [{"image": Path(p).name, "start_s": round(st, 3), "end_s": round(en, 3), "scene": sid}
                           for p, st, en, sid in segs]}
    (OUT / f"{base}_timeline.json").write_text(json.dumps(timeline, indent=1))
    if not a.scenes:
        update_description_chapters(scenes, have_audio)

    # sample frames for review
    if a.frames:
        fdir = OUT / "frames"
        fdir.mkdir(exist_ok=True)
        picks = np.linspace(0, len(scenes) - 1, a.frames).round().astype(int)
        for i in sorted(set(picks)):
            s = scenes[i]
            t = s.start + 0.55 * s.duration
            fp = fdir / f"{base}_{s.sid}_{t:07.1f}s.png"
            subprocess.run([ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i",
                            str(out_mp4), "-frames:v", "1", str(fp)], check=True)
            print("frame", fp.relative_to(ROOT))


if __name__ == "__main__":
    main()
