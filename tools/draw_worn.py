"""Paint 80×80 equipment overlays in the adventurer's pose coordinate system.

Rows are in WORN_ORDER. Columns follow the 28 base adventurer poses.
The art stays on the native dot grid, with the same 74-pixel sole line.
"""
from math import cos, radians, sin
from pathlib import Path

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter

from draw_hero import ARCHER, POSES, frame as adventurer

OUT = Path(__file__).resolve().parents[1] / "assets" / "worn-equipment.png"
WORN_ORDER = ("twig", "bronze", "blade", "sunblade", "bow", "nightbow", "wand", "tidewand",
              "coat", "shell", "glasscoat", "crabguard", "cap")
INK = "#262032"
SUN = "#ffdc8a"
GOLD = "#d99a53"
SILK = "#fff6da"
AMBER = "#865737"
SKIN = {ImageColor.getcolor(hex_color, "RGBA")
        for hex_color in ("#f7c493", "#df9e75", "#ffe6c4")}

# Knuckle centers in the six arm stamps, relative to the front shoulder.
KNUCKLE = {"rest": (5, 9), "back": (-3, 10), "swing": (7, 10),
           "tucked": (5, 8), "out": (10, 4), "backlift": (1, 2)}
DRAW_HANDS = {16 + phase: joints[1] for phase, joints in enumerate(ARCHER)}


def grip_for(pose):
    grip = POSES[pose][-1]
    if grip:
        return grip[:2]
    tx, ty = POSES[pose][2]
    ox, oy = KNUCKLE[POSES[pose][6]]
    return tx + 13 + ox, ty + 3 + oy


def shape(draw, points, fill, outline=INK):
    draw.polygon(points, fill=fill, outline=outline)


class Grip:
    """Draw in integer pixel coordinates along and across the held object."""
    def __init__(self, image, grip, angle):
        self.d = ImageDraw.Draw(image)
        self.grip = grip
        self.c = cos(radians(angle))
        self.s = sin(radians(angle))

    def pt(self, u, v):
        x, y = self.grip
        return round(x + u*self.c - v*self.s), round(y + u*self.s + v*self.c)

    def plate(self, points, color, outline=INK):
        shape(self.d, [self.pt(*p) for p in points], color, outline)

    def line(self, points, color, width=1):
        self.d.line([self.pt(*p) for p in points], fill=color, width=width)

    def jewel(self, u, v, size, fill):
        self.plate([(u-size,v),(u,v-size),(u+size,v),(u,v+size)], fill)
        self.line([(u-1,v-1),(u,v-2)], SILK)


def blade(image, kind, grip, pose):
    angle = {8:-139, 9:-11, 10:37, 11:-52, 12:-32, 13:-48, 14:-70}.get(pose,-33)
    w = Grip(image, grip, angle)
    if kind == "twig":
        w.plate([(-5,-1),(-4,-2),(4,-2),(5,-3),(17,-2),(21,0),(17,2),(5,2),
                 (3,1),(-3,2)], "#b57a40")
        w.line([(5,-1),(15,-1),(18,0)], "#ffe0a0")
        w.line([(7,1),(12,0),(15,1)], "#895134")
        w.plate([(2,-5),(5,-4),(5,4),(3,5)], "#dda256")
        return
    palette = {"bronze": ("#d69c62", "#ffdfaa", "#93634f"),
               "blade": ("#998ac8", "#f0e8ff", "#564978"),
               "sunblade": ("#d17e9a", "#fff0bf", "#754464")}
    core, edge, dark = palette[kind]
    w.plate([(-7,-1),(-5,-2),(3,-2),(5,-1),(5,1),(-5,2),(-7,1)], AMBER)
    w.line([(-5,0),(2,0)], SUN)
    w.jewel(-6,0,2,GOLD)
    if kind == "bronze":
        w.plate([(4,-2),(15,-2),(21,-1),(23,-1),(20,2),(7,3),(4,2)], core)
        w.line([(7,-1),(17,-1),(21,-1)], edge)
        w.line([(8,2),(16,1),(19,1)], dark)
        w.plate([(2,-5),(5,-4),(5,4),(3,5)], GOLD)
        w.line([(3,-4),(4,-2),(4,2)], SUN)
    elif kind == "blade":
        w.plate([(3,-2),(10,-3),(16,-4),(20,-5),(23,-7),(21,-2),
                 (17,1),(10,3),(5,3)], core)
        w.line([(7,-1),(15,-2),(21,-5)], edge, 2)
        w.line([(8,2),(15,0),(18,-1)], dark)
        w.plate([(1,-6),(5,-4),(6,-2),(5,3),(2,7),(2,4),(3,1)], GOLD)
        w.jewel(4,0,3,"#68bbcf")
    else:
        w.plate([(4,-2),(9,-5),(12,-4),(18,-5),(24,-4),(20,0),
                 (12,4),(8,5),(8,3),(4,3)], core)
        w.line([(7,-2),(10,-3),(13,-2),(21,-4)], edge, 2)
        w.line([(9,3),(15,1),(20,-2)], dark)
        w.line([(11,-1),(13,0),(15,-2)], "#f8bf84")
        w.plate([(-1,-7),(4,-5),(6,-2),(6,2),(2,6),(-1,7),(2,2),(2,-2)], GOLD)
        w.line([(1,-5),(4,-3),(5,0)], SUN)
        w.jewel(4,0,3,"#e6a1eb")


