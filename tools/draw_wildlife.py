"""Build the field guide and combat sprites from hand-lettered pixel clusters.

Coordinates use a 36-dot grid. Layers hinge independently for each pose.
The center of the feet is (18, 33), matching the field renderer's anchor.
"""
from pathlib import Path
from PIL import Image, ImageColor

ASSETS = Path(__file__).resolve().parents[1] / "assets"
INK = "#292336"
PAPER = "#fff2d6"

# Each character is one opaque dot. Individual shapes have a one-dot ink edge.
DROP = """
       llllm
     lllwwllmm
    lwwllllllmm
   llwlllllllmmm
  lllllllllllmmmm
 lllllllllllmmmmm
 lllllllllllmmmmmm
 llllllmmmmmmmmmmm
 mlllmmmmmmmmmmmmd
 mmmmmmmmmmmmmmdd
  mmmmmmmmmmmmddd
   dddmmmmmmdddd
     ddddddddd
"""
LEAVES = """
  ggg
 ggGgg        G
  GGGgg     ggG
   GGGGgg  ggGG
     GGGGggGGG
        GGGG
"""
CRYSTALS = """
      w
     wll   ww
  l  wlm  wlm
 wll wlmd wlmd
 wlmd lmddlmdd
  lmd dmddmdd
"""
MUSHROOM_FACE = """
     wwwww
   wwwwyyyyy
  wwwyyyyyyyy
  wwyyyyyyyyr
  wwwyyyyyyyr
  wywwyyyyyrr
   yyyyyyrrr
    ryyyrr
"""
CAP = """
           bbl
         bblwlll
       bbbllwllllm
      bbwwllllmbbmm
    bbbwwlllllmbbbmm
   bbwwllllllmmbbbbmm
  bbbllllbblmmmbbbbmmd
 lbbllllbbllmmmbbbmmmdd
 lllllllbbllmmmbbmmmmdd
  dmmmmmllmmmdddddmmdd
    yyrryyyyrrryyyrr
"""
SALT_CAP = """
           ww
      w   wllw  w
     wlw  wlmw wlw
    wwllw wlmmwllmw
   wllwwllllmlllmmmw
  wlwwllwwwllllwwlmmd
 wllwwwlllllmmlwllmmmd
 wlwwlllllllmmllllmmmd
  lllllmmlllllmmmmdd
    wwwwyyyywwyyrr
"""
SPIRIT = """
       lll
      llwll
    llwwllll
   llwwlllllm
  llwwllllmmm
 llwwlllmmmmmm
 llllllmmlllmm
 lllllmdyyyymmm
  lllmdyyyyyyym
  lllmdwwyyyyyr
   llmdyyyyyyyr
    lmmdyyyyrr
     llmmrrrmm
      llmmmmmm
        llmmmd
          mmmd
"""
TAIL = """
         mm
       mllm
    mllllm
  llwwllm
 llwwllm
 llwllm
  llmm
"""
LUNAR_WING = """
       w
      wlm
    wwllm
   wllmmd
  wllmmd
 lllmmmd
 lmmd
"""
BEACON_BODY = """
     bbbb
   bbwwwwbb
  bbwwyywwwb
  byyybbbyyb
  ddbbllbbdd
    lwwwll
   lwwlllmm
  llwllllmmm
 llwwlllllmmm
 llwllllllmmm
 llllmmmmmmmd
 ddmmmmmmmddd
  bbddbbddbb
"""
BEACON_HAT = """
         b
        ywb
        yyb
      lllllll
     llwlllmmm
   lllwwllllmmmd
   ddddddddddddd
    dwwydwwydww
    dwyydwyydyy
    dybbdybbdbb
  bbbbbbbbbbbbbbb
  ddbyyyyyyyybddd
"""
CRAB_BODY = """
     bbbbbb
   bbwwwlllbb
  blwwlllllmmb
 blwlllllllmmmb
 blwllmmlmllmmb
 lllyyyyyyyyymd
 llywwyyyyyyyymd
 mmywyyyyyyyyrmd
  dyyyyyyyyyrrd
   rrrryyyyrr
"""
CLAW = """
   ll    l
  lwll  llm
 lwlll  lmm
 lwllmmllmd
 lllllllmmd
  lllmmmmd
   dmmmmd
     dd
"""
CRAB_FOOT = """
   mmm
  m'mm
 l'mm
 lmm
 md
""".replace("'", "l")
HELM = """
       llllll
     lllwwlllm
   lllwwllllllmm
  llwwlllllmmllmm
 llwwlllllllmmlmmm
 llwlllmbblllmmlmm
 lllllmbwwblllmmdm
 lllmmbbyybmmmmmdd
  mmdwwwwwwwwwydd
  ddbbbbbbyybbbd
   mmdyyyyyyyyd
    mmddddyddd
"""
ARMOR = """
     bbbbbb
   mblwwllmbb
  mllwwllllmbb
  lwwlllbybbmm
  lllllbwwybmm
   lllmbwybmmm
   mmmmbbbmmd
    dddmmddd
"""
GAUNTLET = """
  llll
 lwllmm
 lllmmd
  mmdd
"""
PLUME = """
      llw
    lllwwm
   lllwwm
  llwwmm
 llwmmd
 lmmd
"""
CRESCENT = """
      ww
   wwwy
  wwy
 wwy
 wyy
 wyy   w
  yyyywy
   yyyy
"""
STAR = """
   w
   y
 wyyyw
  yyy
  y y
"""
AXE = """
   d  l
  dmd lm
  dmd lm
  dmd lm
  dmlllm
   lwwll
   lyyl
    b
    b
    b
    d
"""
FOOT = """
  rrr
 ryyyr
 ywwyrr
 yyyrrr
"""

