"""Bake original pixel backdrops and the two expansion creatures."""
from math import cos, sin
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parents[1] / "assets"


def skyline(key, colors, grove):
    width, height = 576, 156
    im = Image.new("RGB", (width,height))
    d = ImageDraw.Draw(im)
    rng = Random(561 if grove else 812)
    top, bottom, far, mid, near, glow = colors
    for y in range(height):
        t = min(1,y/100)
        d.line((0,y,width,y),fill=tuple(round(a+(b-a)*t) for a,b in zip(top,bottom)))
    for _ in range(200):
        x,y = rng.randrange(width),rng.randrange(100)
        d.point((x,y),fill=glow if y<45 else bottom)
    d.ellipse((390,18,411,39),fill=glow)
    d.ellipse((397,15,415,32),fill=tuple(round(a+(b-a)*.22) for a,b in zip(top,bottom)))
    for index, color in enumerate((far,mid,near)):
        floor = 91 + index*22
        edge = [(x,floor + round(7*sin(x/38+index)+5*cos(x/17))) for x in range(0,width+8,8)]
        d.polygon(edge+[(width,height),(0,height)],fill=color)
        for x in range(-14,width+20,11-index*2):
            x += rng.randrange(-7,7)
            base = floor+round(7*sin(x/38+index)+5*cos(x/17))+10
            h = rng.randrange(14,38)+index*6
            if grove:
                d.line((x,base,x+2,base-h),fill=color,width=4+index)
                for j in range(4,len(range(h))//2+6,5):
                    w = round(j*.46)+4
                    d.polygon([(x+2,base-h+j-8),(x-w,base-h+j+6),(x+w,base-h+j+4)],fill=color)
            else:
                w = rng.randrange(5,15)
                d.rectangle((x,base-h,x+w,base),fill=color)
                d.line((x+w//2,base-h,x+w//2,base-h-rng.randrange(3,13)),fill=color)
                if index:
                    for j in range(2,h-7,6):
                        if rng.random() < .63:
                            d.rectangle((x+2,base-h+j,x+3,base-h+j+1),fill=glow if j%2 else mid)
    for x in range(0,width,13):
        y=142+rng.randrange(-8,12)
        d.line((x,y,x+7,y-1),fill=mid,width=1)
    # Match the far and near silhouettes over a short interval inside the
    # repeated strip. The browser uses this at its baked size.
    overlap = 72
    period = width-overlap
    strip = im.crop((0,0,period,height))
    for x in range(overlap):
        alpha = x/(overlap-1)
        alpha = alpha*alpha*(3-2*alpha)
        column = Image.blend(im.crop((x+period,0,x+period+1,height)),
                             im.crop((x,0,x+1,height)),alpha)
        strip.paste(column,(x,0))
    strip.paste(strip.crop((0,0,1,height)),(period-1,0))
    strip.resize((period*3,468),Image.Resampling.NEAREST).save(ASSETS/(key+".png"),optimize=True)


def monsters():
    atlas=Image.new("RGBA",(64*8,64*2))
    for row in range(2):
        for i in range(8):
            sprite=Image.new("RGBA",(64,64))
            d=ImageDraw.Draw(sprite)
            y = (0,-2,-4,-2,-1,-4,1,4)[i]
            if row == 0:
                d.ellipse((16,30+y,47,58+y),fill="#56756d",outline="#202b40",width=2)
                d.polygon([(17,47+y),(9,32+y),(8,18+y),(14,24+y),(22,16+y),(28,37+y)],fill="#597c6e",outline="#263349")
                d.polygon([(37,35+y),(41,14+y),(46,23+y),(55,16+y),(53,30+y),(47,45+y)],fill="#678878",outline="#263349")
                d.ellipse((18,30+y,44,48+y),fill="#abc08a",outline="#425d69")
                d.rectangle((23,42+y,36,48+y),fill="#293645")
                d.rectangle((23,40+y,26,44+y),fill="#eaea98")
                d.rectangle((33,40+y,36,44+y),fill="#eaea98")
                d.line((24,52+y,35,52+y),fill="#cbd4a5",width=2)
                d.rectangle((20,55+y,26,59+y),fill="#394965")
                d.rectangle((38,55+y,44,59+y),fill="#394965")
            else:
                d.polygon([(6,46+y),(13,36+y),(16,24+y),(23,16+y),(34,13+y),(44,19+y),(49,34+y),
                           (60,29+y),(57,46+y),(47,51+y),(40,49+y),(32,58+y),(30,51+y),
                           (22,55+y),(22,49+y),(13,52+y)],fill="#59718e",outline="#283955",width=2)
                d.polygon([(15,43+y),(19,31+y),(25,20+y),(34,17+y),(42,22+y),(46,37+y),
                           (40,45+y),(31,50+y),(29,45+y),(23,48+y)],fill="#9ab9bf")
                d.polygon([(24,24+y),(32,21+y),(40,25+y),(41,38+y),(34,42+y),(25,38+y)],fill="#485e79")
                d.line((27,32+y,30,32+y),fill="#fff4c3",width=2)
                d.line((35,31+y,38,31+y),fill="#fff4c3",width=2)
            if i == 5:
                d.line((43,35+y,57,33+y),fill="#f7deb6",width=2)
            if i == 6:
                d.line((16,35,45,43),fill="#ffe6d0",width=2)
            if i == 7:
                alpha = sprite.getchannel("A").point(lambda v:v//2)
                sprite.putalpha(alpha)
            atlas.paste(sprite,(i*64,row*64))
    atlas.save(ASSETS/"expansion-mobs.png",optimize=True)


if __name__ == "__main__":
    skyline("ember-grove",((31,41,72),(191,119,125),"#7b637e","#4d596e","#324451","#ffddad"),True)
    skyline("lantern-quay",((19,35,64),(93,136,151),"#546d8b","#3b586e","#233c50","#ffce8e"),False)
    monsters()
