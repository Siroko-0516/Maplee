"""Paint 80×80 equipment overlays in the adventurer's pose coordinate system.

Worn rows follow WORN_ORDER, then four far-hand sword rows, across 28 poses.
The attack atlas packs four sword rows per direction and two arm cutouts.
Both atlases stay on the native dot grid, with the same 74-pixel sole line.
"""
from math import atan2, cos, degrees, hypot, radians, sin, sqrt
from functools import lru_cache
import numpy as np
from classic_gear import ITEM_IDS, fetch, layers
from draw_hero import CELS
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ASSETS = Path(__file__).resolve().parents[1] / "assets"
OUT = ASSETS / "worn-equipment.png"
WORN_ORDER = ("twig", "bronze", "blade", "sunblade", "bow", "nightbow", "wand", "tidewand",
              "coat", "shell", "glasscoat", "crabguard", "cap")
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
def skin(pixel):
    red, green, blue, alpha = pixel
    return alpha and red >= 204 and red >= green >= blue and red - blue >= 16


def edge_point(palm, angle, u, v):
    c,s=cos(radians(angle)),sin(radians(angle))
    return round(palm[0]+u*c-v*s), round(palm[1]+u*s+v*c)


@lru_cache(None)
def weapon_template(kind):
    im, _, pivot = layers(ITEM_IDS[kind],"stand1",0)["weapon"]
    sprite = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    px,py = sprite.width-1-pivot[0],pivot[1]
    # The original stand sprite points forwards and slightly down.
    coords = [(x,y) for y in range(sprite.height) for x in range(sprite.width)
              if sprite.getpixel((x,y))[3] and x>px]
    tx,ty = max(coords,key=lambda xy: (xy[0]-px)**2+(xy[1]-py)**2)
    length=hypot(tx-px,ty-py)
    scale=min(1,24/length)
    tile=Image.new("RGBA",(96,96))
    tile.alpha_composite(sprite,(48-px,48-py))
    side=2*round(48*scale)
    tile=tile.resize((side,side),Image.Resampling.NEAREST)
    return tile,degrees(atan2(ty-py,tx-px))


