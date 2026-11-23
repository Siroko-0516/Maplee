"""Bake Maplee equipment, icons and enlarged right-hand attack sprites."""
from math import cos, hypot, radians, sin, sqrt
from pathlib import Path

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter

ASSETS = Path(__file__).resolve().parents[1] / "assets"
import sys
sys.path.insert(0,str(ASSETS.parent))
from maplee.gear_data import EXPANSION_EQUIPMENT, MELEE_WEAPONS, WORN_ITEMS

CELL, PAD = 112, 16
WEAPON_KEYS = WORN_ITEMS[:8]
KNUCKLES = ("knuckle","stormknuckle")
DAGGERS = ("dagger","shadowdagger")
WANDS = ("wand","tidewand","chimewand","dawnwand")
EQUIPMENT = {entry[0]:entry for entry in EXPANSION_EQUIPMENT}

INK = "#262032"
SUN = "#ffdc8a"
GOLD = "#d99a53"
SILK = "#fff6da"
AMBER = "#865737"
# Register directly to the painted right-facing 80px cells. Each entry is the
# palm center or a pair of (collar center, hip center) landmarks. The melee
# follow-through wraps the weapon hand behind the head.
PALMS = (
    (48,60), (48,60), (50,60), (48,60), (50,57), (47,57), (50,57), (52,52),
    (26,52), (45,54), (21,38), (47,56), (48,52), (48,54), (46,57), (48,54),
    (58,48), (58,48), (58,48), (47,56), (57,40), (55,46), (54,50), (47,56),
)
# Native right-facing coordinates. On a three-quarter front view the right
# shoulder is near when facing right and far when facing left.
NEAR_PALMS = (
    (30,60), (29,60), (28,60), (29,60), (28,57), (36,61), (28,57), (26,56),
    (26,52), (45,54), (22,38), (35,60), (31,47), (31,49), (35,59), (35,59),
    (36,47), (26,47), (26,47), (35,60), (57,41), (55,46), (20,58), (35,60),
)
FAR_PALMS = PALMS[:8] + ((44,56),(25,53),(47,54),(47,56)) + PALMS[12:20] + (
    (48,56),(49,53),(51,50),(47,56),
)
SWORD_ANGLES = (-52,-93,-125,-143,-145,-127,-94,-51,-10,12,30,41,
                49,55,59,61,58,51,39,24,7,-10,-24,-33)
# (wrist x, wrist y) from lift through extension and return, in native dots.
NEAR_WRISTS = ((31,57),(28,54),(25,51),(24,48),(25,45),(30,42),
               (37,42),(44,46),(51,50),(52,52),(52,54),(51,55),
               (49,57),(47,58),(44,59),(41,60),(38,60),(36,60))
FAR_WRISTS = ((46,55),(49,53),(53,50),(56,48),(58,47),(59,46),
              (58,46),(56,47),(55,50),(55,52),(54,54),(53,56),
              (52,57),(51,58),(50,58),(49,58),(48,57),(47,56))

STRING_HAND = {16: (42,45), 17: (29,44)}
TORSO = (
    ((39,46),(39,57)), ((39,46),(39,57)), ((39,46),(39,57)), ((39,46),(39,57)),
    ((39,46),(39,57)), ((39,47),(39,58)), ((39,46),(39,57)), ((39,47),(39,58)),
    ((36,49),(32,61)), ((36,45),(32,58)), ((41,50),(34,61)), ((39,47),(36,58)),
    ((40,44),(37,55)), ((40,46),(37,57)), ((39,46),(37,57)), ((39,48),(37,59)),
    ((34,46),(35,58)), ((34,46),(35,58)), ((34,46),(35,58)), ((39,47),(36,58)),
    ((37,46),(37,57)), ((36,46),(33,58)), ((39,49),(35,60)), ((39,47),(36,58)),
    ((39,48),(39,57)), ((39,48),(39,57)), ((39,48),(39,57)), ((39,48),(39,57)),
)


def skin(pixel):
    red, green, blue, alpha = pixel
    return alpha and red >= 204 and red >= green >= blue and red - blue >= 16


def shape(draw, points, fill, outline=INK):
    draw.polygon(points, fill=fill, outline=outline)


