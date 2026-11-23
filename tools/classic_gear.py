"""MapleStory GMS v83 item IDs, decoded from the public maplestory.io item API."""
import base64
from functools import lru_cache
from io import BytesIO
import json
from pathlib import Path
from tempfile import gettempdir
from urllib.request import Request, urlopen

from PIL import Image

ITEM_IDS = dict(twig=1302022, bronze=1302008, blade=1302005, sunblade=1302020,
                bow=1452000, nightbow=1452022, wand=1372005, tidewand=1372012,
                coat=1040003, shell=1040009, glasscoat=1040024, crabguard=1040025,
                cap=1002026, dew=1112000, prism=1122000, shimmer=1122007, moonseal=1142000)
ICON_IDS = {0:1302022,1:1452000,2:1372005,4:2000000,5:2000003,7:4031041,
            8:4000013,9:4000001,10:4000004,11:4000138,12:4010002,13:4000175,
            14:1040003,15:4001006,16:1302008,17:1302005,18:1302020,19:1452022,
            20:1372012,21:1040009,22:1040024,23:1040025,24:1112000,25:1142000,
            26:1122000,27:1122007,28:1002026}

@lru_cache(None)
def fetch(item, icon=False):
    cache = Path(gettempdir()) / 'maplee-gms83-gear'
    cache.mkdir(exist_ok=True)
    path = cache / (str(item) + ('.png' if icon else '.json'))
    if not path.exists():
        url = 'https://maplestory.io/api/GMS/83/item/' + str(item) + ('/icon' if icon else '')
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}), timeout=25) as response:
            data = response.read()
        if icon:
            Image.open(BytesIO(data)).verify()
        else:
            json.loads(data)
        path.write_bytes(data)
    return Image.open(path).convert('RGBA') if icon else json.loads(path.read_bytes())

@lru_cache(None)
def layers(item, action, frame):
    books = fetch(item)['frameBooks']
    book = books.get(action) or books.get('default') or books['stand1']
    parts = book['frames'][frame % len(book['frames'])]['effects']
    result = {}
    for name,part in parts.items():
        if not part.get('image'):
            continue
        im = Image.open(BytesIO(base64.b64decode(part['image']))).convert('RGBA')
        anchor,offset = next(iter(part['mapOffset'].items()))
        pivot = tuple(part['originOrZero'][axis] + offset[axis] for axis in ('x','y'))
        result[name] = (im,anchor,pivot)
    return result
