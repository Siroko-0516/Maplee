"""Bake the inventory and drop atlas from GMS v83 icons."""
from pathlib import Path
from PIL import Image
from classic_gear import ICON_IDS, fetch

OUT = Path(__file__).resolve().parents[1] / "assets"


def run():
    previous = Image.open(OUT / "item-icons.png").convert("RGBA")
    atlas = Image.new("RGBA", (256,128))
    for i in range(32):
        if i in ICON_IDS:
            icon = fetch(ICON_IDS[i],icon=True).copy()
            icon = icon.crop(icon.getbbox())
            icon.thumbnail((32,32),Image.Resampling.NEAREST)
        elif i < 16:
            x,y=i%4*24,i//4*24
            icon=previous.crop((x,y,x+24,y+24))
        else:
            continue
        atlas.alpha_composite(icon,(i%8*32+(32-icon.width)//2,i//8*32+(32-icon.height)//2))
    atlas.save(OUT / "equipment.png",optimize=True)


if __name__ == "__main__":
    run()
