"""Native-resolution cels for a round, three-quarter-view head looking right."""
from PIL import Image, ImageDraw

COLORS = {
    "K": "#17151b", "B": "#1b191e", "C": "#35323a", "G": "#535058",
    "S": "#68626a", "H": "#8b858b",
    "F": "#ffead1", "L": "#fff3dc", "T": "#ffd9b0", "O": "#efb383",
    "R": "#de936f", "M": "#834f48", "U": "#fffaf0", "I": "#35323f",
    "A": "#565263", "V": "#838197", "W": "#b4b1c6", "P": "#e0daeb",
}


def stamp(draw, x, y, rows):
    for j, row in enumerate(rows.split()):
        for i, color in enumerate(row):
            if color != ".":
                draw.point((x+i,y+j), COLORS[color])


# Row spans keep the contour and silhouette independent of highlights.
SKIN = [
    (17,29),(14,32),(12,34),(10,36),(9,37),(8,38),(7,39),(6,39),
    (5,40),(5,41),(5,41),(4,42),(4,42),(4,42),(4,43),(4,43),
    (4,43),(4,44),(4,44),(4,44),(5,44),(5,44),(6,43),(6,43),
    (7,42),(8,42),(9,41),(10,40),(11,39),(13,38),(15,37),(17,35),
    (19,33),(22,30),
]
# The heavy left lobe opens onto an irregular part two-thirds across the head.
# Its lower edge has three different lengths of lock and ends behind the ear.
LEFT = [
    (12,19),(9,24),(7,26),(6,27),(5,28),(4,28),(3,28),(3,28),(2,27),
    (2,26),(1,25),(1,24),(1,22),(1,21),(1,20),(1,18),(0,17),(0,16),
    (0,14),(0,13),(0,11),(0,10),(1,9),(1,9),(1,8),(2,8),(2,8),(3,8),
    (3,7),(4,7),(4,7),
]
RIGHT = [
    (28,34),(26,37),(25,39),(25,40),(25,41),(25,42),(26,42),(27,43),
    (28,43),(30,44),(30,44),(31,44),(33,45),(34,45),(34,45),(36,45),
    (37,45),(38,45),(38,44),(39,44),(40,44),(41,43),(42,43),
]
GLINT_LEFT = """
.........BBCCCGCB..........
......BCCCGGGGGGCCB........
....BCGGGGSSSSSGGGGCB......
...BCGGSSSGSSSSGSGGGCCB....
..CCGSSGSSS...GSGSSGGGCB...
.BGGSSGS.GS....GSGS..GCCB..
BCGSGSSG..G....CCGG....CCB.
BCGGSGCG..C.....CCG.....CB.
.CGSGCCG.........CB........
.CGGCC.....................
..CC.......................
"""
GLINT_RIGHT = """
......BCCGCCB...
....BCGGSSGGCC..
..BCGSSSSGSGGCB.
.BCGSS.SGS.GGCCB
.CGSG..CGG..GCCB
.CGG....CG...CC.
..CC.....C......
"""
EAR = """
...KKKKK..
..KFFFTTK.
.KLFFFTTTK
.KLTOOOFTK
.KFOMRROTK
.KFOTTOOTK
..KFTOOTTK
..KFFTTOK.
...KFTOK..
....KKK...
"""
# Both pupils are shaded on the same side, with a single large catchlight and
# a tiny, separate reflected highlight. The far eye recedes under its lid.
NEAR_EYE = """
.....KKKIIIK.
..PPPPKKKKII.
.PPPUUKUUUKK.
.UUUUUKUUUKK.
.UUUUUKKIIIK.
.UUUUUKIIIUK.
..UUUUKKIAIK.
..UUUUKAIVAK.
..UUUUIAVVAK.
...UUUUIVAAU.
...UUUUUPPUP.
....KKKKKKK..
"""
FAR_EYE = """
...IIKKK.
..KKKKPP.
..KUUUIUP
..KUUUIUU
..KKIIKUU
..KIIIKUU
..KAIAKUU
..KAVAKU.
..KAVVKU.
...UWAUU.
...UUUU..
...KKKK..
"""


def flesh(draw):
    # Softly lit cheeks retain a one-pixel warm turn at the jaw.
    for row, (left,right) in enumerate(SKIN):
        y = row+9
        draw.line((left,y,right,y), fill=COLORS["K"])
        if row == len(SKIN)-1:
            continue
        light = "O" if row in (29,30,31,32) else "T"
        draw.line((left+1,y,right-1,y), fill=COLORS[light])
        if row < 31:
            draw.line((left+3,y,right-2,y), fill=COLORS["F"])
    stamp(draw,10,29,"..TTT..... TOOOOTT... .TOOOT.... ...TT.....")
    stamp(draw,39,31,".TTT OOTT TTT.")
    stamp(draw,12,35,".LLLLL. ...LLL.")
    stamp(draw,22,40,"TTTTTTTTTTT")


