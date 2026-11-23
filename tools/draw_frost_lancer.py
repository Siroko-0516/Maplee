"""Bake the original Frost Lantern outfit into thirty hand-registered poses."""
from PIL import ImageDraw
import draw_native_avatars as base

# Indices 49 onward are reserved in this sheet for the frost outfit.
FROST = (
    "263148", "43536e", "67748f", "8c99b1", "b1bed3", "d4ddec", "eef7ff",
    "233f56", "376784", "569ab5", "8ad5e3", "b8eff1",
    "4c2c3e", "773345", "a33c50", "d85c68", "ffad9e",
    "a97745", "f4c979", "fff0c0",
)
DARK, SLATE, DUSK, STEEL, OPAL, SILVER, SNOW = range(49,56)
FIN_SHADOW, FIN_BASE, FIN_BLUE, FIN_EDGE, FIN_LIGHT = range(56,61)
WINE, RUBY_SHADOW, RUBY, EMBER, BLUSH, BRASS, GOLD, PEARL = range(61,69)


def frost_head(pose, back):
    im = base.new((52,61))
    draw = ImageDraw.Draw(im)
    bob = (0,1,0,1)[pose%4] if pose < 8 else 0
    sway = (-3,0,3,0)[pose%4] if 4<=pose<=7 else 3 if pose in (9,12,13) else 0

    def poly(points, color, outline=None):
        draw.polygon(points, fill=color, outline=outline)

    def line(points, color, width=1):
        draw.line(points,fill=color,width=width)

    # The asymmetric ribbon ornaments rise from a split silver circlet.
    poly([(10,22),(9,14),(13,7),(18,3),(20,4),(19,11),(22,16),(22,23)],
         FIN_BASE,DARK)
    poly([(11,17),(14,10),(18,5),(17,11),(19,16),(19,19)],FIN_BLUE)
    line([(12,14),(16,8),(18,6)],FIN_LIGHT)
    poly([(26,20),(27,9),(32,7),(36,1),(40,1),(40,8),(37,16),(32,23)],
         FIN_BLUE,DARK)
    poly([(29,16),(30,10),(34,8),(38,3),(38,8),(34,15),(31,20)],FIN_EDGE)
    line([(31,10),(35,7),(38,3)],SNOW)
    line([(28,16),(32,13),(35,11)],FIN_SHADOW)

    # Wind shifts the long gathered tail by a few pixels as the wearer runs.
    tail = [(12,20),(8,25),(7,36),(8,42),(5+sway,47),(5+sway,51),
            (8+sway,55+bob),(13+sway,56+bob),(16+sway,53),
            (12+sway,52),(14+sway,49),(19+sway,44),(19,34),(24,25)]
    poly(tail,SLATE,DARK)
    poly([(11,26),(10,34),(12,40),(9+sway,47),(8+sway,51),
          (11+sway,52),(15+sway,47),(16+sway,41),(15,34),(19,25)],STEEL)
    line([(11,29),(11,36),(13,42),(10+sway,48)],SILVER,2)
    line([(14+sway,49),(15+sway,45),(16,40)],OPAL)
    line([(7+sway,50),(9+sway,54),(12+sway,54)],FIN_BLUE,2)
    poly([(9,36),(12,33),(15,36),(13,40),(10,40)],FIN_BLUE,DARK)
    draw.point((12,35),fill=FIN_LIGHT)

    # Thick bob, then the cheek and its inset shadows.
    poly([(9,28),(8,23),(11,17),(16,13),(24,11),(32,13),(40,16),
          (44,21),(45,31),(42,39),(38,43),(30,43),(25,47),(17,46),
          (11,42),(8,36)],DUSK,DARK)
    if not back:
        poly([(14,27),(22,23),(31,22),(39,25),(42,29),(41,39),(37,43),
              (31,46),(23,46),(18,43),(13,42),(11,38),(11,33)],4,DARK)
        poly([(16,30),(23,26),(30,25),(37,28),(40,31),(39,39),(36,43),
              (29,45),(24,44),(19,41),(16,38)],5)
        line([(20,43),(25,45),(31,45),(35,43)],3)
        line([(14,35),(15,34),(16,35),(15,38)],3)
        draw.point((12,39),fill=GOLD)
        for x,y,w in ((20,34,7),(35,33,5)):
            line([(x,y-2),(x+3,y-3),(x+w-1,y-2)],STEEL)
            if pose in (3,14):
                line([(x,y+2),(x+2,y+1),(x+w-1,y+2)],WINE)
                continue
            poly([(x,y+1),(x+1,y),(x+w-1,y),(x+w,y+2),
                  (x+w-1,y+5),(x+1,y+5),(x,y+4)],SNOW)
            poly([(x+2,y),(x+w-1,y),(x+w-1,y+4),(x+2,y+4)],RUBY_SHADOW)
            line([(x+2,y+3),(x+w-2,y+3)],EMBER)
            draw.point((x+2,y+1),fill=SNOW)
            line([(x,y+1),(x+1,y-1),(x+w-1,y-1),(x+w,y)],WINE)
        line([(26,43),(29,43)],BRASS)
        draw.point((33,39),fill=4)
        line([(18,39),(20,40)],BLUSH)
        line([(37,40),(39,39)],BLUSH)

    # Side-swept fringe has a dark secondary curl and two icy light bands.
    poly([(9,29),(10,22),(13,18),(18,15),(24,13),(32,14),(40,18),(44,24),
          (43,29),(39,28),(36,23),(36,30),(32,28),(29,25),(29,31),
          (24,29),(21,26),(20,32),(16,35),(16,29),(13,33),(13,40),
          (10,38),(9,33)],OPAL,DARK)
    poly([(10,27),(11,22),(15,18),(22,16),(27,16),(23,19),(20,23),
          (17,27),(14,30),(13,36),(11,34)],SILVER)
    poly([(17,25),(22,18),(28,16),(33,17),(38,20),(41,24),(36,22),
          (32,20),(31,23),(33,28),(28,26),(26,22),(24,25),(21,29)],SILVER)
    line([(12,25),(15,21),(18,20)],SNOW,2)
    line([(21,22),(24,19),(28,18),(32,18)],SNOW,2)
    line([(34,19),(38,21)],SNOW,2)
    line([(11,33),(11,36),(13,39)],STEEL)
    line([(23,26),(25,24),(26,21)],OPAL)
    line([(39,24),(41,28),(42,31),(41,34)],FIN_BLUE,2)
    line([(40,24),(42,28),(42,30)],FIN_EDGE)
    if back:
        poly([(9,27),(14,19),(23,17),(34,17),(41,22),(43,29),(42,36),
              (38,41),(32,44),(27,42),(21,45),(16,42),(11,38)],STEEL,DARK)
        poly([(12,25),(20,20),(30,19),(37,23),(38,30),(34,36),
              (27,39),(23,38),(18,41),(14,36)],OPAL)
        line([(16,24),(22,23),(29,22),(35,24)],SILVER,2)
        line([(13,31),(16,33),(19,36)],SILVER)
        poly([(24,35),(28,31),(32,35),(28,39)],FIN_BLUE,FIN_SHADOW)
        draw.point((28,34),fill=FIN_LIGHT)
    return im


