"""Bake the pictured classic beginner into Maplee's right-facing 80px cells.

The private game serves the baked atlas. Only this optional asset rebuild
contacts the public maplestory.io renderer (GMS v83, MapleStory / NEXON).
"""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PARTS = (2000, 12000, 20000, 30000, 1040036, 1060026)
# action, source frame, face expression, distance above the sole baseline
CELS = (
    ("stand1", 0, "default", 0), ("stand1", 1, "default", 0),
    ("stand1", 2, "default", 0), ("stand1", 1, "blink", 0),
    *(("walk1", i, "default", 0) for i in range(4)),
    *(("swingO1", i, "default", 0) for i in range(3)), ("alert", 1, "default", 0),
    ("jump", 0, "default", 4), ("jump", 0, "default", 2),
    ("alert", 2, "hit", 0), ("alert", 0, "default", 0),
    *(("shoot1", i, "default", 0) for i in range(3)), ("alert", 1, "default", 0),
    *(("swingO2", i, "default", 0) for i in range(3)), ("alert", 1, "default", 0),
    *(("ladder", i, "default", 0) for i in (0, 0, 1, 1)),
)


def get_frame(key):
    action, number, expression = key
    parts = [dict(itemId=item, version="83", region="GMS") for item in PARTS]
    parts[2]["animationName"] = expression
    path = ",".join(json.dumps(part, separators=(",", ":")) for part in parts)
    url = f"https://maplestory.io/api/Character/{quote(path, safe=',')}/{action}/{number}"
    with urlopen(Request(url, headers={"User-Agent": "Maplee asset builder"}), timeout=30) as response:
        raw = response.read()
    with Image.open(BytesIO(raw)) as decoded:
        if decoded.format != "PNG":
            raise ValueError(f"Expected a transparent PNG for {key}")
        frame = decoded.convert("RGBA")
    bounds = frame.getchannel("A").getbbox()
    if not bounds:
        raise ValueError(f"Empty character cel: {key}")
    return frame.crop(bounds).transpose(Image.Transpose.FLIP_LEFT_RIGHT)


def run():
    keys = list(dict.fromkeys(cel[:3] for cel in CELS))
    with ThreadPoolExecutor(max_workers=4) as pool:
        frames = dict(zip(keys, pool.map(get_frame, keys)))
    # Pin the matched standing pose so a renderer fallback cannot silently change the face.
    expected_stand = "77f9fa1f896ae910696f56737934baeed54a21b6c571af195df2b4a592c5bfb8"
    if sha256(frames["stand1", 0, "default"].tobytes()).hexdigest() != expected_stand:
        raise ValueError("The renderer returned a different beginner appearance")
    sheet = Image.new("RGBA", (320, 560))
    for i, (action, number, expression, lift) in enumerate(CELS):
        frame = frames[action, number, expression]
        if frame.width > 80 or frame.height + lift > 75:
            raise ValueError(f"Unaligned cel: {action}/{number}")
        x = i % 4 * 80 + (80 - frame.width) // 2
        y = i // 4 * 80 + 75 - lift - frame.height
        sheet.paste(frame, (x, y))
    sheet.save(ROOT / "assets/hero-adventurer.png", optimize=True)


if __name__ == "__main__":
    run()
