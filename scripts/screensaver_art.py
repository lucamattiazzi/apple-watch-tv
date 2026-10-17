"""Original, palette-authored pixel art. Coordinates are native 256×144 pixels."""
from math import sin, cos, pi, sqrt, atan, floor
from PIL import Image, ImageDraw, ImageFont

ACTIONS = ('fishing', 'telescope', 'coconut', 'sandcastle', 'reading', 'sleeping',
           'bottle', 'crab', 'cooking', 'seagull', 'rain', 'raft')

# Every color has an intentional monochrome value; color brightness is not the B/W design.
COLORS = {
    'ink': ('#10152e', 0), 'deep': ('#172e59', 36), 'sea': ('#28598d', 73),
    'water': ('#378dad', 109), 'foam': ('#9adccc', 182), 'white': ('#fff3d4', 255),
    'sky': ('#80b6c2', 109), 'cloud': ('#d2e2ce', 182), 'sand': ('#e5bc76', 182),
    'sandlight': ('#ffe0a0', 219), 'sandshade': ('#af784d', 109),
    'wood': ('#715344', 73), 'bark': ('#b88558', 146), 'leafdark': ('#245c52', 36),
    'leaf': ('#458f62', 109), 'leaflight': ('#8fc275', 182),
    'skin': ('#dc9d74', 182), 'skinlight': ('#ffd0a0', 219), 'shirt': ('#eee7d0', 255),
    'cloth': ('#a35d5b', 109), 'red': ('#e36b50', 146), 'gold': ('#d4a552', 182),
    'goldlight': ('#ffe2a0', 255), 'goldshade': ('#775838', 73),
    'steel': ('#6a8290', 109), 'silver': ('#b9c6c6', 219), 'darksteel': ('#304555', 36),
    'pink': ('#d37b99', 182), 'blue': ('#58b4d1', 182), 'violet': ('#6b628d', 109),
}

