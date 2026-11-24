"""Paint a 26px ladder with cap, repeatable rungs and foot brackets."""
from pathlib import Path

from PIL import Image, ImageDraw

image = Image.new("RGBA",(26,27))
draw = ImageDraw.Draw(image)

# The eight-pixel entrance, fourteen-pixel repeat, and five-pixel foot.
for x in (4,17):
    draw.rectangle((x,2,x+5,25), fill="#302321")
    draw.rectangle((x+1,3,x+4,25), fill="#97643d")
    draw.line((x+1,3,x+1,25),fill="#ebbc78")
    draw.line((x+4,4,x+4,25),fill="#684229")
    draw.rectangle((x-1,3,x+6,5),fill="#74533b",outline="#332929")
    draw.line((x,3,x+4,3),fill="#ccad7e")
    draw.rectangle((x-1,22,x+6,26),fill="#624838",outline="#352923")
    draw.line((x,23,x+4,23),fill="#ab8c6a")
    for y in (5,14,25):
        draw.point((x+3,y), fill="#dfb772")

draw.rectangle((5,12,21,16),fill="#382b24")
draw.line((6,12,19,12),fill="#e6b777")
draw.line((6,13,20,13),fill="#b4844f")
draw.line((6,14,20,14),fill="#97663f")
draw.line((6,15,20,15),fill="#714932")
draw.point((10,14),fill="#d09c65")
draw.point((17,14),fill="#d09c65")
for x in (4,17):
    draw.line((x-1,12,x+5,12),fill="#8d6949")
    draw.line((x-1,13,x+6,13),fill="#c4ac80")
    draw.line((x,14,x+4,14),fill="#ccad7d")
    draw.point((x+4,15),fill="#f0ce94")
draw.line((6,19,6,20),fill="#c2955a")
draw.line((19,9,19,10),fill="#e0a568")

image.save(Path(__file__).resolve().parents[1]/"assets/ladder.png",optimize=True)
