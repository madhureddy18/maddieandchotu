"""Make a Reels cover (1080x1920 JPEG): a frame from the video + big title text in the safe centre area.
   python tools/make_cover.py queue/upi.mp4 16.0 "WHERE DOES YOUR ₹20 GO?"   -> queue/upi.jpg
   python tools/make_cover.py clean_still.jpg 0 "TITLE" queue/upi.jpg           (use a clean render, no captions)
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def main(video, at, title, out=None):
    out = Path(out or Path(video).with_suffix(".jpg"))
    if str(video).lower().endswith((".jpg", ".jpeg", ".png")):
        im = Image.open(video).convert("RGB").resize((1080, 1920))
    else:
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "f.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(at), "-i", video, "-frames:v", "1", str(f)], check=True)
            im = Image.open(f).convert("RGB").resize((1080, 1920))
    # darken the middle band so the title pops
    shade = Image.new("L", im.size, 0)
    ImageDraw.Draw(shade).rectangle((0, 560, 1080, 1180), fill=150)
    im = Image.composite(Image.new("RGB", im.size, (5, 10, 20)), im, shade.filter(ImageFilter.GaussianBlur(90)))
    d = ImageDraw.Draw(im)
    size = 120
    while True:
        font = ImageFont.truetype(FONT, size)
        lines = wrap(d, title.upper(), font, 940)
        if len(lines) <= 3 or size <= 70:
            break
        size -= 8
    lh = int(size * 1.15)
    y = 870 - lh * len(lines) // 2
    for ln in lines:
        d.text((540, y), ln, font=font, fill=(255, 197, 61), anchor="ma", stroke_width=10, stroke_fill=(10, 10, 14))
        y += lh
    im.save(out, "JPEG", quality=90)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]), sys.argv[3], *(sys.argv[4:5]))
