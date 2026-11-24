"""Paint reusable original pixel tiles and mine decorations for Maplee."""

from pathlib import Path
from random import Random

from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parents[1] / "assets"
SHALE = ("#241d20", "#403039", "#604b47", "#896a5a", "#ac8a6f", "#cab398")
RUSSET = ("#30212c", "#4b3034", "#764947", "#9f695c", "#c48b79", "#e0ad8e")
OCHRE = ("#2c281d", "#4d422c", "#76603d", "#9e8050", "#c4a468", "#e2c689")
FERN = ("#233520", "#30462a", "#4c692f", "#70913a", "#a6af51", "#d6d074")
ALPINE = ("#1d3422", "#304f2a", "#537334", "#789d4d", "#a8b760", "#d4d785")
DRY_GRASS = ("#353923", "#4d5327", "#6b702e", "#909242", "#b5b554", "#e0d67d")


def rock(draw, rng, x, y, w, h, palette, tile_edge=False):
    shade = rng.choice((2,3,3,4))
    left_high = y + rng.randint(3,9)
    ridge = [(x,left_high),(x+w//4,y+1),(x+w*3//5,y),(x+w-2,y+5),(x+w,y+h//2)]
    shape = [*ridge,(x+w-4,y+h-4),(x+w//2,y+h),(x+3,y+h-4),(x-2,y+h//2)]
    draw.polygon(shape, fill=palette[shade], outline=palette[0])
    crest = [(x+4,left_high),(x+w//4+1,y+2),(x+w*3//5,y+1),(x+w-5,y+6),(x+w//2,y+h//3),(x+7,y+h//2)]
    draw.polygon(crest, fill=palette[shade+1 if shade < 5 else 5])
    draw.line([(x+5,y+h-6),(x+w//2,y+h-2),(x+w-6,y+h-6),(x+w-2,y+h//2)], fill=palette[1], width=2)
    if not tile_edge:
        draw.line([(x+w//2,y+h//3),(x+w//2-4,y+h//2+3),(x+w//2-1,y+h-5)], fill=palette[2])
    for _ in range(15):
        sx = x+rng.randint(w//4,w*3//4)
        sy = y+rng.randint(h//3,h*2//3)
        draw.line((sx,sy,sx+rng.randrange(1,4),sy), fill=palette[rng.choice((2,3,4,shade))])


def terrain(name, palette, grass, seed):
    width, height = 192, 168
    picture = Image.new("RGB", (width,height), palette[1])
    draw = ImageDraw.Draw(picture)
    rng = Random(seed)
    for row in range(6):
        x = -rng.randint(18,30)
        while x < width:
            w = rng.randint(23,40)
            y = 9 + row * 30 + rng.randint(-6,5)
            rock(draw,rng,x,y,w,rng.randint(25,39),palette,x < 0 or x+w >= width)
            x += w-2
    profile = [12 + rng.choice((0,1,1,2,2,3)) for _ in range(width)]
    draw.polygon([(0,0),(width-1,0),*((x,profile[x]) for x in reversed(range(width)))], fill=grass[0])
    for x in range(-5,width,5):
        y = profile[max(0,x)]
        draw.polygon(((x,-1),(x+7,0),(x+8,y-4),(x+4,y+1),(x+1,y-2)),
                     fill=rng.choice(grass[1:4]))
        draw.line((x+1,2,x+5,1,x+8,3), fill=rng.choice(grass[3:6]), width=2)
        draw.line((x+1,4,x+2,y-4,x+4,y-2), fill=grass[2])
        if rng.randrange(4) == 0:
            yy = rng.randint(23,145)
            for side in (-1,1):
                draw.line((x,yy,x+4*side,yy-rng.randint(2,6)),fill=rng.choice(grass[:3]))
    picture.save(ASSETS/name, optimize=True)


WOOD = ("#251f29", "#553732", "#805743", "#ab815c", "#d5af7a", "#efd1a0")


def beam(draw, x, y, end, bottom, width=8):
    draw.line((x,y,end,bottom), fill=WOOD[0], width=width+3)
    draw.line((x,y,end,bottom), fill=WOOD[2], width=width)
    draw.line((x-1,y-2,end-1,bottom-2), fill=WOOD[4], width=2)


def rivet(draw, x, y):
    draw.rectangle((x-2,y-2,x+2,y+2),fill=WOOD[0])
    draw.point((x-1,y-1),fill=WOOD[5])


def quarry_atlas():
    out = Image.new("RGBA",(512,196))
    tower = Image.new("RGBA",(144,196))
    draw = ImageDraw.Draw(tower)
    for y in range(48,190,34):
        beam(draw,43,y,98,min(191,y+34))
        beam(draw,98,y,43,min(191,y+34))
        beam(draw,38,min(y+34,190),110,min(y+34,190))
    for x in (38,103):
        beam(draw,x,43,x,194,12)
        for y in range(50,190,34):
            rivet(draw,x,y)
    for y in (31,40,49):
        beam(draw,15,y,127,y,7)
    for x in range(20,130,18):
        beam(draw,x,28,x-3,51,4)
    out.paste(tower,(0,0))

    hoist = Image.new("RGBA",(164,192))
    draw = ImageDraw.Draw(hoist)
    beam(draw,36,45,36,192,12)
    beam(draw,67,45,67,192,12)
    for y in range(56,175,35):
        beam(draw,36,y+25,67,y,7)
    beam(draw,17,40,153,40,12)
    beam(draw,42,42,132,39,4)
    beam(draw,67,66,109,40,8)
    for x in (21,41,67,108,144):
        rivet(draw,x,39)
    draw.line((132,47,132,117),fill="#caad79",width=2)
    draw.ellipse((127,113,138,124), fill="#867e72", outline=WOOD[0], width=2)
    draw.arc((126,119,140,134),0,285,fill="#d4c0a3",width=3)
    out.paste(hoist,(144,0))

    arch = Image.new("RGBA",(204,147))
    draw = ImageDraw.Draw(arch)
    rng = Random(765)
    for x in (34,133):
        for y in (52,78,103,125):
            rock(draw,rng,x,y,39,28,OCHRE)
    draw.arc((38,10,172,115), 180, 360, fill=OCHRE[0], width=25)
    draw.arc((42,12,170,112), 180, 360, fill=OCHRE[3], width=19)
    draw.arc((43,13,169,109), 180, 360, fill=OCHRE[5], width=6)
    for x,y in ((45,50),(61,29),(81,19),(105,15),(129,20),(150,30),(166,48)):
        draw.line((x,y,x+3,y+12),fill=OCHRE[1],width=3)
    for x,y in ((13,120),(161,130),(153,122)):
        rock(draw,rng,x,y,27,19,OCHRE)
    out.paste(arch,(308,0))
    out.save(ASSETS/"quarry-scenery.png", optimize=True)


if __name__ == "__main__":
    terrain("grass-cliff.png", SHALE, FERN, 907)
    terrain("copper-ground.png", RUSSET, ALPINE, 490)
    terrain("seed-ground.png", OCHRE, FERN, 511)
    terrain("quarry-ground.png", OCHRE, DRY_GRASS, 238)
    quarry_atlas()
