"""Draw original terrain tiles, layered scenery and monster animation sheets."""

from math import cos, pi, sin
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw

from draw_canopy_world import foliage, panorama

ASSETS = Path(__file__).resolve().parents[1] / "assets"
COPPER = ("#2e2430", "#49323b", "#6d4a44", "#98634e", "#bd8660", "#dda77a")
JADE = ("#172d40", "#214352", "#30626b", "#4d8180", "#75a29a", "#a0c2aa")
GOLD = ("#49373b", "#765243", "#a97b49", "#d4a957", "#e6cb74", "#f1df98")
SEA = ("#224450", "#2e5960", "#397779", "#58a194", "#94c3a3", "#c7d6a2")


def ground_tile(filename, minerals, cover, seed):
    w, h = 176, 148
    im = Image.new("RGB", (w,h), minerals[1])
    d = ImageDraw.Draw(im)
    rng = Random(seed)
    for j in range(8):
        by = 14+j*19
        for i in range(-2,10):
            x = i*22 + (10 if j%2 else 0) + rng.randrange(-4,5)
            y = by+rng.randrange(-3,4)
            width = rng.randint(19,25)
            depth = rng.randint(15,21)
            col = rng.randrange(2,5)
            root = [(x,y+4),(x+4,y),(x+width-6,y-2),(x+width,y+3),(x+width-1,y+depth-6),
                    (x+width-5,y+depth),(x+5,y+depth-1),(x-1,y+depth-7)]
            d.polygon(root,fill=minerals[col],outline=minerals[0])
            d.polygon([(x+2,y+5),(x+6,y+1),(x+width-7,y),(x+width-3,y+4),
                       (x+width-10,y+8),(x+5,y+10)],fill=minerals[min(5,col+1)])
            d.line((x+5,y+depth-1,x+width-5,y+depth),fill=minerals[max(1,col-1)])
            d.line((x+4,y+8,x+3,y+depth-5),fill=minerals[min(5,col+1)])
            for _ in range(7):
                sx=x+rng.randint(5,max(6,width-6))
                sy=y+rng.randint(5,depth-4)
                d.line((sx,sy,sx+rng.randint(0,2),sy),fill=minerals[rng.choice((1,2,3,4))])
    edge=[(x,13+round(2*sin(x/6)+sin(x/3))) for x in range(w)]
    d.polygon([(0,0),(w,0),*reversed(edge)],fill=cover[1])
    d.line([(x, max(0,y-6)) for x,y in edge],fill=cover[3],width=5)
    d.line([(x, max(0,y-9)) for x,y in edge],fill=cover[4],width=2)
    for x in range(1,w-3,2):
        y=edge[x][1]
        d.polygon(((x,y-4),(x+3,y-3),(x+2,y+rng.randint(1,5))),fill=rng.choice(cover[:3]))
    im.save(ASSETS/filename,optimize=True)


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


GEM_COLORS=(
    ("#17364a","#276675","#348f9c","#56bfb8","#95dfc3","#d9f5d7"),
    ("#453436","#77513c","#ad7843","#dda451","#f6d378","#fff0ac"),
)
KEEPER_COLORS=(
    ("#3e2937","#714140","#a45841","#cf834e","#eeb575","#ffe4a2"),
    ("#352b55","#584675","#79578d","#a36fa4","#c48fb0","#f2c2b7"),
)


def gem_cel(d, pose, palette, blink):
    dark, deep, base, lit, bright, shine = palette
    spread = pose
    outline=((6-spread,32),(6,25),(11,19),(17,20),(21,16+pose),
             (27,18+pose),(33+spread,24),(34+spread,31),(29,35),(12,35))
    d.polygon(outline,fill=base,outline=dark)
    d.polygon(((7-spread,31),(12,29),(18,31),(26,30),(32+spread,28),(32,33),
               (28,35),(12,34)),fill=deep)
    d.polygon(((9,26),(12,21),(17,22),(22,18+pose),(27,20+pose),(28,23),
               (19,26),(13,28)),fill=lit)
    d.polygon(((14,25),(18,21),(24,21+pose),(22,24),(17,26)),fill=bright)
    d.line((14,24,17,22),fill=shine)
    d.polygon(((12,23),(10,18),(12,15+pose),(15,17),(17,22)),fill=bright,outline=deep)
    d.line((12,17,13,18),fill=shine)
    d.rectangle((23,26,25,27 if blink else 30),fill=dark)
    d.rectangle((29,25,30,26 if blink else 28),fill=dark)
    d.point((24,26),fill=shine)
    d.line((26,31,29,30),fill=deep)