class Canvas:
    def __init__(self, style, background='ink'):
        self.style = style
        self.image = Image.new('RGB', (256, 144), self.c(background))
        self.d = ImageDraw.Draw(self.image)
    def c(self, name):
        color, gray = COLORS[name]
        return color if self.style == 'color' else (gray, gray, gray)
    def line(self, points, color, width=1):
        self.d.line([(round(x), round(y)) for x,y in points], fill=self.c(color), width=width)
    def poly(self, points, color):
        self.d.polygon([(round(x),round(y)) for x,y in points], fill=self.c(color))
    def rect(self, box, color):
        self.d.rectangle(tuple(round(v) for v in box), fill=self.c(color))
    def oval(self, box, color, outline=None):
        self.d.ellipse(tuple(round(v) for v in box), fill=self.c(color), outline=self.c(outline) if outline else None)
    def arc(self, box, start, end, color):
        self.d.arc(tuple(round(v) for v in box), start, end, fill=self.c(color))
    def text(self, xy, text, color='white'):
        self.d.text(xy, text, font=ImageFont.load_default(size=8), fill=self.c(color))
    def finish(self):
        if self.style == 'bw':
            return self.image.resize((192,108), Image.Resampling.NEAREST).convert('L').point(
                lambda value: round(value * 7 / 255) * 255 // 7)
        return self.image


def cloud(c, x, y, small=False):
    s = .6 if small else 1
    for dx,dy,r in [(0,0,11),(12,-5,13),(27,0,10),(40,3,7)]:
        c.oval((x+(dx-r)*s,y+(dy-r/2)*s,x+(dx+r)*s,y+(dy+r/2)*s),'cloud')
    c.line([(x-9*s,y+5*s),(x+45*s,y+5*s)],'white')


def palm(c, t):
    c.poly([(164,105),(169,104),(181,47),(175,45)],'wood')
    c.line([(167,103),(178,48)],'bark',3)
    for y in range(53,104,6):
        x=178-(y-48)*.2
        c.line([(x-2,y),(x+2,y-1)],'sandshade')
    for i,(dx,dy) in enumerate([(-37,6),(-32,-7),(-20,-17),(3,-20),(25,-14),(37,-1),(28,12),(-14,17)]):
        sway=sin(t*pi/15+i)*2
        tip=(178+dx,47+dy+sway)
        c.poly([(178,46),(178+dx*.55,36+dy*.6),tip,(178+dx*.65,56+dy*.6)],'leafdark')
        c.poly([(178,46),(178+dx*.55,39+dy*.6),tip,(178+dx*.55,51+dy*.6)],'leaf')
        c.line([(178,46),tip],'leaflight')
        for j in (.4,.6,.8):
            x,y=178+dx*j,46+dy*j
            c.line([(x,y),(x+2,y+4)],'leafdark')
    for x,y in [(172,49),(179,51),(184,49)]: c.oval((x-2,y-2,x+2,y+2),'wood','bark')


def person(c, x, y, t, pose='idle', facing=1):
    """Articulated 25-pixel sprite: outlined limbs, torn clothes, beard and expressive head."""
    bob=1 if pose=='walk' and int(t)%2 else 0
    y-=bob
    def p(dx,dy): return (x+dx*facing,y+dy)
    def limb(points, color, width=3):
        points=[p(a,b) for a,b in points]
        c.line(points,'ink',width+2); c.line(points,color,width)
    if pose=='sleep':
        c.oval((x-12,y-5,x+14,y+1),'wood')
        c.rect((x-11,y-6,x+3,y-2),'shirt')
        c.oval((x+3,y-10,x+11,y-3),'skinlight','ink')
        c.line([(x+6,y-7),(x+9,y-7)],'ink')
        c.line([(x-12,y-4),(x-19,y-2)],'skin',3)
        if int(t)%4<3: c.text((x+10,y-21-int(t)%4*2),'z')
        return
    seated=pose in ('read','sit','build')
    if seated:
        y+=4
        limb([(-3,-7),(-5,-3),(3,-2)],'skin')
        limb([(3,-7),(7,-4),(12,-3)],'skin')
    else:
        stride=3*sin(t*pi/2) if pose in ('walk','dance','run') else 0
        limb([(-3,-8),(-4-stride,-3),(-5-stride,0)],'skin')
        limb([(3,-8),(4+stride,-3),(5+stride,0)],'skinlight')
    c.poly([p(-5,-16),p(4,-17),p(5,-7),p(1,-5),p(0,-8),p(-3,-6),p(-6,-8)],'ink')
    c.poly([p(-4,-16),p(3,-16),p(4,-9),p(-4,-8)],'shirt')
    c.poly([p(-4,-9),p(4,-9),p(4,-6),p(0,-7),p(-4,-6)],'cloth')
    c.line([p(-3,-14),p(-2,-11)],'cloud')
    arms={'idle':[(-6,-13),(-6,-9),(5,-10)], 'walk':[(-7,-10),(-5,-12),(7,-13)],
          'fish':[(-5,-12),(2,-14),(10,-15)], 'look':[(-5,-13),(4,-21),(10,-21)],
          'wave':[(-6,-13),(-9,-20),(8,-22+int(t)%3*2)],
          'shake':[(-5,-14),(1,-20),(9,-18)], 'read':[(-5,-11),(0,-10),(9,-11)],
          'sit':[(-6,-10),(0,-11),(7,-10)], 'build':[(-5,-11),(3,-10),(10,-9-int(t)%2*4)],
          'throw':[(-6,-13),(3,-19),(9,-24 if int(t)%2 else -15)],
          'dance':[(-8,-19),(0,-16),(8,-20)], 'run':[(-7,-18),(0,-13),(8,-12)]}
    a,b,d=arms.get(pose,arms['idle'])
    limb([(-4,-16),a],'skin',2)
    limb([(4,-16),b,d],'skinlight',2)
    # Hair, nose, white cap, brows and beard make a readable face in both palettes.
    c.oval((x-5,y-26,x+5,y-16),'ink')
    c.oval((x-3,y-25,x+4,y-18),'skinlight')
    c.rect((x-4,y-19,x+4,y-17),'wood')
    c.rect((x-3,y-17,x+3,y-15),'wood')
    c.rect((x-4,y-26,x+3,y-25),'shirt')
    c.line([(x-5,y-24),(x+5,y-24)],'silver')
    c.rect((x+facing*3,y-22,x+facing*3,y-21),'ink')
    c.oval((x+facing*4-1,y-21,x+facing*4+2,y-19),'skin')
    c.line([(x,y-17),(x+2,y-17)],'sandlight')


def island(t, style, episode):
    c=Canvas(style,'sky'); phase=t*2*pi/30
    cloud(c,28,23); cloud(c,100,13,True); cloud(c,210,28,True)
    c.rect((0,59,255,143),'deep'); c.rect((0,59,255,73),'sea'); c.line([(0,59),(255,59)],'foam')
    # Broken wave contours and a quiet horizon, rather than straight stripes.
    for i in range(36):
        x=(i*61+int(3*sin(phase+i)))%280-14; y=65+(i*17)%75
        c.line([(x,y),(x+5,y-1),(x+12,y),(x+18,y)],'sea' if i%3 else 'water')
    c.oval((59,91,211,125),'water'); c.oval((64,92,206,120),'foam')
    c.poly([(66,109),(75,101),(96,96),(145,94),(181,98),(201,106),(198,113),(177,118),(126,120),(88,116)],'sandshade')
    c.poly([(67,107),(78,101),(101,96),(147,95),(177,98),(199,105),(192,112),(153,116),(113,116),(84,113)],'sand')
    c.poly([(81,103),(112,98),(163,99),(185,103),(180,108),(118,111),(85,109)],'sandlight')
    for i in range(30):
        x=83+(i*43)%104;y=105+(i*7)%9
        c.rect((x,y,x+1,y),'sandshade')
    c.oval((154,105,180,110),'sandshade'); palm(c,t)
    c.line([(66,118),(81,121),(117,123)],'foam'); c.line([(164,121),(196,117),(207,111)],'white')
    # Each vignette starts/ends at home with a pause; props exist only during the action.
    action=ACTIONS[episode]; active=9<=t<=23
    targets={'fishing':190,'telescope':99,'coconut':160,'sandcastle':138,'reading':130,'sleeping':150,
             'bottle':83,'crab':123,'cooking':137,'seagull':120,'rain':129,'raft':95}
    target=targets[action]
    travel=max(0,min(1,(t-5)/4)) if t<24 else max(0,(28-t)/4)
    x=112+(target-112)*travel;y=109
    pose='walk' if 5<t<9 or 24<=t<28 else 'idle'; facing=1 if target>112 else -1
    if t>=24: facing=-facing
    if t<=5 or t>=28: facing=1
    if active:
        q=t-9; facing=1
        if action=='fishing':
            pose='fish'; c.line([(x+8,y-16),(x+20,y-34),(x+35,y-37)],'wood',2)
            fy=119 if q<8 else 119-(q-8)*5
            c.line([(x+35,y-37),(x+40,fy)],'white')
            c.oval((x+38,fy-1,x+42,fy+1),'red')
            if q>=8:
                c.poly([(x+38,fy+2),(x+42,fy+2),(x+42,fy+8),(x+48,fy+8),(x+48,fy+11),(x+37,fy+11)],'wood')
        elif action=='telescope':
            pose='look'; c.line([(x+7,y-21),(x+21,y-21)],'goldshade',5);c.line([(x+9,y-22),(x+21,y-22)],'goldlight',2)
            bx=212-q*6
            c.poly([(bx,69),(bx+17,69),(bx+13,73),(bx+4,73)],'ink');c.line([(bx+8,69),(bx+8,60)],'cloud');c.poly([(bx+9,61),(bx+9,67),(bx+15,67)],'white')
        elif action=='coconut':
            pose='shake' if q<7 else 'sit';x+=int(sin(q*pi/2)*2) if q<7 else 0
            ny=54+min(51,max(0,q-5)*9)
            c.oval((158,ny,164,ny+6),'wood','bark')
            if q in (10,11):c.line([(153,78),(150,74),(153,72)],'white')
        elif action=='sandcastle':
            pose='build';h=min(15,q+2)
            c.rect((153,109-h,177,111),'sandshade');c.rect((155,109-h,175,109),'sand')
            for bx in (153,162,171): c.rect((bx,105-h,bx+5,109-h),'sandlight')
            if q>8:c.rect((163,104,168,111),'wood'); c.line([(174,94),(174,82)],'wood');c.poly([(175,82),(184,85),(175,88)],'red')
        elif action=='reading':
            pose='read';c.poly([(x-2,98),(x+6,96),(x+13,98),(x+13,105),(x+6,103),(x-2,105)],'ink')
            c.poly([(x-1,98),(x+6,97),(x+12,99),(x+12,103),(x+6,102),(x-1,104)],'sandlight')
        elif action=='sleeping': pose='sleep'
        elif action=='bottle':
            pose='throw' if q<5 else 'wave'
            bx=x+9+min(90,q*7);by=89-22*sin(min(1,q/10)*pi)+max(0,q-10)*5
            c.rect((bx,by,bx+4,by+7),'leaf');c.rect((bx+1,by-2,bx+3,by),'sand');c.rect((bx+1,by+2,bx+2,by+5),'white')
        elif action=='crab':
            pose='run';x=120+24*sin(q*pi/7);cx=x-13
            c.oval((cx-4,109,cx+4,113),'red','ink');c.line([(cx-5,108),(cx-7,105)],'red',2);c.line([(cx+5,108),(cx+7,105)],'red',2)
            for dx in (-5,5):c.line([(cx+dx,111),(cx+dx*1.4,114)],'red')
        elif action=='cooking':
            pose='fish';c.line([(x+8,93),(x+35,103)],'wood',2)
            c.line([(153,114),(171,109)],'wood',3);c.line([(155,109),(170,115)],'wood',3)
            c.poly([(155,111),(156,101-q%3),(161,105),(165,97+q%4),(170,111)],'red')
            c.poly([(159,111),(161,103),(166,110)],'goldlight')
            c.oval((160,101,169,105),'gold');c.poly([(169,102),(173,100),(173,106)],'gold')
        elif action=='seagull':
            pose='wave';gx=x+10+q*4;gy=78-8*sin(q*pi/14)
            c.oval((gx-3,gy,gx+5,gy+4),'white');c.line([(gx-1,gy),(gx-7,gy-4-q%2*3)],'white',2);c.line([(gx+1,gy),(gx+9,gy-4-q%2*3)],'white',2)
            c.oval((gx+1,gy+5,gx+9,gy+8),'red')
        elif action=='rain':
            pose='sit';cloud(c,111,51)
            for j in range(14):
                rx=105+j*4;ry=62+(j*11+t*6)%41;c.line([(rx,ry),(rx-2,ry+4)],'foam')
            c.poly([(x-14,82),(x-8,73),(x,71),(x+9,75),(x+15,82)],'leaf');c.line([(x,77),(x,96)],'wood',2)
        elif action=='raft':
            pose='build'
            for j in range(4):c.line([(x+14,104+j*3),(x+40,108+j*3)],'wood',4);c.line([(x+14,103+j*3),(x+40,107+j*3)],'bark')
            for bx in (x+20,x+33):c.line([(bx,103),(bx-2,117)],'sand')
            c.line([(x+9,98),(x+12,88+q%2*7)],'wood',2);c.rect((x+9,86+q%2*7,x+16,90+q%2*7),'steel')
    # Props held at chest height stay visible in front of the body.
    person(c,x,y,t,pose,facing)
    if active and action=='reading':
        c.poly([(x-2,98),(x+6,97),(x+13,99),(x+13,105),(x+6,103),(x-2,105)],'goldlight');c.line([(x+6,98),(x+6,103)],'wood')
    return c.finish()


def fish(c,x,y,size,kind,t,direction=1):
    def p(dx,dy):return x+direction*dx*size,y+dy*size
    def shape(points,color):c.poly([p(a,b) for a,b in points],color)
    wag=.18*sin(t*2*pi/5)
    if kind=='angel':
        shape([(-.5,0),(-.1,-1.6),(.6,-.4),(.9,0),(.5,.6),(-.2,1.6)],'goldshade')
        shape([(-.4,0),(-.1,-1.3),(.5,-.3),(.8,0),(.4,.5),(-.1,1.3)],'goldlight')
        shape([(-.4,0),(-1,-.5+wag),(-1,.5+wag)],'gold')
        c.oval((x-size*.5,y-size*.65,x+size*.6,y+size*.65),'gold')
        for i in (-.25,.2): c.line([p(i,-.5),p(i,.55)],'ink',2)
        c.line([p(.1,.5),p(.2,1.5)],'goldlight')
    else:
        body='red' if kind=='koi' else 'blue'
        shape([(-.6,0),(-1.5,-.7+wag),(-1.3,.1),(-1.5,.7+wag)],body)
        shape([(-.6,-.2),(-.2,-.9),(.4,-.45)],'gold' if kind=='koi' else 'violet')
        c.oval((x-size,y-size*.52,x+size,y+size*.52),'ink')
        c.oval((x-size+.8,y-size*.5+.8,x+size-1,y+size*.5-1),'sandlight' if kind=='koi' else 'blue')
        if kind=='koi':
            for dx,dy,r in [(-.6,-.1,.3),(.2,-.15,.4),(.6,.2,.2)]:
                fx,fy=p(dx,dy);c.oval((fx-r*size,fy-r*size,fx+r*size,fy+r*size),'red')
            c.line([p(-.6,.2),p(.3,.4)],'gold')
        else:c.line([p(-.8,0),p(.6,0)],'white');c.line([p(-.7,.25),p(.1,.25)],'red',2)
        shape([(0,.2),(-.3,.8+wag),(.4,.3)],'white' if kind=='koi' else 'blue')
    ex,ey=p(.55,-.12);c.oval((ex-1,ey-1,ex+1,ey+1),'ink');c.rect((ex,ey-1,ex,ey-1),'white')


def aquarium(t,style):
    c=Canvas(style,'ink');phase=t*2*pi/30
    c.rect((0,0,255,46),'deep');c.rect((0,47,255,111),'darksteel')
    for i in range(5):
        x=i*64+int(sin(phase+i)*3)
        c.poly([(x,0),(x+6,0),(x-26,105),(x-45,105)],'deep')
    # An intricate planted tank, built as layered silhouettes with sparse highlights.
    for layer in range(2):
        for i in range(19):
            x=(i*41)%270-6;h=24+(i*17)%72
            if 65<x<186:h*=.42
            points=[(x+sin(j/13+phase+i)*j/18,128-j) for j in range(int(h))]
            c.line(points,'leafdark' if layer==0 else 'leaf',2)
            if layer:
                for j in range(4,int(h),7):
                    a,b=points[j];side=1 if j%2 else -1
                    c.poly([(a,b+2),(a+side*8,b-3),(a+side*11,b-9),(a+side*3,b-5)],'leafdark' if i%3 else 'leaf')
                    c.line([(a,b),(a+side*9,b-7)],'leaf' if i%3 else 'leaflight')
    c.poly([(0,128),(37,119),(85,128),(143,124),(213,118),(255,121),(255,144),(0,144)],'wood')
    c.poly([(0,127),(35,120),(82,129),(143,125),(213,119),(255,122),(255,127),(163,130),(57,134),(0,133)],'sandshade')
    for i in range(220):
        x=(i*83)%256;y=129+(i*17)%15;c.rect((x,y,x+1,y),'bark' if i%3 else 'sand')
    for x,y,r in [(27,125,20),(222,122,24),(200,129,13)]:
        c.poly([(x-r,y),(x-r*.7,y-r*.6),(x-r*.2,y-r),(x+r*.7,y-r*.7),(x+r,y),(x+r*.4,y+4)],'darksteel')
        c.line([(x-r*.7,y-r*.6),(x-r*.2,y-r),(x+r*.7,y-r*.7)],'steel')
        for j in range(5):c.line([(x-r*.5+j*3,y-r*.5),(x-r*.5+j*3+4,y-r*.3)],'leaf')
    for i in range(11):
        x=41+i*17+sin(phase+i)*2;y=135-((t*3+i*13)%138)
        c.arc((x,y,x+3,y+4),70,300,'steel');c.rect((x+1,y,x+1,y),'foam')
    for i in range(5):fish(c,110+i*12+16*sin(phase),37+6*sin(phase+i*.6),3,'neon',t+i)
    fish(c,92+38*sin(phase),80+7*cos(phase),22,'koi',t,1 if cos(phase)>=0 else -1)
    fish(c,170+26*sin(phase+1),60+8*cos(phase),17,'angel',t,-1)
    fish(c,155+25*cos(phase),108+4*sin(phase),7,'neon',t,1)
    return c.finish()


def orbit(t,style):
    c=Canvas(style);phase=t*2*pi/30
    for i in range(100):
        x=(i*83+17)%256;y=(i*47+3)%144
        c.rect((x,y,x,y),'steel' if i%5 else 'silver')
        if i%23==0:c.line([(x-2,y),(x+2,y)],'silver');c.line([(x,y-2),(x,y+2)],'silver')
    cx,cy,r=132,69,40
    # Rotating surface bands and directional light, rendered pixel by pixel on a sphere.
    for y in range(-r,r+1):
        for x in range(-r,r+1):
            d=(x*x+y*y)/(r*r)
            if d>1:continue
            z=sqrt(1-d);light=max(0,(-x*.5-y*.4)/r+z*.7)
            band=sin(y*.34+sin(x*.055+phase)*1.8)+.45*sin(y*.77+phase)
            color='goldshade' if light<.22 else 'sandshade' if band<-.2 else 'gold' if light<.7 else 'sandlight'
            if light<.07:color='wood'
            c.rect((cx+x,cy+y,cx+x,cy+y),color)
    # Angled rings are correctly hidden behind the globe on their far half.
    for front in (False,True):
        for j in range(260):
            a=j*2*pi/260;x=88*cos(a);y=21*sin(a)
            px=cx+x*.94-y*.34;py=cy+x*.34+y*.94
            if (sin(a)>0)!=front:continue
            if not front and (px-cx)**2+(py-cy)**2<r*r:continue
            c.rect((px,py,px+1,py),'silver' if front else 'steel')
            c.rect((px*1.02-cx*.02,py*1.02-cy*.02,px*1.02-cx*.02+1,py*1.02-cy*.02),'goldlight' if front else 'goldshade')
    mx=132+102*cos(phase);my=70+48*sin(phase)
    c.oval((mx-7,my-7,mx+7,my+7),'ink','steel');c.oval((mx-6,my-6,mx+4,my+5),'silver')
    c.oval((mx-3,my-3,mx,my),'steel');c.rect((mx+1,my+2,mx+3,my+3),'steel')
    c.text((10,126),'ORBITAL / 01','steel');c.line([(9,13),(9,7),(23,7)],'steel');c.line([(234,136),(247,136),(247,129)],'steel')
    return c.finish()


def gear(c,cx,cy,r,teeth,a,kind='gold'):
    c.oval((cx-r-2,cy-r+1,cx+r+2,cy+r+4),'ink')
    pts=[]
    for j in range(teeth*4):
        ang=a+j*2*pi/(teeth*4);rad=r if j%4 in (1,2) else r-2
        pts.append((cx+rad*cos(ang),cy+rad*sin(ang)))
    c.poly(pts,'goldshade' if kind=='gold' else 'steel')
    c.arc((cx-r+1,cy-r+1,cx+r-1,cy+r-1),190,350,'goldlight' if kind=='gold' else 'silver')
    c.oval((cx-r+4,cy-r+4,cx+r-4,cy+r-4),'ink','gold' if kind=='gold' else 'silver')
    for i in range(5 if teeth%5==0 else 6):
        n=5 if teeth%5==0 else 6;ang=a+i*2*pi/n
        points=[(cx+rr*cos(aa),cy+rr*sin(aa)) for rr,aa in [(3,ang-.3),(r-5,ang-.10),(r-5,ang+.10),(3,ang+.3)]]
        c.poly(points,'gold' if kind=='gold' else 'steel');c.line([(cx+5*cos(ang),cy+5*sin(ang)),(cx+(r-6)*cos(ang),cy+(r-6)*sin(ang))],'goldlight' if kind=='gold' else 'silver')
    c.oval((cx-5,cy-5,cx+5,cy+5),'goldshade','goldlight');c.oval((cx-2,cy-2,cx+2,cy+2),'red','ink');c.rect((cx-1,cy-1,cx-1,cy-1),'white')


def clockwork(t,style):
    c=Canvas(style,'darksteel');phase=t*2*pi/30
    c.oval((-27,-59,282,230),'steel','silver');c.oval((-18,-50,273,221),'darksteel','ink')
    for x in range(0,256,13):
        for y in range(-5,145,11):c.arc((x,y,x+15,y+15),35,280,'deep')
    for x,y,r,n,d in [(82,74,38,40,1),(141,61,23,24,-1),(177,91,26,30,1),(211,53,27,30,-1),(42,27,22,24,-1),(46,124,24,24,-1),(124,119,23,24,-1),(147,22,18,20,1)]:
        gear(c,x,y,r,n,d*phase*24/n)
    # Rounded skeleton bridges with bevels, engraved slots and blued screw heads.
    c.poly([(0,74),(14,69),(32,81),(37,99),(27,110),(0,106)],'silver')
    c.line([(0,75),(13,71),(29,82),(34,98)],'white')
    c.poly([(140,0),(167,0),(173,14),(199,22),(215,17),(256,20),(256,34),(211,35),(194,40),(164,28),(158,16),(138,12)],'steel')
    c.line([(144,2),(160,4),(169,21),(193,33),(214,27),(253,29)],'silver',2)
    c.poly([(80,144),(84,131),(108,132),(135,138),(165,133),(168,144)],'silver')
    for x,y in [(17,90),(148,7),(235,26),(101,138)]:
        c.oval((x-6,y-6,x+6,y+6),'ink','white');c.oval((x-4,y-4,x+4,y+4),'deep','steel');c.line([(x-3,y+1),(x+3,y-1)],'silver')
    # A separate, oscillating balance assembly gives the movement a second rhythm.
    cx,cy=223,119;c.oval((cx-23,cy-23,cx+23,cy+23),'ink','goldlight');c.oval((cx-20,cy-20,cx+20,cy+20),'ink','gold')
    a=.7*sin(phase*3)
    for j in range(3):ang=a+j*2*pi/3;c.line([(cx,cy),(cx+18*cos(ang),cy+18*sin(ang))],'gold',2)
    c.line([(cx+(2+j*.09)*cos(j*.24+a),cy+(2+j*.09)*sin(j*.24+a)) for j in range(151)],'silver')
    c.oval((cx-3,cy-3,cx+3,cy+3),'red','goldlight')
    return c.finish()


def labyrinth(t,style):
    c=Canvas(style);a=t*2*pi/30;cx,cy=5.5+3.1*cos(a),5.5+3.1*sin(a);angle=a+pi/2
    c.rect((0,0,255,71),'ink');c.rect((0,72,255,143),'darksteel')
    # Perspective ray casting with stone blocks, luminous niches, ceiling and tiled floor.
    def wall(x,y):return x<=0 or y<=0 or x>=10 or y>=10 or (4<=x<=6 and 4<=y<=6)
    bottoms=[]
    for col in range(256):
        ray=angle+atan((col/255-.5)*1.35);dx,dy=cos(ray),sin(ray);mx,my=floor(cx),floor(cy)
        sx,sy=(1 if dx>0 else -1),(1 if dy>0 else -1);ddx,ddy=abs(1/(dx or 1e-9)),abs(1/(dy or 1e-9))
        tx=((mx+1-cx) if dx>0 else cx-mx)*ddx;ty=((my+1-cy) if dy>0 else cy-my)*ddy
        while True:
            if tx<ty:dist,tx,mx,side=tx,tx+ddx,mx+sx,0
            else:dist,ty,my,side=ty,ty+ddy,my+sy,1
            if wall(mx,my):break
        depth=dist*cos(ray-angle);h=125/max(.2,depth);top=72-h*.5;bottom=72+h*.5;bottoms.append(bottom)
        u=((cy+dist*dy) if side==0 else (cx+dist*dx))%1
        for y in range(max(0,int(top)),min(144,int(bottom)+1)):
            v=(y-top)/h;br=int(v*5);edge=(v*5)%1;bx=(u*2+(br%2)*.5)%1
            color='steel' if side else 'violet'
            if edge<.045 or bx<.045:color='ink'
            elif edge<.085:color='silver' if side else 'steel'
            elif edge>.90:color='darksteel'
            if depth>4 and color in ('steel','violet'):color='darksteel'
            # Brass-framed lamps at alternating wall tiles.
            if (mx+my)%3==0 and .38<u<.62 and .25<v<.65:
                color='goldshade' if u<.41 or u>.59 or v<.29 or v>.61 else 'goldlight'
                if .46<u<.53 and .33<v<.56:color='white'
            c.rect((col,y,col,y),color)
    for y in range(73,144):
        distance=62/(y-72)
        for x in range(256):
            if y<=bottoms[x]:continue
            side=(x/255-.5)*1.35*distance;wx=cx+distance*cos(angle)-side*sin(angle);wy=cy+distance*sin(angle)+side*cos(angle)
            color='darksteel' if (floor(wx)+floor(wy))%2 else 'ink'
            if wx%1<.035 or wy%1<.035:color='steel'
            c.rect((x,y,x,y),color)
    return c.finish()


def render(name,t,style='color',episode=0):
    t=t%30
    if name=='naufrago':return island(t,style,episode)
    return {'acquario':aquarium,'orbita':orbit,'ingranaggi':clockwork,'labirinto':labyrinth}[name](t,style)