class Grip:
    """Draw in integer pixel coordinates along and across the held object."""
    def __init__(self, image, grip, angle):
        self.d = ImageDraw.Draw(image)
        self.grip = grip
        self.factor = 1
        self.c = cos(radians(angle))
        self.s = sin(radians(angle))

    def pt(self, u, v):
        x, y = self.grip
        return round(x + self.factor*(u*self.c - v*self.s)), round(y + self.factor*(u*self.s + v*self.c))

    def plate(self, points, color, outline=INK):
        shape(self.d, [self.pt(*p) for p in points], color, outline)

    def line(self, points, color, width=1):
        self.d.line([self.pt(*p) for p in points], fill=color, width=width)

    def jewel(self, u, v, size, fill):
        self.plate([(u-size,v),(u,v-size),(u+size,v),(u,v+size)], fill)
        self.line([(u-1,v-1),(u,v-2)], SILK)


def blade(image, kind, grip, angle):
    w = Grip(image, grip, angle)
    w.factor = 1.35
    if kind == "frostspear":
        w.factor = 1
        w.plate([(-31,-1),(-29,-2),(20,-2),(22,0),(20,2),(-29,2),(-31,1)],"#ad7648")
        w.line([(-29,-1),(20,-1)],"#f0c273")
        w.plate([(-31,-2),(-27,-3),(-25,-1),(-25,2),(-28,3),(-31,2)],"#bda168")
        w.plate([(-5,-2),(3,-2),(4,2),(-6,2)],"#355774")
        w.plate([(18,-2),(23,-6),(28,-5),(35,0),(28,6),(23,6),(18,2)],"#c58549")
        w.plate([(21,-1),(25,-4),(32,0),(25,4)],"#f0cf87")
        w.line([(24,-3),(32,-1),(28,0)],"#fff1c2")
        w.jewel(22,0,2,"#7dcbd8")
        return
    if kind in KNUCKLES:
        steel, shine, jewel = ("#7990a2","#c6dce3","#ec944f") if kind=="knuckle" else ("#3d466e","#9ec3ea","#b67bfb")
        w.plate([(-8,-4),(-3,-7),(8,-6),(12,-2),(12,4),(8,7),(-4,6),(-8,3)],steel)
        w.line([(0,-4),(7,-4),(10,-1)],shine,2)
        w.jewel(4,1,3,jewel)
        return
    if kind in DAGGERS:
        steel, shine = ("#628ba0","#d0e6d4") if kind=="dagger" else ("#675287","#ead3ff")
        w.plate([(-8,-2),(3,-2),(7,-5),(15,-4),(23,-1),(15,2),(6,4),(2,2),(-8,2)],steel)
        w.line([(5,-2),(13,-3),(21,-1)],shine)
        w.plate([(0,-5),(4,-5),(4,5),(0,5)],"#e3a95b")
        return
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
    string_x, string_y = STRING_HAND[pose] if pose in (16,17) else (x+tips, y)
    d.line([(x+tips,y-height+1),(string_x,string_y),(x+tips,y+height-1)],
           fill="#f9ecca")
    shape(d,[(x-3,y-4),(x+1,y-5),(x+3,y-2),(x+2,y+4),(x-1,y+5),(x-2,y+2)],GOLD)
    d.line([(x,y-3),(x+1,y-2),(x,y+2)],fill=SUN)
    if pose not in (16,17,18):
        # At rest the upper limb points forward; it clears the chin while
        # the lower limb lies beside the near knee.
        tilted = Image.new("RGBA", image.size)
        for row in range(y-height-1, min(80, y+height+2)):
            shift = round((y-row)*.42)
            tilted.paste(image.crop((0,row,80,row+1)), (shift,row))
        image.paste(tilted)
    if pose in (16,17):
        tip_x = min(76, string_x+36)
        d.line([(string_x,string_y),(tip_x,y)],fill=INK,width=2)
        d.line([(string_x+1,string_y),(tip_x-2,y)],fill="#edcb87")
        shape(d,[(tip_x-3,y-2),(tip_x+1,y),(tip_x-3,y+2)],light)
        d.line([(string_x-2,string_y-2),(string_x+1,string_y)],fill=light)


