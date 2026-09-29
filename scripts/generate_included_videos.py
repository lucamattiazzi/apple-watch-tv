#!/usr/bin/env python3
"""Four original geometry-only CC0 loops for the included TV Watch catalog."""
from math import sin, cos, pi
from pathlib import Path
import io
import plistlib
import shutil
import subprocess
from PIL import Image, ImageDraw

TITLES = {'ingranaggi': 'Ingranaggi', 'tennis': 'Tennis', 'pong': 'Pong', 'acquario': 'Acquario'}
IDS = {name: f'9F290001-0000-4000-8000-{i:012d}' for i, name in enumerate(TITLES, 1)}


def make_frames(name, start=0):
    frames = []
    scale = 3
    for t in range(start, start + 30):
        u = (t % 30) / 30
        phase = 2 * pi * u
        image = Image.new('L', (192 * scale, 108 * scale))
        draw = ImageDraw.Draw(image)

        def ellipse(box, fill=None, outline=None, width=1):
            draw.ellipse(tuple(round(v * scale) for v in box), fill=fill, outline=outline, width=width * scale)

        def line(points, fill, width=1):
            draw.line([(round(x*scale), round(y*scale)) for x,y in points], fill=fill, width=width*scale)

        def polygon(points, fill):
            draw.polygon([(round(x*scale), round(y*scale)) for x,y in points], fill=fill)

        if name == 'ingranaggi':
            # Pitch radii share a tooth pitch. Adjacent wheels counter-rotate.
            draw.rectangle((0, 0, 192*scale, 108*scale), fill=24)
            for x,y in [(7,7),(185,7),(7,101),(185,101)]:
                ellipse((x-3,y-3,x+3,y+3),fill=120)
                line([(x-2,y+1),(x+2,y-1)],30)

            def gear(x, y, radius, teeth, angle, tone):
                points=[]
                for tooth in range(teeth):
                    for offset,r in [(0,radius-2),(.18,radius+2),(.58,radius+2),(.76,radius-2)]:
                        a=angle+(tooth+offset)*2*pi/teeth
                        points.append((x+r*cos(a),y+r*sin(a)))
                polygon(points,tone)
                ellipse((x-radius+6,y-radius+6,x+radius-6,y+radius-6),fill=15,outline=210)
                for spoke in range(6):
                    a=angle+spoke*pi/3
                    line([(x,y),(x+(radius-7)*cos(a),y+(radius-7)*sin(a))],tone,4)
                ellipse((x-6,y-6,x+6,y+6),fill=180,outline=245)
                ellipse((x-2,y-2,x+2,y+2),fill=35)
                line([(x-3*cos(angle),y-3*sin(angle)),(x+3*cos(angle),y+3*sin(angle))],45)

            gear(52,57,36,24,phase,170)
            gear(112,57,24,16,-phase*1.5+pi/16,220)
            gear(154,57,18,12,phase*2,145)
            # A fine balance wheel oscillates beneath the small gear.
            a=.8*sin(phase*3)
            ellipse((138,79,170,103),outline=160)
            line([(154-15*cos(a),91-11*sin(a)),(154+15*cos(a),91+11*sin(a))],210,2)
        elif name == 'tennis':
            draw.rectangle((0,0,192*scale,108*scale),fill=28)
            polygon([(31,12),(161,12),(161,96),(31,96)],55)
            for points in [[(31,12),(161,12),(161,96),(31,96),(31,12)],
                           [(31,24),(161,24)],[(31,84),(161,84)],
                           [(63,24),(63,84)],[(129,24),(129,84)],[(63,54),(129,54)]]:
                line(points,150)
            for y in range(14,96,4):
                line([(94,y),(98,y)],100)
            line([(94,10),(94,98)],220)
            line([(98,10),(98,98)],110)

            def player(x,y,side,swing,tone):
                ellipse((x-5,y+9,x+7,y+12),fill=12)
                stride=3*sin(phase*2)
                line([(x,y+2),(x-4,y+9+stride)],190,2)
                line([(x,y+2),(x+4,y+9-stride)],190,2)
                line([(x,y-5),(x,y+3)],tone,5)
                ellipse((x-3,y-11,x+3,y-5),fill=220)
                rx=x+side*11
                ry=y-3+5*swing
                line([(x,y-3),(x+side*6,y),(rx,ry)],220,2)
                ellipse((rx-3,ry-5,rx+3,ry+5),outline=245)
                line([(rx,ry-4),(rx,ry+4)],115)
                line([(rx-3,ry),(rx+3,ry)],115)
                line([(x,y-3),(x-side*5,y+1)],tone,2)

            player(19,41+10*sin(phase),1,sin(phase),225)
            player(173,73+10*sin(phase),-1,-sin(phase),120)
            f=2*u if u<.5 else 2-2*u
            x=30+132*f
            y=38+32*f
            # Two low bounces in each crossing, with a separate ground shadow.
            height=5*abs(sin(f*2*pi))
            ellipse((x-3,y+3,x+3,y+5),fill=20)
            ellipse((x-2,y-height-2,x+2,y-height+2),fill=255)
        elif name == 'pong':
            def triangle(v):
                return 1-abs(2*(v%1)-1)
            line([(5,18),(187,18)],105)
            line([(5,102),(187,102)],105)
            for y in range(23,102,9):
                line([(96,y),(96,y+4)],100)
            # Fixed score: this loop is an uninterrupted rally, with no missed ball.
            for x in [72,112]:
                line([(x,5),(x+6,5),(x+6,12),(x,12),(x,5)],210)
            x=22+148*triangle(u)
            y=23+74*triangle(3*u+.12)
            for px,py in [(17,23+74*triangle(3*u+.10)),(175,23+74*triangle(3*u+.14))]:
                py=max(31,min(89,py+3*sin(phase)))
                line([(px,py-10),(px,py+10)],245,3)
            draw.rectangle(tuple(round(v*scale) for v in (x-2,y-2,x+2,y+2)),fill=255)
        elif name == 'acquario':
            # Fish cross the edge fully offscreen before wrapping around.
            for x,height in [(9,31),(22,22),(166,35),(179,25)]:
                points=[(x+3*sin(phase+j*.55)*j/height,103-j) for j in range(height)]
                line(points,110,2)
                for j in range(7,height,7):
                    line([(x,103-j),(x+7*sin(phase+j),99-j)],130,2)
            for i in range(18):
                x=(i*29)%192
                ellipse((x,101+i%3,x+5,108),fill=70+i%4*25)
            for i in range(6):
                x=36+i*24+3*sin(phase+i)
                y=108-((u+i/6)*120)%120
                ellipse((x-1.5,y-1.5,x+1.5,y+1.5),outline=90)
            for i,(base_y,size,speed,tone) in enumerate([(29,11,1,230),(58,14,-1,170),(79,8,1,205)]):
                x=((u*speed+i*.37)*240)%240-24
                y=base_y+5*sin(phase+i*2)
                side=1 if speed>0 else -1
                tail=x-side*size
                wag=2*sin(phase*3+i)
                polygon([(tail,y),(tail-side*7,y-size*.55+wag),(tail-side*7,y+size*.55+wag)],tone)
                ellipse((x-size,y-size*.5,x+size,y+size*.5),fill=tone)
                polygon([(x-4,y-3),(x+1,y-size*.8),(x+5,y-2)],tone)
                line([(x,y-3),(x-side*3,y+3)],80)
                ellipse((x+side*size*.55-1,y-2,x+side*size*.55+1,y),fill=0)
        else:
            raise ValueError(name)
        frames.append(image.resize((192,108),Image.Resampling.LANCZOS).point(lambda v: round(v*7/255)*255//7))
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
