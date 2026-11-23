"""Layered, hand-pixelled 3/4 head for the right-facing adventurer."""
from PIL import Image, ImageDraw

COLORS = {
    "k": "#100f12", "b": "#161519", "c": "#302e33", "g": "#504e54",
    "s": "#76747a", "f": "#ffedd7", "l": "#fff4df", "t": "#ffd5ab",
    "o": "#edac80", "r": "#d78069", "w": "#fffaf2", "a": "#5b5364",
    "i": "#34303f", "v": "#827e89", "u": "#dedcf4", "m": "#74483e",
}


def stamp(draw, x, y, rows):
    for j, row in enumerate(rows.strip("\n").splitlines()):
        for i, pixel in enumerate(row):
            if pixel != ".":
                draw.point((x+i, y+j), COLORS[pixel])


# Dark masses define the cut. Small reflective clusters sit near the part.
HAIR = """
.............kkkkkkkk...kkkkkkk.............
..........kkkkkkkkkkkkkkkkkkkkkkk...........
........kkkkkkkkkkkkkkkkkkbbbbbkkkk.........
......kkkbbbbbbbkkkkkkkkkbbbbbbbbkkk........
.....kkbbbbcgcbbbbkkkkkkbcccgcbbbbkkk.......
....kkbbccgggcgcccbbkkkbcgggscccbbbkkk......
...kkbbccgsggccggccbbkkbggssgsgccbbbkkk.....
...kbbbccgssgcggsccbbkkbcggsggsgccbbkkk.....
..kkbbbccgggcggggccbbkkkbcgccgggccbbbkkk....
..kbbbbccggcccgcccbkkkkkkbcccgggcccbbkkk....
.kkbbbbbbcccccccbbkkkkkkk.bcccccccccbbkkk...
.kkbbbbbbbbccbbbbkkkkkk...kbccccccbbbkkkk...
.kkkbbbbbbbbbbbkkkkkkk.....kbccbbbbbbkkkk...
.kkkbbbbbbbbbkkkkkkkt......kbbbbbbbbbkkkkk..
.kkkbbbbbbbbkkkkkkt.........kbbbbbbbbbkkkk..
.kkkkbbbbbbkkkkkt..........tkbbbbbbbbbkkkk..
.kkkkbbbbkkkkkk............ttkbbbbbbbbkkkk..
..kkkbbbkkkkkkt............t.kbbbbbbbbbkkk..
..kkkkkkkkkkkt...............tkbbbbbbbbkkk..
...kkkkckkkkt.................tkbbbbbbbkkk..
...kkccgckkt...................tkbbbbbbkkk..
...kccgggck.....................tkbbbbbkkk..
...kccgggck......................tkbbbkkkt..
...kccgssgk.......................tkbbkkk...
...kccgssgk........................tkbkk....
...kccgssgk.........................tkk.....
....kccgsgk.................................
....kkcgsgk.................................
.....kkccc..................................
"""


NEAR_EYE = """
.kkkkiiiiikk
uuuuukkkkkw.
uwwwkiwwikw.
wwwwkiwwikw.
wwwwkkiiikw.
wwwwkkiaikw.
.wwwkaivvkw.
.wwwkiavvkw.
..wwkaavvkw.
..wwwvvaakw.
...wwwwwww..
....kkkkk...
"""
FAR_EYE = """
.kiiikkk
.kkkiuuw
.kwwikuu
.kwwikww
.kiikkww
.kiikkww
.kavvkw.
.kaavkw.
..kavkw.
..wvvuw.
...www..
...kkk..
"""

NEAR_BROW = """
..kkkkk......
.kkkkkkkk....
kkkkkkkikk...
kkkkkkkiikkk.
.kkkkkkkkiiik
"""
FAR_BROW = """
.....kkkk.
...kkkiiik
..kkkiiikk
.kkkiiikk.
kkkiikk...
"""


def head(expression="open"):
    image = Image.new("RGBA", (44, 45))
    d = ImageDraw.Draw(image)
    # Stepped jaw, right temple, left ear. Dark edges taper into a warm chin.
    profile = [(5,19),(10,10),(22,7),(33,9),(39,16),(40,21),(40,25),
               (41,27),(41,32),(40,32),(40,35),(38,35),(38,37),(35,39),
               (32,40),(31,41),(27,42),(20,42),(19,41),(15,41),(14,40),
               (12,40),(11,39),(10,39),(8,37),(7,35),(5,33),(4,29)]
    d.polygon(profile, fill=COLORS["k"])
    d.polygon([(6,20),(13,12),(23,9),(33,11),(38,16),(39,20),(39,26),
               (40,27),(40,31),(39,32),(39,34),(37,35),(37,36),(34,38),
               (31,39),(29,41),(21,41),(16,40),(12,38),(9,36),(7,32)],fill=COLORS["o"])
    d.polygon([(7,20),(13,13),(24,9),(33,12),(37,16),(39,22),(39,27),
               (40,28),(39,32),(37,34),(36,36),(33,38),(29,39),(27,40),
               (21,40),(17,39),(14,38),(10,35),(9,31)],fill=COLORS["t"])
    d.polygon([(9,21),(15,15),(23,10),(30,12),(35,16),(38,21),(38,26),
               (39,28),(38,32),(36,34),(35,36),(32,37),(29,39),(21,39),
               (16,37),(12,35),(10,31)], fill=COLORS["f"])
    stamp(d, 0, 0, HAIR)
    stamp(d, 16, 12, "kkkkk\nkkkk.\n.kk..\n.k...\n.k...")
    stamp(d, 29, 15, ".kkk\n..kk\n..tk")
    stamp(d, 1, 25, """
...kkkk..
..kffffk.
.kltffftk
.kltoomfk
.kftrottk
..kftotfk
..kfffttk
...kftok.
....kkk..
""")
    # A broken highlight along the cheek gives the face volume at field size.
    stamp(d, 11, 31, """
..tt.........
..ooot.......
...ttt.......
""")
    if expression == "half":
        stamp(d, 13, 28, "ukkkiiiiikk\nwwwwwvvaik.\n.wwwwuuvak.\n..wwwwww...\n....kkkkk..")
        stamp(d, 31, 28, ".kiiikk.\n.kvvaku.\n..uuvww.\n..wwww..\n...kkk..")
    elif expression in ("open", "attack"):
        stamp(d, 13, 24, NEAR_EYE)
        stamp(d, 31, 24, FAR_EYE)
    else:
        pain = expression == "hurt"
        stamp(d, 14, 28, ("kkk.....\n..kkkk..\n.....kkk\n..kkkk.." if pain else
                            ".......k\n..kkkkkk\nkkk....."))
        stamp(d, 32, 28, ("...kkk\n.kkk..\nkk....\n..kkk." if pain else
                            "kk....\n.kkkkk\n.....kk"))
    brow_y = 21 if expression in ("attack", "hurt") else 20
    stamp(d, 12, brow_y, NEAR_BROW)
    stamp(d, 30, brow_y, FAR_BROW)
    stamp(d, 26, 26, "tt.\nott\n.tt")
    stamp(d, 28, 37, ".kk.\nkmrk\n.kk." if expression=="hurt" else "kk")
    return image
