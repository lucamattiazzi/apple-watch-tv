"""Exploratory redesigns of the five included screensavers, three variants each.

Same contract as screensaver_art.render: native 256×144 drawing; 'color' frames are
256×144 sRGB, 'bw' frames are 192×108 with eight gray levels, and every loop closes
at 30 s (60 frames at 2 fps). Every palette entry carries an authored gray value.
"""
from functools import lru_cache
from math import sin, cos, pi, sqrt, atan, atan2, floor, exp, hypot
from PIL import Image, ImageColor, ImageDraw

try:
    from .screensaver_art import ACTIONS, COLORS, Canvas, palm
except ImportError:
    from screensaver_art import ACTIONS, COLORS, Canvas, palm

TAU = 2 * pi
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def noise(*values):
    """Deterministic hash in [0, 1)."""
    n = 0x9E3779B9
    for value in values:
        n = ((n ^ (int(value) & 0xffffffff)) * 0x45d9f3b) & 0xffffffff
        n ^= n >> 16
    return (n & 0xffff) / 65536


def smooth(x):
    x = min(max(x, 0), 1)
    return x * x * (3 - 2 * x)


class Scene(Canvas):
    """Canvas with a per-scene palette, fast pixel access and ordered dithering."""

    def __init__(self, style, palette=None, background='ink', base=None, mode='RGB'):
        self.style, self.mode = style, mode
        self.palette = {**COLORS, **(palette or {})}
        if base is not None:
            self.image = base.copy()
        elif mode == 'RGBA':
            self.image = Image.new('RGBA', (256, 144), (0, 0, 0, 0))
        else:
            self.image = Image.new('RGB', (256, 144), self.c(background))
        self.d = ImageDraw.Draw(self.image)
        self.pix = self.image.load()
        self.tones = {}

    def c(self, name):
        color, gray = self.palette[name]
        return color if self.style == 'color' else (gray, gray, gray)

    def tone(self, name):
        if name not in self.tones:
            color = self.c(name)
            rgb = ImageColor.getrgb(color) if isinstance(color, str) else color
            self.tones[name] = rgb + (255,) if self.mode == 'RGBA' else rgb
        return self.tones[name]

    def px(self, x, y, name):
        x, y = int(x), int(y)
        if 0 <= x < 256 and 0 <= y < 144:
            self.pix[x, y] = self.tone(name)

    def dither(self, x, y, amount):
        # B/W is resampled to 192×108, which would scramble a Bayer pattern: use a hard edge.
        return amount > (.5 if self.style == 'bw' else (BAYER[int(y) & 3][int(x) & 3] + .5) / 16)

    def ramp(self, x, y, names, value):
        value = min(max(value, 0), 1) * (len(names) - 1)
        i = min(int(value), len(names) - 2)
        self.px(x, y, names[i + 1] if self.dither(x, y, value - i) else names[i])

    def halo(self, cx, cy, r0, r1, name, strength=.8, y_max=144):
        for y in range(max(0, int(cy - r1)), min(y_max, int(cy + r1) + 1)):
            for x in range(max(0, int(cx - r1)), min(256, int(cx + r1) + 1)):
                d = hypot(x - cx, y - cy)
                if r0 <= d <= r1 and self.dither(x, y, strength * (1 - (d - r0) / (r1 - r0))):
                    self.px(x, y, name)

    def paste(self, layer):
        self.image.paste(layer, (0, 0), layer)


def stars(c, count, seed, y_max=144, names=('stardim', 'star')):
    for i in range(count):
        x, y = int(noise(seed, i, 1) * 256), int(noise(seed, i, 2) * y_max)
        c.px(x, y, names[noise(seed, i, 3) > .8])


