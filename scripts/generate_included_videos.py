#!/usr/bin/env python3
"""Four original, geometry-only CC0 loops, matching Orbita's monochrome space theme."""
from math import sin, cos, pi
from pathlib import Path
import io
import plistlib
import shutil
import subprocess
from PIL import Image, ImageDraw

TITLES = {'eclisse': 'Eclisse', 'cometa': 'Cometa', 'pulsar': 'Pulsar', 'vortice': 'Vortice'}
IDS = {name: f'9F280001-0000-4000-8000-{i:012d}' for i, name in enumerate(TITLES, 1)}


def make_frames(name, start=0):
    frames = []
    scale = 3
    for t in range(start, start + 30):
        phase = 2 * pi * (t % 30) / 30
        image = Image.new('L', (192 * scale, 108 * scale))
        draw = ImageDraw.Draw(image)
        def ellipse(box, fill=None, outline=None, width=1):
            draw.ellipse(tuple(round(v * scale) for v in box), fill=fill, outline=outline, width=width * scale)
        def line(points, fill, width=1):
            draw.line([(round(x*scale), round(y*scale)) for x,y in points], fill=fill, width=width*scale)
        for i in range(45):
            x, y = (i*73+11) % 190, (i*37+7) % 102
            ellipse((x,y,x+.6,y+.6), fill=round(85+60*(1+sin(phase+i))/2))
        if name == 'eclisse':
            for r in range(37, 25, -1):
                ellipse((96-r,54-r,96+r,54+r), outline=round(15+(37-r)*7))
            ellipse((70,28,122,80), fill=235)
            x = 96 + 38 * sin(phase)
            ellipse((x-24,28,x+24,76), fill=8, outline=100)
            glint = 96 + 50*cos(phase)
            ellipse((glint-1,84+5*sin(phase),glint+1,86+5*sin(phase)),fill=200)
            line([(0,100),(30,91),(48,99),(79,90),(105,96),(132,89),(165,99),(192,92)], 95)
        elif name == 'cometa':
            # Closed ellipse with a trailing arc: no jump when the loop repeats.
            for j in range(24, 0, -1):
                a = phase - j*.045
                x,y = 96+69*cos(a),54+31*sin(a)
                r = .8 + (24-j)*.095
                ellipse((x-r,y-r,x+r,y+r), fill=round(25+(24-j)*6))
            x,y=96+69*cos(phase),54+31*sin(phase)
            ellipse((x-3,y-3,x+3,y+3),fill=255)
            ellipse((85,43,107,65),fill=40,outline=135)
        elif name == 'pulsar':
            for ring in range(4):
                r = 6 + ((t % 30 + ring*7.5) % 30)*1.35
                ellipse((96-r,54-r,96+r,54+r),outline=round(180-3*r))
            for side in [0,pi]:
                angle = phase+side
                line([(96,54),(96+57*cos(angle),54+42*sin(angle))],155,2)
            ellipse((89,47,103,61),fill=245)
            ellipse((93,51,99,57),fill=255)
        elif name == 'vortice':
            for arm in range(3):
                points=[]
                for j in range(130):
                    r=4+j*.34
                    a=arm*2*pi/3+phase+j*.045
                    points.append((96+1.5*r*cos(a),54+.85*r*sin(a)))
                line(points,100+arm*50,2)
            ellipse((86,44,106,64),fill=0,outline=240)
        else:
            raise ValueError(name)
        frames.append(image.resize((192,108),Image.Resampling.LANCZOS).quantize(8).convert('L'))
    return frames


def generate():
    output=Path('WatchTV/Shared/IncludedVideos'); output.mkdir(parents=True,exist_ok=True)
    previews=Path('out/included'); previews.mkdir(parents=True,exist_ok=True)
    sheet=Image.new('L',(192*5,108*4))
    for row,(name,title) in enumerate(TITLES.items()):
        frames=make_frames(name)
        pngs=[]
        for frame in frames:
            stream=io.BytesIO(); frame.save(stream,format='PNG'); pngs.append(stream.getvalue())
        payload={'version':2,'id':IDS[name],'title':title,'fonts':[],'frames':pngs}
        (output/f'{name}.video').write_bytes(plistlib.dumps(payload,fmt=plistlib.FMT_BINARY))
        for column,frame in enumerate(frames[::6]): sheet.paste(frame,(column*192,row*108))
        frames[0].save(previews/f'{name}.png')
        subprocess.run([shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg', '-hide_banner','-loglevel','error','-y',
            '-f','rawvideo','-pixel_format','gray','-video_size','192x108','-framerate','1','-i','pipe:0',
            '-vf','scale=960:540:flags=neighbor','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',
            '-movflags','+faststart',str(previews/f'{name}.mp4')],input=b''.join(f.tobytes() for f in frames),check=True)
    sheet.save(previews/'contact.png')

if __name__=='__main__': generate()
