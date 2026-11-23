"""Paint the 16 adventurer cels at their native pixel resolution."""
from pathlib import Path

from PIL import Image, ImageColor

from hero_face import head

ASSETS = Path(__file__).resolve().parents[1] / "assets"
PALETTE = {
    "k": "#27252d", "n": "#5d7d93", "b": "#8abed9", "d": "#b6dded",
    "c": "#a9bcc0", "i": "#dbe4db", "w": "#fff9e9", "l": "#f2ecda",
    "v": "#928a81", "q": "#785541", "a": "#b57a43", "y": "#e6aa5c",
    "e": "#ffce83", "z": "#f9c870", "f": "#f7c493", "s": "#df9e75",
    "p": "#ffe6c4",
}
COLORS = {key: ImageColor.getcolor(value, "RGBA") for key, value in PALETTE.items()}


def stamp(image, x, y, rows):
    for j, row in enumerate(rows.split()):
        for i, color in enumerate(row):
            if color != ".":
                image.putpixel((x+i,y+j), COLORS[color])


# The neck, thin shoulder straps and armholes show skin above the stripe.
TANK = """
......kkkkk.....
....kkpfffskk...
...knkpffffskk..
..kbwkffsnwilk..
..knwdkkwwwwwk..
...kbddbddddbk..
...kbdddddddbk..
...kiwwwwwwwlk..
...kiwwwwwwwlk..
...kbdddddbbbk..
...kbddddddbbk..
...kiwwwwwwwlk..
..kiwwwwwwwwlk..
..kbdddddddbbk..
..knbbbbbbbbbk..
...kncccccccnk..
"""

TANK_TWIST = """
......kkkkk.....
....kkpfffskk...
...knkpfffsksk..
..kbwkffskwikk..
..knwdkkwwwwlk..
...kbdddddbbbk.
...kbdddddbbnk..
...kiwwwwwwlik..
...kiwwwwwllik..
...kbdddddbbbk..
...kbdddddbbnk..
...kiwwwwwlllk..
..kiwwwwwlllik..
..kbdddddbbbnk.
..knbbbbbbbbnk..
...kncccccccnk..
"""

SHORTS = """
...kkkkkkkkkk...
..kvillwllllik..
.kiwwwwwwwwllk..
.kiwwwwlwwwlik..
.kiwwllkwwllik..
.kivvlk.kiillk..
..kkkk...kkkk...
"""

SLIPPER = {
    "flat": """
...kkk....
..kaffk...
.kyeaaykk.
.kaayyyeyk
.kqqqqqqqk
..kkkkkkk.
""",
    "tip": """
...kk....
..kaffk..
..kyeak..
...kayayk.
....kqyeykk
.....kqqqqk
......kkkk.
""",
    "lift": """
..kkk....
.kffak...
.kysaak..
..kqayyk.
...kqqeyk
....kkkk.
""",
}

# Arm cels are hand blocked from the shoulder out to the knuckles. The
# shoulder's light-facing edge is two skin clusters wide in the idle pose.
ARMS = {
    "rest": (0,0, """
.kkk....
kpfsk...
kppfk...
kppfk...
.kpfsk..
.kpfsk..
.kpfsk..
..kpffk.
..kpfsk.
..kpffk.
..kpffsk
..kpfssk
..kffsk.
...kkk..
"""),
    "back": (-6,1, """
.......kkk
......kpfsk
......kpffk
.....kpffk.
.....kpffk.
....kpfsk..
...kpffk...
..kpffk....
.kpffsk....
.kpfssk....
.ksfsk.....
..kkk......
"""),
    "swing": (0,1, """
.kkk......
kppfk.....
kppfsk....
.kpfsk....
.kpffk....
..kpffk...
..kpffsk..
...kpffsk.
....kpffsk
....kpfssk
.....ksfsk
......kkk.
"""),
    "tucked": (0,1, """
.kkk.....
kpffk....
kppfk....
.kpfsk...
.kpfskkk.
..kpffpfk
..ksfpffk
...ksffsk
....kkkk.
"""),
    "out": (0,0, """
.kkkk........
kpffsk.......
kppffsk..kkkk
.kppffskkpffk
..kpffffffssk
...kffsssskk.
....kkkkkk...
"""),
    "backlift": (-7,0, """
.kkk....kkk.
kpfsk..kpffk
kpffskkppfsk
.kppffffffk.
..kffsssskk.
...kkkkkk...
"""),
}
FIST = """
..kkk..
.kpffkk
kppfffk
kpffssk
.ksssk.
..kkk..
"""