# l/m/d are the primary color ramp, y/r skin, b an accent, g/G leaf tones.
COLORS = {
    "dew": ("#8de4be", "#44af95", "#327074", "#fdccac", "#cc846e", "#efb059", "#addd68", "#428354"),
    "pumpkin": ("#ffc05b", "#ed843b", "#ac4838", "#ffe5b6", "#cf9a75", "#ffdb80", "#a1cb75", "#487955"),
    "mist": ("#d5c1f3", "#978dc6", "#645e95", "#f9e8d3", "#c999b4", "#f1c06f", "#8ccbc2", "#467f81"),
    "salt": ("#aadbd3", "#6bb1b5", "#507f9d", "#ffefd2", "#c9baa5", "#d6e8de", "#9cc9a5", "#537b77"),
    "beacon": ("#9dc7da", "#6089a8", "#425473", "#ffe8a0", "#c99555", "#cd934c", "#aac78c", "#4c8676"),
    "glass": ("#91ddd7", "#52a8b2", "#426f99", "#ffddbb", "#db9c94", "#b9eee6", "#a7ce87", "#578f88"),
    "quartz": ("#e2b8ed", "#b684cb", "#815e9b", "#ffe1b5", "#d39591", "#f1c567", "#9bcfa3", "#826794"),
    "iron": ("#9fbdd1", "#718ba5", "#4e6079", "#f3cf81", "#b88755", "#ba8954", "#9fbcbd", "#61857f"),
    "moonwind": ("#b8d6ef", "#8a98c9", "#615f92", "#fff0d0", "#caa8bb", "#edbc65", "#94b3cc", "#6880a2"),
    "mooncrab": ("#cebafa", "#9f8bc4", "#695f97", "#f8dec1", "#caa493", "#e6cc91", "#a0c7a0", "#67877f"),
    "knight": ("#b8aecf", "#81759f", "#514963", "#a5e3df", "#71a6ae", "#d2a55d", "#b5dcad", "#5e9392"),
}
ORDER = tuple(COLORS)


class Portrait:
    def __init__(self, species):
        self.pic = Image.new("RGBA", (36, 36))
        self.colors = dict(zip("lmdyrbgG", COLORS[species]), k=INK, w=PAPER, p="#e59d94")

    def stamp(self, mask, x, y, flip=False, outline=True):
        dots = {}
        lines = mask.strip("\n").splitlines()
        width = max(map(len, lines))
        for row, line in enumerate(lines):
            for col, ch in enumerate(line):
                if ch != " ":
                    dots[(x + (width-1-col if flip else col), y+row)] = self.colors[ch]
        if outline:
            for col, row in dots:
                for a, b in ((col-1,row), (col+1,row), (col,row-1), (col,row+1)):
                    if (a,b) not in dots and 0 <= a < 36 and 0 <= b < 36:
                        self.pic.putpixel((a,b), INK_RGB)
        for (a,b), color in dots.items():
            if 0 <= a < 36 and 0 <= b < 36:
                self.pic.putpixel((a,b), RGBA[color])

    def face(self, x, y, pose, eyes_only=False):
        for i in (0, 6):
            if pose == 3:
                eye = "k  \n kk\nk  "
            elif pose == 2:
                eye = "kk \n kk\n  k" if i == 0 else " kk\nkk \nk  "
            else:
                eye = "kk\nwk\nkk"
            self.stamp(eye,x+i,y,outline=False)
        if not eyes_only:
            self.stamp("pp      pp",x-1,y+3,outline=False)
            mouth = "kk\nrr" if pose == 5 else "kk"
            self.stamp(mouth,x+3,y+4,outline=False)


_RGBA_COLORS = {color for ramp in COLORS.values() for color in ramp} | {INK, PAPER, "#e59d94"}
RGBA = {color: ImageColor.getcolor(color, "RGBA") for color in _RGBA_COLORS}
INK_RGB = RGBA[INK]


