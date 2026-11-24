"""Paint vertical camera overscan around Maplee's finished horizontal panoramas.

The middle frame is copied exactly. New terrain and sky use a periodic field
painted at the scene's native pixel pitch, constrained by its boundary colors.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ASSETS = Path(__file__).resolve().parents[1] / "assets"
TOP, ORIGINAL_HEIGHT, BOTTOM = 144, 468, 64
BIOMES = (
    ("daylight-panorama", "meadow", 1203, 2),
    ("cavern-panorama", "cave", 439, 2),
    ("highland-panorama", "ridge", 905, 2),
    ("ember-grove", "grove", 870, 3),
    ("lantern-quay", "quay", 520, 3),
)


def periodic_noise(rng, x, y, width, x_step, y_step):
    """Smooth value noise, including the interval wrapping back to x=0."""
    columns = max(2, round(width / x_step))
    gx, gy = np.broadcast_arrays(x * columns / width, y / y_step)
    gy = gy - np.floor(gy.min())
    cells = rng.uniform(-1, 1, (int(gy.max())+2, columns))
    ix, iy = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx-ix, gy-iy
    fx, fy = fx*fx*(3-2*fx), fy*fy*(3-2*fy)
    upper = cells[iy, ix%columns]*(1-fx)+cells[iy, (ix+1)%columns]*fx
    lower = cells[iy+1, ix%columns]*(1-fx)+cells[iy+1, (ix+1)%columns]*fx
    return upper*(1-fy)+lower*fy


def edge_brush(row, x, y, displacement, wavelength, spread):
    # Read only the contact color, never a stretched or reflected source strip.
    width = len(row)
    reach = np.minimum(y*spread, 30)
    shift = np.sin(x*2*np.pi*wavelength/width+y/48)*displacement*y
    center = x + shift
    sample = np.zeros((*center.shape, 3))
    for dx, weight in ((-1,.14),(-.46,.21),(0,.3),(.46,.21),(1,.14)):
        index = np.rint(center+dx*reach).astype(int)%width
        sample += row[index]*weight
    return sample


def mix(a, b, opacity):
    return a + (b-a)*np.asarray(opacity)[...,None]


def sky(row, biome, rng, x, d, width):
    high, low = {
        "meadow": ((41,174,231), (34,222,237)),
        "ridge": ((25,26,72), (50,42,102)),
        "grove": ((16,24,48), (31,41,72)),
        "quay": ((10,19,42), (19,35,64)),
    }[biome]
    t = np.broadcast_to(d/TOP, (len(d),len(x[0])))
    color = mix(np.array(low), np.array(high), t**.83)
    broad = periodic_noise(rng, x, d, width, 210, 48)
    if biome == "meadow":
        # Thin, tapered cirrus high above the already painted cumulus line.
        wisps = periodic_noise(rng, x, d+broad*8, width, 126, 6)
        coverage = np.maximum(0, wisps-.30)*np.maximum(0,broad+.22)
        color = mix(color, np.array((193,245,255)), np.minimum(.55,coverage*.9)*t**.32)
    elif biome == "ridge":
        dust = periodic_noise(rng, x, d+.6*broad*d, width, 156, 15)
        color = mix(color, np.array((102,73,130)), np.maximum(0,dust-.25)*.29)
    # Continue the highland's warm cloud tops before they taper into clear sky.
    # The almost uniformly colored dusk sky can meet its sparse star tips directly.
    contact = edge_brush(row, x, d, 1.15 if biome=="ridge" else .45, 3, .7)
    if biome == "ridge":
        age = d/(41+16*broad)
    else:
        age = d/11
    return mix(color, contact, np.exp(-age))


def ceiling(row, rng, x, d, width):
    large = periodic_noise(rng,x,d,width,123,57)
    planes = periodic_noise(rng,x+large*21,d+large*13,width,42,23)
    chips = periodic_noise(rng,x,d+planes*9,width,11,7)
    ribbons = np.sin(x*2*np.pi*4/width+d/13+large*4+planes*.9)
    light = large*.34+planes*.29+chips*.11 + ribbons*.13
    basalt = np.array(((12,14,40),(19,21,53),(26,28,70),(31,34,82),
                       (38,39,94),(43,48,103),(51,57,116),(63,67,133)))
    tone = np.clip(np.floor((light+.65)*6),0,len(basalt)-1).astype(int)
    color = basalt[tone].astype(float)
    # Light grazes narrow strata and the occasional crystal inclusion.
    lode = (abs(ribbons)<.07) & (planes>.03) & (large>.16)
    color[lode] += (12,15,26)
    contact = edge_brush(row,x,d,.64,6,.43)
    weight = np.exp(-d/(24+9*large))
    return mix(color,contact,weight)


def undergrowth(row, biome, rng, x, d, width):
    coarse = periodic_noise(rng,x,d,width,132,35)
    medium = periodic_noise(rng,x+coarse*7,d,width,32,12)
    fine = periodic_noise(rng,x,d+medium*5,width,7,5)
    tone = {
        "meadow": (46,94,68), "cave": (24,24,61), "ridge": (48,44,80),
        "grove": (40,56,66), "quay": (30,45,61),
    }[biome]
    stroke = np.round(coarse*4+medium*3+fine*2)
    color = np.array(tone) + stroke[:,:,None]*np.array((1.7,2,1.8))
    if biome == "quay":
        # Thin stone joints in the silhouette below the wharf.
        joints = (np.mod(d+2*coarse,21)<2) & (abs(medium)<.28)
        color[joints] -= (5,7,9)
    if biome == "grove":
        leaf = (fine>.56) & (medium>.12)
        color[leaf] += (5,9,7)
    contact = edge_brush(row,x,d,.96,7,.38)
    return mix(color,contact,np.exp(-d/(29+9*coarse)))


def paint_band(source, biome, seed, pitch, height, above):
    width = source.width
    row = np.array(source.crop((0,0 if above else source.height-1,width,
                                1 if above else source.height)).convert("RGB"))[0]
    rng = np.random.default_rng(seed)
    x = np.arange(0,width,pitch)[None,:]
    d = np.arange(0,height,pitch)[:,None]
    if above and biome == "cave":
        pixels = ceiling(row,rng,x,d,width)
    elif above:
        pixels = sky(row,biome,rng,x,d,width)
    else:
        pixels = undergrowth(row,biome,rng,x,d,width)
    pixels = np.clip(np.rint(pixels),0,255).astype("uint8")
    if above and biome in ("ridge","grove","quay"):
        points = Image.fromarray(pixels)
        draw = ImageDraw.Draw(points)
        for _ in range(width//30 if biome=="ridge" else width//47):
            sx = int(rng.integers(2,points.width-2))
            sy = int(rng.integers(2,points.height-2))
            if biome == "ridge":
                glow = (rng.choice((159,195,228)),159,199)
            else:
                glow = (200,183,155) if biome=="grove" else (181,164,135)
            draw.point((sx,sy),fill=tuple(map(int,glow)))
            if rng.random()<.08:
                draw.point((sx,sy-1),fill=(107,108,145))
                draw.point((sx+1,sy),fill=(93,99,128))
        pixels = np.array(points)
    # For a non-divisible band, crop the last pixel cell; its size never changes.
    pixels = pixels.repeat(pitch,axis=0).repeat(pitch,axis=1)[:height,:width].copy()
    pixels[0] = row
    pixels[:,-1] = pixels[:,0]
    return Image.fromarray(pixels[::-1] if above else pixels)


def bake(name, biome, seed, pitch):
    with Image.open(ASSETS/(name+".png")) as source:
        if source.height != ORIGINAL_HEIGHT:
            raise ValueError(f"Unexpected middle-frame height in {name}")
        top = paint_band(source,biome,seed,pitch,TOP,True)
        bottom = paint_band(source,biome,seed+1,pitch,BOTTOM,False)
        if source.mode == "P":
            # Give the overscan its own palette entries; the original pixels
            # retain their exact palette indices as well as their decoded color.
            used = max(index for _,index in source.getcolors(256))+1
            bands = Image.new("RGB",(source.width,TOP+BOTTOM))
            bands.paste(top); bands.paste(bottom,(0,TOP))
            extension_palette = bands.quantize(256-used, dither=Image.Dither.NONE)
            palette = source.getpalette()[:used*3]+extension_palette.getpalette()[:(256-used)*3]
            palette = palette+[0]*(768-len(palette))
            key = Image.new("P",(1,1))
            key.putpalette(palette)
            top = top.quantize(palette=key,dither=Image.Dither.NONE)
            bottom = bottom.quantize(palette=key,dither=Image.Dither.NONE)
            result = Image.new("P",(source.width,TOP+ORIGINAL_HEIGHT+BOTTOM))
            result.putpalette(palette)
            for band, y, sy in ((top, TOP-1, 0),(bottom, 0, source.height-1)):
                band.paste(source.crop((0,sy,source.width,sy+1)),(0,y))
        else:
            result = Image.new("RGB",(source.width,TOP+ORIGINAL_HEIGHT+BOTTOM))
        result.paste(top); result.paste(source,(0,TOP)); result.paste(bottom,(0,TOP+ORIGINAL_HEIGHT))
        if result.crop((0,TOP,source.width,TOP+ORIGINAL_HEIGHT)).convert("RGB").tobytes()!=source.convert("RGB").tobytes():
            raise ValueError(f"Original frame changed in {name}")
        if result.crop((0,0,1,result.height)).tobytes()!=result.crop((result.width-1,0,result.width,result.height)).tobytes():
            raise ValueError(f"Horizontal seam in {name}")
        result.save(ASSETS/(name+"-tall.png"),optimize=True)


if __name__ == "__main__":
    for scene in BIOMES:
        bake(*scene)
