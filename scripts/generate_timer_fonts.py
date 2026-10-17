#!/usr/bin/env python3
"""Generate reproducible 30/60-second timer gates, full and half height.

Adapted from AniWeather's make-gate-font.py: staggered one-second gates select
opaque frames at 2 fps without requiring WidgetKit updates for every frame.
The 60-second gate is visible at :00 only; the 30-second gate at :00 and :30.
"""
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

def generate(output, period, rows):
    family = f"TVWatchGate{period}" + ("Half" if rows == 27 else "")
    height = rows * 32
    digits = [f"digit{i}" for i in range(10)]
    frames = [f"frame{i:02d}" for i in range(period)]
    order = [".notdef", "space", "colon"] + digits + frames
    glyphs = {name: TTGlyphPen(None).glyph() for name in order}
    pen = TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.lineTo((0, height))
    pen.lineTo((3072, height))
    pen.lineTo((3072, 0))
    pen.closePath()
    glyphs[frames[0]] = pen.glyph()
    metrics = {name: (3072, 0) for name in order}
    metrics["space"] = metrics["colon"] = (0, 0)
    builder = FontBuilder(2048, isTTF=True)
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap({32: "space", 58: "colon", **{ord(str(i)): digits[i] for i in range(10)}})
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=height, descent=0, lineGap=0)
    builder.setupNameTable({"familyName": family, "styleName": "Regular", "uniqueFontIdentifier": family + "-Regular-1",
                            "fullName": family + " Regular", "psName": family + "-Regular", "version": "Version 1.000"})
    builder.setupOS2(sTypoAscender=height, sTypoDescender=0, sTypoLineGap=0, usWinAscent=height, usWinDescent=0)
    builder.setupPost()
    pairs = "\n".join(f"sub digit{i // 10} digit{i % 10} by frame{i % period:02d};" for i in range(60))
    # `rlig`, not `liga`: timer text disables standard ligatures.
    builder.addOpenTypeFeatures("""
        languagesystem DFLT dflt;
        languagesystem latn dflt;
        @images = [%s];
        @clock = [@images colon];
        feature rlig {
            lookup Seconds { %s } Seconds;
            lookup HidePrefix { sub @images' @clock by space; } HidePrefix;
        } rlig;
    """ % (" ".join(digits + frames), pairs))
    # Fixed timestamps keep the committed font reproducible (2026-01-01).
    builder.font["head"].created = builder.font["head"].modified = 3850070400
    builder.font.recalcTimestamp = False
    output.parent.mkdir(parents=True, exist_ok=True)
    builder.save(output)
    print(f"{output}: {output.stat().st_size} bytes")


if __name__ == "__main__":
    directory = Path(__file__).resolve().parents[1] / "WatchTV/Shared/TimerFonts"
    for period in (30, 60):
        for rows in (54, 27):
            name = f"TVWatchGate{period}" + ("Half" if rows == 27 else "")
            generate(directory / (name + ".ttf"), period, rows)
