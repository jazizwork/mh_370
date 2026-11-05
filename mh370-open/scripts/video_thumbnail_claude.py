"""YouTube thumbnail for the 'I asked Claude to help find MH370' upload (1280x720).

Background: the project's results map (video/visuals/V21_results_map.png), darkened on the left for text.
Run: .venv/bin/python -I scripts/video_thumbnail_claude.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
BG = ROOT / "video/visuals/V21_results_map.png"
OUT = ROOT / "video/youtube_upload/thumbnail.png"


def font(size, bold=True):
    for path, idx in [("/System/Library/Fonts/HelveticaNeue.ttc", 1 if bold else 0),
                      ("/System/Library/Fonts/Helvetica.ttc", 1 if bold else 0)]:
        try:
            return ImageFont.truetype(path, size, index=idx)
        except Exception:
            continue
    return ImageFont.load_default()


im = Image.open(BG).convert("RGB")
# crop the right-hand part of the map (arc + areas), scale to 1280x720
w, h = im.size
crop = im.crop((int(w * 0.30), int(h * 0.05), w, int(h * 0.98)))
crop = crop.resize((1280, int(1280 * crop.height / crop.width)), Image.LANCZOS)
top = max(0, (crop.height - 720) // 2)
crop = crop.crop((0, top, 1280, top + 720))
# left-to-right dark gradient for legibility
grad = Image.new("L", (1280, 720))
gd = ImageDraw.Draw(grad)
for x in range(1280):
    a = 250 if x < 560 else int(250 * max(0.0, 1 - (x - 560) / 360))
    gd.line([(x, 0), (x, 720)], fill=a)
dark = Image.new("RGB", (1280, 720), (8, 16, 30))
canvas = Image.composite(dark, crop, grad)
d = ImageDraw.Draw(canvas)
x0 = 56
d.text((x0, 70), "I ASKED", font=font(92), fill=(245, 245, 245))
d.text((x0, 168), "CLAUDE", font=font(132), fill=(255, 140, 70))
d.text((x0, 300), "TO HELP FIND", font=font(92), fill=(245, 245, 245))
d.text((x0, 398), "MH370", font=font(150), fill=(245, 245, 245))
d.text((x0 + 4, 585), "Public data only · where the probability is now", font=font(34, bold=False), fill=(200, 210, 225))
OUT.parent.mkdir(parents=True, exist_ok=True)
canvas.save(OUT, optimize=True)
print("wrote", OUT, OUT.stat().st_size // 1024, "KB")
