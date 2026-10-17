#!/usr/bin/env python3
"""Generate five original TV Watch loops in monochrome and color."""
from pathlib import Path
import io
import plistlib
import shutil
import subprocess

from PIL import Image, ImageDraw
try:
    from .screensaver_art import ACTIONS, render
except ImportError:
    from screensaver_art import ACTIONS, render

TITLES = {
    'naufrago': 'Isola deserta',
    'orbita': 'Orbita',
    'acquario': 'Acquario',
    'ingranaggi': 'Ingranaggi',
    'labirinto': 'Labirinto 3D',
}
STYLES = ('bw', 'color')
FPS = 2
IDS = {(name, style): f'9F300003-0000-4000-8000-{index:012d}'
       for index, (name, style) in enumerate(
           ((name, style) for name in TITLES for style in STYLES), 1)}



def make_frames(name, start=0, style='bw', episode=0):
    if name not in TITLES or style not in STYLES or not 0 <= episode < (len(ACTIONS) if name == 'naufrago' else 1):
        raise ValueError((name, style, episode))
    return [render(name, start + index / FPS, style, episode) for index in range(30 * FPS)]


def generate():
    output = Path('WatchTV/Shared/IncludedVideos')
    previews = Path('out/included')
    output.mkdir(parents=True, exist_ok=True)
    previews.mkdir(parents=True, exist_ok=True)
    sheet = Image.new('RGB', (256 * len(TITLES), 144 * len(STYLES)))
    for name, title in TITLES.items():
        for style in STYLES:
            frames = [frame for episode in range(len(ACTIONS) if name == 'naufrago' else 1)
                      for frame in make_frames(name, style=style, episode=episode)]
            pngs = []
            for frame in frames:
                stream = io.BytesIO()
                frame.save(stream, format='PNG')
                pngs.append(stream.getvalue())
            payload = {'version': 4, 'id': IDS[name, style], 'title': title,
                       'fonts': [], 'frames': pngs, 'playback': {'framesPerSecond': FPS, 'duration': 30}}
            (output / f'{name}-{style}.video').write_bytes(
                plistlib.dumps(payload, fmt=plistlib.FMT_BINARY))
            frames[0].save(previews / f'{name}-{style}.png')
            sheet.paste(frames[0].convert('RGB').resize((256, 144)),
                        (list(TITLES).index(name) * 256, STYLES.index(style) * 144))
            mode = 'gray' if style == 'bw' else 'rgb24'
            subprocess.run([shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg',
                '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo',
                '-pixel_format', mode, '-video_size',
                f'{frames[0].width}x{frames[0].height}',
                '-framerate', str(FPS), '-i', 'pipe:0',
                '-vf', 'scale=960:540:flags=neighbor', '-c:v', 'libx264',
                '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                str(previews / f'{name}-{style}.mp4')],
                input=b''.join(frame.tobytes() for frame in frames), check=True)
    sheet.save(previews / 'contact.png')


if __name__ == '__main__':
    generate()
