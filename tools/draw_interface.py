"""Rebuild the original in-game menu atlas. Draw at the final pixel resolution."""
from pathlib import Path

from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parents[1] / "assets"
INK = "#242336"
GOLD = "#edb14d"
CREAM = "#fff2ba"


def tile():
    image = Image.new("RGBA", (32, 32))
    return image, ImageDraw.Draw(image)


def status():
    image, d = tile()
    # A surveyor's silver shield with the gold sprout of the village.
    d.polygon([(4,6),(10,6),(14,3),(17,3),(21,6),(27,6),(27,17),
               (25,21),(21,25),(16,29),(13,28),(7,23),(4,18)], "#d0c0a3", INK)
    d.line([(5,7),(10,7),(15,4),(17,4),(21,7),(25,7)], "#fff6c9")
    d.polygon([(7,9),(12,8),(16,6),(21,9),(24,9),(24,17),(21,22),(16,26),
               (11,22),(8,18)], "#465b77", INK)
    d.polygon([(8,10),(12,9),(16,7),(16,23),(12,20),(9,17)], "#66829c")
    d.line([(25,9),(25,18),(22,22),(18,25)], "#826657")
    d.line([(15,21),(15,18),(18,14),(20,12)], "#633e42", 3)
    d.polygon([(11,12),(14,13),(16,16),(15,17),(12,16),(10,13)], GOLD)
    d.polygon([(16,16),(17,12),(21,10),(22,10),(21,13),(18,16)], "#ffdb6d")
    d.line([(16,20),(16,17),(20,12)], CREAM)
    return image


def skill():
    image, d = tile()
    # Lightning captured between two shards of amethyst.
    d.polygon([(4,26),(7,20),(8,15),(13,10),(18,6),(27,4),(25,11),(20,17),
               (16,19),(11,25),(6,28)], "#623784", INK)
    d.polygon([(8,23),(11,16),(16,11),(23,8),(20,14),(18,16),(14,17),
               (14,20)], "#bd77e0")
    d.polygon([(11,21),(14,15),(13,15),(20,10),(23,9),(18,14),(20,14)],
              "#fff1a5")
    d.line([(8,26),(12,23),(15,19)], "#eb9ee9")
    d.polygon([(3,12),(6,11),(7,7),(8,10),(11,11),(8,12),(7,15),(6,13)], "#99d7eb", INK)
    d.point((7,11), "#ffffff")
    d.polygon([(20,22),(23,21),(24,18),(25,21),(28,22),(25,23),(24,26),
               (23,23)], "#ffdc96", "#82495e")
    d.point((24,22), "#ffffff")
    return image


def bag():
    image, d = tile()
    d.polygon([(10,8),(11,4),(14,3),(17,3),(20,5),(20,9),(18,9),(17,6),
               (14,6),(13,9)], "#c48c56", INK)
    d.polygon([(7,10),(10,8),(20,8),(24,11),(25,16),(27,17),(27,24),
               (24,27),(8,27),(4,24),(4,18),(6,16)], "#985139", INK)
    d.rectangle((23,18,26,22), fill="#ca8345", outline="#573b36")
    d.rectangle((5,19,8,22), fill="#ca8345", outline="#573b36")
    d.polygon([(8,10),(11,8),(20,8),(23,11),(22,16),(18,19),(13,19),
               (8,16)], "#327573", INK)
    d.line([(9,11),(12,9),(19,9),(21,10)], "#8ec9a4")
    d.line([(9,15),(13,17),(18,17),(21,15)], "#509b81")
    d.polygon([(9,21),(12,19),(20,19),(22,21),(21,25),(10,25)], "#bf7441", "#6d3e35")
    d.line([(10,21),(13,20),(19,20)], "#e9a557")
    d.rectangle((14,15,18,21), fill=GOLD, outline="#493334")
    d.rectangle((15,16,17,18), fill="#5d5150")
    d.point((15,16), CREAM)
    return image


