"""Maplee's original paper-doll sprites. No source art or network access required.

30 columns of 80px cels per row. Rows pair masculine then feminine for the
jobs in JOBS. Native actors face right and register at (38,75). The final
two poses use the attack wind-up without the near or far weapon arm.
Skin ramp indices 2..6, hair ramp 7..11; these stay unique in decoded RGB.
"""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
JOBS = ("beginner", "guardian", "ranger", "mage", "thief", "pirate", "cleric")
PALETTE = [
    "000000", "272533", # transparent, ink
    "93604f", "c78d69", "e6af83", "f6cda2", "ffe6c0", # skin
    "342b40", "51394d", "755265", "a57784", "cc9aa1", # hair
    "fff5db", "d8e2dc", "9da8ae", "3b434d", "697980", "30333f",
    "85584c", "b77c58", "e8b579", "ffd98f", "c45d68", "f2938c",
    "528d97", "9fcbc4", "554151", "fffaff",
]
# Three local cloth colours per outfit.
CLOTH = (
    ("304c54","44777c","84b6a3"), ("3f4860","61718d","a2b4c4"),
    ("425039","728159","aeb786"), ("53465b","806785","bda3be"),
    ("433e55","686279","9c90a1"), ("854b42","b16a50","e2a675"),
    ("777268","b5ab91","eee4cb"),
)
for colors in CLOTH:
    PALETTE.extend(colors)
PAL = bytes.fromhex("".join(PALETTE)).ljust(768,b"\0")
NEAR = ((30,60),(29,60),(28,60),(29,60),(28,57),(36,61),(28,57),(26,56),
        (26,52),(45,54),(22,38),(35,60),(31,47),(31,49),(35,59),(35,59),
        (36,47),(26,47),(26,47),(35,60),(57,41),(55,46),(20,58),(35,60))
FAR = ((48,60),(48,60),(50,60),(48,60),(50,57),(47,57),(50,57),(52,52),
       (44,56),(25,53),(47,54),(47,56),(48,52),(48,54),(46,57),(48,54),
       (58,48),(58,48),(58,48),(47,56),(48,56),(49,53),(51,50),(47,56))
# Local head coordinates. Each fringe changes the hairline across the brow.
FRINGES = (
    [(1,16),(4,8),(12,4),(26,4),(34,8),(36,15),(31,13),(28,9),(29,14),(23,12),(18,9),(19,13),(12,16),(14,10),(8,15),(6,20)],
    [(1,16),(3,7),(11,3),(24,2),(32,6),(36,12),(35,16),(28,9),(29,13),(22,10),(24,15),(16,10),(12,14),(12,10),(6,18)],
    [(2,18),(2,8),(12,3),(28,3),(34,8),(36,15),(31,12),(29,9),(25,14),(20,16),(23,9),(18,12),(12,16),(14,10),(8,14),(6,21)],
    [(1,19),(2,9),(10,4),(25,2),(33,7),(35,15),(29,13),(26,10),(25,15),(22,18),(22,10),(17,13),(12,19),(12,12),(7,18),(5,23)],
    [(1,17),(4,8),(12,3),(27,2),(34,8),(36,16),(30,12),(30,17),(24,12),(20,16),(14,21),(17,11),(12,16),(9,19),(8,14),(5,21)],
    [(2,18),(4,8),(12,3),(27,3),(33,7),(35,13),(30,12),(27,9),(23,11),(20,8),(16,13),(16,9),(10,12),(8,16),(7,12),(5,21)],
    [(1,17),(4,8),(12,4),(25,4),(33,8),(35,16),(30,13),(27,9),(27,13),(22,13),(19,10),(17,14),(12,12),(13,9),(8,14),(6,20)],
)
CROWNS = (
    [(0,15),(2,8),(7,5),(12,4),(10,1),(17,3),(23,1),(29,3),(33,6),(35,12)],
    [(0,14),(3,6),(9,5),(7,1),(15,4),(18,0),(24,3),(28,1),(28,4),(34,6),(36,12)],
    [(0,15),(3,8),(9,4),(16,2),(21,4),(26,2),(33,6),(35,12)],
    [(0,16),(2,8),(8,4),(18,2),(24,3),(28,1),(29,4),(33,6),(35,12)],
    [(0,17),(2,9),(7,5),(15,3),(22,1),(27,3),(30,2),(34,6),(35,13)],
    [(1,15),(4,8),(8,6),(7,2),(13,4),(12,0),(20,3),(24,1),(28,4),(33,5),(35,11)],
    [(0,16),(2,9),(7,5),(15,3),(21,4),(24,2),(30,4),(34,8),(35,14)],
)


def new(size=(80,80)):
    layer=Image.new("P",size)
    layer.putpalette(PAL)
    return layer