def wand(image, kind, grip, pose):
    angle = {20:-62, 21:-54, 22:-16, 23:-35, 8:-127, 9:-31, 10:19}.get(pose,-38)
    w = Grip(image,grip,angle)
    tide = kind in ("tidewand","dawnwand")
    tint = "#ffd179" if kind in ("chimewand","dawnwand") else "#7dd9e7" if tide else "#c6a2ed"
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
    (neck_x, top), (hip_x, bottom) = TORSO[pose]
    template, ramp = CLOTH[kind]
    rows = template.split()
    colors = {key: ImageColor.getcolor(value, "RGBA")
              for key, value in dict(zip("bmdlwyg",ramp), k=INK).items()}
    pixels = base.load()
    for y in range(top, bottom+1):
        fraction = (y-top)/(bottom-top)
        center = round(neck_x*(1-fraction) + hip_x*fraction)
        row = min(len(rows)-1, round(fraction*(len(rows)-1)))
        pattern = rows[row]
        for x in range(center-8, center+9):
            red, green, blue, alpha = pixels[x,y]
            # The shirt has white highlights and cool blue shading. This
            # matte leaves the actual skin and the black seams of foreground
            # arms and chin visible, including during the diagonal swings.
            if not alpha or not (blue >= green >= red and blue >= 160):
                continue
            col = x-center+len(pattern)//2
            ch = pattern[col] if 0 <= col < len(pattern) else "."
            if ch == ".":
                ch = "m" if blue-red > 55 else "b"
            if pose >= 24 and ch in "ygw":
                ch = "d" if x == center else "l" if x < center else "b"
            image.putpixel((x,y), colors[ch])


def hold_in_hand(image, base, grip):
    """Recover knuckles already painted in the lower character layer."""
    x,y=grip
    hand=Image.new("L",image.size)
    for j in range(max(0,y-4),min(80,y+5)):
        for i in range(max(0,x-4),min(80,x+5)):
            if skin(base.getpixel((i,j))):
                hand.putpixel((i,j),255)
    # Preserve the existing dark outline only where it touches a knuckle.
    edge=hand.filter(ImageFilter.MaxFilter(3))
    for j in range(max(0,y-5),min(80,y+6)):
        for i in range(max(0,x-5),min(80,x+6)):
            if edge.getpixel((i,j)) and base.getpixel((i,j)) == (0,0,0,255):
                hand.putpixel((i,j),255)
    mask=Image.new("L",image.size)
    mask.paste(hand,(PAD,PAD))
    image.putalpha(ImageChops.subtract(image.getchannel("A"),mask))


def padded(source):
    canvas = Image.new("RGBA",(CELL,CELL))
    canvas.alpha_composite(source,(PAD,PAD))
    return canvas


def palette(kind):
    order = list(EQUIPMENT).index(kind)
    ramps = (
        ("#7f314a","#b54c68","#e47780"), ("#5d4a75","#9175a7","#c6add3"),
        ("#315b60","#548f83","#a7c78d"), ("#465772","#728da7","#bbd3d8"),
        ("#495f95","#799bd2","#d4dff2"), ("#6e4e38","#ac7854","#e5b981"),
    )
    return ramps[order % len(ramps)]


def scaled_weapon(image, kind, grip, pose):
    # Keep the palm fixed when enlarging the bow or wand around its grip.
    if kind in MELEE_WEAPONS:
        angle = {8:-139,9:-11,10:-113,11:-52,12:-32,13:-48,14:-25}.get(pose,-33)
        if kind == "frostspear" and pose not in (8,9,10):
            angle = (-14,-10,-8,-10)[pose%4]
        blade(image,kind,(grip[0]+PAD,grip[1]+PAD),angle)
        return
    tool = Image.new("RGBA",(80,80))
    if kind in WANDS:
        wand(tool,kind,grip,(-62,-54,-16)[pose-20] if 20 <= pose <= 22 else -38)
    else:
        # The string hand is fixed on the draw cels; extend the limbs around the grip.
        bow(tool,kind,grip,pose)
    factor = 1.3
    tool = tool.resize((104,104),Image.Resampling.NEAREST)
    image.alpha_composite(tool,(PAD-round(grip[0]*(factor-1)),PAD-round(grip[1]*(factor-1))))