BLADES = {
    "ready": (-4, -20, """
....................kk
..................kkyk
.................kyeak
................kyeayk
...............kyeayk.
..............kyeayk..
.............kyeayk...
............kyeayk....
...........kyeayk.....
..........kyeayk......
.........kyeayk.......
........kyeayk........
.......kyeayk.........
......kyeayk..........
.....kyeayk...........
...kkyeayk............
..kzqayyk.............
...kzyakk.............
....kayayk............
...kaqkkayk...........
..kaqk..kk............
.kqqk.................
..kk..................
"""),
    "back": (-22, -18, """
kk......................
kykk....................
.kaykk..................
..kayykk................
...kayeyk...............
....kayeyk..............
.....kayeyk.............
......kayeyk............
.......kayeyk...........
........kayeyk..........
.........kayeyk.........
..........kayeyk........
...........kayeyk.......
............kayeyk......
.............kayeyk..kk.
..............kayykkzyk.
...............kayaykk..
................kkqqk...
...............kzykkqk..
..............kkak..kqk.
................k....kk.
"""),
    "thrust": (-4, -8, """
.......................kkk
....................kkkyyk
.................kkkyeeak.
..............kkkyyeeakk..
...........kkkyyeeakkk....
.......kkkkyyeeakkk.......
....kkkyyyyeeakk..........
...kzzqaaakkkk............
....kyqkkk................
..kkqaqk..................
.kaqqkqyk.................
..kkk.kzk.................
.......k..................
"""),
    "follow": (-4, -4, """
.....kk.................
....kzak................
.k..kzqk................
kaqkayak................
.kqaqqaykk..............
..kkkyyeykk.............
...kzakayeyk............
..kzak..kayeyk..........
...kk....kayeyk.........
..........kayeyk........
...........kayeyk.......
............kayeyk......
.............kayeyk.....
..............kayeyk....
...............kayeyk...
................kayyk...
.................kayyk..
..................kayykk
...................kkayk
.....................kkk
"""),
}

# Face, tank top, rear foot, front foot, rear arm, front arm and (only in the
# four attack cels) the grip. Feet are keyed to the baseline at row 74.
POSES = [
    ((17,3), "open",  (30,43), (31,74,"flat"), (40,74,"flat"), "rest","rest",None),
    ((17,4), "open",  (30,44), (31,74,"flat"), (40,74,"flat"), "rest","rest",None),
    ((17,4), "half",  (30,44), (31,74,"flat"), (40,74,"flat"), "rest","rest",None),
    ((17,4), "blink", (30,44), (31,74,"flat"), (40,74,"flat"), "rest","rest",None),
    ((18,4), "open",  (31,44), (25,74,"tip"),  (45,74,"flat"), "back","swing",None),
    ((18,3), "open",  (31,43), (30,70,"lift"), (39,74,"flat"), "rest","tucked",None),
    ((17,4), "open",  (30,44), (44,74,"flat"), (25,74,"tip"),  "swing","back",None),
    ((17,2), "open",  (30,42), (37,74,"flat"), (32,70,"lift"), "tucked","rest",None),
    ((14,2), "attack",(27,43), (25,74,"flat"), (39,74,"flat"), "backlift","tucked",(27,49,"back")),
    ((20,4), "attack",(32,44), (26,74,"tip"),  (45,74,"flat"), "back","out",(55,52,"thrust")),
    ((20,5), "attack",(32,45), (25,74,"tip"),  (44,74,"flat"), "back","swing",(54,59,"follow")),
    ((18,4), "open",  (31,44), (28,74,"flat"), (41,74,"flat"), "rest","tucked",(50,55,"ready")),
    ((18,1), "open",  (31,41), (26,66,"lift"), (41,70,"tip"),  "back","out",None),
    ((17,2), "open",  (30,42), (28,68,"lift"), (40,73,"flat"), "backlift","tucked",None),
    ((13,3), "hurt",  (27,43), (27,72,"flat"), (40,70,"tip"),  "backlift","out",None),
    ((18,7), "open",  (30,47), (26,74,"flat"), (43,74,"flat"), "back","swing",None),
]


