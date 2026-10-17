"""Fetch a small aerial-imagery crop around each point, with true-scale court outlines drawn on it.

Why: OSM `sport=` tags on unnamed courts often come from mappers guessing off aerial photos (2026-10-17 padel audit:
Bakersfield CC, San Juan School and others tagged padel were pickleball). Court SIZE separates the sports even when
walls and lines are hard to see, so each crop shows reference outlines at the same scale:
  red    padel                      10.0 x 20.0 m
  yellow pickleball / paddle tennis  6.1 x 13.4 m
  white  tennis                     11.0 x 23.8 m

Usage (needs pillow: `pip install pillow`; run in a scratch folder, never commit the images):
  python ingestion/imagery_crop.py OUT_DIR name:lat:lon [name:lat:lon ...]
Then open the .jpg files and judge by size; record the imagery date and `viewed on` in the seed `evidence`.

Imagery: Esri World Imagery tiles (zoom 19 by default, about 0.25-0.3 m per pixel; set IMG_ZOOM=20 where it exists). Viewing for verification only: tiles are not
stored in the repo and nothing is exported from them (docs/padel_scan.md). Look up the capture date with the layer's
metadata query (World_Imagery/MapServer/<layer>/query, field SRC_DATE2) and quote it in the evidence.
"""
import io
import math
import os
import sys
import urllib.request

from PIL import Image, ImageDraw

UA = "courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)"
Z = int(os.environ.get("IMG_ZOOM", 19))   # 19 everywhere; 20 exists in some cities (about 0.15 m per pixel)
TILE = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
GROUND = 0.2986 * 2 ** (19 - Z)  # metres per pixel at the equator, 256 px tiles
SCALE = 3        # output upscaling
OUTLINES = ((10.0, 20.0, (255, 40, 40)), (6.1, 13.4, (255, 230, 0)), (10.97, 23.77, (255, 255, 255)))


def crop(lat: float, lon: float) -> Image.Image:
    n = 2 ** Z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    tx, ty = int(x), int(y)
    img = Image.new("RGB", (768, 768))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            req = urllib.request.Request(TILE.format(z=Z, y=ty + dy, x=tx + dx), headers={"User-Agent": UA})
            tile = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")
            img.paste(tile, ((dx + 1) * 256, (dy + 1) * 256))
    cx, cy = int((x - tx + 1) * 256), int((y - ty + 1) * 256)
    im = img.crop((cx - 130, cy - 100, cx + 130, cy + 100)).resize((260 * SCALE, 200 * SCALE), Image.LANCZOS)
    ppm = SCALE / (GROUND * math.cos(math.radians(lat)))  # output pixels per metre
    draw = ImageDraw.Draw(im)
    x0 = 12
    for w, h, col in OUTLINES:
        draw.rectangle((x0, 12, x0 + w * ppm, 12 + h * ppm), outline=col, width=2)
        x0 += w * ppm + 12
    draw.text((14, 12 + 24 * ppm + 2), "red=padel 10x20m  yellow=pickleball 6x13m  white=tennis 11x24m", fill=(255, 255, 255))
    return im


def main() -> None:
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for arg in sys.argv[2:]:
        name, lat, lon = arg.split(":")
        crop(float(lat), float(lon)).save(os.path.join(out, name + ".jpg"), quality=90)
        print(name, "ok")


if __name__ == "__main__":
    main()
