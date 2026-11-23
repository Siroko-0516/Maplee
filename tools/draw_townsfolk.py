"""Paint six field NPCs in four 80px idle cels."""
from pathlib import Path

from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parents[1] / "assets"
ROLES = ("quest", "shop", "trainer", "guide", "harbor", "forge")
INK = "#28212b"
PAPER = "#fff4cd"

# Skin, hair and cloth use independent ramps so skin tones remain stable.
COLORS = {
    "quest":  (("#fff0d9","#f3bc93","#c77f66"), ("#59313c","#985040","#cd8052"), ("#47665e","#72ad88","#b2d8a2")),
    "shop":   (("#f1c18d","#d79369","#a7634d"), ("#503536","#765046","#a2755c"), ("#6e4940","#b27546","#e1a864")),
    "trainer":(("#f8d5ad","#d99f7e","#b67561"), ("#302b3d","#4e4459","#75637a"), ("#415467","#587b88","#9eb8ac")),
    "guide":  (("#ffe6c5","#eeb793","#be806a"), ("#72513d","#ac7748","#dea65d"), ("#486655","#75a46b","#a9c47f")),
    "harbor": (("#e0bf9d","#c7997b","#a57461"), ("#62666b","#93918b","#c2bba4"), ("#3f5165","#637e91","#9bb3b1")),
    "forge":  (("#dfab82","#bd8766","#9b6553"), ("#4f3740","#764847","#a66850"), ("#724c44","#a27552","#d6a469")),
}


def cloth(d, points, fill, edge=INK):
    d.polygon(points, fill=fill, outline=edge)


def stamp(d,x,y,rows,colors):
    for j,row in enumerate(rows.split()):
        for i,key in enumerate(row):
            if key != ".":
                d.point((x+i,y+j),colors[key])


def boots(d, x, top, facing=False):
    cloth(d,[(x+1,top),(x+7,top),(x+7,top+5),(x+10,top+6),
             (x+11,top+8),(x+10,top+9),(x,top+9),(x-1,top+6)],"#654b48")
    d.line((x+1,top+7,x+8,top+7),"#bd946f")
    d.line((x+1,top+1,x+6,top+1),"#957754")


def body(d,role,dy):
    skin,_,(dark,mid,light)=COLORS[role]
    boots(d,28,65)
    boots(d,38,65)
    d.polygon([(29,60),(44,60),(46,66),(43,68),(38,68),(36,65),(34,68),(28,67)],"#434654",INK)
    x,y=27,43+dy
    coat = [(x+7,y),(x+11,y-2),(x+15,y),(x+19,y+3),(x+18,y+13),
            (x+21,y+21),(x+13,y+23),(x+9,y+20),(x+6,y+23),(x-1,y+21),
            (x+1,y+14),(x,y+5)]
    cloth(d,coat,mid)
    d.polygon([(x+1,y+8),(x+4,y+4),(x+7,y+6),(x+5,y+14),(x+4,y+21),(x,y+21)],dark)
    d.line([(x+5,y+3),(x+9,y+6),(x+13,y+3),(x+16,y+4)],light,2)
    d.line([(x+3,y+20),(x+8,y+19),(x+10,y+20),(x+15,y+20),(x+18,y+19)],light)
    if role in ("shop","forge"):
        cloth(d,[(32,y+6),(38,y+7),(41,y+5),(42,y+7),(41,y+14),(44,y+21),
                 (40,y+22),(29,y+21),(31,y+13)],"#8f6952" if role=="forge" else "#e8cf99")
        d.line((33,y+14,39,y+14),dark,2)
        d.point((34,y+13),PAPER)
    elif role=="quest":
        cloth(d,[(31,y+1),(37,y+4),(38,y+1),(40,y+3),(37,y+8),(34,y+6),(31,y+7)],"#f2dec2")
        d.line([(31,y+8),(35,y+11),(41,y+12)],"#824d46",2)
    elif role in ("trainer","guide"):
        d.line([(40,y+3),(36,y+10),(31,y+16)],"#604b46",3)
        d.line([(40,y+3),(36,y+10),(31,y+16)],"#c49c6a")
        d.line((29,y+14,44,y+14),"#7f5640",2)
        d.rectangle((36,y+13,38,y+15),fill="#e7bc6a")
    else:
        d.line((36,y+6,36,y+20),dark,2)
        for j in (7,12,17):
            d.rectangle((38,y+j,39,y+j+1),fill="#d2b576")