def head(job, fem, blink, hurt, back):
    im=new((45,43))
    d=ImageDraw.Draw(im)
    def poly(pts,color,border=1):
        d.polygon([(x+5,y+3) for x,y in pts],fill=color,outline=border)
    def line(pts,color,width=1):
        d.line([(x+5,y+3) for x,y in pts],fill=color,width=width)
    if fem and job in (0,3,6):
        # Tied side braid tucked behind the ear, with overlapping woven locks.
        for x,y in ((2,20),(1,24),(1,28),(2,32),(3,35)):
            poly([(x-3,y-3),(x+1,y-4),(x+4,y-1),(x+3,y+3),(x,y+4),(x-3,y+1)],9,7)
            line([(x-1,y-2),(x+1,y-1)],10)
        line([(2,36),(5,36)],22,2)
    elif fem and job in (1,4,5):
        # High gathered knot gives the silhouette lift without changing the brow attachment.
        poly([(-3,8),(-2,4),(1,1),(6,0),(10,2),(10,7),(7,11),(1,13),(-2,11)],8,7)
        line([(-1,6),(1,3),(5,2)],10,2)
    elif job == 3:
        poly([(-2,14),(-3,9),(0,7),(-1,4),(5,5),(11,3),(10,7),(5,12),(2,17)],9,7)
    elif job == 5:
        poly([(-2,12),(-4,11),(0,7),(-1,5),(5,6),(11,2),(9,8)],8,7)
    if fem or job in (2,3):
        tail=[(3,14),(7,17),(7,26),(10,31),(8,34),(5,32),(4,36),(1,33),(-1,36),(-1,30),(-3,29),(0,24),(-1,20)]
        poly(tail,8)
        line([(1,20),(3,23),(2,29),(4,32)],9,2)
        if job in (0,2,5):
            poly([(-1,19),(3,18),(5,20),(3,22),(0,22)],22)
    else:
        poly([(1,14),(6,12),(10,18),(10,25),(8,30),(5,27),(4,30),(3,25),(0,24)],8)
    poly([(3,16),(7,11),(17,7),(27,8),(33,13),(35,18),(34,24),(35,25),(32,27),(30,30),(24,32),(16,32),(11,30),(8,27),(4,26),(2,22)],4)
    poly([(10,14),(18,10),(28,11),(32,15),(34,20),(33,24),(31,27),(27,29),(21,30),(16,30),(12,28),(10,24)],5,None)
    poly([(10,16),(18,12),(28,12),(31,15),(30,18),(24,19),(18,17),(12,20)],6,None)
    line([(14,29),(19,31),(24,31),(29,29)],3)
    poly([(2,19),(5,18),(8,21),(9,25),(6,26),(2,24),(1,22)],4)
    line([(3,21),(5,21),(6,23),(4,23)],2)
    line([(4,19),(6,20)],6)
    if not back:
        for x,y,w in ((13,19,7),(28,18,5)):
            line([(x-1,y-2),(x+1,y-3),(x+w-1,y-2)],8)
            if blink or hurt:
                line([(x,y+3),(x+2,y+1 if hurt else y+3),(x+w-1,y+2)],1)
                continue
            poly([(x,y+1),(x+2,y),(x+w-1,y),(x+w,y+1),(x+w-1,y+5),(x+2,y+6),(x,y+5)],12,None)
            poly([(x+2,y),(x+w-1,y),(x+w-1,y+4),(x+w-3,y+5),(x+2,y+4)],15,None)
            line([(x+3,y+3),(x+w-2,y+3)],24)
            line([(x+3,y+4),(x+w-2,y+4)],25)
            line([(x+3,y+1),(x+3,y+1)],27)
            line([(x-1,y+1),(x+1,y-1),(x+w-2,y-1),(x+w,y)],1)
            if fem:line([(x-2,y-1),(x,y+1)],1)
        line([(25,25),(26,25)],3)
        line([(24,28),(26,28),(27,27)],18)
        line([(11,25),(14,25)],23)
    base=CROWNS[job]+[(35,17),(30,14),(27,12),(16,13),(9,17),(6,22),(2,22)]
    poly(base,8)
    poly(FRINGES[job],9,7)
    poly(CROWNS[job]+[(32,9),(25,7),(18,8),(12,7),(6,12),(2,16)],9,7)
    line([(3,13),(5,9),(10,6),(15,5)],10,2)
    line([(10,6),(13,5)],11)
    line([(18,6),(22,5),(26,5),(30,7)],10,2)
    line([(21,5),(24,5)],11)
    line([(5,18),(7,14),(11,10)],8)
    if job==1: # small brass clasp
        poly([(6,14),(8,13),(10,14),(8,17),(6,16)],21,18)
    elif job==2: # twin leaves
        poly([(2,14),(-2,9),(0,8),(5,11),(6,14)],25,15)
        poly([(5,14),(3,8),(5,7),(8,12),(7,14)],24,15)
    elif job==3:
        poly([(7,11),(8,8),(9,11),(12,12),(9,13),(8,16),(7,13),(5,12)],21,18)
    elif job==4:
        line([(3,11),(6,9),(9,8)],16,2)
    elif job==5:
        line([(4,12),(10,9),(18,8),(27,8),(33,10)],22,2)
        line([(1,13),(-2,15)],22,2)
    elif job==6:
        line([(4,12),(6,8),(10,6),(14,5)],12,2)
        line([(4,11),(6,7)],21)
    if fem:
        poly([(1,15),(4,13),(6,14),(6,17),(3,18),(1,17)],10,7)
        line([(2,15),(4,14)],11)
    if back:
        poly([(2,12),(10,8),(28,9),(34,14),(33,22),(29,29),(24,32),(19,30),(16,32),(11,30),(6,29),(2,24)],8,7)
        line([(4,16),(7,20),(12,23),(15,24)],9,2)
        line([(19,22),(25,20),(30,16)],9,2)
    return im


