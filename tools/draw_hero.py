"""Paint the 28 adventurer cels at their native pixel resolution."""
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
......kkk.........
....kkpsfskk......
...knfpfffknk.....
..kbwkffffkwik....
..kwwdkppkdwdik...
..kllwksskwwwik...
..kdbddkkbdddck...
..kdbddddbdddbk...
..kwwdwwwdwwlik...
..kwwdwwwdwwlik...
..kbbdbbbdbbbnk...
..kbdddddbdddbk..
..kwwdwwwdwwlik...
.kwwldwwwdwwwlik..
.kbbdbbbdbbbbnkk..
..kdddiiidddbnk...
...kccicccicnk....
....kkkkkkkkk.....
"""

TANK_TWIST = """
......kkkk.......
....kkpffskk.....
...knkpfffsnk....
..kwwkfffswkik...
..kwwdkpkkdwik...
..kliwkkwwdwlik..
..kdbddbdddbbnk..
..kdbddbdddbbnk..
..kwwdwwwdiwlik..
..kwwdwwwdiwlik..
..kbbdbbbdbbbnk..
..kbdddbdddbbnk..
...kwdwwwdiwlik..
..kwwdwwwdiwlik..
..kbbdbbbdbbbnk..
...kddiidddbnk...
....kccccccnk....
.....kkkkkkk.....
"""

SHORTS = """
...kkkkkkkkkkkk..
..kvcilllwlllik..
.killwwwliwwllik.
.kiwwwwwwwwwllik.
.kiwwlwwlkwlllik.
.kiwliilkvwllilk.
..kivvik.kcillk..
...kkkk...kkkk...
"""

SLIPPER = {
    "flat": """
..kpfsk..
..kffsk..
.kaeffakk
.kayyyaek
..kqqqqqk
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
..kkk.....
.kppffk...
.kppffsk..
..kppffk..
..kppffk..
...kpffsk.
...kpffsk.
...kppfsk.
..kppffsk.
..kpfsssk.
...kffsk..
....kkk...
"""),
    "hip": (-1,1, """
...kkk....
..kpfsk...
.kppffk...
.kppfkk...
.kpffk....
.kpfsk....
.kpfsk....
.kpffsk...
..kpffsk..
...kppfkk.
....kpfsk.
.....kkk..
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

# Face, tank top, rear foot, front foot, rear arm, front arm and (only in the
# action cels) the grip for the equipment overlay. Feet are keyed to the baseline at row 74.
POSES = [
    ((17,3), "open",  (30,43), (32,73,"flat"), (43,74,"flat"), "hip","rest",None),
    ((17,3), "open",  (29,44), (32,73,"flat"), (43,74,"flat"), "hip","rest",None),
    ((17,3), "open",  (28,43), (32,73,"flat"), (43,74,"flat"), "hip","rest",None),
    ((17,3), "blink", (29,44), (32,73,"flat"), (43,74,"flat"), "hip","rest",None),
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
    # Archer: nock, full draw, release and lower the bow.
    ((17,3), "open",  (30,43), (30,74,"flat"), (42,74,"flat"), "hip","tucked",(51,53,"nock")),
    ((16,3), "attack",(29,43), (26,74,"flat"), (45,74,"flat"), "back","out",(57,49,"draw")),
    ((15,2), "attack",(28,43), (26,74,"flat"), (45,74,"flat"), "backlift","out",(57,49,"release")),
    ((17,4), "open",  (30,44), (29,74,"flat"), (42,74,"flat"), "hip","rest",(52,54,"settle")),
    # Spellcaster: focus at chest, raise, point at target, settle.
    ((16,4), "half",  (29,44), (30,74,"flat"), (41,74,"flat"), "tucked","tucked",(48,54,"focus")),
    ((15,2), "open",  (28,42), (28,74,"flat"), (41,74,"flat"), "backlift","out",(49,44,"raise")),
    ((20,4), "attack",(32,44), (26,74,"tip"),  (45,74,"flat"), "back","out",(56,52,"cast")),
    ((17,4), "open",  (30,44), (29,74,"flat"), (41,74,"flat"), "hip","tucked",(50,55,"settle")),
    # Alternating rung contact in back view. Raised knees and heels swap sides.
    ((15,3), "back", (29,43), (29,69,"lift"), (44,74,"flat"), "out","out",None),
    ((16,2), "back", (30,42), (29,72,"flat"), (44,70,"lift"), "out","out",None),
    ((17,3), "back", (31,43), (30,74,"flat"), (46,69,"lift"), "out","out",None),
    ((16,2), "back", (30,42), (29,70,"lift"), (45,72,"flat"), "out","out",None),
]