def journal():
    image, d = tile()
    d.polygon([(5,9),(7,6),(21,3),(25,6),(26,23),(23,26),(9,29),(5,26)],
              "#66507c", INK)
    d.polygon([(7,22),(22,19),(25,20),(24,24),(10,27),(7,26)], "#f4dfac", INK)
    d.line([(10,25),(23,22)], "#bd9a7e")
    d.polygon([(5,8),(20,4),(24,6),(24,20),(9,24),(5,22)], "#846298", INK)
    d.line([(8,9),(8,21)], "#63426e")
    d.line([(9,8),(20,5)], "#c49bb5")
    d.polygon([(11,10),(14,8),(18,8),(21,9),(21,15),(18,17),(14,18),
               (11,16)], "#be8648", "#50354b")
    d.polygon([(13,11),(17,9),(20,10),(20,14),(15,16),(13,15)], "#483653")
    d.line([(15,14),(16,12),(18,11)], "#f3ce84")
    d.polygon([(16,24),(19,23),(19,28),(17,27),(16,29)], "#cb645c", "#693c50")
    d.point((22,7), CREAM)
    d.point((10,20), GOLD)
    return image


def map_icon():
    image, d = tile()
    d.polygon([(3,9),(10,5),(17,8),(23,4),(27,7),(27,23),(21,27),(15,24),
               (9,28),(3,25)], "#dbbd81", INK)
    d.polygon([(4,10),(10,7),(10,23),(8,26),(4,24)], "#fff1b5")
    d.polygon([(11,7),(17,10),(16,23),(11,24)], "#cba470")
    d.polygon([(17,10),(23,6),(25,7),(25,21),(21,25),(17,23)], "#f0dca2")
    d.line([(5,18),(7,16),(9,17),(12,15),(14,16),(16,15),(19,15),
            (21,13),(25,13)], "#548d99", 2)
    d.polygon([(5,13),(7,10),(9,12),(9,13)], "#63815e")
    d.polygon([(18,12),(21,8),(23,11),(23,12)], "#78915f")
    for x,y in [(7,22),(9,21),(11,20),(13,20),(15,19),(16,18)]:
        d.point((x,y), "#986349")
    d.line([(19,17),(23,20)], "#a44c45", 2)
    d.line([(23,16),(19,21)], "#a44c45", 2)
    return image


def bestiary():
    image, d = tile()
    # Field guide with brass book corners and a pressed paw on the enamel cover.
    d.polygon([(5,6),(8,4),(23,4),(26,7),(26,24),(23,27),(8,28),
               (5,26)], "#386963", INK)
    d.polygon([(7,23),(23,22),(25,23),(23,25),(9,26),(7,25)], "#e7d6a1", INK)
    d.polygon([(6,6),(22,5),(24,7),(24,21),(8,24),(6,22)], "#46867a", INK)
    d.line([(9,7),(9,21)], "#305d5c")
    d.line([(7,8),(7,20)], "#89af85")
    d.polygon([(12,17),(14,14),(16,13),(18,14),(20,16),(20,18),(17,19),
               (15,18),(13,19)], "#ffcf88", "#694f48")
    for x,y in [(11,12),(14,9),(17,8),(20,10)]:
        d.rectangle((x,y,x+2,y+3), fill="#eaba7d", outline="#745a4b")
    d.line([(19,6),(22,6),(23,8)], "#f4d779")
    d.line([(20,20),(23,19),(23,17)], GOLD)
    return image


def account():
    image, d = tile()
    d.polygon([(5,5),(23,5),(26,8),(26,24),(24,26),(6,26),(4,24),
               (4,7)], "#9ca5ac", INK)
    d.rectangle((6,7,24,24), fill="#496890", outline="#5d6772")
    d.line([(6,6),(22,6)], "#e7e1c3")
    d.rectangle((12,3,18,8), fill="#b68c57", outline=INK)
    d.line([(14,4),(16,4)], CREAM)
    d.polygon([(8,22),(10,19),(13,18),(18,18),(22,21),(22,23),(8,23)],
              "#729b9f", "#2e4051")
    d.polygon([(13,18),(16,21),(18,18)], "#f8e5bc")
    d.polygon([(11,12),(13,9),(18,9),(20,11),(19,16),(17,18),(14,18),
               (12,16)], "#efbf89", "#573f40")
    d.polygon([(11,14),(11,11),(14,9),(18,9),(20,11),(20,13),(17,12),
               (15,13),(15,12),(13,14)], "#593f43")
    d.point((15,15), INK); d.point((18,14), INK)
    return image


