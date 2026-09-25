#!/usr/bin/env python3
"""Generate the shared iPhone/watchOS icon: a centered pixel play symbol.

The opaque square is masked by each platform. Keep the same navy and blue
halftone palette as the video display, with no clock strip displacing the mark.

    python make_icon.py --preview
"""

import argparse
import json
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ICONSET = os.path.join(HERE, "WatchTV", "Assets.xcassets", "AppIcon.appiconset")
ACCENTSET = os.path.join(HERE, "WatchTV", "Assets.xcassets", "AccentColor.colorset")

# ---------------------------------------------------------------- the palette
# Colors retained from the original Seiko prototype.
SCREEN_BG = (0x10, 0x30, 0x5E)
SCREEN_INK = (0x93, 0xCE, 0xFF)

S = 1024          # final icon side
SS = 4            # supersampling factor for the vector pass
LEVELS = 6        # same as codec.NTILES

# Center the visible triangle bounds in the full icon, leaving ample room
# for both the circular Watch mask and the rounded iPhone mask.
COLS, ROWS = 16, 16
CELL = S / float(COLS)
GRID_TOP = 0

# Coverage below this much of a cell is dropped, and what survives is pushed to
# the top levels. At 1024 the faint outliers of a true halftone look like fine
# grain; at 44 px they are indistinguishable from noise, and they cost the
# triangle its edge. Chunky cells keep the codec's stepped silhouette legible.
MIN_COVER = 0.30


def _cover_grid(poly):
    """Per-cell coverage of `poly` (icon pixel coords), supersampled."""
    f = 16
    m = Image.new("L", (COLS * f, ROWS * f), 0)
    ImageDraw.Draw(m).polygon(
        [((x / CELL) * f, ((y - GRID_TOP) / CELL) * f) for x, y in poly],
        fill=255)
    small = m.resize((COLS, ROWS), Image.BOX)   # box filter == area coverage
    return [[small.getpixel((c, r)) / 255.0 for c in range(COLS)]
            for r in range(ROWS)]


def draw_icon():
    img = Image.new("RGB", (S * SS, S * SS), SCREEN_BG)
    d = ImageDraw.Draw(img)
    tri = [(5 * CELL, 4 * CELL),
           (5 * CELL, 12 * CELL),
           (11 * CELL, 8 * CELL)]
    cov = _cover_grid(tri)
    cell, top, rows, cols = CELL, GRID_TOP, ROWS, COLS
    squares = []
    for r in range(rows):
        for c in range(cols):
            if cov[r][c] < MIN_COVER:
                continue
            # Remap [MIN_COVER, 1] onto the top half of the level range, so a
            # cell that survives is always a solid square rather than a speck.
            t = (cov[r][c] - MIN_COVER) / (1.0 - MIN_COVER)
            level = int(round((LEVELS - 1) * (0.6 + 0.4 * t)))
            frac = level / float(LEVELS - 1)
            side = cell * frac
            cx = (c + 0.5) * cell
            cy = top + (r + 0.5) * cell
            squares.append((cx - side / 2, cy - side / 2,
                            cx + side / 2, cy + side / 2))
    dx = (S - min(q[0] for q in squares) - max(q[2] for q in squares)) / 2
    dy = (S - min(q[1] for q in squares) - max(q[3] for q in squares)) / 2
    for x0, y0, x1, y1 in squares:
        d.rectangle([(x0 + dx) * SS, (y0 + dy) * SS,
                     (x1 + dx) * SS - 1, (y1 + dy) * SS - 1], fill=SCREEN_INK)

    return img.resize((S, S), Image.LANCZOS)


def circular_preview(img, sizes=(1024, 88, 48, 44)):
    """What watchOS actually shows: the icon under a circular mask."""
    mask = Image.new("L", (S * 4, S * 4), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, S * 4 - 1, S * 4 - 1], fill=255)
    mask = mask.resize((S, S), Image.LANCZOS)
    base = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    base.paste(img, (0, 0), mask)

    pad = 24
    w = sum(s + pad for s in sizes) + pad
    h = max(sizes) + 2 * pad
    sheet = Image.new("RGB", (w, h), (0x44, 0x44, 0x46))
    x = pad
    for s in sizes:
        sheet.paste(base.resize((s, s), Image.LANCZOS),
                    (x, (h - s) // 2), base.resize((s, s), Image.LANCZOS))
        x += s + pad
    return sheet


CONTENTS = {
    "images": [{
        "filename": "AppIcon-1024.png",
        "idiom": "universal",
        "platform": "watchos",
        "size": "1024x1024",
    }],
    "info": {"author": "xcode", "version": 1},
}

ACCENT = {
    "colors": [{
        "color": {
            "color-space": "srgb",
            "components": {"alpha": "1.000", "blue": "1.000",
                           "green": "0.808", "red": "0.576"},
        },
        "idiom": "universal",
    }],
    "info": {"author": "xcode", "version": 1},
}

CATALOG = {"info": {"author": "xcode", "version": 1}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    os.makedirs(ICONSET, exist_ok=True)
    os.makedirs(ACCENTSET, exist_ok=True)

    icon = draw_icon()
    # No alpha: an app icon with an alpha channel is rejected by App Store
    # Connect, and watchOS supplies the circular mask itself.
    icon.convert("RGB").save(os.path.join(ICONSET, "AppIcon-1024.png"))
    phone_iconset = os.path.join(HERE, "WatchTV", "PhoneApp", "PhoneAssets.xcassets", "AppIcon.appiconset")
    os.makedirs(phone_iconset, exist_ok=True)
    icon.convert("RGB").save(os.path.join(phone_iconset, "AppIcon-1024.png"))

    with open(os.path.join(ICONSET, "Contents.json"), "w") as fh:
        json.dump(CONTENTS, fh, indent=2)
        fh.write("\n")
    with open(os.path.join(ACCENTSET, "Contents.json"), "w") as fh:
        json.dump(ACCENT, fh, indent=2)
        fh.write("\n")
    with open(os.path.join(HERE, "WatchTV", "Assets.xcassets", "Contents.json"), "w") as fh:
        json.dump(CATALOG, fh, indent=2)
        fh.write("\n")

    print("wrote", os.path.join(ICONSET, "AppIcon-1024.png"))

    if args.preview:
        out = os.path.join(HERE, "out")
        os.makedirs(out, exist_ok=True)
        p = os.path.join(out, "icon_preview.png")
        circular_preview(icon).save(p)
        print("wrote", p)


if __name__ == "__main__":
    main()
