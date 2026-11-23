"""Browser canvas rendering, using nearest-neighbor sprite sheets."""
from math import cos, sin, pi
from browser import window
from .combat_art import COMBAT_ART
from .content import AREAS, AVATAR_JOBS, CLASSES, EXPANSION_ICON_COLUMNS, LEGACY_WORN, JOB_LOOKS, GROUND, IMAGES, LEDGES, MELEE_IMPACT, MELEE_WEAPONS, MELEE_POSES, NPC_IDLE, NPCS, PROPS, QUESTS, SPRITES, WORN_ITEMS, WORN_ROWS, avatar_style, monster_art
from .engine import HEIGHT, LADDERS, PORTALS, WIDTH, SWING_FOLLOW, SWING_WINDUP, area_at, ground_at, item_icon, limit

WALK = SPRITES["hero"]["animations"]["walk"]["frames"]
WALK_FRAME_MS = SPRITES["hero"]["animations"]["walk"]["durations"][0]
IDLE = SPRITES["hero"]["animations"]["idle"]
IDLE_LENGTH = sum(IDLE["durations"])
# Native-pixel weight shift, anchored at the feet and mirrored with the swing.
MELEE_LEAN = (0, -1, -2, -2, -2, -1, 0, 2, 4, 5, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 0, 0, 0, 0)



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
        self.avatar_cache = (None,None)
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

    def custom_avatar(self, profile, job, full):
        key = (job,profile["sex"],profile["skin"],profile["hair"])
        if full and self.avatar_cache[0] == key:
            return self.avatar_cache[1]
        row = 2*AVATAR_JOBS.index(job)+profile["sex"]
        image = window.mapleePortrait(self.images["custom_avatar"],row,profile["skin"],profile["hair"],full)
        if full:
            self.avatar_cache = (key,image)
        return image

    def avatar(self, ctx, equipment, weapon, frame, x, y, size, facing, opacity=1, swing_tick=None, job=None, rotation=0, thrust=False, profile=None, preview=False):
        """Draw identical anchored artwork in world and equipment coordinates."""
        ctx.save()
        ctx.globalAlpha = opacity
        ctx.translate(round(x), round(y))
        ctx.scale(facing, 1)
        if rotation:
            ctx.translate(0,-27)
            ctx.rotate(rotation)
            ctx.translate(0,27)
        left, top = -round(38 * size / 80), -round(75 * size / 80)
        sword = weapon in MELEE_WEAPONS
        far_hand = facing < 0
        body_sheet, column, row = "hero", frame % 4, frame // 4
        if sword and swing_tick is not None:
            if swing_tick < 18:
                frame = 8
                body_sheet, column, row = "expansion_swing", int(far_hand), 2*len(MELEE_WEAPONS)
            else:
                frame, column, row = 11, 3, 2
        style = avatar_style(profile) if profile else "classic"
        if style == "frost":
            cel = 28+int(far_hand) if body_sheet=="expansion_swing" else frame
            ctx.drawImage(self.images["frost_avatar"],cel*80,0,80,80,left,top,size,size)
        elif style == "custom":
            column = 28+int(far_hand) if body_sheet=="expansion_swing" else frame
            image = self.custom_avatar(profile, job or profile["job"], not preview)
            ctx.drawImage(image,column*80,0,80,80,left,top,size,size)
        elif job in JOB_LOOKS:
            # Each job cel extends eight native pixels around the equipment grid.
            if body_sheet == "expansion_swing":
                row = 7
            pad = round(size * 8 / 80)
            ctx.drawImage(self.images[JOB_LOOKS[job]], column*96, row*96, 96, 96,
                          left-pad, top-pad, size+2*pad, size+2*pad)
        elif body_sheet == "expansion_swing":
            ctx.drawImage(self.images[body_sheet],column*112+16,row*112+16,80,80,left,top,size,size)
        else:
            ctx.drawImage(self.images[body_sheet], column * 80, row * 80, 80, 80,
                          left, top, size, size)
        for item in (equipment.get("armor"), equipment.get("charm"), equipment.get("seal"),
                     equipment.get("head"), equipment.get("ring"), weapon):
            if item in WORN_ROWS:
                if item in LEGACY_WORN:
                    ctx.drawImage(self.images["worn"],frame*80,LEGACY_WORN[item]*80,80,80,left,top,size,size)
                    continue
                moving_blade = item == weapon and swing_tick is not None and sword
                sheet = "expansion_swing" if moving_blade else "expansion_worn"
                column = swing_tick if moving_blade else frame
                row = WORN_ROWS[item]
                if item == weapon and sword:
                    index = MELEE_WEAPONS.index(item)
                    if moving_blade and thrust:
                        row = 2*len(MELEE_WEAPONS)+1+2*int(far_hand)+int(weapon=="shadowdagger")
                    elif moving_blade:
                        row = index + int(far_hand)*len(MELEE_WEAPONS)
                    elif far_hand:
                        row = len(WORN_ITEMS) + index
                pad = round(size*16/80)
                ctx.drawImage(self.images[sheet],column*112,row*112,112,112,
                              left-pad,top-pad,size+2*pad,size+2*pad)
        ctx.restore()

    def icon(self, index, x, y, size):
        sheet = "expansion_icons" if index in EXPANSION_ICON_COLUMNS else "icons"
        index = EXPANSION_ICON_COLUMNS.get(index,index)
        self.ctx.drawImage(self.images[sheet], index % 8 * 32, index // 8 * 32, 32, 32,
                           round(x - size / 2), round(y - size / 2), size, size)

    def backdrop(self, area, left):
        key = area.get("image", "background")
        image = self.images[key]
        width, height = self.sizes[key]
        start, end = area["backdrop"]
        progress = limit((left - area["start"]) / (area["end"] - area["start"] - WIDTH), 0, 1)
        sy = 0 if area.get("image") else min(123,height//5)
        self.ctx.drawImage(image, round(width * (start + (end - start) * progress)), sy,
                           int(.36 * width), min(505,height-sy) if sy else height, 0, 0, WIDTH, HEIGHT)

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
        self.ground(material, max(left,area["start"]), min(right,area["end"]), area["material"] == "stone")
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
        for row, npc in enumerate(NPCS):
            x = npc["x"]
            if not area["start"] <= x < area["end"] or not left - 50 < x < right + 50:
                continue
            y = ground_at(x)
            height, durations = NPC_IDLE[row]
            phase = (game.tick * 1000 // 60 + x) % sum(durations)
            for cel, duration in enumerate(durations):
                if phase < duration:
                    break
                phase -= duration
            self.sprite("villager", row * SPRITES["villager"]["columns"] + cel, x, y)
            label_y = y - height - 5
            self.label(npc["name"] + " · " + npc["role"], x, label_y)
            if npc["kind"] in ("quest", "harbor"):
                index = npc.get("quest", 1 if npc["kind"] == "harbor" else 0)
                progress = game.p["quests"][index]
                if not progress["state"] or progress["state"] == 1 and progress["count"] >= QUESTS[index]["target"]:
                    self.label("◆", x, label_y - 15, "#ffd981", 13)
            if game.nearby()[1] == npc:
                self.label("↑ 대화", x, label_y - 29, "#d7ffed")

    def player_pose(self, game):
        tick = game.tick
        if tick < game.hurt_until:
            return 14, game.facing
        if game.swing:
            age = tick - game.swing["start"]
            if game.swing["melee"]:
                return MELEE_POSES[age], game.swing["dir"]
            if game.swing["attack"] in ("arrow", "bolt"):
                # The projectile leaves on the release/cast cel.
                phase = 0 if age < 7 else 1 if age < SWING_WINDUP else 2 if age < SWING_FOLLOW else 3
                first = 16 if game.swing["attack"] == "arrow" else 20
            else:
                phase = 0 if age < SWING_WINDUP else 1 if age < SWING_FOLLOW else 2 if age < 36 else 3
                first = 8
            return first + phase, game.swing["dir"]
        if game.ladder:
            # Halfway cels interpolate the two 250 ms rung contacts.
            phase = int((game.ladder[2] - game.p["y"]) / 24) % 4
            return 24 + phase, 1
        if game.surface is None:
            return (12 if game.vy < -1 else 13), game.facing
        if tick < game.land_until:
            return 15, game.facing
        if game.walk:
            return WALK[(game.walk * 1000 // (60 * WALK_FRAME_MS)) % len(WALK)], game.facing
        return idle_pose(tick), game.facing

    def monster(self, game, m):
        dead = m["dead"]
        elapsed = game.tick - dead if dead is not None else 0
        species = m["spec"]
        books = species.get("framebooks", {"attack1":(0,(22,)), "die1":(0,(18,))})
        phase_tick = game.tick + m["phase"]
        after_strike = game.tick - m["strike"]
        phase = None
        if dead is not None:
            action = "die1"
            if elapsed >= books[action][1][-1]:
                return
            phase_tick = elapsed
        elif game.tick < m["hurt"]:
            action = "hit1"
        elif m["windup"] or after_strike < 10:
            # Body-attack monsters use their leap or movement cels. Casters
            # play their longer source attack in step with the damage tick.
            action = next((name for name in ("attack1", "skill1", "jump", "move") if name in books), "stand")
            if m["windup"]:
                duration = 24 if m["range"] == 90 else 34 if species.get("elite") else 17
                phase = 0.55 * (1 - (m["windup"] - game.tick) / duration)
            else:
                phase = 0.55 + 0.45 * after_strike / 9
        else:
            action = "move"
        y = m["y"] - (sin(phase_tick / 10) * 3 if species.get("float") else 0)
        scale = 1.5 if species.get("elite") else 1
        if m["windup"]:
            reach = m["range"]
            self.rect(m["x"] if m["dir"] > 0 else m["x"] - reach, m["y"] - 2, reach, 4, "#fbb070a5")
        sx, sy, sw, sh, dx, dy = monster_art(species, action, phase_tick, phase)
        ctx = self.ctx
        ctx.save()
        ctx.translate(round(m["x"]), round(y))
        ctx.scale(m["dir"]*scale, scale)
        ctx.drawImage(self.images[species.get("image","wildlife")], sx, sy, sw, sh, dx, dy, sw, sh)
        ctx.restore()
        if dead is not None:
            return
        y -= round(species["body_size"][1] * scale) + 6
        if species.get("elite") or abs(m["x"] - game.p["x"]) < 105:
            self.label(f"Lv.{species['level']} {species['name']}", m["x"], y, "#fff2bd", 10)
        if m["hp"] < species["hp"] or species.get("elite"):
            w = 64 if species.get("elite") else 30
            self.rect(m["x"] - w / 2, y + 4, w, 5, "#241d32")
            self.rect(m["x"] - w / 2 + 1, y + 5, (w - 2) * m["hp"] / species["hp"], 3, "#ef9875")

    def expansion_effect(self, shape, x, y, age, fraction, facing):
        ctx = self.ctx
        ctx.save()
        ctx.globalAlpha = min(1,(1-fraction)*2)
        if shape in ("stab","stab_hit","kick_hit","heal_hit"):
            color = {"stab":"#c9a4fc","stab_hit":"#e7c1ff","kick_hit":"#b6fcff","heal_hit":"#ffcc79"}[shape]
            for direction in range(8):
                angle = direction*pi/4
                radius = (8+age*1.7) * (1.35 if shape.startswith("stab") else 1)
                px, py = x+radius*cos(angle), y+radius*sin(angle)*.65
                self.rect(px,py,3,2,color)
                self.rect(px-3*cos(angle),py-3*sin(angle),2,1,"#fff7df")
            if shape.startswith("stab"):
                ctx.translate(round(x),round(y))
                ctx.scale(facing,1)
                for offset in (0,5):
                    for step in range(15):
                        self.rect(-21 + step*3,offset+5-step//3,
                                  4,1 if step>12 else 2,color if offset else "#fff3df")
        else:
            palette = {
                "kick": ("#63a8bd","#bff2f5"),
                "heal": ("#e7ad6b","#fff3b6"),
                "buff_thief": ("#5e5685","#b490d8"),
                "buff_pirate": ("#4c9fb7","#b6f1ef"),
                "buff_cleric": ("#e8b16a","#fff2b5"),
            }
            dark, light = palette[shape]
            if shape in ("heal","kick"):
                y += 24
            for band in range(2):
                size = (34 if shape=="kick" else 23)+fraction*(36 if shape=="kick" else 32)
                for step in range(24):
                    angle = step*pi/12 + age*(.17 if band else -.09)
                    if shape == "kick" and step > 17:
                        continue
                    px=x+cos(angle)*size
                    py=y+sin(angle)*size*(.55 if shape=="kick" else .2) - 10-band*(7+fraction*44)
                    self.rect(px,py,4 if band else 6,2,dark)
                    self.rect(px+1,py-1,2,1,light)
            if shape == "heal":
                for offset in (-29,-12,14,30):
                    py=y-20-age*1.8+abs(offset)*.45
                    self.rect(x+offset-3,py,7,2,light)
                    self.rect(x+offset,py-3,2,8,light)
        ctx.restore()

    def effect(self, tick, effect):
        shape, start, x, y, duration, data = effect
        age = tick - start
        fraction = age / duration
        if shape == "damage":
            value, row = data
            digits = str(value)
            ctx = self.ctx
            ctx.save()
            ctx.globalAlpha = min(1, (1-fraction)*3)
            top = round(y - 43 - 24*(1-(1-fraction)**2))
            left = round(x - (len(digits)-1)*10 - 24)
            for index, digit in enumerate(digits):
                ctx.drawImage(self.images["damage"], int(digit)*48, (row + int(index > 0))*48,
                              48, 48, left + index*20, top + (index % 2)*2, 48, 48)
            ctx.restore()
        elif shape == "text":
            self.label(data[0], x, y - fraction * 22, data[1], 16)
        elif shape == "pickup":
            eased = 1 - (1 - fraction) ** 2
            self.icon(data[0], x + (data[1] - x) * eased, y + (data[2] - y) * eased - sin(fraction * pi) * 12, 21)
        elif shape in ("stab","stab_hit","kick","kick_hit","heal","heal_hit","buff_thief","buff_pirate","buff_cleric"):
            self.expansion_effect(shape,x,y,age,fraction,data)
        elif shape in COMBAT_ART:
            row, width, height, origin_x, origin_y, frames = COMBAT_ART[shape]
            if shape in ("slash", "arc", "ring", "stars"):
                y += 24
            phase = min(frames - 1, age * frames // duration)
            if shape in ("arrow", "bolt"):
                facing = data[0]
                x += facing * age * 15
                phase = (age // 3) % frames
            else:
                facing = data
            ctx = self.ctx
            ctx.save()
            ctx.translate(round(x), round(y))
            ctx.scale(facing, 1)
            ctx.drawImage(self.images["combat"], phase*width, row, width, height,
                          -origin_x, -origin_y, width, height)
            ctx.restore()
        elif shape == "dust":
            for i in range(6):
                side = 1 if i % 2 else -1
                spread = (i + 1) * (2 + age) * .38
                self.rect(x + side * spread, y - (age % 14) / 2 - i * 2, 2 + i % 2, 2, "#d6bd9480")
        elif shape == "wave":
            for i in range(-4, 5):
                self.rect(x + i * data / 4, y + (abs(i) - 4) * age * .45, 7, 4, "#ffa48e")

    def draw(self, game, paused, profile=None, portal_fade=0):
        self.ctx.setTransform(int(self.canvas.attrs["width"]) / WIDTH, 0, 0, int(self.canvas.attrs["height"]) / HEIGHT, 0, 0)
        self.ctx.imageSmoothingEnabled = False
        if not self.ready:
            self.rect(0, 0, WIDTH, HEIGHT, "#183744")
            text = "그래픽 파일을 불러오지 못했어요." if self.failed else f"도트 그래픽 불러오는 중 · {len(self.loaded)}/{len(IMAGES)}"
            self.label(text, WIDTH / 2, HEIGHT / 2, size=16)
            return
        ctx = self.ctx
        x, y, tick = game.p["x"], game.p["y"], game.tick
        left = int(game.camera)
        right = left + WIDTH
        visible = [area for area in AREAS if area["end"] > left and area["start"] < right]
        self.backdrop(visible[0], left)
        for area in visible[1:]:
            ctx.save()
            blend = limit((right-area["start"])/WIDTH,0,1)
            ctx.globalAlpha = blend*blend*(3-2*blend)
            self.backdrop(area,left)
            ctx.restore()
        ctx.save()
        ctx.translate(-left, 0)
        for area in visible:
            self.scenery(game, area, left, right)
        for m in game.monsters:
            if left - 100 < m["x"] < right + 100:
                self.monster(game, m)
        for drop in game.drops:
            if left <= drop["x"] <= right:
                elapsed = tick - drop["start"]
                height = 28 * sin(min(1, elapsed / 24) * pi)
                for index, id in enumerate([None] + drop["items"]):
                    self.icon(7 if id is None else item_icon(id), drop["x"] + index * 13 - 11, drop["y"] - 10 - height, 18)
        frame, facing = self.player_pose(game)
        opacity = .48 if tick < game.inv_until and tick % 6 < 3 and tick >= game.hurt_until else 1
        equipment = game.p["equipment"]
        weapon = game.swing["weapon"] if game.swing else equipment.get("weapon")
        swing_tick = None
        lean = 0
        if game.swing and game.swing["melee"] and tick >= game.hurt_until:
            swing_tick = tick - game.swing["start"]
            lean = MELEE_LEAN[swing_tick] * facing
        elif game.swing and weapon in MELEE_WEAPONS and tick >= game.hurt_until:
            # Align the same right-hand stroke with the skill's own impact tick.
            age = tick - game.swing["start"]
            impact = game.swing["impact"]
            duration = game.swing["duration"]
            swing_tick = (age * MELEE_IMPACT // impact if age < impact else
                          MELEE_IMPACT + (age-impact) * (len(MELEE_POSES)-MELEE_IMPACT) // (duration-impact))
        if game.support_value("stealth"):
            opacity *= .45
        rotation = 0
        thrust = False
        if game.swing and game.swing["shape"] == "stab":
            age = tick - game.swing["start"]
            thrust = weapon in ("dagger","shadowdagger") and 5 <= age <= 17
            swing_tick = age-5 if thrust else None
            frame = 11
        if game.swing and game.swing["shape"] == "kick":
            age = tick - game.swing["start"]
            progress = limit((age-5)/18,0,1)
            rotation = 2*pi*progress
            frame = 12 if progress < .5 else 13
            swing_tick = None
            y -= 22*sin(progress*pi)
        self.avatar(ctx, equipment, weapon, frame, x + lean, y, 80, facing, opacity,
                    swing_tick, game.p["job"], rotation, thrust, profile)
        if tick < game.support_until:
            buff_age = tick - game.support_started
            if buff_age < 48:
                self.effect(tick, ("buff_" + game.p["job"], game.support_started, x, y, 48, facing))
            self.rect(x - 12, y - 2, 24, 2, "#b8f6b980")
        name = profile["name"] if profile else CLASSES[game.p["job"]]["name"]
        self.label(f"Lv.{game.p['level']} {name}", x, y - 74)
        for effect in game.effects:
            if effect[0] != "damage":
                self.effect(tick, effect)
        for effect in game.effects:
            if effect[0] == "damage":
                self.effect(tick, effect)
        ctx.restore()
        if portal_fade:
            self.rect(0,0,WIDTH,HEIGHT,f"rgba(19,32,47,{portal_fade*.78})")
        if paused:
            self.rect(0, 0, WIDTH, HEIGHT, "#11283888")
            self.label("일시정지", WIDTH / 2, HEIGHT / 2, size=22)


def ceil_height(value):
    return int(value) + 1