def settings():
    image, d = tile()
    gear = [(13,3),(18,3),(19,7),(21,8),(24,6),(27,9),(25,13),(26,14),
            (29,14),(29,19),(25,20),(24,22),(26,25),(23,28),(19,25),
            (18,26),(18,29),(13,29),(12,25),(10,24),(7,26),(4,22),
            (7,19),(6,18),(3,17),(3,12),(7,12),(8,10),(6,7),(10,4),(12,7)]
    d.polygon(gear, "#ac7445", INK)
    d.line([(13,5),(17,5),(18,8)], CREAM)
    d.line([(4,13),(7,13),(9,10)], "#edc184")
    d.line([(8,7),(10,6),(12,8)], "#edc184")
    d.line([(22,8),(24,7),(25,9)], "#edc184")
    d.ellipse((8,8,23,23), fill=GOLD, outline="#764f3d")
    d.arc((9,9,22,22), 200, 315, fill=CREAM)
    d.ellipse((11,11,20,20), fill="#375e75", outline=INK)
    d.line([(13,16),(13,14),(15,13),(17,13)], "#93c8c9")
    return image


def pause():
    image, d = tile()
    d.polygon([(8,4),(23,4),(27,8),(27,23),(23,27),(8,27),(4,23),(4,8)],
              "#85959b", INK)
    d.line([(5,9),(9,5),(22,5)], "#e8e2c6")
    d.polygon([(9,7),(22,7),(24,9),(24,22),(22,24),(9,24),(7,22),(7,9)],
              "#435c6e", "#364354")
    d.line([(8,20),(8,10),(11,8),(21,8)], "#7290a0")
    for x in (11,17):
        d.rectangle((x,10,x+3,21), fill="#d79846", outline="#473a3c")
        d.rectangle((x+1,11,x+2,19), fill="#f8ca72")
        d.line([(x+1,11),(x+2,11)], CREAM)
    return image


def frame(rings):
    """Corner pixel profiles are fixed; all edge centers can be stretched."""
    image, d = tile()
    steps = [3, 2, 2, 1, 1, 0]
    for i,(top, bottom) in enumerate(rings):
        end, cut = 31-i, steps[i]
        d.polygon([(i+cut,i),(end-cut,i),(end,i+cut),(end,end-cut),(end-cut,end),
                   (i+cut,end),(i,end-cut),(i,i+cut)], fill=top)
        d.line([(i,end-cut),(i+cut,end),(end-cut,end),(end,end-cut),(end,i+cut)],
               fill=bottom)
    return image