def face(d,role,dy,blink):
    skin,hair,_=COLORS[role]
    y=14+dy
    # Hair behind the cheek includes a gather, braid or stray curl.
    if role in ("quest","guide"):
        for i,(x,yy,w) in enumerate(((17,24,8),(14,28,8),(12,32,7),(11,36,5))):
            cloth(d,[(x+2,y+yy-4),(x+w-1,y+yy-3),(x+w,y+yy),(x+3,y+yy+3),(x,y+yy)],hair[1])
            d.line((x+2,y+yy-1,x+4,y+yy-2),hair[2])
        d.line((12,y+37,16,y+36),"#c9c87e" if role=="guide" else "#c17674",2)
    face_width=2 if role in ("shop","forge") else 0
    cloth(d,[(20,y+6),(26,y+1),(40,y),(49,y+4),(54,y+10),(55,y+16),
             (55,y+19),(57,y+21),(56,y+24),(53+face_width,y+25),(53,y+28),(49,y+31),
             (44,y+33),(36,y+34),(29,y+33),(25,y+30),(22,y+26),(19,y+24),(17,y+18)],skin[1])
    d.polygon([(22,y+10),(30,y+5),(44,y+5),(51,y+8),(53,y+13),(53,y+19),
               (55,y+21),(54,y+23),(51,y+25),(51,y+27),(47,y+30),(41,y+31),
               (33,y+31),(28,y+28),(26,y+24),(22,y+22)],skin[0])
    cloth(d,[(18,y+17),(23,y+18),(25,y+21),(24,y+25),(22,y+26),(18,y+24),(16,y+21)],skin[1])
    d.line([(18,y+20),(20,y+19),(22,y+21),(20,y+22)],skin[2])
    d.line((27,y+25,30,y+25),skin[1],2)
    # Lashes, a small clear iris and a receding far eye.
    colors={"k":INK,"i":"#55434d","l":PAPER,"w":"#fffaf0","s":"#99858a"}
    if role in ("harbor","shop"):
        eyes=("..kkkk.. .kkiikk. wwiilww. .wissw.. ..kkk...",".kkk. kiilw .isw. ..kk.")
    else:
        eyes=("..kkkkk. .kkiiikk kwwliiik .wwkliik .wwiiisk ..wsssw. ...kkk..",
              ".kkkk. kiilik wikilk .wissk ..wss. ..kk..")
    if blink:
        eyes=(".....kk. .kkkkkk. kk......", "kk... .kkkk")
    stamp(d,29,y+15,eyes[0],colors)
    stamp(d,46,y+15,eyes[1],colors)
    d.line([(30,y+13),(34,y+12),(37,y+13)],hair[0],2)
    d.line([(46,y+13),(49,y+12),(51,y+12)],hair[0])
    d.point((43,y+22),skin[2])
    d.line([(41,y+26),(43,y+27),(46,y+26)],"#865748")
    if role=="harbor":
        cloth(d,[(27,y+24),(29,y+26),(35,y+28),(38,y+27),(41,y+26),(45,y+27),
                 (50,y+25),(51,y+25),(50,y+30),(47,y+34),(42,y+36),(38,y+35),
                 (34,y+36),(32,y+32),(29,y+31)],hair[1])
        d.line([(34,y+29),(37,y+31),(39,y+31)],hair[2],2)
        d.line((41,y+28,45,y+28),hair[0])
    elif role in ("shop","forge"):
        d.line([(36,y+25),(40,y+23),(43,y+24),(46,y+23),(50,y+25)],hair[0],2)
    # Front hair mass, covering forehead with a staggered hairline.
    cloth(d,[(17,y+22),(15,y+18),(15,y+10),(17,y+5),(23,y+1),(29,y-3),(38,y-3),
             (44,y-2),(49,y+1),(52,y+3),(54,y+8),(54,y+12),(52,y+14),(49,y+10),
             (48,y+12),(45,y+10),(43,y+6),(41,y+9),(37,y+12),(34,y+14),(35,y+9),
             (32,y+11),(28,y+13),(27,y+16),(24,y+18),(23,y+21),(22,y+15),
             (20,y+18),(20,y+23)],hair[0])
    d.polygon([(17,y+12),(19,y+6),(25,y+2),(34,y),(38,y+1),(36,y+3),
               (29,y+4),(25,y+8),(23,y+9),(22,y+14),(19,y+16)],hair[1])
    d.line([(20,y+9),(23,y+5),(29,y+2),(33,y+2)],hair[2],2)
    d.line([(39,y+1),(44,y+2),(49,y+6)],hair[1],2)
    d.point((27,y+6),hair[2])