def bow(image, kind, grip, pose):
    d = ImageDraw.Draw(image)
    x,y = grip
    moon = kind == "nightbow"
    core, shadow, light = ("#9d84c9","#5a487f","#e9d9f5") if moon else ("#83aa76","#466759","#d6e9a1")
    # Positive x points downrange. The stave flexes inward on a full draw.
    tips = -11 if pose == 17 else -9 if pose in (16,18) else -6
    height = 16 if pose == 17 else 18
    for sign in (-1, 1):
        def pts(coords):
            return [(x+a,y+sign*b) for a,b in coords]
        limb = [(0,0),(3,3),(4,6),(3,10),(0,13),(tips+2,height-2),
                (tips,height),(tips-2,height-1),(tips,height-4),(-3,10),(-1,7),(-2,4)]
        shape(d,pts(limb),core)
        d.line(pts([(2,4),(2,8),(-1,11),(tips+1,height-2)]), fill=light)
        d.line(pts([(-1,6),(-2,9),(tips,height-3)]),fill=shadow)
        if moon:
            shape(d,pts([(2,5),(5,6),(6,10),(3,9),(2,8)]),GOLD)
            d.point(pts([(4,7)])[0], fill=SUN)
    string_x, string_y = DRAW_HANDS[pose] if pose in (16,17) else (x+tips, y)
    d.line([(x+tips,y-height+1),(string_x,string_y),(x+tips,y+height-1)],
           fill="#f9ecca")
    shape(d,[(x-3,y-4),(x+1,y-5),(x+3,y-2),(x+2,y+4),(x-1,y+5),(x-2,y+2)],GOLD)
    d.line([(x,y-3),(x+1,y-2),(x,y+2)],fill=SUN)
    if pose not in DRAW_HANDS:
        # At rest the upper limb points forward; it clears the chin while
        # the lower limb lies beside the near knee.
        tilted = Image.new("RGBA", image.size)
        for row in range(y-height-1, min(80, y+height+2)):
            shift = round((y-row)*.42)
            tilted.paste(image.crop((0,row,80,row+1)), (shift,row))
        image.paste(tilted)
    if pose in (16,17):
        tip_x = min(76, string_x+28)
        d.line([(string_x,string_y),(tip_x,y)],fill=INK,width=2)
        d.line([(string_x+1,string_y),(tip_x-2,y)],fill="#edcb87")
        shape(d,[(tip_x-3,y-2),(tip_x+1,y),(tip_x-3,y+2)],light)
        d.line([(string_x-2,string_y-2),(string_x+1,string_y)],fill=light)


def wand(image, kind, grip, pose):
    angle = {20:-62, 21:-83, 22:-19, 23:-46, 8:-127, 9:-31, 10:19}.get(pose,-38)
    w = Grip(image,grip,angle)
    tide = kind == "tidewand"
    tint = "#7dd9e7" if tide else "#c6a2ed"
    dark = "#4c839f" if tide else "#76589f"
    w.plate([(-8,-1),(-6,-2),(13,-1),(16,-2),(16,1),(-6,2),(-8,1)], "#76648e")
    w.line([(-6,0),(13,0)], "#eccbe3")
    for z in (6,10):
        w.line([(z,-1),(z+1,1)], GOLD)
    if tide:
        w.plate([(12,-1),(15,-5),(19,-7),(20,-5),(18,-2),(22,0),(19,4),(16,5),(13,3)], GOLD)
        w.jewel(17,0,4,tint)
        w.line([(17,2),(19,0)],dark)
        w.line([(14,-4),(17,-5)],SUN)
    else:
        w.plate([(12,-2),(16,-3),(18,-7),(20,-3),(23,-2),(21,1),(21,5),
                 (17,3),(14,5),(14,1)],GOLD)
        w.jewel(18,-1,3,tint)
        w.line([(14,-1),(17,-4)],SUN)
    if pose in (21,22):
        reach = 19
        for u,v in ((reach,-8),(reach+1,7),(14,-9)):
            w.line([(u-1,v),(u+1,v)],tint)
            w.line([(u,v-1),(u,v+1)],SILK)


