"""Draw Maplee's new forest, egg basin, and original creatures in native pixels."""

from math import cos, pi, sin
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw


ASSETS = Path(__file__).resolve().parents[1] / "assets"
GREEN = ("#243e37", "#355945", "#54804c", "#75a752", "#a4c865", "#d6e28d")
GOLD = ("#65453b", "#995d3f", "#be7e39", "#dfa04b", "#f3c768", "#ffdf85")


def foliage(draw, rng, x, y, width, height, colors):
    """Build an irregular leaf silhouette, then light its upper clusters."""
    for i in range(38):
        angle = rng.uniform(0, 2*pi)
        radius = rng.uniform(.23, 1)
        dx = round(cos(angle)*width*radius)
        dy = round(sin(angle)*height*radius)
        w, h = rng.randint(4, 13), rng.randint(3, 9)
        draw.ellipse((x+dx-w,y+dy-h,x+dx+w,y+dy+h),fill=colors[0])
    draw.ellipse((x-width+6,y-height+4,x+width-6,y+height-4),fill=colors[1])
    for i in range(390):
        dx, dy = rng.randint(-width,width),rng.randint(-height,height)
        if (dx/width)**2+(dy/height)**2 > 1.07:
            continue
        level = max(1,min(5,round(3.6-2*dy/height+rng.uniform(-1.6,1))))
        u,v=x+dx,y+dy
        w=rng.randint(2,8)
        h=rng.randint(1,4)
        draw.polygon(((u-w,v),(u-2,v-h),(u+w-2,v-h),(u+w,v-1),
                      (u+w-2,v+h),(u-w+2,v+h)),fill=colors[level])
        if i%7 == 0 and level >= 3:
            draw.line((u-2,v-h,u+w-2,v-h),fill=colors[min(5,level+1)])


def giant_tree():
    im=Image.new("RGBA",(224,352))
    d=ImageDraw.Draw(im)
    rng=Random(3117)
    roots=((21,343),(59,328),(76,306),(89,275),(86,230),(90,201),(84,173),
           (78,143),(63,117),(33,89),(19,67),(36,66),(67,84),(93,112),(101,109),
           (93,74),(95,53),(107,44),(116,50),(126,83),(126,111),(145,88),
           (173,70),(198,65),(210,78),(183,97),(155,118),(143,145),(139,190),
           (143,224),(138,267),(144,302),(159,320),(200,338),(213,351),(19,351))
    bark=Image.new("L",im.size)
    ImageDraw.Draw(bark).polygon(roots,fill=255)
    d.polygon(roots,fill="#493e39",outline="#2d3932",width=2)
    d.polygon(((46,343),(72,324),(92,279),(96,235),(101,232),(94,167),(91,123),
               (104,112),(104,66),(114,63),(123,105),(126,151),(120,206),
               (125,266),(121,297),(137,325),(160,343)),fill="#785943")
    d.polygon(((72,343),(94,307),(108,257),(106,216),(110,195),(104,148),(110,112),
               (108,67),(115,78),(117,128),(121,159),(115,196),(119,236),
               (114,277),(119,302),(108,335)),fill="#a17d55")
    marks=Image.new("RGBA",im.size)
    md=ImageDraw.Draw(marks)
    for _ in range(1250):
        x,y=rng.randrange(25,197),rng.randrange(69,351)
        length=rng.randrange(2,23)
        md.line((x,y,x+rng.choice((-4,-2,0,1,3)),y+length),
                fill=rng.choice(("#523f39","#634a3d","#8c684a","#99744b","#af8c56",
                                 "#4b4f39","#536144")),width=rng.randint(1,3))
    im.paste(marks,(0,0),Image.frombytes("L",im.size,bytes(
        min(a,b) for a,b in zip(bark.tobytes(),marks.getchannel("A").tobytes())
    )))
    for side,y0 in ((-1,145),(1,173),(-1,215),(1,263)):
        points=[(112+side*round(19+6*sin(i/5)),y0+i*2) for i in range(29)]
        d.line(points,fill="#2e4d3c",width=5)
        d.line(points,fill="#83a652",width=2)
        for i,(x,y) in enumerate(points[::5]):
            out=side if i%2 else -side
            d.polygon(((x,y),(x+out*8,y-4),(x+out*11,y-1),(x+out*6,y+4)),fill="#91b457")
            d.point((x+out*7,y-2),fill="#cbd981")
    foliage(d,rng,50,77,39,24,GREEN)
    foliage(d,rng,167,75,38,23,GREEN)
    foliage(d,rng,104,48,59,33,GREEN)
    foliage(d,rng,150,114,24,13,GREEN)
    for x,y,rx,ry in ((45,331,22,11),(173,332,25,11),(128,343,26,10)):
        foliage(d,rng,x,y,rx,ry,GREEN)
    return im