def twinkle(c, f, count, seed, y_max=144, name='star'):
    for i in range(count):
        if noise(seed, i, f // 2) > .55:
            continue
        x, y = int(noise(seed, i, 1) * 256), int(noise(seed, i, 2) * y_max)
        if noise(seed, i, 3) > .8:
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                c.px(x + dx, y + dy, 'stardim')
            c.px(x, y, name)


# ─── Isola deserta ──────────────────────────────────────────────────────────────

ISLAND_PALETTES = {
    'giorno': {
        'shirtshade': ('#c9c2aa', 182), 
        'sky0': ('#3f86c6', 109), 'sky1': ('#74b6dc', 146), 'sky2': ('#c2e6e4', 182),
        'sun': ('#fffbe6', 255), 'sunhalo': ('#e2f4ec', 219), 'far': ('#5e9cbc', 146),
        'seahz': ('#4aa3c4', 109), 'sea': ('#2a6a9e', 73), 'deep': ('#173c6c', 36),
        'wave': ('#3c86b4', 109), 'glint': ('#f4fff8', 255), 'water': ('#4fc0c8', 146),
        'foam': ('#d0f6ea', 219), 'sandwet': ('#c49660', 109), 'cloud': ('#f8fcf6', 255),
        'cloudshade': ('#c4dce8', 182), 'bird': ('#f4f4ec', 255), 'shell': ('#f0a090', 219),
    },
    'tramonto': {
        'shirtshade': ('#cc9c8e', 146), 
        'sky0': ('#2a1f4d', 36), 'sky1': ('#5c3570', 73), 'sky2': ('#b04f6e', 109),
        'sky3': ('#ec7f5a', 146), 'sky4': ('#ffc27a', 219), 'sun': ('#fff3c4', 255),
        'sunhalo': ('#ffd890', 219), 'far': ('#3e2452', 36),
        'seahz': ('#a04a72', 109), 'sea': ('#4e2c64', 73), 'deep': ('#281c46', 36),
        'wave': ('#6a3a72', 73), 'glint': ('#ffe2a0', 255), 'water': ('#b05e78', 109),
        'foam': ('#ffc6a2', 219), 'sandwet': ('#8a5062', 73), 'sand': ('#da946a', 146),
        'sandlight': ('#f6bc86', 182), 'sandshade': ('#9a5a5c', 109), 'wood': ('#3a2232', 36),
        'bark': ('#7a3e46', 73), 'leafdark': ('#1e1430', 0), 'leaf': ('#3a2848', 36),
        'leaflight': ('#e2825a', 146), 'cloud': ('#ffb4a0', 182), 'cloudshade': ('#9c4c72', 109),
        'white': ('#fff0d8', 255), 'skin': ('#c87058', 109), 'skinlight': ('#f0a070', 182),
        'shirt': ('#f6d4bc', 219), 'cloth': ('#7a3050', 73), 'bird': ('#2a1a36', 0),
        'shell': ('#ffc0a0', 219),
    },
    'notte': {
        'shirtshade': ('#9298b4', 146), 
        'sky0': ('#04071a', 0), 'sky1': ('#0b1434', 36), 'sky2': ('#1a2a58', 73),
        'sun': ('#f6f2dc', 255), 'sunhalo': ('#24366a', 73), 'crater': ('#c8c2aa', 182),
        'star': ('#eef0ff', 255), 'stardim': ('#6a78a8', 109), 'far': ('#070c24', 0),
        'seahz': ('#22356a', 73), 'sea': ('#111f48', 36), 'deep': ('#08102c', 0),
        'wave': ('#1c3062', 73), 'glint': ('#d4dcf4', 219), 'water': ('#1c4878', 73),
        'foam': ('#72eada', 182), 'sandwet': ('#363f62', 73), 'sand': ('#7a82a4', 146),
        'sandlight': ('#a2a9c4', 182), 'sandshade': ('#4a5274', 73), 'wood': ('#282236', 36),
        'bark': ('#585070', 73), 'leafdark': ('#081420', 0), 'leaf': ('#16363f', 36),
        'leaflight': ('#4a8894', 109), 'cloud': ('#3c4c7c', 73), 'cloudshade': ('#18224a', 36),
        'white': ('#e8ecff', 255), 'skin': ('#a08898', 146), 'skinlight': ('#ccb4bc', 182),
        'shirt': ('#d6dcee', 219), 'cloth': ('#5a3a66', 73), 'shell': ('#9aa4c8', 146),
    },
}
ISLAND_GRADIENTS = {
    'giorno': (('sky0', 'sky1', 'sky2'), ('seahz', 'sea', 'deep')),
    'tramonto': (('sky0', 'sky1', 'sky2', 'sky3', 'sky4'), ('seahz', 'sea', 'deep')),
    'notte': (('sky0', 'sky1', 'sky2'), ('seahz', 'sea', 'deep')),
}
HORIZON = 59


@lru_cache(None)
def island_backdrop(theme, style):
    c = Scene(style, ISLAND_PALETTES[theme])
    sky, sea = ISLAND_GRADIENTS[theme]
    for y in range(HORIZON):
        for x in range(256):
            c.ramp(x, y, sky, (y / (HORIZON - 1)) ** (1.4 if theme == 'tramonto' else 1))
    if theme == 'giorno':
        c.halo(222, 17, 7, 17, 'sunhalo', .7)
        c.oval((215, 10, 229, 24), 'sun')
    elif theme == 'tramonto':
        c.halo(64, 58, 14, 36, 'sunhalo', .75, HORIZON)
        c.oval((50, 44, 78, 72), 'sun')
    else:
        stars(c, 90, 7, HORIZON - 8)
        c.halo(58, 22, 8, 19, 'sunhalo', .7)
        c.oval((50, 14, 66, 30), 'sun')
        for x, y, r in ((55, 19, 2), (61, 24, 1.5), (54, 26, 1)):
            c.oval((x - r, y - r, x + r, y + r), 'crater')
    for y in range(HORIZON, 144):
        for x in range(256):
            c.ramp(x, y, sea, ((y - HORIZON) / 60) ** .8)
    # A second, distant island keeps the horizon from reading as an empty line.
    c.poly([(12, HORIZON), (20, 56), (31, 54), (43, 55), (52, HORIZON)], 'far')
    c.line([(36, 55), (38, 47)], 'far')
    for dx, dy in ((-5, 1), (5, 1), (-3, -2), (4, -2)):
        c.line([(38, 47), (38 + dx, 47 + dy)], 'far')
    c.line([(0, HORIZON), (255, HORIZON)], 'glint' if theme != 'notte' else 'wave')
    return c.image


def puff(c, x, y, s, shade, light):
    blobs = ((0, 0, 10), (11, -4, 12), (24, -1, 9), (34, 2, 6), (-9, 2, 6))
    for dx, dy, r in blobs:
        c.oval((x + (dx - r) * s, y + (dy - r * .6) * s, x + (dx + r) * s, y + (dy + r * .6) * s), shade)
    for dx, dy, r in blobs:
        c.oval((x + (dx - r * .8) * s, y + (dy - r * .62 - 1) * s,
                x + (dx + r * .75) * s, y + (dy + r * .2 - 1) * s), light)


def island_sky(c, theme, t, f, phase):
    if theme == 'giorno':
        puff(c, 26 + 5 * sin(phase), 22, 1, 'cloudshade', 'cloud')
        puff(c, 96 + 4 * sin(phase + 2), 12, .6, 'cloudshade', 'cloud')
        puff(c, 168 + 3 * sin(phase + 4), 36, .45, 'cloudshade', 'cloud')
        for k in range(2):
            x, y = 70 + 26 * cos(phase + k * 2.4), 34 + 5 * sin(2 * phase + k)
            flap = 2 if (f + k) % 2 else 0
            c.line([(x - 4, y - flap), (x - 1, y), (x, y + 1), (x + 1, y), (x + 4, y - flap)], 'bird')
    elif theme == 'tramonto':
        # Long strata lit from below by the setting sun.
        for x, y, w in ((-10, 18, 90), (110, 12, 70), (150, 30, 110), (20, 38, 60), (190, 44, 80)):
            x += 4 * sin(phase + y)
            c.rect((x, y, x + w, y + 1), 'cloudshade')
            c.rect((x + 4, y + 2, x + w - 6, y + 2), 'cloud')
        for k in range(3):
            x, y = 120 + 30 * cos(phase + k * 2), 26 + 4 * sin(2 * phase + k)
            flap = 2 if (f + k) % 2 else 0
            c.line([(x - 3, y - flap), (x, y + 1), (x + 3, y - flap)], 'bird')
    else:
        twinkle(c, f, 26, 7, HORIZON - 8)
        for x, y, s in ((120 + 5 * sin(phase), 16, .8), (200 + 4 * sin(phase + 1), 34, .5)):
            puff(c, x, y, s, 'cloudshade', 'cloud')
        if f in (40, 41):
            x = 214 - (f - 40) * 16
            c.line([(x, 8 + (f - 40) * 6), (x - 14, 14 + (f - 40) * 6)], 'white')


def island_sea(c, theme, t, f, phase):
    for i in range(46):
        y = HORIZON + 3 + (i * 17) % 82
        depth = (y - HORIZON) / 85
        x = (i * 61) % 300 - 22 + (2 + 5 * depth) * sin(phase * 2 + i)
        length = 3 + 14 * depth + (i * 7) % 5
        c.line([(x, y), (x + length * .4, y - 1), (x + length, y)], 'wave')
    for i in range(30):
        if (f + i * 7) % 12 < 3:
            x, y = noise(9, i, 1) * 256, HORIZON + 2 + noise(9, i, 2) * 80
            c.line([(x - 1, y), (x + 1, y)], 'glint')
    if theme in ('tramonto', 'notte'):
        sx, width = (64, 13) if theme == 'tramonto' else (58, 7)
        for y in range(HORIZON + 2, 128, 2):
            fall = (y - HORIZON) / 70
            w = width * (1 - .35 * fall) * (.6 + .5 * noise(f, y, 3))
            jitter = (noise(f, y, 4) - .5) * 6
            gap = noise(f, y, 5) * w
            c.line([(sx - w + jitter, y), (sx - gap + jitter, y)], 'glint')
            c.line([(sx + gap * .5 + jitter, y), (sx + w + jitter, y)], 'glint' if y % 4 else 'sunhalo')


def island_body(c, theme, t, f, phase):
    c.oval((54, 88, 216, 128), 'water')
    for i in range(48):
        a = i * TAU / 48
        x, y = 135 + 70 * cos(a), 107 + 15 * sin(a)
        if (i + f // 2) % 3 == 0:
            c.px(x, y, 'foam')
    swell = 1.5 + 1.5 * sin(phase * 4)
    c.d.ellipse((62 - swell, 91 - swell / 3, 208 + swell, 121 + swell / 3), outline=c.c('foam'))
    c.poly([(63, 110), (73, 100), (95, 95), (145, 92), (183, 97), (204, 106), (200, 114),
            (178, 120), (126, 122), (86, 118)], 'sandwet')
    c.poly([(66, 109), (75, 101), (96, 96), (145, 94), (181, 98), (201, 106), (198, 113),
            (177, 118), (126, 120), (88, 116)], 'sandshade')
    c.poly([(67, 107), (78, 101), (101, 96), (147, 95), (177, 98), (199, 105), (192, 112),
            (153, 116), (113, 116), (84, 113)], 'sand')
    c.poly([(81, 103), (112, 98), (163, 99), (185, 103), (180, 108), (118, 111), (85, 109)], 'sandlight')
    for i in range(40):
        x, y = 83 + (i * 43) % 104, 104 + (i * 7) % 10
        c.px(x, y, 'sandshade' if i % 4 else 'sandlight')
    for x, y in ((92, 111), (186, 108)):
        c.line([(x - 1, y), (x + 1, y)], 'shell')
        c.px(x, y - 1, 'shell')
    if theme == 'tramonto':
        c.poly([(160, 106), (170, 104), (215, 111), (206, 113)], 'sandshade')
    else:
        c.oval((150, 104, 184, 111), 'sandshade')
    palm(c, t)
    c.line([(66, 118), (81, 121), (117, 123)], 'foam')
    c.line([(164, 121), (196, 117), (207, 111)], 'foam')


# Castaway sprite, facing right; rows are listed top-down from the given offset.
# W cap highlight, w cap/shirt, L shirt shade, h hair, b beard, B beard highlight,
# S face, s skin, e eye, c shorts.
CASTAWAY_HEAD = (-4, -26, (
    '..WWWW....',
    '.WwwwwwW..',
    '.wwwwwwwww',
    '.hhSSSSS..',
    '.hsSSSeS..',
    '.hsSSSSSs.',
    '.hhsSbbS..',
    '..hbBbBbb.',
    '..hbbbbb..',
    '...bBbb...',
))
CASTAWAY_TORSO = (-3, -17, (
    '.wwwww.',
    'wwwwwww',
    'Lwwwwww',
    'Lwwwwww',
    'Lwwwwww',
    'Lwwswww',
    'LwwwwwL',
    'w.wLw.w',
    'ccccccc',
    'ccccccc',
    'cc...cc',
))
CASTAWAY_TONES = {'W': 'white', 'w': 'shirt', 'L': 'shirtshade', 'h': 'wood', 'b': 'wood',
                  'B': 'bark', 'S': 'skinlight', 's': 'skin', 'e': 'ink', 'c': 'cloth'}
SEATED = ('read', 'sit', 'build', 'hammer')


def castaway(c, x, y, t, pose='idle', facing=1):
    """26-pixel castaway built on a sprite grid, then outlined as one silhouette."""
    f = round(t * 2)
    cells = {}

    def put(dx, dy, tone):
        cells[dx, dy] = tone

    def sprite(part, shift):
        ox, oy, rows = part
        for row, line in enumerate(rows):
            for col, key in enumerate(line):
                if key != '.':
                    put(ox + col, oy + row + shift, CASTAWAY_TONES[key])

    def limb(points, tone, thick=False):
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            steps = max(abs(x1 - x0), abs(y1 - y0), 1)
            for i in range(steps + 1):
                px, py = round(x0 + (x1 - x0) * i / steps), round(y0 + (y1 - y0) * i / steps)
                put(px, py, tone)
                if thick:
                    put(px + 1, py, tone)

    def leg(hip, knee, ankle, tone):
        limb([hip, knee, ankle], tone, True)
        put(ankle[0], ankle[1] + 1, tone); put(ankle[0] + 1, ankle[1] + 1, tone); put(ankle[0] + 2, ankle[1] + 1, tone)

    if pose == 'sleep':
        breathe = -1 if f % 4 < 2 else 0
        limb([(-13, -2), (-10, -5), (-7, -2)], 'skin', True)
        limb([(-13, -1), (-7, -1)], 'skinlight')
        for dx in range(-6, -2):
            for dy in range(-4, 0): put(dx, dy, 'cloth')
        for dx in range(-2, 6):
            for dy in range(-5 + (breathe if 0 <= dx <= 4 else 0), 0): put(dx, dy, 'shirt' if dy < -1 else 'shirtshade')
        limb([(0, -4), (4, -5)], 'skinlight')
        for dx in range(6, 8):
            for dy in range(-5, 0): put(dx, dy, 'wood')
        put(5, -2, 'bark'); put(6, -3, 'bark')
        for dx in range(8, 12):
            for dy in range(-6, -1): put(dx, dy, 'skinlight')
        put(9, -7, 'skinlight'); put(9, -4, 'ink'); put(10, -4, 'ink')
        for dy in range(-6, -1): put(12, dy, 'white'); put(13, dy, 'shirt')
        put(11, -1, 'wood'); put(12, -1, 'wood')
    else:
        shift = 5 if pose in SEATED else 0
        bob = -1 if pose in ('walk', 'run') and f % 2 else 0
        stride = (2 if pose == 'walk' else 3) * (1 if f % 2 else -1) if pose in ('walk', 'run') else 0
        swing = stride // 2
        arms = {
            'idle': ((-4, -13), (-4, -10), (4, -13), (4, -10)),
            'walk': ((-4 - swing, -13), (-4 - 2 * swing, -10), (4 + swing, -13), (4 + 2 * swing, -10)),
            'run': ((-5, -14), (-3 - swing, -11), (5, -14), (6 + swing, -12)),
            'fish': ((1, -12), (6, -14), (5, -13), (8, -15)),
            'look': ((3, -13), (6, -19), (5, -15), (8, -20)),
            'wave': ((-4, -13), (-4, -10), (6, -19), (6 + f % 2 * 2, -23)),
            'shake': ((2, -19), (5, -22 + f % 2), (5, -18), (8, -21 + f % 2)),
            'throw': ((-4, -13), (-4, -10)) + (((4, -20), (7, -24)) if int(t) % 2 else ((5, -14), (9, -15))),
            'read': ((-1, -11), (2, -13), (5, -11), (8, -13)),
            'sit': ((2, -12), (5, -11), (4, -12), (6, -10)),
            'build': ((3, -12), (7, -11), (6, -12), (10, -14 if f % 2 else -10)),
            'hammer': ((-4, -13), (-4, -10), (5, -13), (9, -16 + f % 2 * 3)),
        }
        be, bh, fe, fhand = arms.get(pose, arms['idle'])
        sh = shift
        limb([(-3, -16 + sh), (be[0], be[1] + sh), (bh[0], bh[1] + sh)], 'skin')
        if shift:
            leg((-1, -3), (4, -6), (6, -2), 'skin')
            leg((1, -3), (6, -5), (8, -2), 'skinlight')
        else:
            leg((-2, -7), (-2 - stride // 2 + 1, -4), (-2 - stride, -2), 'skin')
        sprite(CASTAWAY_TORSO, sh)
        if not shift:
            leg((1, -7), (1 + stride // 2 + 1, -4), (1 + stride, -2), 'skinlight')
        sprite(CASTAWAY_HEAD, sh)
        limb([(3, -16 + sh), (fe[0], fe[1] + sh), (fhand[0], fhand[1] + sh)], 'skin')
        put(bh[0], bh[1] + sh, 'skinlight'); put(fhand[0], fhand[1] + sh, 'skinlight')
        cells = {(dx, dy + bob): tone for (dx, dy), tone in cells.items()}
    outline = {(dx + ox, dy + oy) for dx, dy in cells for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - set(cells)
    for dx, dy in outline:
        c.px(x + dx * facing, y + dy, 'ink')
    for (dx, dy), tone in cells.items():
        c.px(x + dx * facing, y + dy, tone)
    if pose == 'sleep' and int(t) % 4 < 3:
        c.text((x + 10 * facing, y - 19 - int(t) % 4 * 2), 'z')


def island_cast(c, t, episode):
    """The twelve vignettes of screensaver_art.island, unchanged."""
    action = ACTIONS[episode]
    active = 9 <= t <= 23
    targets = {'fishing': 190, 'telescope': 99, 'coconut': 160, 'sandcastle': 138, 'reading': 130,
               'sleeping': 150, 'bottle': 83, 'crab': 123, 'cooking': 137, 'seagull': 120,
               'rain': 129, 'raft': 95}
    target = targets[action]
    travel = max(0, min(1, (t - 5) / 4)) if t < 24 else max(0, (28 - t) / 4)
    x = 112 + (target - 112) * travel
    y = 109
    pose = 'walk' if 5 < t < 9 or 24 <= t < 28 else 'idle'
    facing = 1 if target > 112 else -1
    if t >= 24: facing = -facing
    if t <= 5 or t >= 28: facing = 1
    if active:
        q = t - 9
        facing = 1
        if action == 'fishing':
            pose = 'fish'; c.line([(x+8, y-16), (x+20, y-34), (x+35, y-37)], 'wood', 2)
            fy = 119 if q < 8 else 119-(q-8)*5
            c.line([(x+35, y-37), (x+40, fy)], 'white')
            c.oval((x+38, fy-1, x+42, fy+1), 'red')
            if q >= 8:
                c.poly([(x+38, fy+2), (x+42, fy+2), (x+42, fy+8), (x+48, fy+8), (x+48, fy+11), (x+37, fy+11)], 'wood')
        elif action == 'telescope':
            pose = 'look'; c.line([(x+7, y-21), (x+21, y-21)], 'goldshade', 5); c.line([(x+9, y-22), (x+21, y-22)], 'goldlight', 2)
            bx = 212-q*6
            c.poly([(bx, 69), (bx+17, 69), (bx+13, 73), (bx+4, 73)], 'ink'); c.line([(bx+8, 69), (bx+8, 60)], 'cloud'); c.poly([(bx+9, 61), (bx+9, 67), (bx+15, 67)], 'white')
        elif action == 'coconut':
            pose = 'shake' if q < 7 else 'sit'; x += int(sin(q*pi/2)*2) if q < 7 else 0
            ny = 54+min(51, max(0, q-5)*9)
            c.oval((158, ny, 164, ny+6), 'wood', 'bark')
            if q in (10, 11): c.line([(153, 78), (150, 74), (153, 72)], 'white')
        elif action == 'sandcastle':
            pose = 'build'; h = min(15, q+2)
            c.rect((153, 109-h, 177, 111), 'sandshade'); c.rect((155, 109-h, 175, 109), 'sand')
            for bx in (153, 162, 171): c.rect((bx, 105-h, bx+5, 109-h), 'sandlight')
            if q > 8: c.rect((163, 104, 168, 111), 'wood'); c.line([(174, 94), (174, 82)], 'wood'); c.poly([(175, 82), (184, 85), (175, 88)], 'red')
        elif action == 'reading':
            pose = 'read'; c.poly([(x-2, 98), (x+6, 96), (x+13, 98), (x+13, 105), (x+6, 103), (x-2, 105)], 'ink')
            c.poly([(x-1, 98), (x+6, 97), (x+12, 99), (x+12, 103), (x+6, 102), (x-1, 104)], 'sandlight')
        elif action == 'sleeping': pose = 'sleep'
        elif action == 'bottle':
            pose = 'throw' if q < 5 else 'wave'
            bx = x+9+min(90, q*7); by = 89-22*sin(min(1, q/10)*pi)+max(0, q-10)*5
            c.rect((bx, by, bx+4, by+7), 'leaf'); c.rect((bx+1, by-2, bx+3, by), 'sand'); c.rect((bx+1, by+2, bx+2, by+5), 'white')
        elif action == 'crab':
            pose = 'run'; x = 120+24*sin(q*pi/7); cx = x-13
            c.oval((cx-4, 109, cx+4, 113), 'red', 'ink'); c.line([(cx-5, 108), (cx-7, 105)], 'red', 2); c.line([(cx+5, 108), (cx+7, 105)], 'red', 2)
            for dx in (-5, 5): c.line([(cx+dx, 111), (cx+dx*1.4, 114)], 'red')
        elif action == 'cooking':
            pose = 'fish'; c.line([(x+8, 93), (x+35, 103)], 'wood', 2)
            c.line([(153, 114), (171, 109)], 'wood', 3); c.line([(155, 109), (170, 115)], 'wood', 3)
            c.poly([(155, 111), (156, 101-q % 3), (161, 105), (165, 97+q % 4), (170, 111)], 'red')
            c.poly([(159, 111), (161, 103), (166, 110)], 'goldlight')
            c.oval((160, 101, 169, 105), 'gold'); c.poly([(169, 102), (173, 100), (173, 106)], 'gold')
        elif action == 'seagull':
            pose = 'wave'; gx = x+10+q*4; gy = 78-8*sin(q*pi/14)
            c.oval((gx-3, gy, gx+5, gy+4), 'white'); c.line([(gx-1, gy), (gx-7, gy-4-q % 2*3)], 'white', 2); c.line([(gx+1, gy), (gx+9, gy-4-q % 2*3)], 'white', 2)
            c.oval((gx+1, gy+5, gx+9, gy+8), 'red')
        elif action == 'rain':
            pose = 'sit'; puff(c, 111, 51, 1, 'cloudshade', 'cloud')
            for j in range(14):
                rx = 105+j*4; ry = 62+(j*11+t*6) % 41; c.line([(rx, ry), (rx-2, ry+4)], 'foam')
            c.poly([(x-14, 82), (x-8, 73), (x, 71), (x+9, 75), (x+15, 82)], 'leaf'); c.line([(x, 77), (x, 96)], 'wood', 2)
        elif action == 'raft':
            pose = 'hammer'
            for j in range(4): c.line([(x+14, 104+j*3), (x+40, 108+j*3)], 'wood', 4); c.line([(x+14, 103+j*3), (x+40, 107+j*3)], 'bark')
            for bx in (x+20, x+33): c.line([(bx, 103), (bx-2, 117)], 'sand')
            c.line([(x+9, 98), (x+12, 88+q % 2*7)], 'wood', 2); c.rect((x+9, 86+q % 2*7, x+16, 90+q % 2*7), 'steel')
    castaway(c, x, y, t, pose, facing)
    if active and action == 'reading':
        c.d.polygon([(round(x-2), 98), (round(x+6), 97), (round(x+13), 99), (round(x+13), 105), (round(x+6), 103), (round(x-2), 105)],
                     fill=c.c('white'), outline=c.c('ink'))
        c.line([(x+6, 98), (x+6, 103)], 'red')


def island(theme, t, style, episode):
    c = Scene(style, ISLAND_PALETTES[theme], base=island_backdrop(theme, style))
    f, phase = round(t * 2), t * TAU / 30
    island_sky(c, theme, t, f, phase)
    island_sea(c, theme, t, f, phase)
    island_body(c, theme, t, f, phase)
    island_cast(c, t, episode)
    return c.finish()


# ─── Orbita ─────────────────────────────────────────────────────────────────────

def norm(x, y, z):
    length = sqrt(x * x + y * y + z * z)
    return x / length, y / length, z / length


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


SPACE = {
    'space': ('#04050c', 0), 'neb': ('#17123a', 36), 'neb2': ('#2a1a4a', 36),
    'star': ('#f0f2ff', 255), 'stardim': ('#7880a0', 109), 'hud': ('#4a5a70', 109),
}
SATURN = {**SPACE,
    'pl0': ('#0c0a14', 0), 'pl1': ('#3a2630', 36), 'pl2': ('#7a5040', 73), 'pl3': ('#b98552', 146),
    'pl4': ('#e2b97c', 182), 'pl5': ('#fbe6b0', 255), 'storm': ('#c8603e', 109),
    'rg0': ('#24222e', 36), 'rg1': ('#6e6658', 109), 'rg2': ('#b8a888', 182), 'rg3': ('#efe2c4', 255),
    'mn0': ('#10141e', 0), 'mn1': ('#4e5464', 73), 'mn2': ('#a4aab4', 182), 'mn3': ('#eef0f4', 255),
}
EARTH = {**SPACE,
    'oc0': ('#020816', 0), 'oc1': ('#0a2858', 36), 'oc2': ('#1a5a9a', 73), 'oc3': ('#3a8ccc', 109),
    'ld0': ('#08120a', 0), 'ld1': ('#24401e', 36), 'ld2': ('#4c7c34', 73), 'ld3': ('#8eac5a', 146),
    'ds1': ('#5a4424', 73), 'ds2': ('#b0905a', 146), 'ds3': ('#e0c488', 182),
    'cl0': ('#1c2434', 36), 'cl1': ('#9aaabc', 182), 'cl2': ('#f4f8ff', 255),
    'ice': ('#e4f2ff', 255), 'city': ('#ffd27a', 219), 'spec': ('#d8f0ff', 219),
    'atmo1': ('#3a78d8', 109), 'atmo2': ('#a4d8ff', 219),
    'sun': ('#fffbe8', 255), 'sunhalo': ('#3a3664', 73), 'flare': ('#5a5a9a', 109),
    'mn0': ('#10141e', 0), 'mn1': ('#4e5464', 73), 'mn2': ('#a4aab4', 182), 'mn3': ('#eef0f4', 255),
}
ECLIPSE = {**SPACE,
    'disc': ('#020308', 0), 'earthshine': ('#0c1020', 36),
    'cor0': ('#2a0c22', 36), 'cor1': ('#6a1c34', 73), 'cor2': ('#c8502e', 146),
    'cor3': ('#ffb45e', 219), 'cor4': ('#fff6dc', 255), 'blink': ('#ff5050', 146),
}


@lru_cache(None)
def space_backdrop(name, style):
    palette = {'saturno': SATURN, 'terra': EARTH, 'eclisse': ECLIPSE}[name]
    c = Scene(style, palette, 'space')
    if name != 'eclisse':
        # A faint diagonal band of nebula behind the stars.
        for y in range(144):
            for x in range(256):
                band = abs((x * .5 - y) - 10 + 14 * sin(x * .03)) / 34
                if band < 1 and c.dither(x, y, (1 - band) * .55 * (.6 + .4 * noise(x // 3, y // 3))):
                    c.px(x, y, 'neb')
    stars(c, 140, {'saturno': 1, 'terra': 2, 'eclisse': 3}[name])
    if name == 'saturno':
        c.text((10, 128), 'ORBITA / 01', 'hud')
        c.line([(9, 13), (9, 7), (23, 7)], 'hud'); c.line([(232, 136), (247, 136), (247, 129)], 'hud')
    if name == 'terra':
        c.halo(18, 16, 5, 30, 'sunhalo', .8)
        for k in range(8):
            a = k * TAU / 8 + .2
            c.line([(18 + 7 * cos(a), 16 + 7 * sin(a)), (18 + (22 if k % 2 else 14) * cos(a), 16 + (22 if k % 2 else 14) * sin(a))], 'flare')
        c.oval((12, 10, 24, 22), 'sun')
    return c.image


def saturn(t, style):
    c = Scene(style, SATURN, base=space_backdrop('saturno', style))
    f, phase = round(t * 2), t * TAU / 30
    twinkle(c, f, 40, 1)
    cx, cy, r = 128, 72, 34
    inc, roll = .46, -.26
    U = (cos(roll), sin(roll), 0)
    V = (-sin(roll) * sin(inc), cos(roll) * sin(inc), cos(inc))
    N = (U[1] * V[2] - U[2] * V[1], U[2] * V[0] - U[0] * V[2], U[0] * V[1] - U[1] * V[0])
    L = norm(-.62, -.42, .66)
    det = U[0] * V[1] - U[1] * V[0]
    ln = dot(L, N)
    a = phase + .6
    M = tuple(2.55 * r * (cos(a) * U[i] + sin(a) * V[i]) for i in range(3))
    mr = 5
    planet = ('pl0', 'pl1', 'pl2', 'pl3', 'pl4', 'pl5')
    ring = ('space', 'rg0', 'rg1', 'rg2', 'rg3')
    moon = ('mn0', 'mn1', 'mn2', 'mn3')

    def ring_density(rad):
        if rad < 1.25 or rad > 2.3: return 0
        if rad < 1.45: return .3
        if rad < 1.85: return .9 + .08 * sin(rad * 70)
        if rad < 1.93: return 0
        if 2.13 < rad < 2.16: return .15
        return .68 if rad < 2.26 else .35

    for py in range(0, 144):
        for px in range(28, 230):
            x, y = px - cx, py - cy
            best, value, tones = -1e9, None, None
            d2 = x * x + y * y
            if d2 <= r * r:
                z = sqrt(r * r - d2)
                n = (x / r, y / r, z / r)
                lam = max(0, dot(n, L))
                lat = dot(n, N)
                lon = atan2(dot(n, U), dot(n, V)) + phase
                band = sin(lat * 12 + .5 * sin(lon * 3)) + .4 * sin(lat * 27)
                value = lam * (.8 + .16 * band) + .04
                if .28 < lat < .4 and abs((lon % TAU) - 2) < .3:
                    value *= .75
                    tones = ('pl0', 'pl1', 'storm', 'pl3', 'pl4', 'pl5')
                s = -(x * N[0] + y * N[1] + z * N[2]) / ln
                if s > 0 and ring_density(hypot(x + s * L[0], y + s * L[1], z + s * L[2]) / r) > .2:
                    value *= .4
                best, tones = z, tones or planet
            ra = (x * V[1] - y * V[0]) / det
            rb = (U[0] * y - U[1] * x) / det
            density = ring_density(hypot(ra, rb) / r)
            if density:
                z = ra * U[2] + rb * V[2]
                if z > best and (tones is None or c.dither(px, py, density + .2)):
                    bb = x * L[0] + y * L[1] + z * L[2]
                    disc = bb * bb - (x * x + y * y + z * z - r * r)
                    shadow = disc > 0 and -bb + sqrt(disc) > 0
                    best, tones, value = z, ring, density * (.3 if shadow else 1)
            dm2 = (x - M[0]) ** 2 + (y - M[1]) ** 2
            if dm2 <= mr * mr:
                zz = sqrt(mr * mr - dm2)
                if M[2] + zz > best:
                    best, tones = M[2] + zz, moon
                    value = max(0, dot(((x - M[0]) / mr, (y - M[1]) / mr, zz / mr), L)) * 1.05
            if tones:
                c.ramp(px, py, tones, value)
    return c.finish()


def earth(t, style):
    c = Scene(style, EARTH, base=space_backdrop('terra', style))
    f, phase = round(t * 2), t * TAU / 30
    twinkle(c, f, 30, 2)
    cx, cy, r = 176, 100, 62
    L = norm(-.86, -.38, .34)
    tilt = .35
    # Moon: one orbit per loop on an inclined ellipse.
    a = phase + 2.2
    mx, my, mz, mr = cx + 98 * cos(a), cy - 40 + 22 * sin(a), sin(a), 7

    def draw_moon():
        for py in range(int(my - mr), int(my + mr) + 1):
            for px in range(int(mx - mr), int(mx + mr) + 1):
                d2 = (px - mx) ** 2 + (py - my) ** 2
                if d2 <= mr * mr:
                    n = ((px - mx) / mr, (py - my) / mr, sqrt(mr * mr - d2) / mr)
                    crater = .8 if noise(int((px - mx) * 1.3), int((py - my) * 1.3), 4) > .8 else 1
                    c.ramp(px, py, ('mn0', 'mn1', 'mn2', 'mn3'), max(0, dot(n, L)) * 1.1 * crater)

    if mz < 0: draw_moon()
    ct, st = cos(tilt), sin(tilt)
    for py in range(max(0, cy - r - 4), 144):
        for px in range(max(0, cx - r - 4), min(256, cx + r + 5)):
            x, y = px - cx, py - cy
            d = hypot(x, y)
            if d > r:
                if d < r + 4:
                    edge = max(0, dot((x / d, y / d, 0), L) + .35)
                    if c.dither(px, py, (1 - (d - r) / 4) * edge * 1.2):
                        c.px(px, py, 'atmo2' if d < r + 1.5 else 'atmo1')
                continue
            n = (x / r, y / r, sqrt(max(0, 1 - (x * x + y * y) / (r * r))))
            lam = dot(n, L)
            u, v = n[0] * ct - n[1] * st, n[0] * st + n[1] * ct
            lat = atan2(v, sqrt(u * u + n[2] * n[2]))
            lon = atan2(u, n[2]) + phase * .5
            # Even longitude frequencies: half a turn per loop closes the cycle.
            h = (.5 * sin(2 * lon + 1.3 * sin(3 * lat) + .4) + .35 * sin(4 * lon - 2.2 * lat + 1.1)
                 + .2 * sin(6 * lon + 4 * lat) + .25 * cos(2.5 * lat))
            lonc = lon + phase * .5
            # Latitude-aligned streaks broken up along longitude, like weather fronts.
            cloud = (sin(11 * lat + 2.2 * sin(3 * lonc + 2 * lat)) * (.6 + .4 * sin(2 * lonc + 3 * lat))
                     + .25 * sin(13 * lonc - 9 * lat))
            light = max(0, lam)
            if abs(lat) > 1.12 or (h > .55 and abs(lat) > 1.0):
                tones, value = ('oc0', 'cl0', 'cl1', 'ice'), light * 1.1
            elif h > .55:
                arid = sin(2 * lon - 3 * lat + 2) + .6 * sin(4 * lon + 5 * lat)
                tones = ('ld0', 'ds1', 'ds2', 'ds3') if abs(lat) < .6 and arid > .7 else ('ld0', 'ld1', 'ld2', 'ld3')
                value = light * (.85 + .25 * (h - .55))
            else:
                tones, value = ('oc0', 'oc1', 'oc2', 'oc3'), light * (.75 + .25 * (h + .6))
                hx, hy, hz = norm(L[0], L[1], L[2] + 1)
                if (n[0] * hx + n[1] * hy + n[2] * hz) > .985:
                    tones, value = ('oc0', 'oc3', 'spec'), light
            if cloud > .62:
                tones, value = ('oc0', 'cl0', 'cl1', 'cl2'), light * 1.15
            if lam < .04 and h > .55 and cloud <= .62 and noise(int(lon * 30), int(lat * 30), 6) > .9:
                c.px(px, py, 'city')
                continue
            if d > r - 2 and lam > 0:
                tones, value = ('oc0', 'atmo1', 'atmo2'), light * 1.2
            c.ramp(px, py, tones, value)
    if mz >= 0: draw_moon()
    return c.finish()


def eclipse(t, style):
    c = Scene(style, ECLIPSE, base=space_backdrop('eclisse', style))
    f, phase = round(t * 2), t * TAU / 30
    twinkle(c, f, 40, 3)
    cx, cy, r = 128, 72, 34
    sun_angle = -.8 + .35 * sin(phase)
    corona = ('space', 'cor0', 'cor1', 'cor2', 'cor3', 'cor4')
    for py in range(144):
        for px in range(40, 216):
            x, y = px - cx, py - cy
            d = hypot(x, y)
            theta = atan2(y, x)
            diff = (theta - sun_angle + pi) % TAU - pi
            if d < r:
                if d > r - 1.6 and abs(diff) < .9:
                    c.px(px, py, 'cor4' if abs(diff) < .5 else 'cor3')
                elif c.dither(px, py, .45 * max(0, cos(diff)) * (d / r) ** 3):
                    c.px(px, py, 'earthshine')
                else:
                    c.px(px, py, 'disc')
                continue
            rr = d - r
            streamer = (.5 + .5 * sin(6 * theta + 1.5 * sin(2 * theta - phase) + phase)) * (.5 + .5 * sin(11 * theta - 2 * phase))
            value = exp(-rr / (3 + 13 * streamer)) * (.72 + .18 * sin(2 * phase + 3 * theta))
            value += 1.4 * exp(-diff * diff / .03 - rr / 4)
            if value > .06:
                c.ramp(px, py, corona, value)
    # Bead of light at the limb, with a short horizontal flare.
    bx, by = cx + (r + 1) * cos(sun_angle), cy + (r + 1) * sin(sun_angle)
    for dx in range(-24, 25):
        if c.dither(bx + dx, by, 1 - abs(dx) / 24):
            c.px(bx + dx, by, 'cor3' if abs(dx) > 6 else 'cor4')
    c.oval((bx - 2, by - 2, bx + 2, by + 2), 'cor4')
    # A satellite crosses once per loop.
    sx = -10 + t / 30 * 276
    sy = 126 - .16 * sx
    c.rect((sx - 2, sy, sx + 2, sy), 'stardim'); c.px(sx, sy - 1, 'stardim')
    if f % 4 == 0: c.px(sx + 3, sy, 'blink')
    return c.finish()


# ─── Acquario ───────────────────────────────────────────────────────────────────

REEF = {
    'wt0': ('#62d4e2', 182), 'wt1': ('#2ea6c8', 146), 'wt2': ('#1a7aac', 109), 'wt3': ('#105282', 73),
    'wt4': ('#0a3862', 36), 'ray': ('#94e8ee', 182), 'reef': ('#1c6890', 73), 'reef2': ('#145478', 73),
    'sand': ('#ead49c', 182), 'sandshade': ('#b89a68', 109), 'sandlight': ('#fff4cc', 255),
    'rock': ('#4c5c70', 73), 'rocklight': ('#7e90a2', 146), 'rockdark': ('#2a3446', 36),
    'coral': ('#ff7c6a', 146), 'corald': ('#c04a50', 73), 'brain': ('#dcc464', 182),
    'braind': ('#8a7a30', 73), 'fan': ('#b45ad2', 109), 'fand': ('#6a2a92', 36),
    'tube': ('#ff9c3c', 146), 'tubed': ('#a85820', 73), 'anem': ('#f070b0', 146),
    'anemtip': ('#ffd4f0', 255), 'anemd': ('#a03080', 73), 'clown': ('#ff7a20', 146),
    'black': ('#141418', 0), 'white': ('#ffffff', 255), 'tang': ('#2a5ae0', 73),
    'tangfin': ('#ffd030', 219), 'tangdark': ('#102060', 0), 'turtle': ('#6e9044', 109),
    'turtled': ('#3a5020', 36), 'turtlel': ('#acc474', 182), 'shell': ('#7a5a30', 73),
    'shelll': ('#c09a52', 146), 'bubble': ('#dcfaff', 219), 'grass': ('#4aa262', 109),
    'grassd': ('#2a6a42', 73),
}
ABYSS = {
    'ab0': ('#000207', 0), 'ab1': ('#03101e', 0), 'ab2': ('#081c34', 36),
    'snow': ('#8ca2b8', 109), 'snowdim': ('#2c3c52', 36), 'mud': ('#0c1420', 36), 'mudl': ('#1c2a3a', 73),
    'j0': ('#06303c', 36), 'j1': ('#1a8a9c', 109), 'j2': ('#5ae8f2', 182), 'j3': ('#dcffff', 255),
    'k0': ('#2c0a32', 36), 'k1': ('#8a2aa2', 109), 'k2': ('#e070f2', 182), 'k3': ('#ffe2ff', 255),
    'a0': ('#2c1806', 36), 'a1': ('#a0601a', 109), 'a2': ('#ffb240', 182), 'a3': ('#fff2c4', 255),
    'fish0': ('#121a26', 36), 'fish1': ('#34445c', 109), 'teeth': ('#e8f0f4', 255),
    'l0': ('#16280e', 36), 'l1': ('#4e9a2c', 109), 'l2': ('#b8ff62', 219), 'l3': ('#f6ffdc', 255),
    'worm': ('#ff4a5c', 146), 'wormd': ('#3a1a24', 36),
}
POND = {
    'pw0': ('#0b2a2e', 36), 'pw1': ('#144640', 36), 'pw2': ('#246a58', 73), 'pebble': ('#3a7a64', 109),
    'stone0': ('#3e4040', 36), 'stone1': ('#6e6e66', 109), 'stone2': ('#aaa898', 182), 'moss': ('#4a6a2a', 73),
    'pad0': ('#1a4e26', 73), 'pad1': ('#3a8a3a', 109), 'pad2': ('#7cc262', 182),
    'lotus': ('#f290b2', 182), 'lotusl': ('#ffe4ee', 255), 'lotusc': ('#ffd040', 219),
    'koiw': ('#f6f2e8', 255), 'koio': ('#ff7a22', 146), 'koir': ('#e03222', 109),
    'koib': ('#16161a', 0), 'koig': ('#ecc442', 219), 'kshadow': ('#061a1c', 0),
    'ripple': ('#5ea894', 146), 'glint': ('#dcfff2', 255),
}


def branch(c, x, y, angle, length, depth, color, light):
    x1, y1 = x + length * cos(angle), y + length * sin(angle)
    c.line([(x, y), (x1, y1)], color, max(1, depth))
    c.line([(x - 1, y), (x1 - 1, y1)], light)
    if depth > 0:
        for spread in (-.45, .5):
            branch(c, x1, y1, angle + spread, length * .72, depth - 1, color, light)


@lru_cache(None)
def reef_layers(style):
    back = Scene(style, REEF, 'wt4')
    for y in range(144):
        for x in range(256):
            back.ramp(x, y, ('wt0', 'wt1', 'wt2', 'wt3', 'wt4')[::-1], 1 - y / 130)
    for x in range(256):
        top = 96 + 10 * sin(x * .05) + 6 * sin(x * .13 + 1)
        back.rect((x, top, x, 120), 'reef')
        if x % 7 == 0:
            back.rect((x, top - 4 - (x % 3) * 2, x + 1, top), 'reef')
    front = Scene(style, REEF, mode='RGBA')
    front.poly([(0, 122), (40, 117), (90, 121), (150, 116), (210, 119), (256, 115), (256, 144), (0, 144)], 'sand')
    for i in range(260):
        x, y = int(noise(1, i, 1) * 256), 120 + int(noise(1, i, 2) * 24)
        front.px(x, y, 'sandshade' if i % 3 else 'sandlight')
    for x, y, w, h in ((14, 120, 30, 16), (188, 116, 40, 22), (120, 124, 18, 9)):
        front.oval((x - w / 2, y - h / 2, x + w / 2, y + h / 2), 'rockdark')
        front.oval((x - w / 2, y - h / 2, x + w / 2 - 3, y + h / 2 - 4), 'rock')
        front.arc((x - w / 2 + 2, y - h / 2 + 1, x + w / 2 - 4, y + h / 2), 190, 300, 'rocklight')
    branch(front, 32, 118, -pi / 2 - .2, 13, 3, 'coral', 'corald')
    branch(front, 24, 120, -pi / 2 + .4, 9, 2, 'coral', 'corald')
    # Brain coral with meandering grooves.
    front.oval((96, 108, 126, 126), 'braind'); front.oval((97, 108, 125, 124), 'brain')
    for k in range(5):
        front.line([(100 + j, 112 + k * 3 + sin(j * .7 + k) * 1.4) for j in range(0, 23, 2)], 'braind')
    # Sea fan.
    for k in range(9):
        a = -pi / 2 + (k - 4) * .19
        front.line([(218, 112), (218 + 26 * cos(a), 112 + 26 * sin(a))], 'fand')
    for rad in (9, 15, 21):
        front.arc((218 - rad, 112 - rad, 218 + rad, 112 + rad), 220, 320, 'fan')
    for x, h in ((150, 16), (156, 22), (162, 12)):
        front.rect((x, 120 - h, x + 4, 120), 'tubed'); front.rect((x + 1, 120 - h, x + 3, 120), 'tube')
        front.rect((x + 1, 119 - h, x + 3, 121 - h), 'tubed')
    front.oval((54, 118, 84, 128), 'rockdark'); front.oval((56, 117, 82, 125), 'rock')
    return back.image, front.image


def clownfish(c, x, y, direction):
    c.poly([(x - direction * 5, y), (x - direction * 9, y - 3), (x - direction * 9, y + 3)], 'black')
    c.poly([(x - direction * 5, y), (x - direction * 8, y - 2), (x - direction * 8, y + 2)], 'clown')
    c.oval((x - 6, y - 3, x + 6, y + 3), 'black')
    c.oval((x - 5, y - 2, x + 5, y + 2), 'clown')
    for dx in (-2, 2):
        c.line([(x + dx * direction, y - 2), (x + dx * direction, y + 2)], 'white')
    c.px(x + 4 * direction, y - 1, 'black')


def tang(c, x, y, direction, wag):
    c.poly([(x - direction * 4, y), (x - direction * 8, y - 3 + wag), (x - direction * 8, y + 3 + wag)], 'tangfin')
    c.oval((x - 5, y - 3, x + 5, y + 3), 'tangdark')
    c.oval((x - 4, y - 2, x + 5, y + 2), 'tang')
    c.line([(x - 3 * direction, y - 1), (x + 2 * direction, y - 2)], 'tangdark')
    c.px(x + 3 * direction, y - 1, 'white')


def turtle(c, x, y, f, direction=-1):
    def p(dx, dy): return x + direction * dx, y + dy
    stroke = (f % 4) / 3
    for side in (-1, 1):
        c.poly([p(6, side * 3), p(2 - 6 * stroke, side * (12 - 4 * stroke)), p(-6, side * (9 + 2 * stroke))], 'turtled')
        c.poly([p(-10, side * 4), p(-15, side * 8), p(-12, side * 3)], 'turtled')
    hx, _ = p(14, 0)
    c.oval((hx - 5, y - 4, hx + 5, y + 3), 'turtle'); c.px(*p(16, -1), 'black')
    c.oval((x - 13, y - 8, x + 12, y + 8), 'shell')
    c.oval((x - 11, y - 7, x + 10, y + 5), 'shelll')
    for dx, dy in ((-5, -3), (2, -3), (-2, 1), (6, 0), (-8, 1)):
        px, py = p(dx, dy)
        c.oval((px - 3, py - 2, px + 3, py + 2), 'shell')
    c.arc((x - 9, y - 7, x + 8, y + 1), 200, 320, 'turtlel')


def reef(t, style):
    back, front = reef_layers(style)
    c = Scene(style, REEF, base=back)
    f, phase = round(t * 2), t * TAU / 30
    for i in range(4):
        for y in range(0, 116):
            xc = 30 + i * 62 + 10 * sin(phase + i * 1.7) + y * .42
            w = 5 + y * .09
            for x in range(int(xc - w), int(xc + w) + 1):
                if c.dither(x, y, (1 - y / 118) * .6 * (1 - abs(x - xc) / w)):
                    c.px(x, y, 'ray')
    for x in range(256):
        y = 2 + 1.5 * sin(x * .16 + phase * 4)
        c.px(x, y, 'sandlight' if (x + f) % 9 == 0 else 'wt0')
    # Seagrass behind the corals, swaying with the surge.
    for i in range(16):
        bx = 6 + (i * 37) % 250
        h = 14 + (i * 11) % 16
        c.line([(bx + sin(phase * 2 + i + j / 6) * j / 5, 124 - j) for j in range(h)], 'grassd' if i % 2 else 'grass', 2)
    c.paste(front)
    for y in range(116, 144):
        for x in range(256):
            if c.pix[x, y] == c.tone('sand'):
                v = sin(x * .23 + 1.6 * sin(y * .35 + phase * 2) + phase * 2) + sin(y * .3 - x * .12 + 1.4 * cos(x * .17 - phase * 2))
                if abs(v) < .16:
                    c.px(x, y, 'sandlight')
    # Anemone with swaying tentacles and its two residents.
    for k in range(15):
        a = -pi + .2 + k * (pi - .4) / 14
        sway = 3 * sin(phase * 4 + k * .5)
        tip = (69 + 13 * cos(a) + sway, 117 + 11 * sin(a))
        c.line([(69 + 4 * cos(a), 117), tip], 'anemd' if k % 2 else 'anem', 2)
        c.px(tip[0], tip[1], 'anemtip')
    c.oval((60, 114, 78, 120), 'anemd')
    for k in range(2):
        a = phase * 2 + k * pi
        clownfish(c, 69 + 16 * cos(a), 100 + 5 * sin(a * 2), -1 if sin(a) > 0 else 1)
    shoal = -60 + ((t + 12) % 30) / 30 * 380
    for k in range(9):
        dx, dy = (k % 3) * 14 - (k // 3) * 7, (k // 3) * 9 + (k % 2) * 3
        tang(c, shoal - dx, 66 + dy + 2 * sin(phase * 4 + k), 1, 1 if (f + k) % 2 else -1)
    turtle(c, 300 - t / 30 * 360, 36 + 5 * sin(phase * 2), f)
    for i in range(7):
        y = 112 - (t * 5 + i * 21) % 150
        x = 158 + 2 * sin(y * .2 + i)
        r = 1 + (i % 2)
        if y > 4:
            c.d.ellipse((x - r, y - r, x + r, y + r), outline=c.c('bubble'))
    return c.finish()


@lru_cache(None)
def abyss_backdrop(style):
    c = Scene(style, ABYSS, 'ab0')
    for y in range(144):
        for x in range(256):
            c.ramp(x, y, ('ab0', 'ab1', 'ab2'), (1 - y / 144) ** 1.6)
    c.poly([(0, 132), (50, 128), (110, 134), (170, 129), (256, 133), (256, 144), (0, 144)], 'mud')
    c.line([(0, 132), (50, 128), (110, 134), (170, 129), (256, 133)], 'mudl')
    stars(c, 60, 11, 128, ('snowdim', 'snowdim'))
    return c.image


def jelly(c, x, y, w, pulse, phase, k, tones):
    t0, t1, t2, t3 = tones
    bw, bh = w * (1 - .18 * pulse), w * .72 * (1 + .16 * pulse)
    c.halo(x, y - bh * .3, bw * .6, bw * 1.9, t0, .55)
    for j in range(7):
        sx = x - bw * .8 + j * bw * 1.6 / 6
        c.line([(sx + 2.5 * sin(s * .35 - phase * 6 + j + k), y + s * 1.4) for s in range(int(14 + w * 1.4))], t1)
    for j in (-1, 1):
        c.line([(x + j * 2 + 3 * sin(s * .25 - phase * 4 + j), y + s * 1.2) for s in range(int(w * 1.1))], t2, 2)
    top = [(x + bw * cos(a), y - bh * sin(a)) for a in [i * pi / 16 for i in range(17)]]
    rim = [(x - bw + 2 * bw * i / 12, y + 1.5 * sin(i * 1.2 + phase * 6)) for i in range(13)]
    c.poly(top + rim[::-1][1:], t1)
    c.oval((x - bw * .6, y - bh * .85, x + bw * .25, y - bh * .25), t2)
    for px, py in rim[::2]:
        c.px(px, py, t3)
    c.px(x - bw * .3, y - bh * .7, t3)


def angler(c, x, y, direction, glow):
    def p(dx, dy): return x + direction * dx, y + dy
    c.poly([p(-16, 0), p(-28, -9), p(-25, 0), p(-28, 9)], 'fish0')
    c.line([p(-28, -9), p(-25, 0), p(-28, 9)], 'fish1')
    c.oval((x - 18, y - 13, x + 18, y + 12), 'fish0')
    c.arc((x - 18, y - 13, x + 18, y + 12), 200 if direction > 0 else 250, 290 if direction > 0 else 340, 'fish1')
    c.poly([p(4, -14), p(-6, -18), p(-10, -12)], 'fish0')
    # Gaping jaw with needle teeth.
    c.poly([p(8, 2), p(22, -3), p(20, 9), p(6, 8)], 'ab0')
    for i in range(5):
        c.line([p(9 + i * 3, 1 - i), p(10 + i * 3, 4 - i)], 'teeth')
        c.line([p(8 + i * 3, 8), p(9 + i * 3, 5)], 'teeth')
    c.px(*p(9, -6), 'teeth')
    lx, ly = p(26, -24 + 2 * sin(glow * 3))
    c.line([p(2, -13), p(12, -26), (lx, ly)], 'fish1')
    c.halo(lx, ly, 2, 7 + 3 * glow, 'l1', .5 + .4 * glow)
    c.oval((lx - 2, ly - 2, lx + 2, ly + 2), 'l2'); c.px(lx, ly, 'l3')


def abyss(t, style):
    c = Scene(style, ABYSS, base=abyss_backdrop(style))
    f, phase = round(t * 2), t * TAU / 30
    for i in range(60):
        x = noise(12, i, 1) * 256 + 2 * sin(phase + i)
        y = (noise(12, i, 2) * 144 + t * 4.8) % 144
        c.px(x, y, 'snow' if i % 4 else 'snowdim')
    for i, x in enumerate((24, 44, 212, 236)):
        sway = sin(phase * 2 + i)
        c.line([(x, 132), (x + sway, 122 - i % 2 * 4)], 'wormd', 2)
        c.px(x + sway, 121 - i % 2 * 4, 'worm' if (f + i) % 6 else 'a3')
    for x, y, w, k, speed, tones in ((52, 38, 13, 0, 4, ('j0', 'j1', 'j2', 'j3')),
                                     (204, 30, 10, 2, 6, ('k0', 'k1', 'k2', 'k3')),
                                     (236, 86, 7, 4, 5, ('a0', 'a1', 'a2', 'a3'))):
        pulse = .5 + .5 * sin(phase * speed + k)
        jelly(c, x + 6 * sin(phase + k), y - 6 * sin(phase * 2 + k) - 3 * pulse, w, pulse, phase, k, tones)
    glow = .5 + .5 * sin(phase * 6)
    angler(c, 118 + 48 * sin(phase), 96 + 5 * sin(phase * 2), 1 if cos(phase) >= 0 else -1, glow)
    return c.finish()


@lru_cache(None)
def pond_layers(style):
    back = Scene(style, POND, 'pw0')
    for y in range(144):
        for x in range(256):
            depth = min(1, hypot((x - 130) / 150, (y - 76) / 80))
            back.ramp(x, y, ('pw0', 'pw1', 'pw2'), depth ** 1.5)
            if depth > .6 and noise(x // 2, y // 2, 13) > .9:
                back.px(x, y, 'pebble')
    front = Scene(style, POND, mode='RGBA')
    for i in range(30):
        a = i * TAU / 30
        x, y = 128 + 150 * cos(a), 72 + 86 * sin(a)
        r = 9 + noise(i, 2) * 8
        front.oval((x - r - 1, y - r * .8 - 1, x + r + 1, y + r * .8 + 2), 'stone0')
        front.oval((x - r, y - r * .8, x + r - 2, y + r * .8 - 1), 'stone1')
        front.arc((x - r + 2, y - r * .8 + 1, x + r - 3, y + r * .5), 200, 290, 'stone2')
        if i % 4 == 0:
            front.oval((x - 3, y + r * .2, x + 4, y + r * .6), 'moss')
    for x, y, r, notch in ((206, 30, 14, .6), (230, 54, 10, 2.2), (186, 52, 8, 4), (40, 112, 13, 5.2),
                           (64, 128, 9, 1.4), (22, 88, 8, 3.3)):
        front.oval((x - r - 1, y - r * .8, x + r + 1, y + r * .8 + 2), 'pad0')
        front.oval((x - r, y - r * .8, x + r, y + r * .8), 'pad1')
        front.d.pieslice((x - r, y - r * .8, x + r, y + r * .8), notch * 57.3 - 18, notch * 57.3 + 18, fill=front.c('pad0'))
        for k in range(5):
            a = notch + pi + (k - 2) * .55
            front.line([(x, y), (x + r * .8 * cos(a), y + r * .65 * sin(a))], 'pad2')
    lx, ly = 206, 28
    for k in range(8):
        a = k * TAU / 8 + .2
        front.poly([(lx, ly), (lx + 7 * cos(a - .3), ly + 6 * sin(a - .3)), (lx + 10 * cos(a), ly + 8 * sin(a)),
                    (lx + 7 * cos(a + .3), ly + 6 * sin(a + .3))], 'lotus')
    for k in range(6):
        a = k * TAU / 6
        front.line([(lx, ly), (lx + 5 * cos(a), ly + 4 * sin(a))], 'lotusl')
    front.oval((lx - 2, ly - 2, lx + 2, ly + 2), 'lotusc')
    return back.image, front.image


KOI = (
    (lambda s: (118 + 72 * cos(s * TAU / 30), 74 + 32 * sin(s * TAU / 30) + 5 * sin(s * TAU / 10)),
     ('koiw', 'koir', 'koiw', 'koir', 'koir', 'koiw', 'koiw', 'koiw', 'koiw'), 5.2),
    (lambda s: (128 + 84 * sin(s * TAU / 30 + 1), 72 + 28 * sin(2 * (s * TAU / 30 + 1))),
     ('koio', 'koio', 'koib', 'koio', 'koio', 'koib', 'koio', 'koio', 'koio'), 4.6),
    (lambda s: (150 - 36 * cos(-s * TAU / 15), 82 + 24 * sin(-s * TAU / 15)),
     ('koig', 'koig', 'koiw', 'koig', 'koiw', 'koiw', 'koig', 'koiw', 'koiw'), 4),
)


def koi(c, path, pattern, size, t, f, shadow):
    points = [path(t - k * .24) for k in range(9)]
    radii = [s * size / 3.2 for s in (2.6, 3.3, 3.5, 3.3, 3, 2.5, 2, 1.5, 1.1)]
    ox, oy = (3, 4) if shadow else (0, 0)
    hx, hy = points[0][0] - points[1][0], points[0][1] - points[1][1]
    length = hypot(hx, hy) or 1
    nx, ny = -hy / length, hx / length
    tx, ty = points[8][0] - points[7][0], points[8][1] - points[7][1]
    tl = hypot(tx, ty) or 1
    wag = 2.5 * sin(f * 1.6)
    end = points[8]
    color = 'kshadow' if shadow else 'koiw'
    c.poly([(end[0] + ox, end[1] + oy),
            (end[0] + tx / tl * 7 + nx * (5 + wag) + ox, end[1] + ty / tl * 7 + ny * (5 + wag) + oy),
            (end[0] + tx / tl * 4 + ox, end[1] + ty / tl * 4 + oy),
            (end[0] + tx / tl * 7 - nx * (5 - wag) + ox, end[1] + ty / tl * 7 - ny * (5 - wag) + oy)], color)
    px_, py_ = points[2]
    for side in (-1, 1):
        c.poly([(px_ + side * nx * radii[2] + ox, py_ + side * ny * radii[2] + oy),
                (px_ + side * nx * (radii[2] + 4) - hx / length * 3 + ox, py_ + side * ny * (radii[2] + 4) - hy / length * 3 + oy),
                (px_ - hx / length * 3 + ox, py_ - hy / length * 3 + oy)], color)
    for k in range(8, -1, -1):
        x, y = points[k]
        r = radii[k]
        c.oval((x - r + ox, y - r + oy, x + r + ox, y + r + oy), 'kshadow' if shadow else pattern[k])
    if not shadow:
        x, y = points[0]
        for side in (-1, 1):
            c.px(x + hx / length * 1.5 + side * nx * 1.6, y + hy / length * 1.5 + side * ny * 1.6, 'koib')


def pond(t, style):
    back, front = pond_layers(style)
    c = Scene(style, POND, base=back)
    f, phase = round(t * 2), t * TAU / 30
    for path, pattern, size in KOI:
        koi(c, path, pattern, size, t, f, True)
    for path, pattern, size in KOI:
        koi(c, path, pattern, size, t, f, False)
    for i, (x, y) in enumerate(((78, 46), (176, 104), (122, 30))):
        age = (t + i * 2) % 6
        r = age * 5
        for k in range(int(r * 6) + 1):
            a = k * TAU / (r * 6 + 1)
            if age < 4.5 or k % 2:
                c.px(x + r * cos(a), y + r * .75 * sin(a), 'ripple')
    for i in range(14):
        if (f + i * 5) % 10 < 3:
            x, y = 40 + noise(14, i, 1) * 176, 20 + noise(14, i, 2) * 104
            c.line([(x - 1, y), (x + 1, y)], 'glint')
    c.paste(front)
    return c.finish()


# ─── Ingranaggi ─────────────────────────────────────────────────────────────────

TEETH_PER_LOOP = 20
MODULE = 1.5
TRAIN = (  # (teeth, spokes, parent, direction from parent)
    (40, 6, None, (70, 74)),
    (12, 3, 0, -.55),
    (30, 6, 1, .35),
    (16, 4, 2, -.75),
    (24, 6, 3, .25),
    (12, 3, 4, 1.25),
    (24, 6, 0, 2.1),
    (20, 5, 2, 1.6),
)


def place_train(t, train=TRAIN, module=MODULE, teeth=TEETH_PER_LOOP, spin=1):
    """Centres and angles of a meshing train; every wheel turns `teeth` pitches per loop."""
    gears = []
    for n, spokes, parent, where in train:
        # The loop closes only if each wheel's spoke pattern repeats after `teeth` pitches.
        assert teeth * spokes % n == 0, (n, spokes)
        if parent is None:
            cx, cy = where
            angle = spin * teeth * TAU / n * t / 30
        else:
            pn, _, pcx, pcy, pa = gears[parent]
            distance = module * (pn + n) / 2
            cx, cy = pcx + distance * cos(where), pcy + distance * sin(where)
            u = (where - pa) * pn / TAU
            angle = where + pi - pi / n + TAU / n * u
        gears.append((n, spokes, cx, cy, angle))
    return gears


def gear_outline(cx, cy, n, angle, module):
    rp = module * n / 2
    ro, rr = rp + module, rp - 1.25 * module
    points = []
    for j in range(n):
        base, half = angle + j * TAU / n, pi / n
        for radius, offset in ((rr, -.62), (ro, -.3), (ro, .3), (rr, .62)):
            points.append((cx + radius * cos(base + offset * half), cy + radius * sin(base + offset * half)))
    return points, rr


def gear_windows(cx, cy, rr, spokes, angle):
    rh, ri = max(4, rr * .3), rr - 3
    if ri - rh < 4:
        return []
    width = max(2, rr * .16)
    windows = []
    for i in range(spokes):
        a0, a1 = angle + i * TAU / spokes, angle + (i + 1) * TAU / spokes
        inner = [(cx + rh * cos(a), cy + rh * sin(a)) for a in
                 [a0 + width / 2 / rh + (a1 - a0 - width / rh) * k / 6 for k in range(7)]]
        outer = [(cx + ri * cos(a), cy + ri * sin(a)) for a in
                 [a1 - width / 2 / ri - (a1 - a0 - width / ri) * k / 8 for k in range(9)]]
        windows.append(inner + outer)
    return windows


def wheel(c, gear, tones, module=MODULE, shadow=True):
    n, spokes, cx, cy, angle = gear
    points, rr = gear_outline(cx, cy, n, angle, module)
    if shadow:
        c.poly([(x + 2, y + 3) for x, y in points], tones['shadow'])
    c.poly(points, tones['tooth'])
    c.oval((cx - rr + .5, cy - rr + .5, cx + rr - .5, cy + rr - .5), tones['face'])
    c.arc((cx - rr + 1, cy - rr + 1, cx + rr - 1, cy + rr - 1), 170, 290, tones['light'])
    c.arc((cx - rr + 1, cy - rr + 1, cx + rr - 1, cy + rr - 1), 10, 110, tones['dark'])
    for window in gear_windows(cx, cy, rr, spokes, angle):
        c.poly(window, tones['recess'])
        c.line(window[7:12], tones['dark'])
    hub = max(3, rr * .22)
    c.oval((cx - hub, cy - hub, cx + hub, cy + hub), tones['dark'], tones['light'])
    c.oval((cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5), tones['jewel'])
    c.px(cx - 1, cy - 1, tones['glint'])


MOVEMENT = {
    'plate0': ('#4e5a64', 109), 'plate1': ('#66727c', 109), 'plate2': ('#86929c', 146), 'plate3': ('#a6b0b8', 146),
    'gold': ('#d8a84e', 182), 'goldlight': ('#ffe6a2', 255), 'goldshade': ('#8a6230', 73),
    'recess': ('#1e242c', 0), 'shadow': ('#2c343c', 36), 'ruby': ('#d42a4a', 109), 'white': ('#ffffff', 255),
    'bridge': ('#b8c4cc', 182), 'bridgelight': ('#eef4f8', 255), 'bridgedark': ('#5e6a74', 73),
    'screw': ('#2c4cc0', 73), 'screwlight': ('#7a9cff', 182), 'chaton': ('#c09040', 146),
    'steel': ('#8a96a0', 146),
}
GOLD = {'tooth': 'goldshade', 'face': 'gold', 'light': 'goldlight', 'dark': 'goldshade',
        'recess': 'recess', 'jewel': 'ruby', 'glint': 'white', 'shadow': 'shadow'}


def screw(c, x, y, a):
    c.oval((x - 4, y - 4, x + 4, y + 4), 'bridgedark')
    c.oval((x - 3, y - 3, x + 3, y + 3), 'screw')
    c.px(x - 1, y - 2, 'screwlight')
    c.line([(x - 3 * cos(a), y - 3 * sin(a)), (x + 3 * cos(a), y + 3 * sin(a))], 'recess')


def jewel(c, x, y):
    c.oval((x - 4, y - 4, x + 4, y + 4), 'chaton')
    c.oval((x - 2, y - 2, x + 2, y + 2), 'ruby')
    c.px(x - 1, y - 1, 'white')


def bridge(c, points, width=11):
    c.line(points, 'bridgedark', width + 2)
    for x, y in points:
        c.oval((x - width / 2 - 1, y - width / 2 - 1, x + width / 2 + 1, y + width / 2 + 1), 'bridgedark')
    c.line(points, 'bridge', width)
    for x, y in points:
        c.oval((x - width / 2, y - width / 2, x + width / 2, y + width / 2), 'bridge')
    c.line([(x - 1, y - width / 2 + 1) for x, y in points], 'bridgelight')


@lru_cache(None)
def movement_layers(style):
    back = Scene(style, MOVEMENT, 'plate1')
    for y in range(144):
        for x in range(256):
            # Côtes de Genève: curved diagonal stripes with a brushed falloff.
            u = (x * .6 + y * .8 + ((x * .8 - y * .6 - 60) ** 2) * .0035) / 22
            back.ramp(x, y, ('plate0', 'plate1', 'plate2', 'plate3'), .38 + .3 * smooth(abs(u % 1 - .5) * 2))
    gears = place_train(0)
    front = Scene(style, MOVEMENT, mode='RGBA')
    bridge(front, [(-6, 30), gears[1][2:4], gears[3][2:4], (262, 18)], 13)
    bridge(front, [gears[4][2:4], gears[5][2:4], (262, 86)], 11)
    bridge(front, [(262, 140), (224, 114)], 11)
    for i in (1, 3, 4, 5):
        jewel(front, *gears[i][2:4])
    jewel(front, 224, 114)
    for x, y, a in ((28, 26, .4), (232, 22, 1.2), (246, 84, .2), (244, 130, 2.0)):
        screw(front, x, y, a)
    return back.image, front.image


def movement(t, style):
    back, front = movement_layers(style)
    c = Scene(style, MOVEMENT, base=back)
    f, phase = round(t * 2), t * TAU / 30
    gears = place_train(t)
    for gear in gears:
        wheel(c, gear, GOLD)
    # Escapement: the escape wheel advances one tooth per beat, locked to the balance.
    beat = 1 if sin(phase * 15) >= 0 else -1
    escape = (15, 3, 176, 108, f * TAU / 30)
    points, rr = gear_outline(176, 108, 15, f * TAU / 30, 1.4)
    c.poly([(x + 2, y + 3) for x, y in points], 'shadow')
    c.poly(points, 'steel'); c.oval((172, 104, 180, 112), 'recess'); c.oval((174, 106, 178, 110), 'ruby')
    fork = .25 * beat
    c.line([(196, 110), (196 + 16 * cos(pi + fork), 110 + 16 * sin(pi + fork))], 'steel', 3)
    c.line([(196, 110), (196 + 9 * cos(fork), 110 + 9 * sin(fork))], 'steel', 2)
    swing = 1.7 * sin(phase * 15)
    cx, cy = 224, 114
    c.oval((cx - 21, cy - 19, cx + 23, cy + 25), 'shadow')
    c.oval((cx - 21, cy - 21, cx + 21, cy + 21), 'goldshade')
    c.oval((cx - 18, cy - 18, cx + 18, cy + 18), 'recess')
    c.arc((cx - 20, cy - 20, cx + 20, cy + 20), 170, 290, 'goldlight')
    for k in range(3):
        a = swing + k * TAU / 3
        c.line([(cx, cy), (cx + 18 * cos(a), cy + 18 * sin(a))], 'gold', 2)
    for k in range(8):
        a = swing + k * TAU / 8 + .2
        c.px(cx + 20 * cos(a), cy + 20 * sin(a), 'goldlight')
    c.line([(cx + (2 + j * .07 * (1 + .08 * sin(phase * 15))) * cos(j * .21 + swing * .3),
              cy + (2 + j * .07 * (1 + .08 * sin(phase * 15))) * sin(j * .21 + swing * .3)) for j in range(190)], 'bridgelight')
    c.paste(front)
    return c.finish()


TOURBILLON = {
    **MOVEMENT,
    'dial0': ('#07090e', 0), 'dial1': ('#10141c', 36), 'ring': ('#2a3038', 73), 'tick': ('#c8d0d8', 219),
    'tickdim': ('#5a646e', 109),
}
STEEL = {'tooth': 'bridgedark', 'face': 'steel', 'light': 'bridgelight', 'dark': 'bridgedark',
         'recess': 'dial0', 'jewel': 'ruby', 'glint': 'white', 'shadow': 'dial0'}
SIDE_TRAIN = ((24, 6, None, (22, 30)), (16, 4, 0, 1.25), (30, 5, 1, 1.9))
BARREL = ((48, 4, None, (244, 110)),)


@lru_cache(None)
def tourbillon_backdrop(style):
    c = Scene(style, TOURBILLON, 'dial0')
    for y in range(144):
        for x in range(256):
            a = atan2(y - 72, x - 128)
            c.ramp(x, y, ('dial0', 'dial1'), .25 + .5 * abs(sin(a * 36)))
    c.oval((128 - 67, 72 - 67, 128 + 67, 72 + 67), 'ring')
    c.oval((128 - 61, 72 - 61, 128 + 61, 72 + 61), 'dial0')
    for k in range(60):
        a = k * TAU / 60 - pi / 2
        inner = 61.5 if k % 5 else 58
        c.line([(128 + inner * cos(a), 72 + inner * sin(a)), (128 + 66 * cos(a), 72 + 66 * sin(a))],
               'tick' if k % 5 == 0 else 'tickdim')
    # Fixed seconds wheel with inner teeth around the cage.
    for k in range(48):
        a = k * TAU / 48
        c.line([(128 + 37 * cos(a), 72 + 37 * sin(a)), (128 + 40 * cos(a), 72 + 40 * sin(a))], 'goldshade', 2)
    c.d.ellipse((128 - 41, 72 - 41, 128 + 41, 72 + 41), outline=c.c('gold'))
    return c.image


def tourbillon(t, style):
    c = Scene(style, TOURBILLON, base=tourbillon_backdrop(style))
    f, phase = round(t * 2), t * TAU / 30
    for gear in place_train(t, SIDE_TRAIN, teeth=12):
        wheel(c, gear, GOLD)
    for gear in place_train(t, BARREL, teeth=12, spin=-1):
        wheel(c, gear, STEEL)
    cx, cy, cage = 128, 72, phase
    # Cage: three tapered arms and a ring, one revolution per loop.
    c.d.ellipse((cx - 33, cy - 33, cx + 33, cy + 33), outline=c.c('bridgedark'), width=3)
    c.d.ellipse((cx - 32, cy - 32, cx + 32, cy + 32), outline=c.c('bridge'))
    for k in range(3):
        a = cage + k * TAU / 3
        nx, ny = -sin(a), cos(a)
        c.poly([(cx + 4 * nx, cy + 4 * ny), (cx + 32 * cos(a) + 2 * nx, cy + 32 * sin(a) + 2 * ny),
                (cx + 32 * cos(a) - 2 * nx, cy + 32 * sin(a) - 2 * ny), (cx - 4 * nx, cy - 4 * ny)], 'bridge')
        c.line([(cx + 4 * nx, cy + 4 * ny), (cx + 32 * cos(a) + 2 * nx, cy + 32 * sin(a) + 2 * ny)], 'bridgelight')
        screw(c, cx + 30 * cos(a), cy + 30 * sin(a), a * 3)
    # Escape wheel riding on the cage, ticking one tooth per beat.
    ea = cage + pi / 3
    ex, ey = cx + 22 * cos(ea), cy + 22 * sin(ea)
    points, _ = gear_outline(ex, ey, 15, f * TAU / 30 + cage, 1.1)
    c.poly(points, 'steel'); c.oval((ex - 2, ey - 2, ex + 2, ey + 2), 'ruby')
    beat = 1 if sin(phase * 15) >= 0 else -1
    pa = cage + pi / 3 - .55
    px, py = cx + 15 * cos(pa), cy + 15 * sin(pa)
    c.line([(px, py), (px + 8 * cos(pa + pi / 2 + .3 * beat), py + 8 * sin(pa + pi / 2 + .3 * beat))], 'steel', 2)
    # Balance wheel: two-second oscillation, gold rim with timing screws, breathing hairspring.
    swing = cage + 1.9 * sin(phase * 15)
    breathe = 1 + .1 * sin(phase * 15)
    c.line([(cx + (2 + s * .05 * breathe) * cos(s * .19 + swing * .4), cy + (2 + s * .05 * breathe) * sin(s * .19 + swing * .4))
            for s in range(200)], 'bridgelight')
    c.d.ellipse((cx - 17, cy - 17, cx + 17, cy + 17), outline=c.c('goldshade'), width=3)
    c.d.ellipse((cx - 17, cy - 17, cx + 17, cy + 17), outline=c.c('gold'))
    for k in range(2):
        a = swing + k * pi
        c.line([(cx + 3 * cos(a), cy + 3 * sin(a)), (cx + 16 * cos(a), cy + 16 * sin(a))], 'gold', 2)
    for k in range(10):
        a = swing + k * TAU / 10
        c.px(cx + 18 * cos(a), cy + 18 * sin(a), 'goldlight')
    # Fixed upper bridge across the cage.
    bridge(c, [(cx - 44, cy + 44), (cx, cy)], 7)
    screw(c, cx - 44, cy + 44, .6)
    jewel(c, cx, cy)
    return c.finish()


BLUEPRINT = {
    'bp': ('#123a6e', 36), 'grid': ('#1a4a84', 73), 'grid2': ('#2a5e9c', 73),
    'line': ('#eaf4ff', 255), 'dim': ('#8ab8ec', 146), 'faint': ('#4a7cba', 109),
}


@lru_cache(None)
def blueprint_backdrop(style):
    c = Scene(style, BLUEPRINT, 'bp')
    for x in range(0, 256, 8):
        c.line([(x, 0), (x, 143)], 'grid2' if x % 32 == 0 else 'grid')
    for y in range(0, 144, 8):
        c.line([(0, y), (255, y)], 'grid2' if y % 32 == 0 else 'grid')
    gears = place_train(0)
    for n, spokes, cx, cy, _ in gears:
        rp = MODULE * n / 2
        for k in range(0, 360, 3):
            if k % 9:
                c.px(cx + rp * cos(k * pi / 180), cy + rp * sin(k * pi / 180), 'dim')
        for k in range(-int(rp) - 6, int(rp) + 7, 4):
            c.line([(cx + k, cy), (cx + k + 2, cy)], 'faint')
            c.line([(cx, cy + k), (cx, cy + k + 2)], 'faint')
        c.text((cx + rp * .7 + 2, cy - rp * .7 - 9), f'Z{n}', 'dim')
    # Dimension line between the first two arbors.
    (_, _, x0, y0, _), (_, _, x1, y1, _) = gears[0], gears[1]
    ox, oy = 7 * sin(-.55), -7 * cos(-.55)
    c.line([(x0 + ox, y0 + oy), (x1 + ox, y1 + oy)], 'dim')
    for x, y in ((x0, y0), (x1, y1)):
        c.line([(x, y), (x + ox * 1.4, y + oy * 1.4)], 'faint')
    c.rect((172, 114, 251, 139), 'bp')
    c.d.rectangle((172, 114, 251, 139), outline=c.c('line'))
    c.line([(172, 126), (251, 126)], 'dim'); c.line([(222, 126), (222, 139)], 'dim')
    c.text((176, 115), 'RUOTISMO', 'line')
    c.text((176, 128), 'm 1.5  Z 8', 'dim'); c.text((226, 128), 'TAV.3', 'dim')
    for x, y, sx, sy in ((4, 4, 1, 1), (251, 4, -1, 1), (4, 139, 1, -1)):
        c.line([(x, y + sy * 8), (x, y), (x + sx * 8, y)], 'dim')
    return c.image


def blueprint(t, style):
    c = Scene(style, BLUEPRINT, base=blueprint_backdrop(style))
    phase = t * TAU / 30
    for i, (n, spokes, cx, cy, angle) in enumerate(place_train(t)):
        points, rr = gear_outline(cx, cy, n, angle, MODULE)
        c.d.polygon([(round(x), round(y)) for x, y in points], outline=c.c('line'))
        for window in gear_windows(cx, cy, rr, spokes, angle):
            c.d.polygon([(round(x), round(y)) for x, y in window], outline=c.c('dim'))
        hub = max(3, rr * .22)
        c.d.ellipse((cx - hub, cy - hub, cx + hub, cy + hub), outline=c.c('line'))
        # Rotation arrow just outside the tip circle.
        direction = 1 if i in (0, 2, 4, 6) and i != 6 or i == 7 else -1
        ro = MODULE * n / 2 + MODULE + 3
        start = -2.4 + (i % 3) * .3
        arc = [(cx + ro * cos(start + k * .06 * direction), cy + ro * sin(start + k * .06 * direction)) for k in range(10)]
        c.line(arc, 'faint')
        hx, hy = arc[-1]
        a = start + .6 * direction + direction * pi / 2
        c.line([(hx, hy), (hx - 3 * cos(a - .5), hy - 3 * sin(a - .5))], 'faint')
        c.line([(hx, hy), (hx - 3 * cos(a + .5), hy - 3 * sin(a + .5))], 'faint')
    # Scanning cursor sweeping the sheet once per loop.
    sx = int(t / 30 * 256)
    for y in range(0, 144, 2):
        c.px(sx, y, 'faint')
    return c.finish()


# ─── Labirinto 3D ───────────────────────────────────────────────────────────────

LAB_MAP = (
    '############',
    '#..........#',
    '#.###.####.#',
    '#.#...#..#.#',
    '#.#.###..#.#',
    '#....#...#.#',
    '#.#..#.###.#',
    '#.##.#.....#',
    '#.#....##..#',
    '#.####.#.#.#',
    '#..........#',
    '############',
)
CORNERS = ((1.5, 1.5), (10.5, 1.5), (10.5, 10.5), (1.5, 10.5))
FOV = 1.35
SCALE = 82  # half wall height on screen at unit depth


def lab_wall(mx, my):
    return not (0 <= mx < 12 and 0 <= my < 12) or LAB_MAP[my][mx] == '#'


def lab_camera(t):
    """Walk one side in 5.5 s, then round the corner on a half-cell arc in 2 s."""
    side, local = int(t // 7.5) % 4, t % 7.5
    heading = side * pi / 2
    dx, dy, nx, ny = cos(heading), sin(heading), -sin(heading), cos(heading)
    (x0, y0), (x1, y1) = CORNERS[side], CORNERS[(side + 1) % 4]
    x0, y0, x1, y1 = x0 + dx / 2, y0 + dy / 2, x1 - dx / 2, y1 - dy / 2
    if local < 5.5:
        s = smooth(local / 5.5)
        return x0 + (x1 - x0) * s, y0 + (y1 - y0) * s, heading
    turn = smooth((local - 5.5) / 2) * pi / 2
    ax, ay = x1 + nx / 2, y1 + ny / 2
    return (ax + (-nx * cos(turn) + dx * sin(turn)) / 2,
            ay + (-ny * cos(turn) + dy * sin(turn)) / 2, heading + turn)


def lab_cast(cx, cy, heading):
    columns = []
    for col in range(256):
        ray = heading + atan((col / 255 - .5) * FOV)
        dx, dy = cos(ray), sin(ray)
        mx, my = floor(cx), floor(cy)
        sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
        ddx, ddy = abs(1 / (dx or 1e-9)), abs(1 / (dy or 1e-9))
        tx = ((mx + 1 - cx) if dx > 0 else cx - mx) * ddx
        ty = ((my + 1 - cy) if dy > 0 else cy - my) * ddy
        while True:
            if tx < ty: dist, tx, mx, side = tx, tx + ddx, mx + sx, 0
            else: dist, ty, my, side = ty, ty + ddy, my + sy, 1
            if lab_wall(mx, my): break
        depth = max(.05, dist * cos(ray - heading))
        u = ((cy + dist * dy) if side == 0 else (cx + dist * dx)) % 1
        h = SCALE / depth
        columns.append((depth, side, u, mx, my, 72 - h, 72 + h))
    return columns


def lab_floor(cx, cy, heading, col, y):
    depth = SCALE / abs(y - 71.5)
    k = (col / 255 - .5) * FOV
    return depth, cx + depth * (cos(heading) - k * sin(heading)), cy + depth * (sin(heading) + k * cos(heading))


DUNGEON = {
    'ink': ('#07060a', 0), 'st0': ('#1e1614', 36), 'st1': ('#3e2e26', 73), 'st2': ('#6e5440', 109),
    'st3': ('#a8825a', 182), 'st4': ('#e4bc84', 219), 'fl0': ('#16120e', 0), 'fl1': ('#2e2620', 36),
    'fl2': ('#544638', 73), 'fl3': ('#8a7458', 146), 'beam': ('#2a1a10', 36), 'ceil': ('#120e0c', 0),
    'iron': ('#2a2a30', 36), 'flame1': ('#ff8a2a', 182), 'flame2': ('#ffd25a', 219), 'flame3': ('#fff6d0', 255),
}
VECTOR = {
    'ink': ('#000000', 0), 'g0': ('#0a3018', 36), 'g1': ('#14703a', 73), 'g2': ('#2ec46a', 146),
    'g3': ('#9affc4', 255), 'hud': ('#2ec46a', 146),
}
HEDGE = {
    'sky0': ('#4a92d8', 109), 'sky1': ('#8cc4ec', 146), 'sky2': ('#d8f0f4', 219), 'cloud': ('#ffffff', 255),
    'cloudshade': ('#c4dcf0', 182), 'haze': ('#b4d4cc', 182), 'h0': ('#123a1c', 36), 'h1': ('#25602c', 73),
    'h2': ('#3e8a3a', 109), 'h3': ('#78bc58', 146), 'h4': ('#b4e07a', 182), 'flower': ('#ff8ab4', 182),
    'flowerw': ('#fff4f8', 255), 'gv0': ('#8a7a5a', 109), 'gv1': ('#c4b08a', 146), 'gv2': ('#e8d8b2', 219),
    'grass': ('#5a9a3c', 109), 'grassl': ('#8cc65a', 146), 'shade': ('#6a6448', 73),
}


def dungeon(t, style):
    c = Scene(style, DUNGEON)
    f = round(t * 2)
    cx, cy, heading = lab_camera(t)
    columns = lab_cast(cx, cy, heading)
    flick = .9 + .12 * noise(f, 21)
    stone, ground = ('ink', 'st0', 'st1', 'st2', 'st3', 'st4'), ('ink', 'fl0', 'fl1', 'fl2', 'fl3')
    for col, (depth, side, u, mx, my, top, bottom) in enumerate(columns):
        light = flick * 1.15 / (1 + .3 * depth * depth)
        torch = noise(mx, my, side, 3) > .7 and depth < 7
        for y in range(144):
            if y < top or y > bottom:
                fd, wx, wy = lab_floor(cx, cy, heading, col, y)
                fl = flick * 1.15 / (1 + .3 * fd * fd)
                if y > 72:
                    grout = (wx * 2) % 1 < .07 or (wy * 2) % 1 < .07
                    v = fl * (.62 + .2 * noise(floor(wx * 2), floor(wy * 2), 5)) * (.45 if grout else 1)
                    c.ramp(col, y, ground, v)
                else:
                    beam = wx % 1 < .14 or wy % 1 < .14
                    c.ramp(col, y, ('ink', 'ceil', 'beam', 'st1'), fl * (.55 if beam else .3))
                continue
            v = (y - top) / (bottom - top)
            row = int(v * 4)
            bx = u * 2 + (row % 2) * .5
            value = light * (.78 if side else 1) * (.72 + .28 * noise(mx, my, side, row, int(bx)))
            if (v * 4) % 1 < .08 or bx % 1 < .05:
                value *= .4
            elif (v * 4) % 1 < .16:
                value *= 1.15
            if torch:
                du, dv = u - .5, v - .36
                value += .9 * flick * exp(-(du * du * 26 + dv * dv * 18)) / (1 + .1 * depth)
                if abs(du) < .035 and .4 < v < .48:
                    c.px(col, y, 'iron'); continue
                tip = .26 - .05 * noise(f, mx, my)
                if tip < v < .4 and abs(du) < .05 * (v - tip) / (.4 - tip) + .01:
                    c.px(col, y, 'flame3' if abs(du) < .015 and v > .33 else 'flame2' if v > .31 else 'flame1'); continue
            c.ramp(col, y, stone, value)
    return c.finish()


def vector(t, style):
    c = Scene(style, VECTOR)
    f = round(t * 2)
    cx, cy, heading = lab_camera(t)
    columns = lab_cast(cx, cy, heading)
    for col, (depth, side, u, mx, my, top, bottom) in enumerate(columns):
        for y in list(range(0, max(0, int(top)))) + list(range(min(144, int(bottom) + 1), 144)):
            fd, wx, wy = lab_floor(cx, cy, heading, col, y)
            w = .025 + .012 * fd
            if wx % 1 < w or wy % 1 < w:
                if y > 72:
                    c.px(col, y, 'g1' if fd < 3.5 else 'g0')
                elif (col + y) % 2 == 0:
                    c.px(col, y, 'g0')
        tone = 'g3' if depth < 2.2 else 'g2' if depth < 4.5 else 'g1'
        c.px(col, top, tone); c.px(col, bottom, tone)
        if col:
            prev = columns[col - 1]
            if (prev[3], prev[4], prev[1]) != (mx, my, side) or abs(prev[2] - u) > .5:
                near = (depth, top, bottom) if depth <= prev[0] else (prev[0], prev[5], prev[6])
                ncol = col if depth <= prev[0] else col - 1
                ntone = 'g3' if near[0] < 2.2 else 'g2' if near[0] < 4.5 else 'g1'
                c.line([(ncol, max(0, near[1])), (ncol, min(143, near[2]))], ntone)
    # Minimap and compass in the corner, like a vector arcade HUD.
    ox, oy, cell = 214, 6, 3
    c.rect((ox - 2, oy - 2, ox + 12 * cell + 1, oy + 12 * cell + 1), 'ink')
    for my in range(12):
        for mx in range(12):
            if lab_wall(mx, my):
                c.rect((ox + mx * cell, oy + my * cell, ox + mx * cell + cell - 2, oy + my * cell + cell - 2), 'g0')
    px, py = ox + cx * cell, oy + cy * cell
    c.line([(px, py), (px + 5 * cos(heading), py + 5 * sin(heading))], 'g3')
    c.rect((px - 1, py - 1, px + 1, py + 1), 'g3')
    degrees = round(heading * 180 / pi) % 360
    c.text((6, 4), f'SETTORE 7   {degrees:03d}°', 'hud')
    if f % 4 < 2:
        c.rect((6, 136, 8, 138), 'g2')
    c.text((12, 132), 'SCANSIONE', 'hud')
    return c.finish()


@lru_cache(None)
def hedge_sky(style):
    c = Scene(style, HEDGE)
    for y in range(72):
        for x in range(256):
            c.ramp(x, y, ('sky0', 'sky1', 'sky2'), y / 71)
    return c.image


def hedges(t, style):
    c = Scene(style, HEDGE, base=hedge_sky(style))
    cx, cy, heading = lab_camera(t)
    # Clouds sit on a 360° panorama so they slide as the camera turns.
    width = TAU * 128 / (FOV / 2)
    for i, (px, py, s) in enumerate(((0, 14, 1), (230, 26, .6), (480, 10, .8), (700, 22, .5), (900, 16, .9))):
        x = (px - heading * width / TAU) % width
        for wrap in (x, x - width):
            if -60 < wrap < 300:
                puff(c, wrap, py, s, 'cloudshade', 'cloud')
    columns = lab_cast(cx, cy, heading)
    leaves = ('h0', 'h1', 'h2', 'h3', 'h4')
    for col, (depth, side, u, mx, my, top, bottom) in enumerate(columns):
        fog = min(1, depth / 10)
        for y in range(max(0, int(top)), 144):
            if y <= bottom:
                v = (y - top) / (bottom - top)
                iu, iv = int(u * 36), int(v * 36)
                value = (.62 if side else .82) * (.6 + .3 * noise(mx, my, side, iu, iv) + .2 * noise(mx, my, side, iu // 4, iv // 4))
                if v < .05: value = .95
                elif v > .9: value *= .5
                if depth < 5 and noise(mx, my, side, iu, iv, 7) > .97 and .1 < v < .85 and .25 < (u * 36) % 1 < .75 and .25 < (v * 36) % 1 < .75:
                    tone = 'flower' if noise(mx, my, iu, 8) > .5 else 'flowerw'
                    c.px(col, y, 'haze' if c.dither(col, y, fog) else tone); continue
                if c.dither(col, y, fog * .9):
                    c.px(col, y, 'haze')
                else:
                    c.ramp(col, y, leaves, value)
                continue
            fd, wx, wy = lab_floor(cx, cy, heading, col, y)
            fx, fy, gx, gy = wx % 1, wy % 1, floor(wx), floor(wy)
            grass = ((fx < .16 and lab_wall(gx - 1, gy)) or (fx > .84 and lab_wall(gx + 1, gy))
                     or (fy < .16 and lab_wall(gx, gy - 1)) or (fy > .84 and lab_wall(gx, gy + 1)))
            shaded = (fx < .3 and lab_wall(gx - 1, gy)) or (fy < .3 and lab_wall(gx, gy - 1))
            speck = noise(floor(wx * 16), floor(wy * 16), 9)
            if c.dither(col, y, min(1, fd / 10) * .9):
                tone = 'haze'
            elif grass:
                tone = 'grassl' if speck > .6 else 'grass'
            else:
                tone = ('gv0' if speck < .25 else 'gv2' if speck > .8 else 'gv1')
                if shaded: tone = 'shade' if speck < .6 else 'gv0'
            c.px(col, y, tone)
    return c.finish()


# ─── Registry ───────────────────────────────────────────────────────────────────

VARIANTS = {
    'naufrago': {
        'giorno': ('Mezzogiorno', 'Cielo sfumato, sole, nuvole morbide, gabbiani e riflessi sull’acqua.',
                   lambda t, s, e: island('giorno', t, s, e)),
        'tramonto': ('Tramonto', 'Sole sull’orizzonte, scia luminosa sul mare, palma in controluce.',
                     lambda t, s, e: island('tramonto', t, s, e)),
        'notte': ('Notte', 'Luna e stelle, scia lunare, schiuma bioluminescente, una stella cadente.',
                  lambda t, s, e: island('notte', t, s, e)),
    },
    'orbita': {
        'saturno': ('Anelli', 'Gigante gassoso in 3D: anelli con divisioni, ombre reciproche, luna in orbita.',
                    lambda t, s, e: saturn(t, s)),
        'terra': ('Pianeta blu', 'Continenti in rotazione, nuvole, luci notturne delle città e atmosfera.',
                  lambda t, s, e: earth(t, s)),
        'eclisse': ('Eclisse', 'Corona solare animata e anello di diamante; quasi tutto nero, ideale per OLED.',
                    lambda t, s, e: eclipse(t, s)),
    },
    'acquario': {
        'barriera': ('Barriera corallina', 'Raggi di luce, caustiche sulla sabbia, pesci pagliaccio, banco e tartaruga.',
                     lambda t, s, e: reef(t, s)),
        'abisso': ('Abisso', 'Meduse bioluminescenti, rana pescatrice con esca luminosa, neve marina.',
                   lambda t, s, e: abyss(t, s)),
        'stagno': ('Stagno koi', 'Vista dall’alto: tre carpe koi, ninfee, fiore di loto e cerchi nell’acqua.',
                   lambda t, s, e: pond(t, s)),
    },
    'ingranaggi': {
        'movimento': ('Movimento', 'Ruotismo che ingrana davvero, Côtes de Genève, ponti, rubini e bilanciere.',
                      lambda t, s, e: movement(t, s)),
        'tourbillon': ('Tourbillon', 'Gabbia rotante con bilanciere e scappamento a scatti, quadrante nero.',
                       lambda t, s, e: tourbillon(t, s)),
        'progetto': ('Progetto', 'Tavola tecnica blu: profili dei denti, quote e circonferenze primitive.',
                     lambda t, s, e: blueprint(t, s)),
    },
    'labirinto': {
        'torce': ('Torce', 'Dungeon in pietra illuminato da torce tremolanti, travi e lastre sul pavimento.',
                  lambda t, s, e: dungeon(t, s)),
        'vettoriale': ('Vettoriale', 'Wireframe verde fosforo anni ’80 con minimappa e bussola.',
                       lambda t, s, e: vector(t, s)),
        'siepi': ('Siepi', 'Labirinto di siepi in pieno giorno: ghiaia, erba, fiori e nuvole che ruotano.',
                  lambda t, s, e: hedges(t, s)),
    },
}


def render(name, variant, t, style='color', episode=0):
    return VARIANTS[name][variant][2](t % 30, style, episode)
