"""Repack classic interface artwork from the maplestory.io public WZ API.

KMS 284 assets are from Nexon's MapleStory. Window content is drawn separately
so Maplee's localized labels, character sheet and actions stay live in-game.
"""
import argparse
import base64
import io
import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://maplestory.io/api/wz/KMS/284/UI/"
STAT = "UIWindow2.img/Stat/main/"
ITEM = "UIWindow2.img/Item/"
STATUS = "StatusBar3.img/mainBar/"
MINIMAP = "UIWindow2.img/MiniMap/MaxMap/"
WINDOWS = {
    "character": STAT, "inventory": "UIWindow2.img/Equip/character/",
    "skills": "UIWindow2.img/Skill/main/", "journal": "UIWindow2.img/Quest/list/",
}


def pack(cache):
    cache.mkdir(exist_ok=True, parents=True)

    @lru_cache(maxsize=None)
    def source(path):
        dest = cache / (path.replace("/", "_").replace(":", "_") + ".png")
        if not dest.is_file():
            url = SOURCE + quote(path, safe="/:")
            with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as response:
                encoded = json.load(response)["value"]
            dest.write_bytes(base64.b64decode(encoded))
        with Image.open(dest) as im:
            return im.convert("RGBA")

    pieces = {}
    sheet = source(STAT+"backgrnd")
    # Reassemble the named frame without its fixed text or fixed body height.
    outer = Image.new("RGBA",(48,48))
    for x,sx in [(0,0),(24,sheet.width-24)]:
        for y,sy,sh in [(0,0,24),(24,sheet.height-24,24)]:
            outer.paste(sheet.crop((sx,sy,sx+24,sy+sh)),(x,y))
    pieces["chrome"] = outer
    paper = source(ITEM+"backgrnd2")
    inner = Image.new("RGBA",(60,60))
    for x,sx in [(0,0),(30,paper.width-30)]:
        for y,sy,h in [(0,0,30),(30,paper.height-30,30)]:
            inner.paste(paper.crop((sx,sy,sx+30,sy+h)),(x,y))
    pieces["paper"] = inner
    for name,prefix in WINDOWS.items():
        bg=source(prefix+"backgrnd")
        pieces[name+"_title"] = bg.crop((bg.width//2-58,3,bg.width//2+58,21))

    stats = source(STAT+"backgrnd2")
    row = stats.crop((5,6,195,24))
    row.paste(row.crop((51,0,52,18)).resize((48,18)),(3,0))
    pieces["stat_row"] = row
    for name,y in (("name",6),("job",24),("level",42),("exp",60),("hp",132),("mp",150)):
        pieces[name+"_label"] = stats.crop((7,y+1,52,y+16))
    pieces["ap"] = source(STAT+"backgrnd3")
    pieces["up"] = source(STAT+"BtStrUp/normal/0")
    pieces["up_off"] = source(STAT+"BtStrUp/disabled/0")
    pieces["detail_open"] = source(STAT+"BtDetailOpen/normal/0")
    pieces["detail_close"] = source(STAT+"BtDetailClose/normal/0")
    pieces["close"] = source("Basic.img/BtClose3/normal/0")
    for name,node in (("prev","prev0"),("next","next0"),("thumb","thumb0")):
        pieces[name] = source("Basic.img/VScr4/enabled/"+node)

    cells = source(ITEM+"backgrnd3")
    pieces["cell"] = cells.crop((3,5,35,37))
    button = source(STAT+"BtDetailOpen/normal/0").copy()
    button.paste(button.crop((2,0,3,16)).resize((59,16)),(4,0))
    pieces["button"] = button
    for name,node in (("tab_on","enabled"),("tab_off","disabled")):
        tab = source(ITEM+"Tab/"+node+"/0").copy()
        tab.paste(tab.crop((2,0,3,tab.height)).resize((24,tab.height)),(3,0))
        pieces[name] = tab

    pieces["panel_card"] = source("UIWindow2.img/Skill/main/skill0")
    pieces["hud"] = source(STATUS+"status/layer:cover")
    pieces["hud_hp"] = source(STATUS+"status/gauge/hp/layer:0")
    pieces["hud_mp"] = source(STATUS+"status/gauge/mp/layer:0")
    pieces["lv"] = source(STATUS+"status/layer:Lv")
    pieces["exp_strip"] = source(STATUS+"EXPBar/800/layer:gauge").crop((17,0,105,7))
    quick = source(STATUS+"quickSlot/backgrnd")
    pieces["quick_cell"] = quick.crop((0,0,32,32))
    pieces["hud_character"] = source(STATUS+"menu/button:Character/normal/0")
    pieces["hud_setting"] = source(STATUS+"menu/button:Setting/normal/0")
    pieces["hud_account"] = source(STATUS+"menu/button:Community/normal/0")
    plate = pieces["hud_character"].copy()
    plate.paste(plate.crop((4,3,5,30)).resize((23,27)),(6,3))
    pieces["hud_plate"] = plate

    for key in ("nw","n","ne","w","c","e","sw","s","se"):
        pieces["mini_"+key] = source(MINIMAP+key)
    pieces["quest_top"] = source("UIWindow2.img/QuestAlarm/backgrndmax")
    pieces["quest_body"] = source("UIWindow2.img/QuestAlarm/backgrndcenter")
    pieces["quest_end"] = source("UIWindow2.img/QuestAlarm/backgrndbottom")
    book = source("UIWindow2.img/MonsterBook/backgrnd")
    pieces["book_paper"] = book.crop((18,26,194,154))
    pieces["book_edge"] = book.crop((0,5,16,110))
    # A tightly packed atlas plus crop coordinates for the Python renderer.
    width=512
    x=y=height=0
    regions={}
    for key,im in pieces.items():
        if x+im.width>width:
            x,y,height=0,y+height+1,0
        regions[key]=(x,y,im.width,im.height)
        x+=im.width+1
        height=max(height,im.height)
    atlas=Image.new("RGBA",(width,y+height))
    for name,region in regions.items():
        atlas.paste(pieces[name],region[:2])
    atlas.save(ROOT/"assets/classic-ui.png",optimize=True)
    lines = ['"""Packed WZ interface source rectangles, generated by tools/import_classic_ui.py."""',
             "CLASSIC_REGIONS = {"]
    lines.extend(f"    {key!r}: {region!r}," for key,region in regions.items())
    lines.append("}")
    (ROOT/"maplee/classic_skin.py").write_text("\n".join(lines)+"\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=ROOT/".cache"/"classic-ui")
    pack(parser.parse_args().cache)