def overlay(kind,pose,base,far=False):
    image = Image.new("RGBA",(80,80))
    if kind in WEAPON_KEYS or kind in EQUIPMENT and EQUIPMENT[kind][2]=="weapon":
        result = padded(image)
        if pose < 24:
            grip = (FAR_PALMS if far else NEAR_PALMS)[pose] if kind in MELEE_WEAPONS else PALMS[pose]
            scaled_weapon(result,kind,grip,pose)
            if kind not in KNUCKLES:
                hold_in_hand(result,base,grip)
            if kind in ("bow","nightbow") and pose in (16,17):
                hold_in_hand(result,base,STRING_HAND[pose])
        return result
    if kind not in EQUIPMENT:
        return padded(image)
    dark, middle, light = palette(kind)
    if EQUIPMENT[kind][2] == "armor":
        pattern = (VEST,CUIRASS,GLASS,MANTLE)[list(EQUIPMENT).index(kind)%4]
        CLOTH[kind] = (pattern,(middle,dark,INK,light,"#f9edcf","#c49568","#a2d6bc"))
        armor(image,kind,pose,base)
    else:
        top = base.getchannel("A").getbbox()[1]
        hair = [x for x in range(80) for y in range(top,top+9) if base.getpixel((x,y))[3] and base.getpixel((x,y))[0] < 90]
        x = (min(hair)+max(hair))//2
        draw = ImageDraw.Draw(image)
        rise = 12 if kind in ("wizardhat","vikinghelm") else 7
        shape(draw,[(x-18,top+8),(x-13,top-2),(x-7,top-rise+5),(x+4,top-rise),
                    (x+12,top-3),(x+17,top+7),(x+20,top+11),(x-20,top+11)],middle)
        draw.line((x-15,top+7,x+16,top+7),fill=light,width=2)
        draw.rectangle((x-4,top+3,x+2,top+7),fill=dark,outline=INK)
        draw.point((x-2,top+4),fill="#ffe4a0")
    return padded(image)


# Blade-tip registration in the same along/across coordinates as blade().
CUT_EDGE = {
    "twig":     ((20, 0),  "#c38c5a", "#ffdfa0"),
    "bronze":   ((22, -1), "#d19b71", "#fff0be"),
    "blade":    ((22, -6), "#a29bd6", "#e3dafa"),
    "sunblade": ((23, -4), "#d98eab", "#ffdfc2"),
    "frostspear": ((26, 0), "#a7a177", "#ffedac"),
}


