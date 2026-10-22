"""One-off: draw the 1200x630 link-preview card (app/share-card.png) used by og:image / twitter:image.

Same logo as app/favicon.svg, drawn with Pillow at 4x and scaled down. Re-run only if the logo or tagline changes:
    .venv/Scripts/python ingestion/oneoff/make_share_card.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[2] / "app" / "share-card.png"
W, H, S = 1200, 630, 4          # card size, supersample factor
BLUE, GOLD, BG, TEXT, MUTED = "#1F5FA8", "#F2B134", "#fbfaf7", "#1f2328", "#59636e"
FONTS = Path("C:/Windows/Fonts")


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size * S)


img = Image.new("RGB", (W * S, H * S), BG)
d = ImageDraw.Draw(img)

# logo tile (favicon.svg is a 64-unit box scaled by k)
k, ox, oy = 5.0 * S, 80 * S, 125 * S
def p(x, y): return (ox + x * k, oy + y * k)
d.rounded_rectangle([*p(0, 0), *p(64, 64)], radius=14 * k, fill=BLUE)
d.ellipse([*p(32 - 17, 25 - 20), *p(32 + 17, 25 + 20)], outline="white", width=int(4.5 * k))
d.line([p(32, 45), p(32, 58)], fill="white", width=int(6 * k))
d.ellipse([*p(29, 55), *p(35, 61)], fill="white")                    # round cap on the handle end
d.ellipse([*p(23, 14.5), *p(41, 32.5)], fill=GOLD)                   # pin head
d.polygon([p(23.9, 28), p(40.1, 28), p(32, 38)], fill=GOLD)          # pin point
d.ellipse([*p(32 - 3.2, 23.5 - 3.2), *p(32 + 3.2, 23.5 + 3.2)], fill=BLUE)

x = 500 * S
d.rectangle([x, 150 * S, x + 90 * S, 158 * S], fill=GOLD)
d.text((x, 185 * S), "CourtConnect", font=font("segoeuib.ttf", 92), fill=TEXT)
d.text((x, 285 * S), "CalNeva", font=font("segoeuib.ttf", 92), fill=BLUE)
d.text((x, 415 * S), "Where to play racket sports", font=font("segoeui.ttf", 40), fill=TEXT)
d.text((x, 465 * S), "in California + Nevada", font=font("segoeui.ttf", 40), fill=TEXT)
d.text((x, 535 * S), "Tennis · pickleball · padel · squash · badminton · more", font=font("segoeui.ttf", 26), fill=MUTED)

img.resize((W, H), Image.LANCZOS).save(OUT, optimize=True)
print("wrote", OUT, OUT.stat().st_size, "bytes")
