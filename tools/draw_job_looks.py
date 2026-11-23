"""Bake GMS v83 adventurer looks in Maplee's existing sole and hand coordinates."""
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from PIL import Image, ImageChops

from draw_hero import CELS, PARTS

ASSETS = Path(__file__).resolve().parents[1] / "assets"
LOOKS = {"guardian": (30070, 20001), "ranger": (30100, 20002), "mage": (30040, 20003)}
TILE = 96
PAD = 8


def render(key):
    hair, face, action, index, expression = key
    ids = list(PARTS)
    ids[2:4] = face, hair
    parts = [dict(itemId=i, region="GMS", version="83") for i in ids]
    parts[2]["animationName"] = expression
    path = ",".join(json.dumps(item, separators=(",", ":")) for item in parts)
    url = f"https://maplestory.io/api/Character/{quote(path, safe=',')}/{action}/{index}"
    with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as response:
        image = Image.open(BytesIO(response.read())).convert("RGBA")
    return image.crop(image.getbbox()).transpose(Image.Transpose.FLIP_LEFT_RIGHT)


def aligned(frame, base):
    # Hair affects the server's crop box. Register the feet using identical
    # lower-body pixels, allowing longer hair above the original tile.
    bottom = base.getbbox()[3]
    y = bottom - frame.height
    strip = frame.crop((0, frame.height-12, frame.width, frame.height))
    feet = base.crop((0, bottom-12, 80, bottom))
    x = feet.getbbox()[0] - strip.getbbox()[0]
    placed = Image.new("RGBA", (80,12))
    placed.paste(strip,(x,0))
    if placed.tobytes() != feet.tobytes():
        raise ValueError("Rendered legs no longer match the base pose")
    cell = Image.new("RGBA",(TILE,TILE))
    cell.paste(frame,(PAD+x,PAD+y))
    if cell.getbbox()[1] == 0:
        raise ValueError("Hair extends beyond the atlas cell")
    return cell


def run():
    base = Image.open(ASSETS/"hero-adventurer.png").convert("RGBA")
    swing = Image.open(ASSETS/"swing-weapons.png").convert("RGBA")
    for job, (hair,face) in LOOKS.items():
        keys = list(dict.fromkeys((hair,face,*cel[:3]) for cel in CELS))
        with ThreadPoolExecutor(max_workers=4) as pool:
            images = dict(zip(keys,pool.map(render,keys)))
        sheet = Image.new("RGBA",(4*TILE,8*TILE))
        for i, (action,index,expression,_) in enumerate(CELS):
            x, y = i%4*80,i//4*80
            original = base.crop((x,y,x+80,y+80))
            cell = aligned(images[hair,face,action,index,expression],original)
            sheet.paste(cell,(i%4*TILE,i//4*TILE))
            if i == 8:
                for far in range(2):
                    cut = swing.crop((far*80,640,far*80+80,720))
                    mask = ImageChops.subtract(original.getchannel("A"),cut.getchannel("A"))
                    without_arm = cell.copy()
                    without_arm.paste((0,0,0,0),(PAD,PAD,PAD+80,PAD+80),mask)
                    sheet.paste(without_arm,(far*TILE,7*TILE))
        sheet.save(ASSETS/f"hero-{job}.png",optimize=True)


if __name__ == "__main__":
    run()
