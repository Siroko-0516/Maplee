"""Original character frames, drawn with opaque colors on an 80px grid."""
from pathlib import Path
from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parents[1] / "assets"
INK = "#141925"
HAIR = "#222936"
HAIR_LIGHT = "#526a75"
HAIR_SHADE = "#344551"
SKIN = "#ffeccd"
SKIN_SHADE = "#ecbb8c"
HIGHLIGHT = "#fff9ec"
TEAL = "#347c78"
TEAL_LIGHT = "#86c5a4"
COPPER = "#dc985b"

def fill(draw, points, color):
    draw.polygon(points, fill=color, outline=INK, width=1)

def hand(draw, x, y):
    fill(draw,[(x-4,y-3),(x+2,y-4),(x+5,y-1),(x+3,y+3),(x-3,y+3)],SKIN_SHADE)
    draw.line([(x-2,y-2),(x+2,y-2)],fill=SKIN,width=1)

def blade(draw, x, y, pose):
    directions = {"rise":(7,-20),"strike":(17,-3),"follow":(16,11),"idle":(12,-14),"hurt":(9,-13)}
    dx, dy = directions.get(pose, directions["idle"])
    fill(draw,[(x-2,y-3),(x+dx-2,y+dy),(x+dx+3,y+dy-3),(x+dx+1,y+dy+4),(x+2,y+2)],"#c7deed")
    draw.line([(x+1,y-1),(x+dx+1,y+dy-1)],fill="#fff4d3",width=1)
    draw.line([(x-4,y-3),(x+4,y+3)],fill="#bc8154",width=2)

