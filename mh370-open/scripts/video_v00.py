"""Build V00_colsto_ref.png: credited reference card showing a screenshot of colsto's video.

Input: video/assets/colsto_reference_screenshot.png (screenshot supplied by the channel owner).
Output: video/visuals/V00_colsto_ref.png (1920x1080). Content kept above the caption zone (y < 860).
Run: .venv/bin/python -I scripts/video_v00.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "video/assets/colsto_reference_screenshot.png"
OUT = ROOT / "video/visuals/V00_colsto_ref.png"
BG = (14, 26, 43)


def font(size, bold=False):
    for path in ["/System/Library/Fonts/Avenir Next.ttc", "/System/Library/Fonts/HelveticaNeue.ttc",
                 "/System/Library/Fonts/Helvetica.ttc"]:
        try:
            return ImageFont.truetype(path, size, index=(1 if bold else 0))
        except Exception:
            continue
    return ImageFont.load_default()


canvas = Image.new("RGB", (1920, 1080), BG)
shot = Image.open(SRC).convert("RGB")
max_w, max_h = 1360, 730
scale = min(max_w / shot.width, max_h / shot.height)
shot = shot.resize((round(shot.width * scale), round(shot.height * scale)), Image.LANCZOS)
x = (1920 - shot.width) // 2
y = 70
# subtle frame
d = ImageDraw.Draw(canvas)
d.rounded_rectangle([x - 6, y - 6, x + shot.width + 6, y + shot.height + 6], radius=10, fill=(40, 56, 80))
canvas.paste(shot, (x, y))
cap = "colsto, “I discovered a sound that leaks your exact location (and it's everywhere)”, YouTube, November 2026"
f = font(26)
w = d.textlength(cap, font=f)
d.text(((1920 - w) / 2, y + shot.height + 24), cap, font=f, fill=(190, 200, 215))
OUT.parent.mkdir(parents=True, exist_ok=True)
canvas.save(OUT)
print("wrote", OUT, shot.size)
