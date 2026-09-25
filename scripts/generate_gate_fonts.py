"""Generate the production full-frame and half-frame PNG mask fonts."""
from pathlib import Path
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

def make_font(period, family, output, rows=54):
    height = rows * 32
    output.parent.mkdir(parents=True, exist_ok=True)
    digits = [f'digit{i}' for i in range(10)]
    frames = [f'frame{i:02d}' for i in range(period)]
    order = ['.notdef', 'space', 'colon'] + digits + frames
    glyphs = {name: TTGlyphPen(None).glyph() for name in order}
    pen = TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.lineTo((0, height))
    pen.lineTo((3072, height))
    pen.lineTo((3072, 0))
    pen.closePath()
    glyphs[frames[0]] = pen.glyph()
    metrics = {name: (3072, 0) for name in order}
    metrics['space'] = metrics['colon'] = (0, 0)
    b = FontBuilder(2048, isTTF=True)
    b.setupGlyphOrder(order)
    b.setupCharacterMap({32: 'space', 58: 'colon', **{ord(str(i)): digits[i] for i in range(10)}})
    b.setupGlyf(glyphs)
    b.setupHorizontalMetrics(metrics)
    b.setupHorizontalHeader(ascent=height, descent=0, lineGap=0)
    b.setupNameTable({'familyName': family, 'styleName': 'Regular',
                     'uniqueFontIdentifier': family + '-Regular-1',
                     'fullName': family + ' Regular', 'psName': family + '-Regular',
                     'version': 'Version 1.000'})
    b.setupOS2(sTypoAscender=height, sTypoDescender=0, sTypoLineGap=0,
               usWinAscent=height, usWinDescent=0)
    b.setupPost()
    pairs = '\n'.join(f'sub digit{i // 10} digit{i % 10} by frame{i % period:02d};' for i in range(60))
    b.addOpenTypeFeatures('''
        languagesystem DFLT dflt;
        languagesystem latn dflt;
        @images = [%s];
        @clock = [@images colon];
        feature rlig {
            lookup Seconds { %s } Seconds;
            lookup HidePrefix { sub @images' @clock by space; } HidePrefix;
        } rlig;
    ''' % (' '.join(digits + frames), pairs))
    b.save(output)
    print('Gate font:', (output).stat().st_size, 'bytes')


if __name__ == "__main__":
    make_font(30, "FontTVGate", Path("WatchTV/Shared/FontTVGate.ttf"))
    make_font(30, "FontTVGateHalf", Path("WatchTV/Shared/FontTVGateHalf.ttf"), rows=27)