def hat(d,role,dy):
    y=dy
    if role=="quest":
        # A paper flower pinned into the gathered braid.
        cloth(d,[(17,y+17),(14,y+13),(17,y+11),(19,y+13),(21,y+10),(24,y+12),(23,y+16),
                 (26,y+16),(24,y+20),(21,y+20),(18,y+22),(16,y+20)],"#d87873")
        d.rectangle((19,y+15,21,y+17),fill="#ffe5a1")
    if role in ("shop","guide"):
        primary,shadow,glint=("#b67e4d","#805341","#edbe77") if role=="shop" else ("#ae9764","#7b7051","#f0d490")
        cloth(d,[(15,y+20),(16,y+14),(19,y+8),(23,y+4),(30,y+3),(35,y+5),(41,y+4),
                 (47,y+6),(50,y+10),(50,y+18),(55,y+19),(59,y+21),(57,y+23),
                 (51,y+24),(42,y+22),(34,y+20),(24,y+19),(19,y+21),(14,y+22)],primary)
        d.line([(18,y+15),(26,y+13),(33,y+14),(42,y+17),(49,y+17)],shadow,3)
        d.line([(18,y+17),(28,y+15),(39,y+17),(51,y+20),(55,y+21)],glint)
        d.line([(22,y+10),(25,y+7),(31,y+6)],glint,2)
        if role=="guide":
            cloth(d,[(24,y+15),(19,y+12),(18,y+7),(16,y+2),(20,y+3),(23,y+7),(26,y+13)],"#6c9f7d")
            d.line((18,y+4,24,y+14),"#b7d398")
        else:
            d.line([(28,y+32),(29,y+29),(36,y+29),(38,y+31),(37,y+36),(31,y+37),(28,y+35),(28,y+32)],"#735a43")
            d.line([(38,y+31),(44,y+31),(46,y+29),(51,y+29),(52,y+33),(50,y+35),(46,y+35),(44,y+32)],"#735a43")
    if role=="trainer":
        cloth(d,[(15,y+22),(18,y+17),(24,y+14),(31,y+13),(40,y+14),(47,y+16),(52,y+18),(53,y+21),
                 (49,y+20),(41,y+18),(33,y+17),(24,y+18),(18,y+21),(12,y+25),(10,y+24)],"#b95951")
        d.line([(20,y+17),(28,y+15),(35,y+15)],"#ee9470")
    if role=="harbor":
        cloth(d,[(15,y+20),(16,y+13),(20,y+9),(22,y+6),(31,y+5),(37,y+3),(44,y+5),(49,y+8),
                 (52,y+15),(55,y+18),(54,y+22),(49,y+23),(42,y+20),(35,y+19),(27,y+19),(18,y+23)],"#476377")
        d.line([(18,y+18),(24,y+15),(34,y+14),(43,y+16),(52,y+19)],"#90a8ad",3)
        for x in (22,27,32,37,42):
            d.line((x,y+10,x-2,y+13),"#638396")
    if role=="forge":
        d.line([(16,y+20),(22,y+15),(33,y+12),(49,y+13)],"#593b36",4)
        for x,yy in ((25,y+10),(39,y+9)):
            cloth(d,[(x,yy+1),(x+3,yy-1),(x+9,yy),(x+10,yy+6),(x+7,yy+9),(x+1,yy+8),(x-1,yy+4)],"#c78d53")
            d.rectangle((x+2,yy+1,x+7,yy+6),fill="#507486",outline="#645360")
            d.line((x+3,yy+4,x+5,yy+2),"#dcf2e1")