def keeper_cel(d, pose, palette, blink):
    dark, deep, base, lit, bright, shine = palette
    d.polygon(((13,27),(26,26),(30,34),(26,35),(12,35),(10,33)),fill="#45655f",outline=dark)
    for x,step in ((13,pose),(24,-pose)):
        d.polygon(((x,32),(x+4,32),(x+3-step,35),(x-2-step,35)),fill="#333e50",outline=dark)
    d.polygon(((13,16),(23,14),(29,18),(28,28),(24,30),(15,30),(12,25)),
              fill=bright,outline=dark)
    d.polygon(((18,19),(24,17),(26,21),(23,26),(17,27)),fill=shine)
    d.rectangle((22,21,24,22 if blink else 24),fill="#4d3948")
    d.point((23,21),fill="#fff5d5")
    d.line(((25,17),(27,22),(26,27)),fill=deep)
    d.polygon(((6,18),(10,12),(15,10),(17,5),(23,5),(28,8),(29,12),
               (34,15),(34,18),(27,20),(12,21)),fill=base,outline=dark)
    d.polygon(((10,16),(14,13),(18,8),(23,7),(27,10),(25,13),(18,15)),fill=lit)
    d.line((14,15,17,12),fill=bright)
    d.line((9,19,27,18),fill=deep)
    d.line(((28,27),(33+pose,23),(34+pose,18)),fill="#4d665b",width=2)
    d.point((34+pose,18),fill=shine)


def creature_sheet():
    out=Image.new("RGBA",(28*80,4*80))
    directions=(0,1,2,1,0,-1,-1,0)
    for row,(paint,palette) in enumerate(((gem_cel,GEM_COLORS[0]),(keeper_cel,KEEPER_COLORS[0]),
                                         (gem_cel,GEM_COLORS[1]),(keeper_cel,KEEPER_COLORS[1]))):
        for frame in range(28):
            movement=4<=frame<12
            attack=12<=frame<19
            pose=directions[(frame-4)%8] if movement else 0
            dx,dy=(0,0)
            if movement:
                dy=(0,0,-2,-4,-4,-2,0,1)[frame-4] if row%2==0 else (0,-1,0,-1,0,-1,0,0)[frame-4]
            elif attack:
                dx=(-2,-3,-1,3,4,2,0)[frame-12]
                dy=(0,1,-2,-3,-2,0,0)[frame-12]
                pose=(-1,-2,-1,2,2,1,0)[frame-12]
            elif 19<=frame<22:
                dx=-(frame-18)
                dy=1
            sprite=Image.new("RGBA",(40,40))
            paint(ImageDraw.Draw(sprite),pose,palette,frame in (3,19,20))
            cel=Image.new("RGBA",sprite.size)
            if frame>=22:
                stage=frame-22
                height=40-stage*4
                sprite=sprite.resize((40,height),Image.Resampling.NEAREST)
                sprite.putalpha(sprite.getchannel("A").point(lambda n:n*(6-stage)//6))
                cel.paste(sprite,(0,round(stage*3.5)))
                dust=ImageDraw.Draw(cel)
                for i in range(4):
                    x=8+i*7+stage%2
                    y=34-stage-i%2*4
                    dust.rectangle((x,y,x+1,y+1),fill=palette[(i+stage)%4+2])
            else:
                cel.paste(sprite,(dx,dy))
                if 15<=frame<=17:
                    glow=ImageDraw.Draw(cel)
                    glow.line(((30,21),(35,18),(39,18)),fill=palette[5])
                    glow.line(((34,23),(38,22)),fill=palette[4])
            out.paste(cel.resize((80,80),Image.Resampling.NEAREST),(frame*80,row*80))
    out.save(ASSETS/"terrace-monsters.png",optimize=True)


if __name__=="__main__":
    ground_tile("copper-ground.png",COPPER,GOLD,641)
    ground_tile("seed-ground.png",JADE,SEA,762)
    panorama("terrace-sky.png",((58,111,156),(239,183,137),(144,130,137),
                                (124,114,115),(105,96,96),"#f3d9ae"),473)
    panorama("seed-sky.png",((36,117,168),(173,226,188),(99,169,163),
                             (59,139,137),(48,106,109),"#d7efe1"),492)
    canopy_layer()
    props=Image.new("RGBA",(694,255))
    for x,image in ((0,copper_cluster()),(150,field_ferns()),(298,seedpods()),(480,glass_tree())):
        props.paste(image,(x,0))
    props.save(ASSETS/"terrace-props.png",optimize=True)
    creature_sheet()
