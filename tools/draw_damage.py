"""Pack the classic GMS v83 BasicEff damage glyphs on a native pixel grid."""
import base64
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import json
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image

FONTS = ("NoRed1", "NoRed0", "NoViolet1", "NoViolet0")
URL = "https://maplestory.io/api/wz/GMS/83/Effect/BasicEff.img/"


def glyph(key):
    with urlopen(Request(URL + key, headers={"User-Agent":"Mozilla/5.0"}), timeout=30) as response:
        data = json.load(response)
    image = Image.open(BytesIO(base64.b64decode(data["value"]))).convert("RGBA")
    return image.crop(image.getbbox())


if __name__ == "__main__":
    sheet = Image.new("RGBA", (480, 192))
    with ThreadPoolExecutor(max_workers=6) as pool:
        for index, image in enumerate(pool.map(glyph, (f"{font}/{digit}" for font in FONTS for digit in range(10)))):
            row, digit = divmod(index, 10)
            if max(image.size) > 48:
                raise ValueError(image.size)
            sheet.paste(image, (digit*48 + (48-image.width)//2, row*48 + 48-image.height))
    sheet.save(Path(__file__).resolve().parents[1] / "assets/damage.png", optimize=True)