def attach(im,layer,xy):
    im.paste(layer,xy,Image.frombytes("L",layer.size,layer.tobytes()).point(lambda p:255 if p else 0))


def actor(job,fem,cel,head_factory=None):
    pose=8 if cel>=28 else cel
    back=24<=pose<=27
    im=new(); d=ImageDraw.Draw(im)
    bob=(0,1,0,1)[pose%4] if pose<8 else 0
    leap=-4 if pose==12 else -2 if pose==13 else 0
    attack_offset={8:(3,2),9:(-2,-1),10:(4,2),16:(-3,-1),17:(-3,-1),18:(-3,-1),22:(2,1)}
    sx,sy=attack_offset.get(pose,(0,0))
    pelvis=(38+sx//2,60+bob+leap)
    nx,ny=38+sx,45+sy+bob+leap
    cloth=28+3*job
    def line(points,c,w=1):d.line(points,fill=c,width=w)
    def poly(points,c,edge=1):d.polygon(points,fill=c,outline=edge)
    feet=((34,73),(44,73))
    if 4<=pose<=7: feet=(((28,72),(47,72)),((39,69),(44,73)),((44,73),(30,71)),((48,69),(35,73)))[pose-4]
    elif pose in (8,10,22):feet=((22,73),(44,73))
    elif pose==9:feet=((30,68),(38,73))
    elif pose in (12,13):feet=((27,64+leap),(52,62+leap))
    elif back:feet=((33,70-(pose%2)*3),(44,67+(pose%2)*4))
    for side,foot in enumerate(feet):
        x,y=foot
        leg=(pelvis[0]+side*7-4,pelvis[1])
        knee=((leg[0]+x)//2+2,(leg[1]+y)//2)
        line([leg,knee,(x,y-1)],1,5);line([leg,knee,(x,y-1)],4,3)
        poly([(x-2,y-3),(x+1,y-3),(x+3,y-1),(x+5,y-1),(x+5,y+1),(x-3,y+1)],18)
        line([(x,y-2),(x+2,y-2)],20)
    near=NEAR[pose] if not back else ((31,45),(30,47),(31,53),(30,50))[pose-24]
    far=FAR[pose] if not back else ((45,53),(46,50),(45,45),(46,47))[pose-24]
    def arm(side,hand):
        shoulder=(nx+(-4 if side==0 else 5),ny+3)
        elbow=((hand[0]+shoulder[0])//2+(-2 if side==0 else 1),(hand[1]+shoulder[1])//2+2)
        line([shoulder,elbow,hand],1,6);line([shoulder,elbow,hand],3 if side else 4,4)
        x,y=hand
        poly([(x-3,y-2),(x-1,y-3),(x+2,y-2),(x+3,y),(x+2,y+3),(x-2,y+3),(x-3,y+1)],5)
        line([(x-1,y-2),(x+1,y-2)],6)
        line([(x-2,y+2),(x,y+2)],3)
    poly([(nx-3,ny-4),(nx+3,ny-4),(nx+3,ny+2),(nx-2,ny+3)],4)
    if cel!=29:arm(1,far)
    x,y=pelvis
    poly([(x-6,y-4),(x+6,y-4),(x+7,y+3),(x+1,y+4),(x,y+1),(x-3,y+5),(x-7,y+3)],16)
    poly([(nx-5,ny),(nx+3,ny-1),(nx+7,ny+3),(nx+5,ny+8),(x+7,y),(x+3,y+2),(x-8,y),(nx-7,ny+5)],cloth+1)
    line([(nx-4,ny+2),(nx-2,ny+4),(nx+1,ny+4),(nx+4,ny+1)],cloth+2,2)
    line([(nx+4,ny+6),(x+3,y-3)],cloth)
    line([(x-6,y-2),(x+5,y-1)],18,2)
    line([(x,y-2),(x+2,y-2)],21)
    if job in (2,4,5):line([(nx+4,ny+3),(x-4,y-3)],19,2)
    if job in (3,6):poly([(nx-5,ny+1),(nx+3,ny+2),(nx+1,ny+7),(nx-3,ny+5)],12,cloth)
    if cel!=28:arm(0,near)
    h = head_factory(pose,back) if head_factory else head(job,fem,pose==3,pose==14,back)
    attach(im,h,(nx-22,ny-36))
    return im


def run():
    atlas=new((30*80,14*80))
    for j in range(len(JOBS)):
        for fem in (0,1):
            for cel in range(30):
                atlas.paste(actor(j,fem,cel),(cel*80,(j*2+fem)*80))
    atlas.save(ROOT/"assets/maplee-avatars.png",transparency=0,optimize=True)


if __name__=="__main__":
    run()