def hair(draw):
    for spans in (LEFT, RIGHT):
        for y,(left,right) in enumerate(spans):
            draw.line((left,y,right,y), fill=COLORS["K"])
            if right-left>4 and y>1:
                draw.line((left+2,y,right-2,y),fill=COLORS["B"])
    stamp(draw,3,3,GLINT_LEFT)
    stamp(draw,27,2,GLINT_RIGHT)
    stamp(draw,7,5,"....GSSS.... ..GGSHHSG... .CGSSSSG.... .CGG..GC....")
    stamp(draw,32,4,".SSG.. .SHSS. ..SSSG ...GGG")
    # Three locks split at different heights. Their curved tips leave a little
    # skin breathing room above the brow instead of a straight diagonal part.
    stamp(draw,17,10, """
....BBKKKK...
...BBKKKK....
..BBKKK......
.BBKKK.......
BKKK.........
KK...........
K............
""")
    stamp(draw,23,6,".BBKKKK. ..BKKKBK ...KKKK. ....KKK. .....KK. .....OK.")
    # A hooked lock crosses the brow-side part before separating into a tip.
    stamp(draw,18,9, """
.....BBKKKK.
....BBBKKKK.
...BBKKKKK..
..BBKKKK.K..
.BBKKKK..K..
BKKKKKK..O..
KKKK..K.....
KK....O.....
""")
    stamp(draw,32,9, "BBKK.... .BBKK... ..BKKK.. ...KKKK. ....K.KK ......OK")
    stamp(draw,2,21, """
...CCB..
..CGGCB.
.CGSGGC.
.CSGCGG.
.CSGCCB.
..CGGCB.
..CCGGC.
...CGCB.
...CCB..
""")


def eyes(draw, expression):
    if expression in ("open","attack"):
        stamp(draw,12,24,NEAR_EYE)
        stamp(draw,33,24,FAR_EYE)
    elif expression == "half":
        stamp(draw,13,26,".KKKKKKKKKK.. KKPIIIIIIPPK .PUKIIIVUUK. .UUIIIAVUUK. ..UUAAVVUUP. ...UUWWUUP.. ....KKKKK...")
        stamp(draw,34,26,".KKKKKK. KIIPIIIK .UIIIAUK .UIAVVUK ..UWWUU. ...KKK..")
    elif expression == "hurt":
        stamp(draw,14,26, "KK........ .KKKK..... ...KKKK... .....KKKK. ...KKKK... .KKK......")
        stamp(draw,35,25, ".....KK. ...KKK.. .KKK.... KK...... ..KKK... ....KK..")
    else:
        stamp(draw,13,28, "KK......... .KK......KK ..KKKKKKKK. ....KKKK...")
        stamp(draw,35,28, ".....KK. KK..KK.. .KKKK...")
    # Near brow is fuller and slightly arched; far brow is foreshortened.
    level = 1 if expression in ("hurt","attack") else 0
    stamp(draw,12,19+level,"..KKKKKK..... .KKKKKKKKK... KKKBBKKKKKK.. KKKBBIIKKKKK. KKKKKKKIIIKKK ....KKKKKKKK.")
    stamp(draw,33,19+level,".....KKKK ....KKBBKK ..KKKIIKKK .KKKIIKKK. KKKIIKK... .KKKK.....")


def head(expression="open"):
    image = Image.new("RGBA",(46,45))
    draw = ImageDraw.Draw(image)
    if expression == "back":
        back = [(13,22),(10,32),(8,35),(6,38),(5,39),(4,40),(3,41),(2,42),
                (2,43),(1,43),(1,44),(1,44),(0,44),(0,45),(0,45),(0,45),
                (0,45),(0,45),(0,45),(0,45),(0,45),(1,45),(1,45),(1,44),
                (2,44),(2,43),(3,43),(3,42),(4,42),(4,41),(5,40),(5,40),
                (6,39),(6,39),(7,38),(8,37),(9,36),(10,35),(12,34),
                (13,32),(15,31),(17,29),(19,28)]
        for y, (left,right) in enumerate(back):
            draw.line((left,y,right,y),fill=COLORS["K"])
            if right-left>5 and y>1:
                draw.line((left+2,y,right-2,y),fill=COLORS["B"] if y<34 else COLORS["C"])
        stamp(draw,3,3,GLINT_LEFT)
        stamp(draw,28,3,GLINT_RIGHT)
        stamp(draw,6,28,"..C....... ...CC..... ...BCCG... ....BCGC.. .....BCG.. ......BC..")
        stamp(draw,22,31,"...CC........ ......C...... ......CC..... ..CC...CC.... ...CC...GG... ....CC...GG.. .....C....GC.")
        stamp(draw,16,38,"KCCBCCCBCCBBBK .KKBBCCCBBKKK. ..KKBKKBBKK... ....K..KK.....")
        return image
    flesh(draw)
    hair(draw)
    stamp(draw,6,19,"..KKKKK. .KKCCCBK KCGGCGCK KGSSGCBK KSGGGCK. KGGCCBK. KCCCBK.. .KCBK... ..KK....")
    stamp(draw,1,24,EAR)
    eyes(draw,expression)
    stamp(draw,26,24, ".TTTT. TTOOTT TTOOTT TTTOTT ..TTTT ...TT.")
    stamp(draw,30,37, ".KK. KMRK .KK." if expression=="hurt" else "KKK")
    return image