def egg_cluster():
    im=Image.new("RGBA",(172,128))
    d=ImageDraw.Draw(im)
    rng=Random(811)
    foliage(d,rng,45,112,30,11,GREEN)
    foliage(d,rng,128,109,28,11,GOLD)
    colors=("#6d6156","#95826b","#bb9d78","#d8bc8d","#f1daad","#fff0c9")
    for x,y,rx,ry in ((40,83,18,25),(132,80,20,34),(83,64,34,54)):
        for i,col in enumerate(colors):
            d.ellipse((x-rx+i*2,y-ry+i*2,x+rx-i*4,y+ry-i*3),fill=col)
        for _ in range(rx*6):
            u,v=rng.randint(-rx,rx),rng.randint(-ry,ry)
            if (u/rx)**2+(v/ry)**2 < .79:
                d.line((x+u,y+v,x+u+1,y+v),fill=rng.choice(("#dbbd8b","#e3c395","#f7e3b5")))
        d.line(((x-4,y-ry+8),(x-8,y-ry+17),(x-3,y-ry+24),(x-10,y-ry+32)),
               fill=colors[1],width=2)
    for x in range(9,164,3):
        y=rng.randint(116,125)
        d.line((x,y,x+rng.randint(-3,3),y-rng.randint(2,11)),fill=rng.choice(GREEN))
    return im