def prop(d,role,y):
    if role=="quest":
        cloth(d,[(44,y+49),(51,y+47),(55,y+49),(55,y+60),(47,y+62),(43,y+61)],"#944f55")
        d.line([(46,y+51),(51,y+50),(53,y+50)],"#e2ab82")
        d.line((47,y+58,53,y+56),PAPER)
    elif role=="shop":
        cloth(d,[(45,y+60),(46,y+55),(49,y+52),(47,y+48),(51,y+49),(54,y+47),(55,y+50),
                 (53,y+53),(57,y+56),(57,y+60),(54,y+63),(48,y+63)],"#b98249")
        d.line((47,y+54,54,y+53),PAPER)
        d.rectangle((51,y+57,53,y+60),fill="#edc66d")
    elif role=="trainer":
        cloth(d,[(44,y+58),(54,y+45),(61,y+38),(64,y+37),(64,y+41),(56,y+51),(48,y+60)],"#be8754")
        d.line((49,y+55,62,y+39),"#f4d099")
        d.line((44,y+53,52,y+59),"#68483a",3)
    elif role=="guide":
        d.line([(51,73),(52,y+51),(54,y+39),(57,y+37)],INK,4)
        d.line([(51,72),(52,y+51),(54,y+39),(57,y+37)],"#b89268",2)
    elif role=="harbor":
        d.line([(47,y+57),(49,y+53),(52,y+52),(55,y+54),(56,y+59)],"#847053",2)
        cloth(d,[(48,y+58),(56,y+58),(57,y+60),(56,y+68),(54,y+69),(49,y+68),(48,y+66)],"#b68b57")
        d.rectangle((50,y+60,54,y+65),fill="#fedc83")
        d.line((52,y+60,52,y+65),"#fff0b0")
    else:
        d.line([(46,y+60),(58,y+40)],INK,5)
        d.line([(47,y+59),(58,y+41)],"#b98b68",2)
        cloth(d,[(53,y+37),(57,y+36),(67,y+43),(66,y+48),(62,y+50),(52,y+42)],"#62717a")
        d.line([(54,y+38),(57,y+38),(65,y+44)],"#b4bdba",2)


def frame(role,index):
    img=Image.new("RGBA",(80,80))
    dy=(0,1,1,0)[index]
    skin,_,cloth_colors=COLORS[role]
    d=ImageDraw.Draw(img)
    body(d,role,dy)
    prop(d,role,dy)
    face(d,role,dy,index==2)
    hat(d,role,dy)
    cloth(d,[(42,48+dy),(46,48+dy),(48,51+dy),(48,54+dy),(45,55+dy),(42,53+dy)],cloth_colors[1])
    cloth(d,[(44,54+dy),(47,53+dy),(50,52+dy),(52,53+dy),(52,56+dy),
             (50,58+dy),(47,58+dy),(44,57+dy)],skin[1])
    d.line((46,55+dy,50,54+dy),skin[0],2)
    if index==3:
        # Long held idle with the prop-bearing hand back at rest, eyes reopened.
        d.point((49,56+dy),skin[0])
    return img


if __name__=="__main__":
    atlas=Image.new("RGBA",(320,480))
    for r, role in enumerate(ROLES):
        for i in range(4):
            atlas.paste(frame(role,i),(80*i,80*r))
    atlas.save(ASSETS/"townsfolk.png",optimize=True)