def leg(image, hip_x, hip_y, step, distant, climbing=False):
    ankle_x, sole, profile = step
    slipper = SLIPPER[profile]
    if climbing:
        slipper = (".kkkkk. ksppfsk kyaaayk keyyyak .kaaqk. ..kkk.." if profile == "lift"
                   else ".kkk.. kfffsk kyaayk keyyak kqaqqk .kkkk.")

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
            for xx in range(left,x+(4 if not segment and i < steps//2 else 3)):
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


# These joints are the same coordinates used by the independent equipment
# sheets. Both hands stay attached when the bowstring moves behind the cheek.
ARCHER = [
    ((37,57),(44,54),(47,57),(51,53)),
    ((24,53),(32,49),(49,50),(57,49)),
    ((22,49),(28,47),(47,50),(57,49)),
    ((32,59),(39,55),(46,57),(52,54)),
]
CAST_ELBOWS = [(46,58),(47,52),(49,55),(46,59)]
MELEE_ELBOWS = [(34,54),(46,53),(50,57),(46,58)]
CLIMB = [
    ((24,49),(18,34),(54,53),(56,45)),
    ((23,48),(18,39),(53,50),(58,38)),
    ((24,55),(20,45),(55,48),(58,34)),
    ((24,50),(19,38),(54,48),(58,39)),
]
BACK_SHIRT = """
......kkkkk......
....kkffssskk....
...kiwkssskwwk...
..kwwdwkkdwwwik..
..kwwdwwwdwwwik..
..kbddbbdbdddbk..
...kbdddbdddbk..
...kwdwwwdwwik...
...kwdwwwdwwik...
...kbdbbbdbbbk...
...kbdbbbdbbbk...
...kwdwwwdwwik...
..kwwdwwwdwwlik..
..kbddbbdbdddbk..
..kbddddbddddbk..
...kccccccccck...
....kkkkkkkkk....
"""


def bent_arm(image, shoulder, elbow, hand, distant=False, open_hand=False):
    # Lay in a joined silhouette from shoulder to wrist, then paint its lit and
    # shaded faces. The tapered forearm is thinner where it meets the thumb.
    pixels = set()
    joints = (shoulder,elbow,hand)
    for segment, ((x0,y0),(x1,y1)) in enumerate(zip(joints,joints[1:])):
        steps = max(1,abs(x1-x0),abs(y1-y0))
        for index in range(steps+1):
            x = round(x0 + (x1-x0)*index/steps)
            y = round(y0 + (y1-y0)*index/steps)
            narrow = segment and index > steps//2
            pattern = ("..X..", ".XXX.", "XXXXX", ".XXX.", "..X..") if narrow else (
                ".XXX.", "XXXXX", "XXXXX", "XXXXX", ".XXX.")
            for row, marks in enumerate(pattern):
                for col, mark in enumerate(marks):
                    if mark == "X":
                        pixels.add((x+col-2,y+row-2))
    for x,y in pixels:
        if any((x+dx,y+dy) not in pixels for dx,dy in ((1,0),(-1,0),(0,-1),(0,1))):
            color = "k"
        elif (x+1,y+2) not in pixels:
            color = "s"
        else:
            color = "f" if distant else "p"
        image.putpixel((x,y), COLORS[color])
    hx,hy = hand
    stamp(image,hx-3,hy-3,(".kk.kk. kpfkpfk kpppffk .kpffsk ..kssk. ...kk.." if open_hand else FIST))


def frame(index):
    face, expression, tank, back_foot, front_foot, back_arm, front_arm, grip = POSES[index]
    x,y = tank
    climbing = expression == "back"
    shorts_y = min(y+15,61)
    image = Image.new("RGBA",(80,80))
    leg(image,x+5,shorts_y+4,back_foot,True,climbing)
    leg(image,x+12,shorts_y+4,front_foot,False,climbing)
    stamp(image,x-2,y+2,"...kkkkkk .kkppppffk kpppffffsk .ksffsskk. ..kkkkk...")
    if 16 <= index < 20:
        rear_elbow,rear_hand,near_elbow,near_hand = ARCHER[index-16]
        bent_arm(image,(x+1,y+5),rear_elbow,rear_hand,True, index==18)
    elif climbing:
        rear_elbow,rear_hand,near_elbow,near_hand = CLIMB[index-24]
        bent_arm(image,(x+1,y+5),rear_elbow,rear_hand,True)
    else:
        arm(image,x-3,y+3,back_arm)
    stamp(image,x+1,shorts_y,SHORTS)
    twist = index in (8,9,10,12,14,17,18,20,21,22)
    stamp(image,x,y,BACK_SHIRT if climbing else TANK_TWIST if twist else TANK)
    if climbing or 16 <= index < 20:
        bent_arm(image,(x+13,y+5),near_elbow,near_hand)
    elif grip:
        elbow = MELEE_ELBOWS[index-8] if index<12 else CAST_ELBOWS[index-20]
        bent_arm(image,(x+13,y+5),elbow,grip[:2])
    else:
        arm(image,x+13,y+3,front_arm)
    image.alpha_composite(head(expression),face)
    return image


def run():
    atlas = Image.new("RGBA", (320,560))
    for index in range(len(POSES)):
        atlas.paste(frame(index), ((index%4)*80,(index//4)*80))
    atlas.save(ASSETS / "hero-adventurer.png", optimize=True)


if __name__ == "__main__":
    run()
