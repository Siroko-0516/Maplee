"""Draw the equipment atlas on an unscaled 32x32 pixel grid."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"
OUTLINE = "#20192c"
GOLD = "#e9a74d"
LIGHT = "#ffedab"
SHADE = "#8c5444"
CYAN = "#7fe0e8"

def polygon(d, points, color):
    d.polygon(points, fill=color, outline=OUTLINE, width=1)

def gem(d, x, y, radius, fill=CYAN):
    polygon(d, [(x, y-radius), (x+radius,y), (x,y+radius), (x-radius,y)], fill)
    d.line([(x-radius+2,y),(x,y-radius+2),(x+1,y-2)],fill="#f7ffff")
    d.point((x+1,y+1),fill="#458cab")

def spark(d, x, y, color=LIGHT):
    d.line([(x-2,y),(x+2,y)],fill=color)
    d.line([(x,y-2),(x,y+2)],fill=color)
    d.point((x,y), fill="#fff9e2")

def sword(d, metal, edge, grip, magical=False):
    polygon(d,[(3,28),(3,23),(17,9),(25,6),(26,12),(12,27)],metal)
    d.line([(4,26),(18,11),(24,8)],fill=edge,width=2)
    d.line([(6,26),(20,13),(24,12)],fill=grip,width=1)
    polygon(d,[(21,13),(21,8),(28,2),(30,3),(30,6),(24,13)],grip)
    d.line([(24,8),(27,5),(29,4)],fill=LIGHT)
    polygon(d,[(15,9),(18,5),(21,8),(25,10),(26,15),(22,16),(19,13)],GOLD)
    d.line([(16,9),(18,7),(21,10),(24,12),(24,14)],fill=LIGHT)
    if magical:
        gem(d, 21, 11, 4)
        polygon(d, [(19,8),(14,6),(13,3),(18,5),(22,8)], "#dbd4ec")
        polygon(d, [(24,12),(28,13),(30,17),(27,17),(24,15)], "#a8a8d9")
        spark(d, 9, 14, "#f9c5ff")
        spark(d, 28, 23)

def bow(d, color, edge):
    polygon(d,[(3,24),(8,26),(13,23),(16,18),(22,15),(27,10),(28,4),(25,2),(24,7),(20,10),(14,12),(11,18),(7,22)],color)
    d.line([(5,25),(26,4)], fill="#f0ece4")
    d.line([(6,24),(10,25),(15,20),(17,16),(24,12),(27,6)],fill=edge,width=2)
    polygon(d,[(12,16),(15,12),(20,11),(21,16),(17,20),(13,20)],GOLD)
    gem(d, 17, 16, 3)
    spark(d,25,21)

def staff(d, color, gem_color):
    polygon(d,[(3,26),(6,29),(24,11),(22,8)],color)
    d.line([(5,27),(22,10)],fill="#d9c3f9")
    polygon(d,[(16,9),(16,5),(21,7),(22,2),(26,2),(27,6),(30,5),(29,11),(26,13),(25,17),(22,15),(18,15)],GOLD)
    d.line([(17,7),(21,9),(23,4),(26,3),(26,8),(28,7)],fill=LIGHT)
    gem(d,23,9,5,gem_color)
    spark(d,9,15,gem_color)

def armor(d, base, highlight):
    polygon(d,[(5,7),(10,5),(13,8),(18,8),(21,5),(26,7),(29,12),(24,17),(23,25),(20,27),(12,26),(8,28),(7,17),(2,12)],base)
    polygon(d,[(5,8),(10,6),(12,10),(10,15),(5,14),(3,11)],GOLD)
    polygon(d,[(21,6),(26,8),(28,11),(24,15),(20,10)],GOLD)
    d.line([(9,17),(13,13),(17,15),(21,13),(24,16)],fill=highlight,width=2)
    d.line([(9,24),(13,22),(17,24),(21,22)],fill=GOLD,width=2)
    gem(d,16,17,3)

def trinket(d, tint, link, medallion=False):
    if medallion:
        d.arc((5,2,27,24),188,343,fill=OUTLINE,width=3)
        d.arc((5,2,27,24),188,343,fill=link,width=1)
        polygon(d,[(16,9),(25,15),(24,22),(16,29),(8,24),(6,16)],link)
        d.line([(8,16),(12,12),(16,11),(22,15)],fill=LIGHT,width=2)
        gem(d,16,19,6,tint)
    else:
        d.ellipse((6,9,25,27),fill=OUTLINE)
        d.ellipse((8,11,23,26),fill=link)
        d.ellipse((11,13,20,23),fill=(0,0,0,0))
        d.arc((7,10,24,26),85,229,fill=LIGHT,width=2)
        gem(d, 20, 10, 6, tint)
    spark(d, 28, 22, tint)

def shield(d, base, trim):
    polygon(d,[(5,7),(10,7),(16,3),(22,7),(27,7),(25,20),(21,25),(16,29),(10,25),(6,20)],trim)
    polygon(d,[(8,10),(12,10),(16,6),(20,10),(24,10),(22,21),(16,26),(10,21)],base)
    d.line([(7,9),(11,9),(16,5),(20,9),(25,9)],fill=LIGHT,width=2)
    gem(d,16,16,5)

def run():
    previous = Image.open(OUT / "item-icons.png").convert("RGBA")
    atlas = Image.new("RGBA", (32 * 8, 32 * 4))
    for i in range(16):
        x,y=i%4*24,i//4*24
        icon=previous.crop((x,y,x+24,y+24))
        atlas.alpha_composite(icon,(i%8*32+4,i//8*32+4))
    art = {
        0: lambda d:sword(d,"#9a683f","#f0bc78","#53384a"),
        1: lambda d:bow(d,"#426f65","#94c68b"),
        2: lambda d:staff(d,"#573e85","#b989f1"),
        3: lambda d:shield(d,"#3e8190","#c08860"),
        14: lambda d:armor(d,"#726355","#deb697"),
        16: lambda d:sword(d,"#b8bbc7","#fff5e1","#77646e"),
        17: lambda d:sword(d,"#7a67b6","#ddc8f9","#4e3f78",True),
        18: lambda d:sword(d,"#965881","#f5acce","#452c60",True),
        19: lambda d:bow(d,"#6e47a4","#cbb0ff"),
        20: lambda d:staff(d,"#684ea8","#91e6eb"),
        21: lambda d:armor(d,"#a4b3cf","#fcf2eb"),
        22: lambda d:armor(d,"#517e94","#8ee9eb"),
        23: lambda d:shield(d,"#775293","#dfa864"),
        24: lambda d:trinket(d,"#aaedc7","#a17751"),
        25: lambda d:trinket(d,"#edd2ff","#bc8dc9",True),
        26: lambda d:trinket(d,"#a2e6ff","#bd9859",True),
        27: lambda d:trinket(d,"#fa98b9","#dc975d"),
        28: lambda d:polygon(d,[(5,17),(6,11),(10,7),(21,7),(25,13),(27,17),(23,20),(17,19),(10,21)],"#bc794c"),
    }
    for index, painter in art.items():
        icon=Image.new("RGBA",(32,32))
        painter(ImageDraw.Draw(icon))
        atlas.alpha_composite(icon,(index%8*32,index//8*32))
    atlas.save(OUT / "equipment.png", optimize=True)

if __name__ == "__main__":
    run()
