"""Draw the terraces and seed forest background and decoration layers."""

from math import pi, sin
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw

from draw_canopy_world import foliage, panorama

ASSETS = Path(__file__).resolve().parents[1] / "assets"
COPPER = ("#2e2430", "#49323b", "#6d4a44", "#98634e", "#bd8660", "#dda77a")
JADE = ("#172d40", "#214352", "#30626b", "#4d8180", "#75a29a", "#a0c2aa")
GOLD = ("#49373b", "#765243", "#a97b49", "#d4a957", "#e6cb74", "#f1df98")
SEA = ("#224450", "#2e5960", "#397779", "#58a194", "#94c3a3", "#c7d6a2")



def prism(draw,x,y,w,h,palette):
    d=draw
    points=((x-w,y),(x-w+2,y-h*2//3),(x-3,y-h),(x+w//2,y-h+5),
            (x+w,y-h//2),(x+w-2,y))
    d.polygon(points,fill=palette[3],outline=palette[0])
    d.polygon(((x-w+3,y-2),(x-w+4,y-h*2//3),(x-3,y-h+1),(x-5,y-4)),
              fill=palette[4])
    d.polygon(((x-5,y-3),(x-3,y-h+1),(x+w//2,y-h+6),(x+w//2-4,y-2)),
              fill=palette[2])
    d.line((x-w+6,y-h*2//3+4,x-5,y-h+6),fill=palette[5],width=2)
    d.line((x+w//2-2,y-5,x+w-3,y-h//2+4),fill=palette[1])


def copper_cluster():
    im=Image.new("RGBA",(150,110))
    d=ImageDraw.Draw(im)
    rng=Random(14)
    for x,y,w,h in ((29,102,15,42),(116,99,22,39),(43,103,22,62),(89,101,28,82),(71,106,19,48)):
        prism(d,x,y,w,h,COPPER)
    for _ in range(88):
        x=rng.randrange(9,140)
        y=rng.randrange(97,110)
        d.line((x,y,x+rng.randrange(-2,3),max(92,y-rng.randrange(1,6))),fill=rng.choice(GOLD[:5]))
    return im


def field_ferns():
    im=Image.new("RGBA",(148,151))
    d=ImageDraw.Draw(im)
    rng=Random(32)
    for x,dx,h in ((64,-42,62),(71,46,81),(78,-19,94),(87,26,52)):
        points=[(x+round(dx*sin(i*pi/50)),149-h*i//24) for i in range(25)]
        d.line(points,fill=SEA[0],width=4)
        d.line(points,fill=SEA[3],width=2)
        for i,(px,py) in enumerate(points[4::3]):
            wing=max(5,23-2*i)
            for side in (-1,1):
                d.polygon(((px,py+2),(px+wing*side,py-13),(px+wing*side,py-5),(px+2*side,py+6)),
                          fill=rng.choice(SEA[1:5]),outline=SEA[1])
        px,py=points[-1]
        d.ellipse((px-5,py-7,px+6,py+5),fill=GOLD[4],outline=GOLD[1])
        d.point((px-1,py-4),fill=GOLD[5])
    return im


def seedpods():
    im=Image.new("RGBA",(182,167))
    d=ImageDraw.Draw(im)
    rng=Random(142)
    for x,bend,y,w,h in ((41,-19,153,15,41),(128,25,151,19,51),(88,-13,155,31,75)):
        d.line(((x+24,166),(x+16,141),(x+bend,104),(x+bend//2,88)),fill=SEA[1],width=5)
        d.line(((x+22,166),(x+14,141),(x+bend-1,104)),fill=SEA[3],width=2)
        prism(d,x,y,w,h,JADE)
        d.line((x-w//2,y-h//2,x-w//3,y-7),fill=SEA[5])
        for _ in range(17):
            dy=rng.randint(6,h-6)
            dx=rng.randint(-w//3,max(1,w//3))
            d.point((x+dx,y-dy),fill=rng.choice(SEA[3:]))
    for x in range(20,163,3):
        y=rng.randint(153,166)
        d.line((x,y,x+rng.randrange(-3,4),y-rng.randrange(2,10)),fill=rng.choice(SEA[1:]))
    return im


def glass_tree():
    im=Image.new("RGBA",(214,255))
    d=ImageDraw.Draw(im)
    rng=Random(3821)
    trunk=((65,253),(86,224),(97,185),(94,148),(82,120),(62,104),(68,97),
           (98,115),(106,134),(115,116),(119,81),(128,63),(139,74),(134,117),
           (123,143),(123,174),(126,216),(145,241),(174,254))
    d.polygon(trunk,fill="#4c5052",outline=SEA[0],width=2)
    d.line(((93,245),(106,207),(109,168),(103,144),(115,122),(125,88)),
           fill="#94a681",width=8)
    for i in range(230):
        y=rng.randrange(145,245)
        center=110+round((y-185)/12)
        x=center+rng.randrange(-12,14)
        if im.getpixel((x,y))[3]:
            d.line((x,y,x+rng.choice((-1,0,1)),min(y+rng.randrange(1,7),251)),
                   fill=rng.choice(("#bcb28a","#657159","#566255","#75896c")))
    for x,y,w,h in ((53,95,39,21),(163,86,36,24),(105,52,55,27),(60,117,27,16)):
        foliage(d,rng,x,y,w,h,SEA)
    for x,y in ((48,126),(122,109),(154,117),(64,144),(176,104)):
        d.line((x,y-7,x-2,y+7),fill=SEA[2])
        d.polygon(((x-2,y+5),(x+1,y+9),(x-3,y+15),(x-6,y+10)),fill="#dec36e",outline=GOLD[1])
        d.point((x-3,y+8),fill=GOLD[5])
    for x,y in ((63,239),(157,242),(109,247)):
        foliage(d,rng,x,y,22,8,SEA)
    return im


def canopy_layer():
    width,height=1000,376
    im=Image.new("RGBA",(width,height))
    d=ImageDraw.Draw(im)
    rng=Random(427)
    colors=("#355b6695","#457785a4","#568e91a8","#68a2a5ad","#8abcb99e","#a9cbbb9e")
    # Draw with toroidal margins so the canopy has the same silhouette at both edges.
    for x in range(12,width,92):
        y=rng.randint(167,251)
        lean=rng.randint(-24,27)
        rx=rng.randint(24,59)
        ry=rng.randint(13,30)
        for shifted in (x-width,x,x+width):
            d.polygon(((shifted-12,height),(shifted+2,y+12),(shifted+lean,y),
                       (shifted+lean+8,y+17),(shifted+18,height)),fill=colors[0])
            d.line((shifted+1,y+47,shifted-29,y+19),fill=colors[1],width=6)
            foliage(d, Random(x),shifted+lean,y,rx,ry,colors)
    im.resize((width*2,height*2),Image.Resampling.NEAREST).save(ASSETS/"seed-canopy.png",optimize=True)


if __name__=="__main__":
    panorama("terrace-sky.png",((58,111,156),(239,183,137),(144,130,137),
                                (124,114,115),(105,96,96),"#f3d9ae"),473)
    panorama("seed-sky.png",((36,117,168),(173,226,188),(99,169,163),
                             (59,139,137),(48,106,109),"#d7efe1"),492)
    canopy_layer()
    props=Image.new("RGBA",(694,255))
    for x,image in ((0,copper_cluster()),(150,field_ferns()),(298,seedpods()),(480,glass_tree())):
        props.paste(image,(x,0))
    props.save(ASSETS/"terrace-props.png",optimize=True)