def small_tree():
    im=Image.new("RGBA",(172,224))
    d=ImageDraw.Draw(im)
    rng=Random(418)
    for points,width in (
        (((76,220),(86,190),(81,146),(91,103),(83,68)),16),
        (((87,155),(58,133),(43,98)),10),
        (((86,140),(118,103),(133,78)),9),
    ):
        d.line(points,fill="#5a473c",width=width)
        d.line([(x-3,y) for x,y in points],fill="#ae8457",width=max(2,width//3))
    foliage(d,rng,46,93,34,24,GOLD)
    foliage(d,rng,125,75,36,24,GOLD)
    foliage(d,rng,76,51,41,32,GOLD)
    for x in range(36,134,6):
        y=rng.randrange(211,222)
        d.line((x,y,x+rng.randint(-5,5),y-rng.randint(3,18)),fill=rng.choice(GREEN))
    return im


def ledge_grove():
    im=Image.new("RGBA",(224,146))
    d=ImageDraw.Draw(im)
    rng=Random(612)
    for x in (32,60,128,180):
        h=rng.randint(28,73)
        d.line(((x-11,145),(x+2,114),(x,145-h)),fill="#554b41",width=7)
        foliage(d,rng,x,137-h,18,15,GREEN)
    for x, y, w in ((37,129,20),(81,129,23),(150,128,31),(185,135,17)):
        foliage(d,rng,x,y,w,8,GREEN)
    for x in range(8,219,9):
        y=rng.randint(134,145)
        color=rng.choice(("#f6ddb1","#faf18b","#ed9c7f","#a4d587"))
        d.line((x,y,x+2,y-8),fill="#648450")
        d.rectangle((x,y-10,x+3,y-8),fill=color)
    return im


def panorama(filename, palette, seed):
    width,height=1060,376
    rng=Random(seed)
    sky, horizon, hill, trees, fore, highlights=palette
    im=Image.new("RGB",(width,height))
    d=ImageDraw.Draw(im)
    for y in range(height):
        f=min(1,y/244)
        d.line((0,y,width,y),fill=tuple(round(a+(b-a)*f) for a,b in zip(sky,horizon)))
    for x in range(-65,width+75,100):
        x+=rng.randrange(-30,30)
        y=rng.randint(85,241)
        for i in range(rng.randint(4,8)):
            u=x+rng.randint(-37,37)
            v=y+rng.randint(-9,9)
            d.ellipse((u-14,v-3,u+30,v+4),fill=highlights)
    for index,color in enumerate((hill,trees,fore)):
        y0=228+index*47
        edge=[(x,y0+round(8*cos(x/57+index)+10*sin(x/37-index)+5*sin(x/16)))
              for x in range(0,width+8,8)]
        d.polygon(edge+[(width,height),(0,height)],fill=color)
        verge=rng.randrange(2,10)
        for x in range(-10,width+22,verge if index else 8):
            y=y0+round(8*cos(x/57+index)+10*sin(x/37-index)+5*sin(x/16))
            h=rng.randint(2,12+index*7)
            w=rng.randint(3,7+index*2)
            d.ellipse((x-w,y-h,x+w,y+h),fill=color)
            if index:
                d.line((x,y-1,x-rng.randint(1,4),y+12),fill=color,width=2)
        for _ in range(350):
            x=rng.randrange(width)
            y=rng.randrange(min(height-1,y0+12),height)
            d.line((x,y,x+rng.randint(1,6),y),fill=tuple(
                max(0,min(255,c+rng.choice((-5,4,9)))) for c in color
            ))
    # Blend the overlapping margins into one continuous strip.
    overlap=60
    period=width-overlap
    strip=im.crop((0,0,period,height))
    for x in range(overlap):
        p=x/(overlap-1)
        p=p*p*(3-2*p)
        strip.paste(Image.blend(im.crop((period+x,0,period+x+1,height)),
                               im.crop((x,0,x+1,height)),p),(x,0))
    strip.paste(strip.crop((0,0,1,height)),(period-1,0))
    strip.resize((period*2,height*2),Image.Resampling.NEAREST).save(ASSETS/filename,optimize=True)


def beetle(d, phase, blink):
    ink="#342b37"
    for x in (9,14,23,27):
        foot=phase if x%2 else -phase
        d.line(((x,29),(x+foot,33),(x+foot-2,35)),fill=ink,width=2)
    d.ellipse((5,19,30,32),fill="#7d5037",outline=ink,width=2)
    d.polygon(((6,25),(9,19),(17,16),(25,19),(28,25),(24,29),(11,29)),
              fill="#c58d40",outline=ink)
    d.polygon(((8,24),(11,19),(17,18),(23,21),(20,24),(12,25)),fill="#ffce68")
    d.line((15,19,18,27),fill="#8b6846")
    d.ellipse((24,21,35,31),fill="#6d6850",outline=ink)
    for x,y in ((28,22),(32,22)):
        d.line((x,y,x+3,y-6),fill=ink,width=1)
        d.point((x+3,y-6),fill="#f6c864")
    d.rectangle((31,24,32,24 if blink else 26),fill="#ffefa9")


def bird(d, phase, blink):
    ink="#30384d"
    d.polygon(((14,28),(5,23),(5,27),(10,33),(17,32)),fill="#496b76",outline=ink)
    d.ellipse((11,17,30,33),fill="#75ada0",outline=ink,width=2)
    d.ellipse((20,13,32,27),fill="#d9dfaf",outline=ink)
    d.polygon(((29,21),(36,24),(30,26)),fill="#deaa54",outline=ink)
    d.polygon(((19,26),(10,23+phase*2),(6,26+phase*2),(11,30+phase),(20,30)),
              fill="#8bc7b3",outline=ink)
    d.line((11,26+phase,18,29),fill="#e1ecd0")
    d.polygon(((23,16),(23,10),(27,12),(29,8),(29,15)),fill="#619b88",outline=ink)
    d.rectangle((27,19,28,19 if blink else 21),fill=ink)
    d.line((20,33,20+phase,35),fill="#d3ad61",width=2)


def shell(d, phase, blink):
    ink="#483e50"
    for x in (8,15,25,30):
        foot=phase if x%2 else -phase
        d.ellipse((x+foot-2,30,x+foot+3,35),fill="#7d6174",outline=ink)
    d.ellipse((5,22,33,32),fill="#a2838d",outline=ink,width=2)
    d.ellipse((8,10,29,30),fill="#b78991",outline=ink,width=2)
    d.ellipse((10,11,24,27),fill="#e1bd9b")
    d.ellipse((11,12,19,21),fill="#f5ddba")
    d.line(((17,13),(18,17),(22,18),(19,23),(25,24),(26,26)),fill="#906f80")
    d.ellipse((24,23,36,32),fill="#9e8a83",outline=ink)
    d.rectangle((31,26,32,26 if blink else 28),fill="#f8d275")
    d.point((33,30),fill="#eacaac")


def guardian(d, phase, blink):
    ink="#293a48"
    for x in (9,14,23,29):
        foot=phase if x%2 else -phase
        d.line(((x,28),(x+foot,34),(x+foot+2,35)),fill=ink,width=2)
    d.polygon(((5,25),(6,20),(13,19),(19,21),(27,17),(33,18),(34,24),
               (30,29),(19,32),(8,30)),fill="#647f75",outline=ink)
    d.line((7,22,19,24),fill="#aac195",width=2)
    d.polygon(((24,17),(23,11),(26,10),(28,14),(34,13),(37,20),(36,25),
               (30,26),(27,23)),fill="#8bab8a",outline=ink)
    for points in (((28,15),(23,9),(22,3),(24,1)),((32,14),(34,8),(33,4),(36,2)),
                   ((23,10),(19,7),(18,4)),((34,8),(37,7),(39,4))):
        d.line(points,fill="#6f534a",width=2)
        d.line(points[:2],fill="#d2a263")
        x,y=points[-1]
        d.line((x-1,y,x+1,y),fill="#efb066")
    d.rectangle((33,17,34,17 if blink else 19),fill="#ffe09b")
    d.line((33,23,35,23),fill="#dce7a5")
    for x,y in ((12,24),(16,26),(20,24),(27,19)):
        d.point((x,y),fill="#f1c872")


def creature_atlas():
    atlas=Image.new("RGBA",(80*23,80*4))
    for row,paint in enumerate((beetle,bird,shell,guardian)):
        for col in range(23):
            sprite=Image.new("RGBA",(40,40))
            moves=(-1,0,1,2,1,0)
            step=moves[(col-4)%6] if 4 <= col < 10 else 0
            paint(ImageDraw.Draw(sprite),step,col in (2,17))
            cel=Image.new("RGBA",sprite.size)
            if 10 <= col < 16:
                dx=(-2,-3,-1,2,2,0)[col-10]
                dy=(1,0,-1,-3,-1,0)[col-10] if row!=2 else 0
                cel.paste(sprite,(dx,dy))
                if 12 <= col <= 14:
                    color=("#ffc77b","#bcebe7","#efc2a0","#eec783")[row]
                    ImageDraw.Draw(cel).line(((32,24),(36,22),(39,22)),fill=color)
            elif col >= 18:
                stage=col-18
                height=40-3*stage
                sprite=sprite.resize((40,height),Image.Resampling.NEAREST)
                sprite.putalpha(sprite.getchannel("A").point(lambda a:a*(5-stage)//5))
                cel.paste(sprite,(0,round((40-height)*.9)))
            elif col in (16,17):
                cel.paste(sprite,(-2,1))
            else:
                dy=-round(2*sin((col%6)*pi/3)) if row==1 else -int(col in (1,5,8))
                cel.paste(sprite,(0,dy))
            atlas.paste(cel.resize((80,80),Image.Resampling.NEAREST),(col*80,row*80))
    atlas.save(ASSETS/"canopy-monsters.png",optimize=True)


if __name__=="__main__":
    scenery=Image.new("RGBA",(792,352))
    for x,image in ((0,giant_tree()),(224,egg_cluster()),(396,small_tree()),(568,ledge_grove())):
        scenery.paste(image,(x,0))
    scenery.save(ASSETS/"canopy-scenery.png",optimize=True)
    panorama("windroot.png",((27,108,163),(160,216,181),(77,135,125),(57,108,86),
                             (54,92,69),"#bfe6e1"),504)
    panorama("sunegg.png",((68,123,168),(245,210,155),(143,151,119),(110,122,84),
                           (86,109,74),"#f8ebcf"),719)
    creature_atlas()