def frame(kind, pose):
    p = Portrait(kind)
    # Stand, passing step, anticipation, recoil, lifted step, contact.
    dx = (0, 1, -2, -2, 0, 3)[pose]
    dy = (0, -1, 2, -2, -2, 0)[pose]
    leg = (0, -2, 1, 0, 2, -1)[pose]
    if kind in ("dew", "quartz"):
        x, y = 8 + dx, 19 + dy
        p.stamp(FOOT, 10-leg, 29, flip=True)
        p.stamp(FOOT, 20+leg, 29-abs(leg)//2)
        p.stamp(DROP,x,y-1)
        crown = LEAVES if kind == "dew" else CRYSTALS
        p.stamp(crown,x+3-leg//2,y-6)
        p.face(x+6,y+3,pose)
    elif kind in ("pumpkin", "salt"):
        x, y = 10+dx, 20+dy
        p.stamp(FOOT,x-1+leg,29-abs(leg)//2,flip=True)
        p.stamp(FOOT,x+9-leg,29)
        p.stamp(MUSHROOM_FACE,x,y+1)
        p.face(x+4,y+4,pose)
        p.stamp(CAP if kind == "pumpkin" else SALT_CAP,x-3,y-9)
        if kind == "pumpkin":
            p.stamp("  gg\n ggG\ngGG ",x+8-leg//2,y-12)
    elif kind in ("mist", "moonwind"):
        x, y = 9+dx, 11+dy
        p.stamp(TAIL,x-4-leg,y+14)
        if kind == "moonwind":
            p.stamp(LUNAR_WING,x-5,y+4+leg)
            p.stamp(LUNAR_WING,x+11,y+2-leg,flip=True)
        p.stamp(SPIRIT,x,y)
        p.face(x+6,y+7,pose)
        p.stamp(CRESCENT if kind=="moonwind" else "  w\n wyw\n  b",x+3,y-3)
    elif kind == "beacon":
        x, y = 9+dx, 17+dy
        p.stamp(GAUNTLET,x-5-leg,y+5+leg)
        p.stamp(BEACON_BODY,x,y)
        p.face(x+5,y+5,pose,eyes_only=True)
        p.stamp(BEACON_HAT,x-1,y-13)
        p.stamp(GAUNTLET,x+14+leg,y+7-leg)
    elif kind in ("glass", "mooncrab"):
        x, y = 8+max(-1,min(dx,1)), 18+dy
        for at in (3,9,17):
            p.stamp(CRAB_FOOT,x+at-leg//2,27, flip=at>4)
        claw_up = (0,-1,-4,2,1,-2)[pose]
        p.stamp(CLAW,x-5,y+1-claw_up,flip=True)
        p.stamp(CRAB_BODY,x,y)
        if kind == "mooncrab":
            p.stamp(CRESCENT,x+5,y-6)
        else:
            p.stamp("   w\n  wlm\n  wlmd\n wllmd",x+6,y-4)
        p.face(x+5,y+5,pose)
        p.stamp(CLAW,x+13+(1 if pose==5 else 0),y+claw_up)
    else:
        x,y = 8+min(dx,1), 9+dy
        p.stamp(FOOT,x+2+leg,28,flip=True)
        p.stamp(FOOT,x+12-leg,28-abs(leg)//2)
        p.stamp(ARMOR,x+1,y+13)
        p.stamp(GAUNTLET,x-1-leg//2,y+13+leg)
        p.stamp(HELM,x,y)
        p.face(x+6,y+9,pose,eyes_only=True)
        p.stamp(CRESCENT if kind == "knight" else PLUME,x+3-leg//2,y-5)
        if kind == "iron":
            p.stamp(STAR,x+7,y+3,outline=False)
        weapon_x = 2 if pose==2 else 16
        p.stamp(AXE,x+weapon_x,y+7-(4 if pose==2 else leg))
        p.stamp(GAUNTLET,x+weapon_x,y+16-leg//2)
    # Compress for the windup, then extend horizontally on the contact frame.
    # Resize the opaque dot raster before the final 2× pixel enlargement.
    if pose in (2, 5) and kind in ("dew", "quartz", "pumpkin", "salt", "mist", "moonwind"):
        left, top, right, bottom = p.pic.getbbox()
        wide = min(35-left, right-left + (2 if pose==2 else 3))
        height = bottom-top - (3 if pose==2 else 1)
        body = p.pic.crop((left,top,right,bottom)).resize((wide,height), Image.Resampling.NEAREST)
        p.pic = Image.new("RGBA", (36,36))
        p.pic.paste(body,(left, bottom-height))
    return p.pic.resize((72,72), Image.Resampling.NEAREST)


def run():
    sheet = Image.new("RGBA", (432, 72*len(ORDER)))
    for row, kind in enumerate(ORDER):
        for pose in range(6):
            sheet.paste(frame(kind, pose), (pose*72, row*72))
    sheet.save(ASSETS / "wildlife.png", optimize=True)


if __name__ == "__main__":
    run()