def frame(index):
    pic = Image.new("RGBA",(80,80))
    d = ImageDraw.Draw(pic)
    gait = [-4,-2,3,2][index-4] if 4 <= index <= 7 else 0
    swing = {8:"rise",9:"strike",10:"follow",11:"idle",12:"rise",14:"hurt"}.get(index, "idle")
    jump = index in (12,13)
    squat = 3 if index==15 else 0
    shift = -4 if index==14 else (2 if index in (9,10) else 0)
    bob = (1 if index in (1,3,5,7) else 0) + squat
    top = 12 + bob
    x = 17 + shift
    # Looping steps and takeoff use a common foot origin at row 74.
    for i, foot in enumerate((30+gait,42-gait)):
        lift = (5 if i else 9) if jump else (2 if gait and i==int(gait<0) else 0)
        fy = 74 - lift
        fill(d,[(foot-4,64+min(squat,1)),(foot+4,65),(foot+4,fy-4),(foot+8,fy-4),
                (foot+8,fy),(foot-4,fy),(foot-5,fy-3)],"#3b4b59")
        d.line([(foot-2,fy-3),(foot+4,fy-3)],fill="#91a7a3")
    # Waistcoat and copper scarf.
    fill(d,[(x+12,49+bob),(x+29,48+bob),(x+33,54+bob),(x+32,66),(x+26,68),
            (x+10,67),(x+8,60)],TEAL)
    d.line([(x+11,57+bob),(x+15,55+bob),(x+18,58+bob),(x+21,54+bob)],fill=TEAL_LIGHT,width=2)
    d.line([(x+12,64),(x+30,64)],fill="#a96e46",width=2)
    fill(d,[(x+10,48+bob),(x+24,47+bob),(x+28,51+bob),(x+24,54+bob),(x+14,53+bob),
            (x+8,59+bob),(x+8,54+bob)],COPPER)
    d.line([(x+11,50+bob),(x+22,49+bob)],fill="#ffda91")
    arm = {
        "rise": (x+34,52+bob), "strike": (x+39,56+bob),
        "follow": (x+37,61+bob), "idle": (x+33+gait//2,58+bob), "hurt": (x+31,56+bob)
    }[swing]
    d.line([(x+26,54+bob),(arm[0]-2,arm[1])],fill=INK,width=6)
    d.line([(x+26,54+bob),(arm[0]-2,arm[1])],fill=TEAL_LIGHT,width=3)
    blade(d,*arm,swing)
    hand(d,*arm)
    # Face on a 37-pixel silhouette with stepped opaque shading.
    fill(d,[(x+8,top+16),(x+14,top+9),(x+33,top+13),(x+38,top+21),(x+39,top+25),
             (x+44,top+27),(x+45,top+34),(x+40,top+39),(x+37,top+39),(x+32,top+45),
             (x+18,top+46),(x+10,top+42),(x+6,top+35),(x+6,top+26)], SKIN)
    fill(d,[(x+38,top+26),(x+43,top+27),(x+44,top+32),(x+40,top+36),(x+36,top+36),
            (x+37,top+32)],SKIN_SHADE)
    d.line([(x+9,top+38),(x+14,top+43),(x+22,top+44),(x+31,top+43),(x+35,top+40)],
           fill=SKIN_SHADE,width=2)
    d.line([(x+16,top+39),(x+19,top+40),(x+21,top+40)], fill="#eaa692")
    # Both bright eyes include separate iris and highlight clusters.
    left, right = x+13, x+28
    if index == 14:
        for eye in (left,right):
            d.line([(eye,top+29),(eye+4,top+32),(eye,top+34)], fill=INK, width=2)
        d.rectangle((x+24,top+37,x+26,top+39),fill="#9d624d")
    else:
        for eye in (left,right):
            pts=[(eye-2,top+28),(eye+4,top+27),(eye+6,top+30),(eye+5,top+36),(eye,top+37),(eye-2,top+34)]
            fill(d,pts,HIGHLIGHT)
            d.rectangle((eye,top+29,eye+4,top+35),fill="#258782")
            d.rectangle((eye+1,top+29,eye+3,top+34),fill="#142e39")
            d.point((eye+3,top+30),fill=HIGHLIGHT)
            d.line([(eye-1,top+27),(eye+4,top+27)],fill=INK,width=2)
        d.line([(x+25,top+39),(x+27,top+39)],fill="#9a5f4f")
    # Side-swept indigo hair with individual opaque highlight clusters.
    fill(d,[(x+4,top+7),(x+12,top+2),(x+17,top+2),(x+22,top-1),(x+34,top+1),(x+41,top+6),
             (x+44,top+12),(x+45,top+19),(x+41,top+27),(x+37,top+26),(x+35,top+18),
             (x+31,top+13),(x+30,top+21),(x+26,top+20),(x+23,top+12),(x+20,top+19),
             (x+15,top+23),(x+15,top+17),(x+11,top+23),(x+10,top+29),(x+6,top+32),
             (x+4,top+26),(x+1,top+20),(x+1,top+13)], HAIR)
    d.polygon([(x+5,top+11),(x+10,top+6),(x+20,top+3),(x+24,top+5),(x+16,top+7),
               (x+10,top+13),(x+8,top+18),(x+5,top+19)],fill=HAIR_SHADE)
    d.line([(x+6,top+12),(x+10,top+8),(x+15,top+5),(x+19,top+5)], fill=HAIR_LIGHT,width=2)
    d.polygon([(x+25,top+3),(x+33,top+3),(x+39,top+8),(x+41,top+14),(x+39,top+13),
               (x+33,top+8),(x+28,top+7)],fill=HAIR_SHADE)
    d.line([(x+28,top+4),(x+33,top+5),(x+36,top+8)],fill=HAIR_LIGHT,width=1)
    d.line([(x+20,top+10),(x+17,top+14),(x+14,top+16)],fill=HAIR_LIGHT,width=1)
    d.rectangle((x+4,top+21,x+7,top+24),fill="#dba870")
    d.point((x+5,top+21),fill="#ffde8a")
    return pic

def run():
    sheet = Image.new("RGBA",(320,320))
    for i in range(16):
        sheet.alpha_composite(frame(i),(i%4*80,i//4*80))
    sheet.save(ASSETS / "hero-crisp.png",optimize=True)

if __name__ == "__main__":
    run()