def portrait():
    # The wind observatory, viewed from its arcaded balcony.
    im = Image.new("RGB", (120,100), "#6195b9")
    d = ImageDraw.Draw(im)
    d.rectangle((0,21,119,40), fill="#78acc5")
    d.rectangle((0,41,119,58), fill="#96c4ce")
    d.rectangle((0,59,119,83), fill="#c3d8cf")
    clouds = [(1,16,19),(26,27,13),(33,7,8),(62,19,22),(92,9,18),(108,35,9)]
    for x,y,w in clouds:
        d.rectangle((x-5,y+4,x+w+5,y+5), fill="#a2c7d5")
        d.polygon([(x,y+4),(x+2,y+2),(x+5,y+2),(x+6,y),(x+10,y),
                   (x+12,y+2),(x+w,y+2),(x+w+2,y+4)], fill="#dce6dc")
    d.polygon([(0,58),(12,52),(16,54),(29,41),(39,52),(45,48),(54,55),
               (71,37),(78,45),(83,42),(99,55),(111,44),(119,50),(119,75),(0,75)],
              fill="#84acad")
    d.polygon([(54,55),(71,37),(73,41),(71,40),(67,48),(65,46)], "#c7d6cc")
    d.polygon([(20,51),(29,41),(33,46),(28,44),(26,48)], "#c7d6cc")
    d.polygon([(0,63),(16,58),(24,62),(40,54),(57,62),(74,51),(90,59),
               (107,51),(119,53),(119,78),(0,78)], fill="#648c8e")
    d.polygon([(0,70),(14,66),(29,70),(45,64),(58,69),(76,64),(89,66),
               (103,61),(119,65),(119,80),(0,80)], fill="#486f76")
    # A far tower and a copper observatory dome lend scale and a clear horizon.
    d.rectangle((18,47,24,68), fill="#d9cfac")
    d.rectangle((23,47,24,65), fill="#a89d8a")
    d.rectangle((20,51,21,54), fill="#56717a")
    d.polygon([(16,47),(18,44),(21,39),(24,44),(26,47)], fill="#4d8293")
    d.line([(19,44),(21,40)], "#99bec0")
    d.line([(21,39),(21,36)], "#8d7357")
    d.rectangle((93,49,103,68), fill="#c4b59b")
    d.rectangle((99,50,103,67), fill="#a19587")
    for x in [95,99]:
        d.rectangle((x,52,x+1,56), fill="#617780")
    d.polygon([(90,48),(92,44),(96,41),(98,38),(100,41),(104,43),(107,48)],
              fill="#759ea3", outline="#4b7382")
    d.line([(95,44),(98,40),(100,43)], "#b7d1c4")
    d.rectangle((90,48,106,50), fill="#d8c6a7")
    for x, y in [(5,58),(12,61),(30,60),(76,59),(83,57),(108,57),(115,56)]:
        d.polygon([(x-4,y+11),(x-2,y+5),(x-3,y+5),(x,y),(x+2,y+4),(x+4,y+10)], "#527d75")
        d.line([(x-2,y+6),(x,y+2)], "#85a68b")
    d.rectangle((0,74,119,79), fill="#9db6ae")
    d.rectangle((0,72,119,73), fill="#e1d5ae")
    for x in range(0,120,13):
        d.rectangle((x,75,x+2,81), fill="#bfb59e")
        d.line([(x,75),(x,80)], "#e2d4ad")
    d.rectangle((0,81,119,99), fill="#b6b4ae")
    for y in [82,88,97]:
        d.line([(0,y),(119,y)], "#969ca2")
        d.line([(0,y+1),(119,y+1)], "#d1cbc0")
    for x in range(-70,185,20):
        d.line([(60+(x-60)//2,82),(x,99)], fill="#9b9da0")
    for mirrored in (False,True):
        def p(x):
            return 119-x if mirrored else x
        def rect(x0,y0,x1,y1,color):
            d.rectangle((min(p(x0),p(x1)),y0,max(p(x0),p(x1)),y1), fill=color)
        d.polygon([(p(x),y) for x,y in [(0,0),(22,0),(22,2),(15,4),(11,7),
                  (9,11),(8,15),(0,15)]], fill="#616473")
        for x,y,w in [(0,0,22),(0,2,15),(0,4,10),(0,6,8)]:
            rect(x,y,w,y+1,"#c6b99d")
        rect(0,12,9,14,"#736f74"); rect(0,12,8,12,"#dad0b3")
        rect(0,15,7,81,"#a39c92"); rect(1,15,3,81,"#ded2b0")
        rect(6,15,7,81,"#777780")
        rect(0,80,9,83,"#c3b8a0"); rect(0,83,11,85,"#7c7d85")
        rect(0,80,9,80,"#e5d5af")
    return im


def build():
    sheet = Image.new("RGBA", (9*32,164))
    for i, draw in enumerate((status, skill, bag, journal, map_icon, bestiary,
                              account, settings, pause)):
        sheet.paste(draw(), (i*32,0))
    styles = [
        [("#393d49","#262937"),("#fffff1","#646975"),("#c7c9c4","#92959c"),
         ("#e6e5db","#a7a8a5"),("#9b9d9e","#f3f1e8"),("#e2e2db","#e2e2db")],
        [("#272c39","#161b2a"),("#a6aeb3","#555e6a"),("#6e7a86","#3c4452"),
         ("#465563","#27313e"),("#2d3948","#54606b"),("#344250","#344250")],
        [("#93999e","#faf9ef"),("#b8bcbb","#c6c9c7"),("#f4f3e9","#e8e8e3"),
         ("#eeeeea","#eeeeea"),("#eeeeea","#eeeeea"),("#eeeeea","#eeeeea")],
        [("#285873","#183d5b"),("#b3edf1","#48799a"),("#65c5dc","#3789b6"),
         ("#45a6cf","#438fbb"),("#4da4c9","#4da4c9"),("#4da4c9","#4da4c9")],
        [("#48562a","#39432a"),("#f3f9b3","#75923c"),("#d5ef89","#8ca947"),
         ("#c3df6b","#a3bd53"),("#b4d35e","#b4d35e"),("#b4d35e","#b4d35e")],
    ]
    for i, rings in enumerate(styles):
        sheet.paste(frame(rings), (i*32,32))
    sheet.paste(portrait(), (0,64))
    sheet.save(ASSETS / "interface.png", optimize=True)


if __name__ == "__main__":
    build()
