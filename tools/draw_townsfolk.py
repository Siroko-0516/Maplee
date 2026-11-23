"""Rebuild the classic NPC atlas from maplestory.io's GMS v83 render API.

The original MapleStory NPC artwork belongs to Nexon. Names correspond to
the same character IDs in the KMS database. Gameplay uses the bundled PNG.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
API = "https://maplestory.io/api/GMS/83/npc"
CELL = 96
COLUMNS = 12
ORIGIN = (48, 92)
# Each row follows the order of NPCS in maplee/content.py.
CLIPS = (
    (1010100, "blink"), (1011001, "stand"), (1012100, "stand"),
    (1002101, "stand"), (1012101, "stand"), (1001001, "stand"),
    (1002103, "eye"), (1022004, "stand"), (1022006, "stand"),
    (1022007, "stand"), (1032100, "stand"), (1021001, "stand"),
    (1022002, "stand"),
)


def load_clip(clip, cache):
    npc_id, action = clip
    file = cache / f"{npc_id}-{action}.gif"
    if not file.exists():
        request = Request(f"{API}/{npc_id}/render/{action}", headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=30) as response:
            data = response.read()
        with Image.open(BytesIO(data)) as source:
            source.verify()
        file.write_bytes(data)
    with Image.open(file) as source:
        frames = [(f.convert("RGBA"), f.info.get("duration") or 1200)
                  for f in ImageSequence.Iterator(source)]
    if len(frames) > COLUMNS:
        raise ValueError(f"{npc_id} exceeds the atlas row width")
    return frames


def build(cache):
    cache.mkdir(parents=True, exist_ok=True)
    atlas = Image.new("RGBA", (COLUMNS * CELL, len(CLIPS) * CELL))
    with ThreadPoolExecutor(max_workers=6) as workers:
        clips = list(workers.map(lambda clip: load_clip(clip, cache), CLIPS))
    for row, frames in enumerate(clips):
        for column, (image, _) in enumerate(frames):
            x, y = ORIGIN[0] - image.width // 2, ORIGIN[1] - image.height
            if x < 0 or y < 0 or x + image.width > CELL:
                raise ValueError(f"{CLIPS[row]} does not fit its cell")
            atlas.paste(image, (column * CELL + x, row * CELL + y))
        print(CLIPS[row][0], "height", frames[0][0].height,
              "durations", tuple(duration for _, duration in frames))
    atlas.save(ROOT / "assets/townsfolk.png", optimize=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache/classic-npcs")
    build(parser.parse_args().cache)