# Segmented rows in the native torso system. Plates, raised collar and coat
# skirts give each item its own silhouette even before the trim is painted.
VEST = """
.....kk....kk...
....kydk..kydk..
..kklybdkkbydkk.
.kbylydydydylbk.
..kllldbybdllk..
...kbldbybdlbk..
...kdldbybdldk..
...kbldbybdlbk..
...kbldbybdldk..
...kdldbybdldk..
...kymbbybbmyk..
...kbbmkggkmbk..
..kbldbyygyblk..
..kbldbk.kbldk..
..kmbbk...kbbk..
...kkk.....kk...
"""
CUIRASS = """
....kkk....kkk..
..kkyldk..kdlykk
.klywwbbkkbbwwyk
.klyllbbbbbllllk
..kdblwlyylwldk.
...kllyywwyylk..
...kdlbywgyblk..
...kdllbyybllk..
...kblldbbdldk..
...kbdlydbylbk..
...kbblyddybbk..
..kdlyyygbyybdk.
..klbddbybbdllk.
..kyddlbkbdlyyk.
...kydbk.kddyk..
....kkk...kkk...
"""
GLASS = """
.....kk...kk....
...kklbkkkblk...
.kklwwbbybbwlkk.
.kwwlmlyyyblwwk.
..kblbywgwyblk..
...kllygwgyllk..
...kbbbyyylbmk..
...kmllbybllbk..
...kblldbdlbbk..
...kbylbdbylbk..
...kdbbgygbddk..
..klyyddyddyylk.
..kblbdylybdlbk.
...klbmbybmbbk..
....kybk.kbyk...
.....kk...kk....
"""
MANTLE = """
....kkk....kkk...
..kklylk..klylkk.
.kbblyllkkllgybbk
.klwwlllllllwwlbk
..kbbllbybyllbbk.
..kbbdlywgyldbbk.
...kbllyyylldbk..
...kdbbyybybbbk..
...kbdbydbybdbk..
...kllybdblylbk..
..klllydbyylllk..
..kblbbyybblbdk..
..kblbyddbylldk..
.kdbbbyk.kbybbdk.
.kblbdk...kblbbk.
..kddk.....kddk..
...kk.......kk...
"""
CLOTH = {
    "coat": (VEST, ("#a27853","#8a6149","#624953","#cf9b66","#f2d19a","#e2aa58","#d6bb78")),
    "shell": (CUIRASS, ("#a4b3c8","#91a2ba","#59677c","#d7d9d5","#fff9ec","#c79c70","#88bace")),
    "glasscoat": (GLASS, ("#4f8395","#4d758f","#38566e","#80bfc3","#ddfaf1","#b7c99f","#72e3e7")),
    "crabguard": (MANTLE, ("#956a98","#86567c","#593f65","#c397a3","#ffe0b4","#d5a36c","#8bded7")),
}


def armor(image, kind, pose, base):
    x,y = POSES[pose][2]
    template, ramp = CLOTH[kind]
    colors = dict(zip("bmdlwyg",ramp), k=INK)
    # Upper-arm matte from the actual cel plus its one-dot dark edge. Mask
    # after painting so sleeves remain behind the forward arm and knuckles.
    skin = Image.new("L",image.size)
    pix, mask = base.load(), skin.load()
    for j in range(max(0,y), min(y+19,80)):
        for i in range(max(0,x-4), min(x+23,80)):
            if pix[i,j] in SKIN:
                mask[i,j]=255
    skin = skin.filter(ImageFilter.MaxFilter(3))
    head_x, head_y = POSES[pose][0]
    for j,line in enumerate(template.split()):
        for i,ch in enumerate(line):
            a,b=x+i,y+j
            if ch=="." or skin.getpixel((a,b)):
                continue
            # The chin is painted in front of the collar in front-facing cels.
            if b < head_y+43 and head_x < a < head_x+42 and pix[a,b][3]:
                continue
            image.putpixel((a,b), ImageColor.getcolor(colors[ch],"RGBA"))
    if pose >= 24:
        # The back panel has a center seam and no front-facing jewel.
        d = ImageDraw.Draw(image)
        for j in range(5,12):
            for off,color in ((7,ramp[1]),(8,ramp[2]),(9,ramp[0])):
                at = (x+off,y+j)
                if image.getpixel(at)[3]:
                    d.point(at,fill=color)


