"""Build the four beats of each combat effect on a transparent pixel grid."""
from math import cos, pi, sin
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 72
ASSETS = Path(__file__).resolve().parents[1] / "assets"
ROWS = ("slash", "arc", "impact", "arrow", "bolt", "ring", "stars")
ICE = ("#4b4893", "#868ee8", "#aef4ff", "#fffde1")
GOLD = ("#ac614c", "#f3ad5c", "#ffe5a0", "#fffbe6")
MINT = ("#376977", "#54b69b", "#b0f5c0", "#fffce1")


def spark(d, x, y, reach, colors):
    d.line((x-reach,y,x+reach,y), fill=colors[1])
    d.line((x,y-reach-1,x,y+reach+1), fill=colors[1])
    inner = max(1, reach//2)
    d.polygon(((x,y-inner-1),(x+1,y-1),(x+inner,y),(x+1,y+1),(x,y+inner+1),
               (x-1,y+1),(x-inner,y),(x-1,y-1)), fill=colors[2])
    d.point((x,y), fill=colors[3])


def ribbon(d, cx, cy, rx, ry, begin, end, thickness, color):
    outside, inside = [], []
    for i in range(33):
        t = i / 32
        angle = (begin+(end-begin)*t)*pi/180
        taper = sin(pi*t)**.68 * thickness
        outside.append((round(cx+cos(angle)*rx), round(cy+sin(angle)*ry)))
        inside.append((round(cx+cos(angle)*(rx-taper)), round(cy+sin(angle)*(ry-taper))))
    d.polygon(outside+inside[::-1], fill=color)


def swing(d, phase, skill):
    a,b = ((-102,-39),(-100,23),(-73,63),(3,84))[phase]
    colors = ICE if skill else GOLD
    width = (4,8,6,3)[phase]
    for inset, thick, shade in ((0,width,0),(1,max(2,width-2),1),(2,max(1,width-3),2)):
        ribbon(d,14,35,47-inset,31-inset,a,b,thick,colors[shade])
    ribbon(d,14,35,46,30,a+7,b-7,2,colors[3])
    ribbon(d,15,36,39,24,a+14,b+5,2,colors[1])
    if phase in (1,2):
        spark(d,57,22+phase*7,3,colors)


def arrow(d, phase):
    colors = {"o":"#33364a", "b":"#926033", "g":"#c89762", "w":"#fff3c5",
              "f":"#83cac1", "s":"#48809b", "m":"#94aabe"}
    rows = (
        "offo..................o....",
        ".osffo................omo..",
        "..osffo...............owmo.",
        "...obgggggggggggggggggwwmmo",
        "..osffooooooooooooooooommo.",
        ".osffo................omo..",
        "offo..................o....",
    )
    for j,row in enumerate(rows):
        for i,char in enumerate(row):
            if char in colors:
                d.point((i+20,j+32), fill=colors[char])
    if phase%2 == 0:
        d.line((12,35,17,35),fill="#a9dbcc")


def paint(kind, phase):
    im = Image.new("RGBA",(SIZE,SIZE))
    d = ImageDraw.Draw(im)
    if kind in ("slash","arc"):
        swing(d,phase,kind=="arc")
    elif kind=="arrow":
        arrow(d,phase)
    elif kind=="bolt":
        glow = (3,4,5,4)[phase]
        ribbon(d,32,36,12,glow+1,145,336,3,ICE[1])
        ribbon(d,32,36,11,glow,155,344,2,ICE[2])
        spark(d,38,35,glow,ICE)
        d.line((16,37,23,35),fill=ICE[0])
        d.point((12+phase,35),fill=ICE[2])
    elif kind=="impact":
        radius = (5,12,17,21)[phase]
        for i in range(7):
            angle=(2*pi*i/7)-.24
            vx,vy=cos(angle),sin(angle)
            x,y=36+vx*radius,36+vy*radius
            tail = (4,10,6,2)[phase]
            d.line((round(x-vx*tail),round(y-vy*tail),round(x),round(y)),fill=GOLD[1],width=2)
            d.point((round(x),round(y)),fill=GOLD[3])
        if phase<3:
            spark(d,36,36,(5,8,3)[phase],GOLD)
    elif kind=="ring":
        radius = (10,18,25,30)[phase]
        for i in range(3):
            a=phase*13+i*120
            ribbon(d,36,39,radius,max(5,radius*.47),a,a+101,3,MINT[2])
            angle=a*pi/180
            spark(d,round(36+cos(angle)*radius),round(39+sin(angle)*radius*.47),3,MINT)
    elif kind=="stars":
        for i,(x,y) in enumerate(((17,45),(39,27),(56,42),(27,20))):
            reach = (2,6,4,1)[(phase+i)%4]
            spark(d,x,y-phase*2,reach,ICE)
            d.point((x+reach+2,y-1),fill=ICE[1])
    return im


if __name__ == "__main__":
    sheet = Image.new("RGBA",(SIZE*4,SIZE*len(ROWS)))
    for row, kind in enumerate(ROWS):
        for phase in range(4):
            sheet.paste(paint(kind,phase),(phase*SIZE,row*SIZE))
    sheet.save(ASSETS/"combat-fx.png",optimize=True)