def leg(image, hip_x, hip_y, step, distant):
    ankle_x, sole, profile = step
    slipper = SLIPPER[profile]
    ankle_y = sole - len(slipper.split()) + 2
    # A bent knee still connects the hip to the ankle when a lifted foot is
    # almost level with the hem. Work along both axes for those short spans.
    if profile == "lift":
        knee = (hip_x+2, max(hip_y+3,ankle_y+1))
    else:
        knee = ((hip_x+ankle_x)//2+1, (hip_y+ankle_y)//2)
    joints = ((hip_x,hip_y), knee, (ankle_x,ankle_y))
    covered = set()
    for segment, ((x0,y0),(x1,y1)) in enumerate(zip(joints, joints[1:])):
        steps = max(1,abs(x1-x0),abs(y1-y0))
        for i in range(steps+1):
            x = round(x0+(x1-x0)*i/steps)
            y = round(y0+(y1-y0)*i/steps)
            left = x-1 if segment and i > steps//2 else x-2
            for xx in range(left,x+3):
                covered.add((xx,y))
                covered.add((xx,y+1))
    for xx,yy in covered:
        if any((xx+dx,yy+dy) not in covered for dx,dy in ((0,-1),(0,1),(-1,0),(1,0))):
            color = "k"
        elif (xx+2,yy) not in covered:
            color = "s"
        else:
            color = "f" if distant else "p"
        image.putpixel((xx,yy), COLORS[color])
    stamp(image,ankle_x-4,sole-len(slipper.split())+1,slipper)


def arm(image,x,y,pose):
    dx,dy,art = ARMS[pose]
    stamp(image,x+dx,y+dy,art)


def frame(index):
    face, expression, tank, back_foot, front_foot, back_arm, front_arm, weapon = POSES[index]
    x,y = tank
    shorts_y = min(y+14,60)
    image = Image.new("RGBA",(80,80))
    leg(image,x+4,shorts_y+4,back_foot,True)
    leg(image,x+11,shorts_y+4,front_foot,False)
    stamp(image,x-2,y+2,"...kkkkkk .kkppppffk kpppffffsk .ksffsskk. ..kkkkk...")
    arm(image,x-3,y+3,back_arm)
    stamp(image,x+1,shorts_y,SHORTS)
    stamp(image,x,y,TANK_TWIST if index in (8,9,10,12,14) else TANK)
    arm(image,x+12,y+3,front_arm)
    if weapon:
        gx,gy,kind = weapon
        dx,dy,art = BLADES[kind]
        stamp(image,gx+dx,gy+dy,art)
        stamp(image,gx-3,gy-3,FIST)
    image.alpha_composite(head(expression),face)
    return image


def run():
    atlas = Image.new("RGBA", (320,320))
    for index in range(16):
        atlas.paste(frame(index), ((index%4)*80,(index//4)*80))
    atlas.save(ASSETS / "hero-adventurer.png", optimize=True)


if __name__ == "__main__":
    run()
