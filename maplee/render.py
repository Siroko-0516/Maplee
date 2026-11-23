"""Browser canvas rendering, using nearest-neighbor sprite sheets."""
from math import sin, pi
from browser import window
from .content import AREAS, CLASSES, GROUND, IMAGES, LEDGES, NPCS, PROPS, QUESTS, SPRITES
from .engine import HEIGHT, LADDERS, PORTALS, WIDTH, SWING_WINDUP, area_at, ground_at, item_icon, limit

WALK = SPRITES["hero"]["animations"]["walk"]["frames"]
IDLE = SPRITES["hero"]["animations"]["idle"]
IDLE_LENGTH = sum(IDLE["durations"])


def idle_pose(tick):
    phase = tick * 1000 // 60 % IDLE_LENGTH
    for frame, duration in zip(IDLE["frames"], IDLE["durations"]):
        if phase < duration:
            return frame
        phase -= duration

def number(value):
    try:
        return float(value)
    except TypeError:
        return float(str(value))


class Renderer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.resize()
        self.ctx = canvas.getContext("2d")
        self.ctx.imageSmoothingEnabled = False
        self.images = {}
        self.sizes = {}
        self.loaded = set()
        self.failed = set()
        for name, path in IMAGES.items():
            img = window.Image.new()
            img.onload = lambda *events, name=name, img=img: self.image_loaded(name, img)
            img.onerror = lambda *events, name=name: self.failed.add(name)
            self.images[name] = img
            img.src = "assets/" + path

    def image_loaded(self, name, image):
        # Brython reserves DOMNode.width/height for CSS. Decode intrinsic pixels once.
        width = int(number(image.naturalWidth))
        height = int(number(image.naturalHeight))
        if width > 0 and height > 0:
            self.sizes[name] = (width, height)
            self.loaded.add(name)
        else:
            self.failed.add(name)

    def resize(self, _=None):
        bounds = self.canvas.getBoundingClientRect()
        fit = min(number(bounds.width) / WIDTH, number(bounds.height) / HEIGHT)
        multiplier = max(1, min(3, (fit or 1) * number(window.devicePixelRatio or 1)))
        width, height = round(WIDTH * multiplier), round(HEIGHT * multiplier)
        if self.canvas.attrs["width"] != str(width) or self.canvas.attrs["height"] != str(height):
            self.canvas.attrs["width"] = str(width)
            self.canvas.attrs["height"] = str(height)

    @property
    def ready(self):
        return len(self.loaded) == len(IMAGES)

    def rect(self, x, y, w, h, color):
        self.ctx.fillStyle = color
        self.ctx.fillRect(round(x), round(y), round(w), round(h))

    def label(self, text, x, y, color="#fff0c4", size=11):
        ctx = self.ctx
        ctx.font = f"bold {size}px system-ui, sans-serif"
        ctx.textAlign = "center"
        ctx.lineJoin = "round"
        ctx.strokeStyle = "#172632"
        ctx.lineWidth = 3
        ctx.strokeText(text, round(x), round(y))
        ctx.fillStyle = color
        ctx.fillText(text, round(x), round(y))

    def sprite(self, name, frame, x, y, facing=1, scale=1, opacity=1, tint="none"):
        ctx = self.ctx
        sprite = SPRITES[name]
        width, height = sprite["frameWidth"], sprite["frameHeight"]
        columns = sprite["columns"]
        anchor = sprite["anchor"]
        ctx.save()
        ctx.globalAlpha = opacity
        ctx.translate(round(x), round(y))
        if facing < 0:
            ctx.scale(-1, 1)
        if tint != "none":
            ctx.filter = tint
        ctx.drawImage(self.images[name], frame % columns * width, frame // columns * height, width, height,
                      -round(anchor[0] * scale), -round(anchor[1] * scale), round(width * scale), round(height * scale))
        ctx.restore()

    def icon(self, index, x, y, size):
        self.ctx.drawImage(self.images["icons"], index % 8 * 32, index // 8 * 32, 32, 32,
                           round(x - size / 2), round(y - size / 2), size, size)

    def backdrop(self, area, left):
        key = area.get("image", "background")
        image = self.images[key]
        width, height = self.sizes[key]
        start, end = area["backdrop"]
        progress = limit((left - area["start"]) / (area["end"] - area["start"] - WIDTH), 0, 1)
        self.ctx.drawImage(image, round(width * (start + (end - start) * progress)), 0 if area.get("image") else 123,
                           int(.36 * width), height if area.get("image") else 505, 0, 0, WIDTH, HEIGHT)

    def tile_band(self, material, left, right, deep=False):
        ctx = self.ctx
        image = self.images[material]
        width, height = self.sizes[material]
        for tile in range(int(left // width), int(right // width) + 1):
            mirrored = tile % 2
            ctx.save()
            ctx.translate((tile + mirrored) * width, 0)
            if mirrored:
                ctx.scale(-1, 1)
            ctx.drawImage(image, 0, 0)
            if deep:
                ctx.translate(0, height * 2)
                ctx.scale(1, -1)
                ctx.drawImage(image, 0, height - 52, width, 52, 0, height - 52, width, 52)
            ctx.restore()

    def ground(self, material, left, right, stone):
        ctx = self.ctx
        segments = []
        for (x, y), (end, end_y) in zip(GROUND, GROUND[1:]):
            start = max(x, left)
            finish = min(end, right)
            if start < finish:
                slope = (end_y - y) / (end - x)
                segments.append((start, finish, slope, y - slope * x - 5))
        ctx.save()
        ctx.beginPath()
        ctx.moveTo(left, ground_at(left) - 5)
        for _, end, slope, offset in segments:
            ctx.lineTo(end, slope * end + offset)
        ctx.lineTo(right, HEIGHT)
        ctx.lineTo(left, HEIGHT)
        ctx.closePath()
        ctx.clip()
        self.rect(left, 283, right - left, HEIGHT, "#887765" if stone else "#564522")
        for start, end, slope, offset in segments:
            ctx.save()
            ctx.beginPath()
            ctx.rect(start - .5, 0, end - start + 1, HEIGHT)
            ctx.clip()
            ctx.transform(1, slope, 0, 1, 0, offset)
            self.tile_band(material, start - .5, end + .5, True)
            ctx.restore()
        ctx.restore()

    def scenery(self, game, area, left, right):
        ctx = self.ctx
        material = area["material"]
        for prop in PROPS:
            x, id, width = prop[:3]
            if not area["start"] <= x < area["end"] or not left - 175 < x < right + 175:
                continue
            sx, sy, sw, sh = SPRITES["props"][id]
            height = round(width * sh / sw)
            floor = prop[3] if len(prop) > 3 else ground_at(x)
            ctx.drawImage(self.images["props"], sx, sy, sw, sh, round(x - width / 2), round(floor - height + 2), width, height)
        for x, top, bottom in LADDERS:
            if area["start"] <= x < area["end"] and left - 12 < x < right + 12:
                self.rect(x - 10, top, 4, bottom - top, "#956b48")
                self.rect(x + 6, top, 4, bottom - top, "#956b48")
                for y in range(top + 8, ceil_height(bottom), 10):
                    self.rect(x - 7, y, 15, 2, "#d1af75")
        self.ground(material, left, right, area["material"] == "stone")
        for ledge in LEDGES:
            x, y, w = ledge["x"], ledge["y"], ledge["w"]
            if x < area["start"] or x + w > area["end"] or x + w <= left or x >= right:
                continue
            ctx.save()
            ctx.beginPath()
            ctx.roundRect(x, y - 5, w, 32, 5)
            ctx.clip()
            ctx.translate(0, y - 5)
            self.tile_band(material, x, x + w)
            self.rect(x, 28, w, 4, "#233121aa")
            ctx.restore()
        for x, _, target in PORTALS:
            if area["start"] <= x < area["end"] and left - 60 < x < right + 60:
                y = ground_at(x)
                self.rect(x - 9, y - 41, 18, 41, "#5adbee60")
                for i in range(6):
                    self.rect(x - 8 + 3 * i, y - ((game.tick + i * 11) % 37), 2, 5, "#cdfbff")
                self.label("↑ " + AREAS[target]["name"], x, y - 50, "#baf6ff")
        for npc in NPCS:
            x = npc["x"]
            if not area["start"] <= x < area["end"] or not left - 50 < x < right + 50:
                continue
            y = ground_at(x)
            tint = {"shop": "hue-rotate(42deg)", "trainer": "hue-rotate(196deg)", "forge": "hue-rotate(235deg)"}.get(npc["kind"], "none")
            self.sprite("villager", (game.tick // 13 + int(x)) % 4, x, y, scale=1, tint=tint)
            self.label(npc["name"] + " · " + npc["role"], x, y - 54)
            if npc["kind"] in ("quest", "harbor"):
                index = npc.get("quest", 1 if npc["kind"] == "harbor" else 0)
                progress = game.p["quests"][index]
                if not progress["state"] or progress["state"] == 1 and progress["count"] >= QUESTS[index]["target"]:
                    self.label("◆", x, y - 69, "#ffd981", 13)
            if game.nearby()[1] == npc:
                self.label("↑ 대화", x, y - 71, "#d7ffed")

    def player_pose(self, game):
        tick = game.tick
        if tick < game.hurt_until:
            return 14, game.facing
        if game.swing:
            age = tick - game.swing["start"]
            frame = (8 if age < SWING_WINDUP else 9 if age < 9 else 10 if age < 15 else 11)
            return frame, game.swing["dir"]
        if game.ladder:
            return WALK[(tick // 5) % len(WALK)], game.facing
        if game.surface is None:
            return (12 if game.vy < -1 else 13), game.facing
        if tick < game.land_until:
            return 15, game.facing
        if game.walk:
            return WALK[int(game.walk / 18) % len(WALK)], game.facing
        return idle_pose(tick), game.facing

    def monster(self, game, m):
        dead = m["dead"]
        elapsed = game.tick - dead if dead is not None else 0
        if elapsed >= 20:
            return
        species = m["spec"]
        old = game.tick + m["phase"]
        gait = (0, 1, 0, 4)[(old // (6 if m["state"] == "pursuit" else 10)) % 4]
        frame = 3 if dead is not None or game.tick < m["hurt"] else 2 if m["windup"] else 5 if game.tick - m["strike"] < 8 else gait
        y = m["y"] - (sin(old / 10) * 3 if species.get("float") else 0) - .25 * elapsed
        scale = 1.5 if species.get("elite") else 1
        if m["windup"]:
            reach = m["range"]
            self.rect(m["x"] if m["dir"] > 0 else m["x"] - reach, m["y"] - 2, reach, 4, "#fbb070a5")
        self.sprite("wildlife", species["sprite"] * 6 + frame, m["x"], y, m["dir"], scale,
                    1 - elapsed / 20, species.get("tint", "none"))
        if dead is not None:
            return
        y = y - round(68 * scale) - 6
        if species.get("elite") or abs(m["x"] - game.p["x"]) < 105:
            self.label(f"Lv.{species['level']} {species['name']}", m["x"], y, "#fff2bd", 10)
        if m["hp"] < species["hp"] or species.get("elite"):
            w = 64 if species.get("elite") else 30
            self.rect(m["x"] - w / 2, y + 4, w, 5, "#241d32")
            self.rect(m["x"] - w / 2 + 1, y + 5, (w - 2) * m["hp"] / species["hp"], 3, "#ef9875")

    def effect(self, tick, effect):
        shape, start, x, y, duration, data = effect
        age = tick - start
        fraction = age / duration
        if shape == "text":
            self.label(data[0], x, y - fraction * 22, data[1], 16)
        elif shape == "pickup":
            eased = 1 - (1 - fraction) ** 2
            self.icon(data[0], x + (data[1] - x) * eased, y + (data[2] - y) * eased - sin(fraction * pi) * 12, 21)
        elif shape == "arrow":
            self.rect(x + data * age * 15, y, 12, 2, "#b7ffc4")
        elif shape in ("impact", "dust"):
            for i in range(6):
                side = 1 if i % 2 else -1
                spread = (i + 1) * (2 + age) * .38
                self.rect(x + side * spread, y - (age % 14) / 2 - i * 2, 2 + i % 2, 2, "#fff7af" if shape == "impact" else "#d6bd9480")
        elif shape in ("slash", "arc"):
            for i in range(15):
                offset = (i - 7) * 3
                front = (52 if shape == "slash" else 84) - abs(i - 7) * 4 + age
                self.rect(x + data * front, y + offset, max(1, 5 - fraction * 4), 3, "#fff4b4" if age < 4 else "#f2ad61a0")
        elif shape in ("stars", "wave", "ring"):
            radius = data if shape == "wave" else 105 if shape == "ring" else 155
            for i in range(-4, 5):
                self.rect(x + i * radius / 4, y + (abs(i) - 4) * age * .45, 7, 4,
                          "#ffa48e" if shape == "wave" else "#b5e9ff")

    def draw(self, game, paused):
        self.ctx.setTransform(int(self.canvas.attrs["width"]) / WIDTH, 0, 0, int(self.canvas.attrs["height"]) / HEIGHT, 0, 0)
        self.ctx.imageSmoothingEnabled = False
        if not self.ready:
            self.rect(0, 0, WIDTH, HEIGHT, "#183744")
            text = "그래픽 파일을 불러오지 못했어요." if self.failed else f"도트 그래픽 불러오는 중 · {len(self.loaded)}/{len(IMAGES)}"
            self.label(text, WIDTH / 2, HEIGHT / 2, size=16)
            return
        ctx = self.ctx
        x, y, tick = game.p["x"], game.p["y"], game.tick
        area = AREAS[area_at(x)]
        left = int(game.camera)
        right = left + WIDTH
        self.backdrop(area, left)
        ctx.save()
        ctx.translate(-left, 0)
        self.scenery(game, area, left, right)
        if area.get("tint"):
            self.rect(left, 0, WIDTH, HEIGHT, area["tint"])
        for m in game.monsters:
            if left - 75 < m["x"] < right + 75 and area["start"] <= m["x"] < area["end"]:
                self.monster(game, m)
        for drop in game.drops:
            if left <= drop["x"] <= right:
                elapsed = tick - drop["start"]
                height = 28 * sin(min(1, elapsed / 24) * pi)
                for index, id in enumerate([None] + drop["items"]):
                    self.icon(7 if id is None else item_icon(id), drop["x"] + index * 13 - 11, drop["y"] - 10 - height, 18)
        frame, facing = self.player_pose(game)
        opacity = .48 if tick < game.inv_until and tick % 6 < 3 and tick >= game.hurt_until else 1
        self.sprite("hero", frame, x, y, facing, 1, opacity)
        if tick < game.support_until:
            self.rect(x - 12, y - 2, 24, 2, "#b8f6b980")
        self.label(f"Lv.{game.p['level']} {CLASSES[game.p['job']]['name']}", x, y - 74)
        for effect in game.effects:
            self.effect(tick, effect)
        ctx.restore()
        if paused:
            self.rect(0, 0, WIDTH, HEIGHT, "#11283888")
            self.label("일시정지", WIDTH / 2, HEIGHT / 2, size=22)


def ceil_height(value):
    return int(value) + 1