def cutting_trail(image, kind, palm, heading, previous, tick):
    if kind in KNUCKLES or not 5 <= tick <= 12:
        return
    tip, shade, light = CUT_EDGE.get(kind,((22,0),"#967fbb","#eee2f7"))
    tip = tuple(v*1.35 for v in tip)
    palm = (palm[0]+PAD,palm[1]+PAD)
    tail = (0.48, 0.78, 0.94, 1.0, 0.95, 0.83, 0.72, 0.60)[tick-5]
    span = (heading - previous) * tail
    samples = max(2, round(span / 4))
    outer, inner = [], []
    for step in range(samples+1):
        progress = step / samples
        direction = heading - span*(1-progress)
        path = Grip(image, palm, direction)
        outer.append(path.pt(*tip))
        thickness = (2.9 if 7 <= tick <= 9 else 2.0) * progress
        inner.append(path.pt(tip[0]-thickness, tip[1]))
    draw = ImageDraw.Draw(image)
    draw.polygon(outer + list(reversed(inner)), fill=shade)
    draw.line(outer[samples//3:], fill=light)


def lunge_body(hero, far):
    """Remove only the striking arm from swingO1.0, up to its shirt seam."""
    body = hero.crop((0, 160, 80, 240))
    draw = ImageDraw.Draw(body)
    if far:
        # Left edge of the far arm, following the outline of the shirt.
        for y, x in enumerate((38,38,38,38,39,41,43,43), 51):
            draw.line((x,y, 41 if y==51 else 48,y), fill=(0,0,0,0))
    else:
        for y, x in enumerate((33,32,31,31,30,29,28), 48):
            draw.line((20,y,x,y), fill=(0,0,0,0))
    return body


def sword_arm(grip, far):
    # Two jointed segments connect the shoulder to the moving grip.
    shoulder = (39,52) if far else (34,50)
    dx,dy = grip[0]-shoulder[0], grip[1]-shoulder[1]
    length = hypot(dx,dy) or 1
    bend = sqrt(max(0, 9.5**2 - (length/2)**2))
    elbow = (round((shoulder[0]+grip[0])/2 - dy/length*bend),
             round((shoulder[1]+grip[1])/2 + dx/length*bend))
    arm = Image.new("RGBA",(80,80))
    d = ImageDraw.Draw(arm)
    for radius, color in ((3,"#080808"),(2,"#ffcb86")):
        d.line((shoulder,elbow,grip),fill=color,width=radius*2+1)
        for x,y in (elbow,shoulder):
            d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=color)
    d.line((elbow,grip), fill="#ffe5b9",width=2)
    return arm


def swing_weapons(hero):
    # Swing rows are followed by the body cutouts and four dagger thrust rows.
    body_row = 2*len(MELEE_WEAPONS)
    atlas = Image.new("RGBA", (24*CELL,(body_row+5)*CELL))
    # The closed fist comes from the actual raised-hand cel.
    fist = hero.crop((2*80+17,2*80+33,2*80+28,2*80+44))
    outline = Image.new("L",fist.size)
    ImageDraw.Draw(outline).polygon([(4,0),(6,0),(9,2),(10,4),(10,7),(7,10),
                                     (3,10),(1,8),(0,6),(0,3)],fill=255)
    fist.putalpha(ImageChops.multiply(fist.getchannel("A"),outline))
    ready = hero.crop((240,160,320,240))
    knuckles = fist.resize((8,8),Image.Resampling.NEAREST)
    for far, wrists in enumerate((NEAR_WRISTS,FAR_WRISTS)):
        body = lunge_body(hero,far)
        atlas.paste(body,(far*CELL+PAD,body_row*CELL+PAD))
        # On the far shoulder the wind-up arcs around the outside of the cheek.
        headings = (-45,-60,-76,-89,-96,-88,-72,-44) + SWORD_ANGLES[8:] if far else SWORD_ANGLES
        for tick,heading in enumerate(headings):
            moving = tick < len(wrists)
            grip = wrists[tick] if moving else (FAR_PALMS if far else NEAR_PALMS)[11]
            for row,kind in enumerate(MELEE_WEAPONS):
                cel = padded(sword_arm(grip,far)) if moving else Image.new("RGBA",(CELL,CELL))
                cutting_trail(cel,kind,grip,heading,headings[max(0,tick-1)],tick)
                blade(cel,kind,(grip[0]+PAD,grip[1]+PAD),heading)
                if moving:
                    # A compact knuckle patch leaves the pommel and guard exposed.
                    if kind not in KNUCKLES:
                        cel.alpha_composite(knuckles,(PAD+grip[0]-4,PAD+grip[1]-4))
                    if far:
                        cel.putalpha(ImageChops.subtract(cel.getchannel("A"),padded(body).getchannel("A")))
                else:
                    hold_in_hand(cel,ready,grip)
                atlas.paste(cel,(tick*CELL,(len(MELEE_WEAPONS)*far+row)*CELL))
        # Extension peaks four and nine ticks into the stab sequence.
        thrust = (0,3,8,14,19,13,6,5,13,20,13,6,0)
        for tick,extension in enumerate(thrust):
            grip = ((43 if far else 34)+extension, (56 if far else 57)-extension//5)
            for row,kind in enumerate(DAGGERS):
                cel = padded(sword_arm(grip,far))
                blade(cel,kind,(grip[0]+PAD,grip[1]+PAD),-6-extension//2)
                cel.alpha_composite(knuckles,(PAD+grip[0]-4,PAD+grip[1]-4))
                if far:
                    cel.putalpha(ImageChops.subtract(cel.getchannel("A"),padded(body).getchannel("A")))
                atlas.paste(cel,(tick*CELL,(body_row+1+2*far+row)*CELL))
    atlas.save(ASSETS/"expansion-swing.png",optimize=True)


def run():
    hero = Image.open(ASSETS/"hero-adventurer.png").convert("RGBA")
    atlas = Image.new("RGBA",(28*CELL,(len(WORN_ITEMS)+len(MELEE_WEAPONS))*CELL))
    icons = Image.new("RGBA",(256,32*((8+len(EXPANSION_EQUIPMENT)+7)//8)))
    for pose in range(28):
        x,y = (pose % 4)*80,(pose // 4)*80
        base = hero.crop((x,y,x+80,y+80))
        for row,kind in enumerate(WORN_ITEMS):
            tile = overlay(kind,pose,base)
            atlas.paste(tile,(pose*CELL,row*CELL))
            if pose == 0 and (kind in WEAPON_KEYS or kind in EQUIPMENT):
                index = row if row<8 else row-5
                icon = tile.crop(tile.getbbox())
                icon.thumbnail((29,29),Image.Resampling.NEAREST)
                icons.paste(icon,(index%8*32+(32-icon.width)//2,index//8*32+(32-icon.height)//2))
        for row,kind in enumerate(MELEE_WEAPONS,len(WORN_ITEMS)):
            atlas.paste(overlay(kind,pose,base,True),(pose*CELL,row*CELL))
    atlas.save(ASSETS/"expansion-worn.png",optimize=True)
    icons.save(ASSETS/"expansion-icons.png",optimize=True)
    swing_weapons(hero)


if __name__ == "__main__":
    run()