def outfit(pose):
    frame = base.actor(0,1,pose,head_factory=frost_head)
    draw = ImageDraw.Draw(frame)
    cel = 8 if pose >= 28 else pose
    if not 24 <= cel <= 27:
        # Decorative clasps sit on the centre of the tunic, clear of the arms.
        dx = {8:3,9:-2,10:4,16:-3,17:-3,18:-3,22:2}.get(cel,0)
        dy = {8:2,9:-1,10:2,12:-4,13:-2,16:-1,17:-1,18:-1,22:1}.get(cel,0)
        y = 56 + dy + (cel % 2 if cel < 8 else 0)
        x = 39 + dx
        draw.polygon([(x-2,y),(x,y-2),(x+2,y),(x,y+2)],fill=GOLD,outline=BRASS)
        draw.point((x,y-1),fill=PEARL)
    return frame


def run():
    colors = base.PALETTE.copy()
    colors[2:7] = ["895c51","b78677","d4a89b","ebcabe","fae3d5"]
    colors[18:21] = ["3b4056","b1cadd","9fb5c8"]
    colors[28:31] = ["3c465c","6a7a92","e3edf3"]
    colors.extend(FROST)
    base.PAL = bytes.fromhex("".join(colors)).ljust(768,b"\0")
    atlas = base.new((30*80,80))
    for pose in range(30):
        atlas.paste(outfit(pose),(pose*80,0))
    atlas.save(base.ROOT/"assets/hero-frost-lancer.png",transparency=0,optimize=True)


if __name__ == "__main__":
    run()
