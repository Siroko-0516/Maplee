"""Browser canvas rendering, using nearest-neighbor sprite sheets."""
from math import ceil, cos, sin, pi, sqrt
from browser import window
from .combat_art import COMBAT_ART
from .content import AREAS, CLASSES, EXPANSION_ICON_COLUMNS, LEGACY_WORN, JOB_LOOKS, GROUND, IMAGES, LEDGES, LEDGE_DEPTH, MELEE_IMPACT, MELEE_WEAPONS, MELEE_POSES, NPC_IDLE, NPCS, PANORAMA_Y, PROPS, QUESTS, SPRITES, WORN_ITEMS, WORN_ROWS, monster_art
from .engine import AREA_LADDERS, AREA_LEDGES, CAMERA_TOP, HEIGHT, LOWEST_GROUND, PORTALS, WIDTH, SWING_FOLLOW, SWING_WINDUP, area_at, ground_at, item_icon, limit, monster_feet_y

WALK = SPRITES["hero"]["animations"]["walk"]["frames"]
WALK_FRAME_MS = SPRITES["hero"]["animations"]["walk"]["durations"][0]
IDLE = SPRITES["hero"]["animations"]["idle"]
IDLE_LENGTH = sum(IDLE["durations"])
FIELD_ZOOM = 1.25
TERRAIN_TILE_WIDTH = 512
TERRAIN_TOP = CAMERA_TOP - 8
TERRAIN_BOTTOM = max(LOWEST_GROUND, ceil(HEIGHT * FIELD_ZOOM)) + 12
TERRAIN_CACHE_SIZE = 8
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
        self.terrain_cache = {}
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
        css_width = number(bounds.width) or WIDTH
        css_height = number(bounds.height) or HEIGHT
        # Match the actual field ratio. Tall screens show a narrower part of
        # the map, and ultrawide screens show a slightly shorter field.
        fit = max(css_width/1440,css_height/HEIGHT) / FIELD_ZOOM
        self.view_width = round(css_width/fit)
        self.view_height = round(css_height/fit)
        budget = 1_250_000 if css_width < 800 else 2_300_000
        multiplier = min(limit(fit*number(window.devicePixelRatio or 1),1,3),
                         sqrt(budget/(self.view_width*self.view_height)))
        width = round(self.view_width*multiplier)
        height = round(self.view_height*multiplier)
        self.scale_x, self.scale_y = width/self.view_width,height/self.view_height
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

    def avatar(self, ctx, equipment, weapon, frame, x, y, size, facing, opacity=1, swing_tick=None, job=None, rotation=0, thrust=False):
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
        if job in JOB_LOOKS:
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

    def panorama_layer(self, key, offset, camera_y, vertical_scroll):
        width, height = self.sizes[key]
        source = offset%width
        rows = min(self.view_height,height)
        top = limit(PANORAMA_Y+round(camera_y*vertical_scroll),0,height-rows)
        x = 0
        while x < self.view_width:
            span = min(self.view_width-x,width-source)
            self.ctx.drawImage(self.images[key],source,top,span,rows,x,0,span,rows)
            x += span
            source = 0

    def backdrop(self, area, left, camera_y):
        distance = max(0,left-area["start"])
        view = area["view"]
        self.panorama_layer(area["image"],view+round(distance*.33),camera_y,.5)
        if area.get("mid_image"):
            self.panorama_layer(area["mid_image"],view+round(distance*.56),camera_y,.7)

    def ladder(self, x, top, bottom):
        # Paint over the leading edge of both ledges. Rungs and rails stay on
        # whole pixels even on slopes and on ladders with a partial last tile.
        width, _ = self.sizes["ladder"]
        image = self.images["ladder"]
        left = round(x)-width//2
        y, end = round(top), round(bottom)
        self.ctx.drawImage(image,0,0,width,8,left,y-7,width,8)
        for rung in range(y+1,end,14):
            height = min(14,end-rung)
            self.ctx.drawImage(image,0,8,width,height,left,rung,width,height)
        self.ctx.drawImage(image,0,22,width,5,left,end-2,width,5)

    def tile_band(self, material, left, right, depth=0):
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
            for offset in range(0,max(0,ceil(depth-height)),52):
                reflected = offset % 104 == 0
                ctx.save()
                ctx.translate(0,height+offset+(52 if reflected else 0))
                if reflected:
                    ctx.scale(1,-1)
                ctx.drawImage(image,0,height-52,width,52,0,0,width,52)
                ctx.restore()
            ctx.restore()

    def ground(self, material, left, right, stone, bottom):
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
        ctx.lineTo(right, bottom)
        ctx.lineTo(left, bottom)
        ctx.closePath()
        ctx.clip()
        if bottom > 283:
            self.rect(left,283,right-left,bottom-283,"#887765" if stone else "#564522")
        for start, end, slope, offset in segments:
            ctx.save()
            ctx.beginPath()
            ctx.rect(start - .5, 0, end - start + 1, bottom)
            ctx.clip()
            ctx.transform(1, slope, 0, 1, 0, offset)
            depth = bottom-min(ground_at(start),ground_at(end))+5
            self.tile_band(material,start-.5,end+.5,depth)
            ctx.restore()
        ctx.restore()

    def static_scenery(self, region, left, right, bottom):
        ctx = self.ctx
        area = AREAS[region]
        material = area["material"]
        for prop in PROPS:
            x, id, width = prop[:3]
            if not area["start"] <= x < area["end"] or x + width/2 <= left or x - width/2 >= right:
                continue
            atlas = prop[4] if len(prop) > 4 else "props"
            sx, sy, sw, sh = SPRITES[atlas][id]
            height = round(width * sh / sw)
            floor = prop[3] if len(prop) > 3 and prop[3] is not None else ground_at(x)
            ctx.drawImage(self.images[atlas], sx, sy, sw, sh, round(x - width / 2), round(floor - height + 2), width, height)
        self.ground(material,max(left,area["start"]),min(right,area["end"]),material=="stone",bottom)
        for ledge in AREA_LEDGES[region]:
            x, y, w = ledge["x"], ledge["y"], ledge["w"]
            if x < area["start"] or x + w > area["end"] or x + w <= left or x >= right:
                continue
            ctx.save()
            ctx.beginPath()
            ctx.roundRect(x, y - 5, w, LEDGE_DEPTH, 5)
            ctx.clip()
            ctx.translate(0, y - 5)
            self.tile_band(material, x, x + w)
            self.rect(x, LEDGE_DEPTH-4, w, 4, "#233121aa")
            ctx.restore()
        for x, top, bottom in AREA_LADDERS[region]:
            if left-14 < x < right+14:
                self.ladder(x,top,bottom)

    def terrain_tile(self, region, index):
        key = (region,index)
        if key in self.terrain_cache:
            tile = self.terrain_cache.pop(key)
            self.terrain_cache[key] = tile
            return tile
        area = AREAS[region]
        left = area["start"] + index*TERRAIN_TILE_WIDTH
        right = min(area["end"],left+TERRAIN_TILE_WIDTH)
        # Add a small margin so slopes and props join cleanly across tile edges.
        padded_left = max(area["start"],left-2)
        padded_right = min(area["end"],right+2)
        image = window.document.createElement("canvas")
        image.attrs["width"] = str(padded_right-padded_left)
        image.attrs["height"] = str(TERRAIN_BOTTOM-TERRAIN_TOP)
        original = self.ctx
        self.ctx = image.getContext("2d")
        try:
            self.ctx.imageSmoothingEnabled = False
            self.ctx.translate(-padded_left,-TERRAIN_TOP)
            self.static_scenery(region,padded_left,padded_right,TERRAIN_BOTTOM)
        finally:
            self.ctx = original
        tile = image,left-padded_left,right-left
        self.terrain_cache[key] = tile
        if len(self.terrain_cache) > TERRAIN_CACHE_SIZE:
            del self.terrain_cache[next(iter(self.terrain_cache))]
        return tile

    def terrain(self, region, left, right):
        area = AREAS[region]
        origin = area["start"]
        first = max(0,(left-origin)//TERRAIN_TILE_WIDTH)
        last = (min(right,area["end"])-origin-1)//TERRAIN_TILE_WIDTH
        height = TERRAIN_BOTTOM-TERRAIN_TOP
        for index in range(first,last+1):
            image,sx,width = self.terrain_tile(region,index)
            x = origin+index*TERRAIN_TILE_WIDTH
            self.ctx.drawImage(image,sx,0,width,height,x,TERRAIN_TOP,width,height)

    def scenery(self, game, area, left, right):
        for x, _, target in PORTALS:
            if area["start"] <= x < area["end"] and left - 60 < x < right + 60:
                y = ground_at(x)
                self.rect(x - 9, y - 41, 18, 41, "#5adbee60")
                for i in range(6):
                    self.rect(x - 8 + 3 * i, y - ((game.tick + i * 11) % 37), 2, 5, "#cdfbff")
                self.label("↑ " + AREAS[target]["name"], x, y - 50, "#baf6ff")
        nearby = None
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
            if nearby is None:
                nearby = game.nearby()
            if nearby[1] == npc:
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
                duration = m["windup_duration"]
                phase = 0.55 * (1 - (m["windup"] - game.tick) / duration)
            else:
                phase = 0.55 + 0.45 * after_strike / 9
        else:
            action = "move"
        y = monster_feet_y(m, game.tick)
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

    def draw(self, game, paused, profile=None, portal_fade=0, peers=()):
        width,height = self.view_width,self.view_height
        self.ctx.setTransform(self.scale_x,0,0,self.scale_y,0,0)
        self.ctx.imageSmoothingEnabled = False
        if not self.ready:
            self.rect(0,0,width,height,"#183744")
            text = "그래픽 파일을 불러오지 못했어요." if self.failed else f"도트 그래픽 불러오는 중 · {len(self.loaded)}/{len(IMAGES)}"
            self.label(text,width/2,height/2,size=16)
            return
        ctx = self.ctx
        x, y, tick = game.p["x"], game.p["y"], game.tick
        left,top = round(game.camera),round(game.camera_y)
        right = left+width
        region = area_at(x)
        area = AREAS[region]
        self.backdrop(area,left,top)
        ctx.save()
        ctx.translate(-left,-top)
        self.terrain(region,left,right)
        self.scenery(game,area,left,right)
        for m in game.monsters_in_area(region):
            if left - 100 < m["x"] < right + 100 and top-100 < m["y"] < top+height+140:
                self.monster(game, m)
        for drop in game.drops:
            if left <= drop["x"] <= right:
                elapsed = tick - drop["start"]
                bounce = 28 * sin(min(1, elapsed / 24) * pi)
                for index, id in enumerate([None] + drop["items"]):
                    self.icon(7 if id is None else item_icon(id), drop["x"] + index * 13 - 11, drop["y"] - 10 - bounce, 18)
        for player, px, py in peers:
            if left-80 < px < right+80 and top-20 < py < top+height+90:
                equipment = player["equipment"]
                lean = MELEE_LEAN[player["swing"]]*player["facing"] if player["swing"] is not None else 0
                self.avatar(ctx,equipment,equipment.get("weapon"),player["frame"],px+lean,py,80,
                            player["facing"],swing_tick=player["swing"],job=player["job"])
                self.label(f"Lv.{player['level']} {player['name']}",px,py-74,"#a7e6ff")
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
                    swing_tick, game.p["job"], rotation, thrust)
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
            self.rect(0,0,width,height,f"rgba(19,32,47,{portal_fade*.78})")
        if paused:
            self.rect(0,0,width,height,"#11283888")
            self.label("일시정지",width/2,height/2,size=22)
