"""Paint Maplee's bronze-and-enamel window skin and woodland platform art."""

from pathlib import Path
from random import Random
import sys

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from maplee.classic_skin import ADVENTURE_REGIONS

ASSETS = ROOT / "assets"
BRONZE = ("#251b1a", "#41303a", "#765037", "#ab7748", "#dec481", "#f4e0ab")
PINE = ("#152422", "#283f3e", "#345652", "#476c62", "#72a082", "#b9d2a0")
LINEN = ("#816e60", "#ab9581", "#cab99a", "#d9ccb4", "#e8dec8", "#f5ead2")


def cut_box(d, left, top, right, bottom, n, fill):
    d.polygon(((left+n,top),(right-n,top),(right,top+n),(right,bottom-n),
               (right-n,bottom),(left+n,bottom),(left,bottom-n),(left,top+n)), fill=fill)


def tile(name, w, h):
    im = Image.new("RGBA", (w,h))
    d = ImageDraw.Draw(im)
    if name == "chrome":
        cut_box(d,0,0,w-1,h-1,5,BRONZE[0])
        cut_box(d,1,1,w-2,h-2,5,BRONZE[3])
        cut_box(d,2,2,w-3,h-3,4,BRONZE[4])
        cut_box(d,3,3,w-4,h-4,4,BRONZE[2])
        cut_box(d,4,4,w-5,h-5,4,PINE[0])
        for y,c in enumerate(("#41564f","#394d47","#344641","#2a3d37","#253630"), 5):
            d.rectangle((5,y,w-6,y+2),fill=c)
        d.rectangle((5,20,w-6,21),fill=BRONZE[2])
        d.line((7,21,w-8,21),fill=BRONZE[3])
        d.line((6,h-5,w-7,h-5),fill=BRONZE[2])
        for x,y in ((5,5),(w-6,5),(5,h-6),(w-6,h-6)):
            d.point((x,y),fill=BRONZE[5])
    elif name == "paper":
        cut_box(d,0,0,w-1,h-1,3,LINEN[0])
        cut_box(d,1,1,w-2,h-2,3,LINEN[2])
        cut_box(d,2,2,w-3,h-3,2,LINEN[5])
        d.line((4,h-3,w-5,h-3),fill=LINEN[3])
    elif name == "stat_row":
        cut_box(d,0,0,w-1,h-1,2,LINEN[1])
        cut_box(d,1,1,w-2,h-2,2,"#fff8e9")
        d.line((3,1,w-4,1),fill=LINEN[3])
        d.line((3,h-2,w-4,h-2),fill=LINEN[4])
    elif name in ("cell","quick_cell","panel_card"):
        dark = name == "quick_cell"
        cut_box(d,0,0,w-1,h-1,3,PINE[0] if dark else LINEN[0])
        cut_box(d,1,1,w-2,h-2,2,PINE[3] if dark else LINEN[2])
        cut_box(d,2,2,w-3,h-3,2,PINE[1] if dark else LINEN[5])
        d.line((4,2,w-5,2),fill=PINE[2] if dark else LINEN[3])
        d.line((4,h-3,w-5,h-3),fill=PINE[3] if dark else LINEN[4])
    else:
        active = name in ("button","tab_on","up","prev","next","thumb")
        edge,middle,face,light = (BRONZE[0],PINE[1],PINE[3],PINE[4]) if active else (
            BRONZE[0],BRONZE[1],BRONZE[2],"#996c52")
        if name == "close":
            middle,face,light = "#5a2e2e","#8c4a3a","#b87154"
        cut_box(d,0,0,w-1,h-1,2,edge)
        cut_box(d,1,1,w-2,h-2,2,middle)
        cut_box(d,2,2,w-3,h-3,1,face)
        d.line((3,2,w-4,2),fill=light)
        if name == "close":
            d.line((4,4,8,8),fill=LINEN[5],width=2)
            d.line((8,4,4,8),fill=LINEN[5],width=2)
        if name in ("up","up_off","prev","next"):
            cx,cy = w//2,h//2
            color = LINEN[5] if active else LINEN[2]
            if name == "next":
                d.polygon(((cx-3,cy-2),(cx+3,cy-2),(cx,cy+2)),fill=color)
            else:
                d.polygon(((cx-3,cy+2),(cx+3,cy+2),(cx,cy-2)),fill=color)
        if name == "thumb":
            for y in range(h//2-3,h//2+4,3):
                d.line((3,y,w-4,y),fill=PINE[5])
    return im


def plank():
    im = Image.new("RGBA", (144,42))
    d = ImageDraw.Draw(im)
    cut_box(d,0,4,143,34,5,BRONZE[0])
    cut_box(d,2,5,141,32,4,BRONZE[2])
    cut_box(d,3,5,140,27,2,"#a67a4d")
    d.rectangle((4,6,139,10),fill="#c99761")
    d.line((6,6,137,6),fill=BRONZE[4])
    d.line((4,27,139,27),fill="#634232")
    d.line((7,31,136,31),fill="#5a3b2b")
    rng = Random(228)
    for _ in range(68):
        x,y = rng.randrange(8,138),rng.randrange(8,26)
        length = min(138-x, rng.randrange(2,23))
        d.line((x,y,x+length,y),fill=rng.choice(("#ba8d53","#8e603b","#9c6c42","#ab7c48")))
    for x in (12,131):
        d.rectangle((x-1,12,x+1,15),fill="#3a322c")
        d.point((x,12),fill="#e8c78a")
        for j in range(3):
            d.line((x-5+j,34,x-6+j,39),fill=("#39281d","#5d4534","#826245")[j])
    return im


if __name__ == "__main__":
    atlas = Image.new("RGBA", (224,136))
    for name,(x,y,w,h) in ADVENTURE_REGIONS.items():
        atlas.paste(tile(name,w,h), (x,y))
    atlas.save(ASSETS/"adventure-ui.png", optimize=True)
    plank().save(ASSETS/"lobby-plank.png", optimize=True)