def blade(image, kind, grip, angle):
    tile,rest = weapon_template(kind)
    rotated=tile.rotate(rest-angle,Image.Resampling.NEAREST,center=(tile.width/2,tile.height/2))
    image.alpha_composite(rotated,(grip[0]-tile.width//2,grip[1]-tile.height//2))


def match_anchor(base, template):
    # Recover the original WZ navel/brow registration in each fitted body cel.
    image, _, pivot = template
    image=image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    target=np.array(base)
    raw=np.array(image)
    ys,xs=np.where(raw[:,:,3]>200)
    colors=raw[ys,xs]
    best=(-1,0,0)
    for y in range(0,81-image.height):
        for x in range(0,81-image.width):
            similarity=(target[ys+y,xs+x]==colors).all(axis=1).sum()
            if similarity>best[0]:
                best=(similarity,x,y)
    return best[1]+image.width-1-pivot[0],best[2]+pivot[1]


def anchored_parts(image, kind, pose):
    action,frame,*_=CELS[pose]
    for part,anchor,pivot in layers(ITEM_IDS[kind],action,frame).values():
        ax,ay=ANCHORS[pose][anchor]
        px,py=part.width-1-pivot[0],pivot[1]
        part=part.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if kind in ("bow","nightbow"):
            # Reserve space for the limbs inside the fitted 80px game cel.
            scale=min(1, ax/max(1,px), (79-ax)/max(1,part.width-1-px),
                      ay/max(1,py),(79-ay)/max(1,part.height-1-py))
            if scale<1:
                part=part.resize((max(1,round(part.width*scale)),max(1,round(part.height*scale))),Image.Resampling.NEAREST)
                px,py=round(px*scale),round(py*scale)
        image.alpha_composite(part,(ax-px,ay-py))


ACCESSORIES=("dew","prism","shimmer","moonseal")
ANCHORS={}


def accessory(image, kind, pose):
    # These classic items ship UI icons only. Fit small native-palette
    # charms to the hand, collar or lapel so the equipped slot reads in play.
    if pose>=24:
        return
    icon=fetch(ITEM_IDS[kind],icon=True)
    tile=icon.crop(icon.getbbox())
    size=5 if kind=="dew" else 8
    tile.thumbnail((size,size),Image.Resampling.NEAREST)
    if kind=="dew":
        x,y=FAR_PALMS[pose]
    else:
        x,y=ANCHORS[pose]["navel"]
        x+=3 if kind=="moonseal" else 0
        y-=3 if kind=="moonseal" else 7
    image.alpha_composite(tile,(x-tile.width//2,y-tile.height//2))


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
    image.putalpha(ImageChops.subtract(image.getchannel("A"),hand))


def overlay(kind,pose,base, far=False):
    image=Image.new("RGBA",(80,80))
    if kind in ACCESSORIES:
        accessory(image,kind,pose)
    elif kind in ("coat","shell","glasscoat","crabguard","cap"):
        anchored_parts(image,kind,pose)
    elif pose < 24:
        grip = PALMS[pose]
        if kind in WORN_ORDER[:4]:
            grip = (FAR_PALMS if far else NEAR_PALMS)[pose]
            angle = {8:-139, 9:-11, 10:-113, 11:-52, 12:-32, 13:-48, 14:-25}.get(pose,-33)
            blade(image,kind,grip,angle)
        elif kind in ("bow","nightbow"):
            anchored_parts(image,kind,pose)
        else:
            blade(image,kind,grip,-38 if pose not in (20,21,22) else (-62,-54,-16)[pose-20])
        hold_in_hand(image,base,grip)
        if kind in ("bow","nightbow") and pose in (16,17):
            hold_in_hand(image,base,STRING_HAND[pose])
    return image


# Blade-tip registration in the same along/across coordinates as blade().
CUT_EDGE = {
    "twig":     ((20, 0),  "#c38c5a", "#ffdfa0"),
    "bronze":   ((22, -1), "#d19b71", "#fff0be"),
    "blade":    ((22, -6), "#a29bd6", "#e3dafa"),
    "sunblade": ((23, -4), "#d98eab", "#ffdfc2"),
}


def cutting_trail(image, kind, palm, heading, previous, tick):
    if not 5 <= tick <= 12:
        return
    tip, shade, light = CUT_EDGE[kind]
    tail = (0.48, 0.78, 0.94, 1.0, 0.95, 0.83, 0.72, 0.60)[tick-5]
    span = (heading - previous) * tail
    samples = max(2, round(span / 4))
    outer, inner = [], []
    for step in range(samples+1):
        progress = step / samples
        direction = heading - span*(1-progress)
        outer.append(edge_point(palm,direction,*tip))
        thickness = (2.9 if 7 <= tick <= 9 else 2.0) * progress
        inner.append(edge_point(palm,direction,tip[0]-thickness,tip[1]))
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
    # Rows 0–3 face right, 4–7 face left. Row 8 stores the two matching
    # body cutouts, so the original arm cannot remain under the moving one.
    atlas = Image.new("RGBA", (24 * 80, 9 * 80))
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
        atlas.paste(body,(far*80,8*80))
        # On the far shoulder the wind-up arcs around the outside of the cheek.
        headings = (-45,-60,-76,-89,-96,-88,-72,-44) + SWORD_ANGLES[8:] if far else SWORD_ANGLES
        for tick,heading in enumerate(headings):
            moving = tick < len(wrists)
            grip = wrists[tick] if moving else (FAR_PALMS if far else NEAR_PALMS)[11]
            for row,kind in enumerate(WORN_ORDER[:4]):
                cel = sword_arm(grip,far) if moving else Image.new("RGBA",(80,80))
                cutting_trail(cel,kind,grip,heading,headings[max(0,tick-1)],tick)
                blade(cel,kind,grip,heading)
                if moving:
                    # A compact knuckle patch leaves the pommel and guard exposed.
                    cel.alpha_composite(knuckles,(grip[0]-4,grip[1]-4))
                    if far:
                        cel.putalpha(ImageChops.subtract(cel.getchannel("A"),body.getchannel("A")))
                else:
                    hold_in_hand(cel,ready,grip)
                atlas.paste(cel,(tick*80,(4*far+row)*80))
    atlas.save(ASSETS/"swing-weapons.png",optimize=True)


def run():
    with Image.open(ASSETS / "hero-adventurer.png") as source:
        hero = source.convert("RGBA")
    if hero.size != (320,560):
        raise ValueError("Expected a 4×7 adventurer atlas with 80px cells")
    atlas = Image.new("RGBA",(28*80,(len(WORN_ORDER)+4+len(ACCESSORIES))*80))
    for pose in range(28):
        x,y = pose%4*80, pose//4*80
        base = hero.crop((x,y,x+80,y+80))
        action,frame,*_=CELS[pose]
        hair=layers(30000,action,frame)
        ANCHORS[pose]={"navel":match_anchor(base,layers(1060026,action,frame)["pants"]),
                       "brow":match_anchor(base,next(iter(hair.values())))}
        for row,kind in enumerate(WORN_ORDER):
            atlas.paste(overlay(kind,pose,base),(pose*80,row*80))
        for row, kind in enumerate(WORN_ORDER[:4],len(WORN_ORDER)):
            atlas.paste(overlay(kind,pose,base,far=True),(pose*80,row*80))
        for row,kind in enumerate(ACCESSORIES,len(WORN_ORDER)+4):
            atlas.paste(overlay(kind,pose,base),(pose*80,row*80))
    atlas.save(OUT,optimize=True)
    swing_weapons(hero)


if __name__=="__main__":
    run()