def cap(image, pose):
    x,y = POSES[pose][0]
    # The base cel starts one pixel from the sheet edge at the top of a
    # jump. Keep the leather crown in the tile while covering the hair part.
    y=max(1,y-2)
    d=ImageDraw.Draw(image)
    def pts(coords):
        return [(x+a,y+b) for a,b in coords]
    def patch(coords,color,outline=INK):
        shape(d,pts(coords),color,outline)
    patch([(-1,14),(0,9),(3,5),(7,3),(12,1),(18,0),(26,0),(31,1),(35,3),
           (39,6),(41,10),(41,14),(38,17),(31,17),(27,15),(19,15),(12,17),
           (7,20),(3,20),(0,18)],"#aa6b43")
    patch([(1,12),(3,8),(7,5),(12,3),(20,1),(25,1),(20,3),(14,5),(9,8),
           (7,12),(4,14)],"#dca16a",None)
    patch([(25,2),(31,3),(36,6),(39,10),(39,13),(35,13),(33,8),(30,5)],"#c98752",None)
    d.line(pts([(4,11),(8,7),(13,5),(16,4)]),fill="#f1c489")
    d.line(pts([(23,2),(19,4),(16,8),(15,11)]),fill="#88503b")
    patch([(0,14),(4,15),(10,13),(19,11),(30,10),(39,12),(41,14),
           (38,16),(30,14),(21,14),(12,16),(5,19),(1,18)],"#79503d")
    d.line(pts([(3,16),(11,14),(21,12),(31,12),(37,13)]),fill="#d49a5d")
    if pose < 24:
        patch([(14,14),(20,12),(30,12),(38,13),(44,15),(45,17),(42,18),
               (35,18),(28,16),(18,16)],"#c88c53")
        d.line(pts([(20,14),(29,13),(37,14),(43,16)]),fill="#edb875")
        patch([(8,12),(11,10),(14,11),(14,14),(10,16),(8,15)],GOLD)
        d.point(pts([(11,12)])[0],fill=SUN)


def hold_in_hand(image, base, grip):
    """Recover knuckles already painted in the lower character layer."""
    x,y=grip
    hand=Image.new("L",image.size)
    for j in range(max(0,y-4),min(80,y+5)):
        for i in range(max(0,x-4),min(80,x+5)):
            if base.getpixel((i,j)) in SKIN:
                hand.putpixel((i,j),255)
    # Preserve the existing dark outline only where it touches a knuckle.
    edge=hand.filter(ImageFilter.MaxFilter(3))
    for j in range(max(0,y-5),min(80,y+6)):
        for i in range(max(0,x-5),min(80,x+6)):
            if edge.getpixel((i,j)) and base.getpixel((i,j))[:3] == (39,37,45):
                hand.putpixel((i,j),255)
    image.putalpha(ImageChops.subtract(image.getchannel("A"),hand))


def overlay(kind,pose,base):
    image=Image.new("RGBA",(80,80))
    if kind in CLOTH:
        armor(image,kind,pose,base)
    elif kind=="cap":
        cap(image,pose)
    elif pose < 24 and (kind!="twig" or pose >= 8):
        grip=grip_for(pose)
        if kind in ("twig","bronze","blade","sunblade"):
            blade(image,kind,grip,pose)
        elif kind in ("bow","nightbow"):
            bow(image,kind,grip,pose)
        else:
            wand(image,kind,grip,pose)
        hold_in_hand(image,base,grip)
        if kind in ("bow","nightbow") and pose in (16,17):
            hold_in_hand(image,base,DRAW_HANDS[pose])
    return image


def run():
    if len(POSES)!=28:
        raise ValueError("Regenerate with the matching 28-pose adventurer")
    atlas=Image.new("RGBA",(28*80,len(WORN_ORDER)*80))
    for pose in range(28):
        base=adventurer(pose)
        for row,kind in enumerate(WORN_ORDER):
            atlas.paste(overlay(kind,pose,base),(pose*80,row*80))
    atlas.save(OUT,optimize=True)


if __name__=="__main__":
    run()
