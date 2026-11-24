"""Composite the licensed tree layer into the Bellflower forest backdrop."""

from argparse import ArgumentParser
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FOREST_LAYER = "Tall Forest Files/Layers/middle.png"


def pack_forest(path):
    with ZipFile(path) as archive:
        tree = Image.open(BytesIO(archive.read(FOREST_LAYER))).convert("RGBA")
    backdrop = Image.open(ASSETS / "daylight-panorama-tall.png").convert("RGBA")
    tree = tree.resize((tree.width * 2, tree.height * 2), Image.Resampling.NEAREST)
    alpha = tree.getchannel("A")
    # Blend the source layer's cropped edges into the sky and distant foliage.
    for y in range(tree.height):
        opacity = min(1, y / 66, (tree.height - 1 - y) / 44)
        row = alpha.crop((0, y, tree.width, y + 1)).point(
            [round(v * opacity * 0.9) for v in range(256)]
        )
        alpha.paste(row, (0, y))
    tree.putalpha(alpha)
    flipped = tree.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    for x, y, layer in ((34, 150, tree), (406, 112, flipped), (770, 153, tree),
                        (1150, 123, flipped), (1560, 147, flipped), (1950, 122, tree)):
        backdrop.alpha_composite(layer, (x, y))
    backdrop.convert("RGB").save(ASSETS / "bellflower-forest.png", optimize=True)


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--forest", type=Path, required=True)
    pack_forest(parser.parse_args().forest)
