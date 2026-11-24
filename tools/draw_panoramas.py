"""Bake one continuous, pixel-sized backdrop per biome from Maplee's landscape plates.

Overlapping pieces follow a low-contrast cut down the scene, including where the
last piece meets the first. The game displays the finished pixels at native size.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


ASSETS = Path(__file__).resolve().parents[1] / "assets"
HEIGHT = 468
OVERLAP = 112


def take_piece(source, span, x, top, source_height, mirror):
    target_width = span + OVERLAP
    source_width = round(target_width * source_height / HEIGHT)
    visible = source.crop((x, top, x + source_width, top + source_height))
    if mirror:
        visible = ImageOps.mirror(visible)
    return visible.resize((target_width, HEIGHT), Image.Resampling.LANCZOS)


def landscape_cut(left, right):
    """Return a curved boundary that follows similar pixels in both paintings."""
    a = np.asarray(left.filter(ImageFilter.GaussianBlur(2)), dtype=np.int32)
    b = np.asarray(right.filter(ImageFilter.GaussianBlur(2)), dtype=np.int32)
    distance = np.abs(a-b).sum(axis=2)
    height, width = distance.shape
    # Discourage the path from sticking to either edge of the shared strip.
    cost = distance + abs(np.arange(width)-width//2)[None, :] * .32
    candidates = np.zeros((height, width), dtype=np.int16)
    offsets = np.arange(-2, 3)
    running = cost[0]
    for y in range(1, height):
        padded = np.pad(running, 2, constant_values=1e8)
        options = np.stack([padded[2+d:2+d+width] + abs(d)*2.8 for d in offsets])
        best = options.argmin(axis=0)
        candidates[y] = offsets[best]
        running = cost[y] + options[best, np.arange(width)]
    edge = np.empty(height, dtype=int)
    edge[-1] = running.argmin()
    for y in range(height-1, 0, -1):
        edge[y-1] = edge[y] + candidates[y, edge[y]]
    # A few pixels soften color transitions before the final pixel quantization.
    # Fine edges can follow a rock or a tree, but a whole mountain or river
    # bank needs to meet over a wider distance. Blend broad tones separately.
    a = np.asarray(left, dtype=float)
    b = np.asarray(right, dtype=float)
    out = np.zeros_like(a)
    for radius, fade in ((2, 6), (8, 22), (24, 55)):
        small_a = np.asarray(left.filter(ImageFilter.GaussianBlur(radius)), dtype=float)
        small_b = np.asarray(right.filter(ImageFilter.GaussianBlur(radius)), dtype=float)
        boundary = np.clip(edge, fade//2, width-1-fade//2)
        mask = np.clip((np.arange(width)[None, :]-boundary[:, None])/fade+.5, 0, 1)[:,:,None]
        out += (a-small_a)*(1-mask)+(b-small_b)*mask
        a, b = small_a, small_b
    mask = np.linspace(0,1,width)[None,:,None]
    out += a*(1-mask)+b*mask
    return Image.fromarray(np.clip(out,0,255).astype("uint8"))


def ring(source, places):
    pieces = [take_piece(source, *place) for place in places]
    spans = [p[0] for p in places]
    result = Image.new("RGB", (sum(spans), HEIGHT))
    x = 0
    for index, (span, piece) in enumerate(zip(spans, pieces)):
        previous = pieces[index-1]
        a = previous.crop((previous.width-OVERLAP, 0, previous.width, HEIGHT))
        b = piece.crop((0, 0, OVERLAP, HEIGHT))
        result.paste(landscape_cut(a, b), (x, 0))
        result.paste(piece.crop((OVERLAP, 0, span, HEIGHT)), (x+OVERLAP, 0))
        x += span
    return result


def remove_moon(source):
    # Save the illuminated crescent as an independent landmark so that
    # repeating mountain ridges do not also repeat a sky full of moons.
    clean = source.copy()
    region = (503, 6, 634, 130)
    sky = source.crop((351, 6, 482, 130)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    soft = Image.new("L", sky.size)
    draw = ImageDraw.Draw(soft)
    draw.ellipse((5, 4, 125, 116), fill=255)
    soft = soft.filter(ImageFilter.GaussianBlur(6))
    clean.paste(sky, region[:2], soft)
    original = np.array(source.crop(region), dtype=float)
    base = np.array(clean.crop(region), dtype=float)
    contrast = (original-base).max(axis=2)
    # Restore only the illuminated surface and its edge pixels.
    lunar_alpha = np.clip((contrast-18)/65, 0, 1) * np.asarray(soft)/255
    moon = source.crop(region).convert("RGBA")
    moon.putalpha(Image.fromarray((lunar_alpha*255).astype("uint8")))
    return clean, moon


def windmill(image, x, y):
    """A tiny distant grain mill overlooks the meadow."""
    draw = ImageDraw.Draw(image)
    draw.polygon([(x-8,y), (x-5,y-22), (x+3,y-24), (x+8,y)], fill="#d8c88a")
    draw.polygon([(x+1,y), (x+1,y-20), (x+4,y-23), (x+8,y)], fill="#819573")
    draw.polygon([(x-8,y-21), (x-1,y-28), (x+7,y-22)], fill="#957e6c")
    draw.rectangle((x-3,y-10,x,y-2), fill="#687f73")
    hub = (x-1,y-19)
    for dx, dy in ((-13,-10),(10,-13),(13,10),(-10,13)):
        tip=(hub[0]+dx,hub[1]+dy)
        draw.line((hub,tip), fill="#715c55", width=2)
        nx, ny = dx*.19, dy*.19
        blade=[(tip[0],tip[1]),(tip[0]-ny,tip[1]+nx),
               (hub[0]+dx*.4-ny,hub[1]+dy*.4+nx),(hub[0]+dx*.4,hub[1]+dy*.4)]
        draw.polygon(blade, fill="#ece1b6")


def native_pixels(image, name):
    # Consolidate busy isolated marks into solid color clusters. A one-pixel
    # rim is preserved around sharper contours instead of adding dither noise.
    image = image.filter(ImageFilter.MedianFilter(3))
    base = image.resize((image.width//2, HEIGHT//2), Image.Resampling.BOX)
    base = base.quantize(colors=152, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    base = base.resize(image.size, Image.Resampling.NEAREST)
    # Cut the circular field within a native pixel cluster. It makes the first
    # and final columns bit-identical without artificially flattening the seam.
    result = ImageChops.offset(base, 1, 0)
    result.save(ASSETS / name, optimize=True)
    return result


def build():
    day = Image.open(ASSETS / "landscape.jpg").convert("RGB")
    valley = ring(day, [
        (1104, 0, 3, 525, False), (654, 373, 7, 525, True), (642, 70, 0, 532, True),
    ])
    windmill(valley, 334, 342)
    native_pixels(valley, "daylight-panorama.png")

    depths = Image.open(ASSETS / "depths.jpg").convert("RGB")
    cave = depths.crop((0, 0, 700, 467))
    cavern = ring(cave, [
        (720, 0, 45, 385, False), (664, 102, 32, 347, True), (696, 121, 96, 319, False),
    ])
    native_pixels(cavern, "cavern-panorama.png")

    ridge, moon = remove_moon(depths.crop((700, 0, 1400, 467)))
    hills = ring(ridge, [
        (720, 0, 4, 386, False), (664, 100, 8, 355, True), (696, 82, 8, 350, True),
    ])
    hills.paste(moon, (419, 2), moon)
    native_pixels(hills, "highland-panorama.png")


if __name__ == "__main__":
    build()
