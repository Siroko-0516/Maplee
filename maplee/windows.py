"""Pixel-atlas game HUD and live windows. Coordinates are logical screen pixels."""
from browser import document, window
from .content import AREAS, ATTRIBUTES, CLASSES, GROUND, HOTBAR_ACTIONS, ITEMS, LEDGES, SLOTS, SPECIES, SPRITES, SUPPORTS
from .engine import PORTALS, area_at, ground_at, item_icon, limit
from .render import idle_pose, number


TITLES = {"character": "CHARACTER STAT", "inventory": "EQUIPMENT", "skills": "SKILL BOOK",
          "journal": "QUEST LOG", "map": "WORLD MAP", "bestiary": "MONSTER BOOK",
          "account": "ACCOUNT", "hotkeys": "KEY SETTINGS", "shop": "ITEM SHOP",
          "trainer": "JOB ADVANCEMENT", "forge": "WORKSHOP"}
MENU_NAMES = ("능력치", "스킬", "장비", "퀘스트", "지도", "도감", "계정", "설정", "정지")
STAT_CODES = ("STR", "VIT", "SPI", "AGI")
INK = "#263547"
CREAM = "#ffdc78"
WHITE = "#f6fafb"


class GameInterface:
    def __init__(self, app, canvas, menus):
        self.app, self.canvas, self.menus = app, canvas, menus
        self.ctx = canvas.getContext("2d")
        self.hits = []
        self.pointer = {}
        self.clip = None
        self.hover = self.focus = None
        self.scroll = self.maximum = 0
        self.position = None
        self.frame_box = None
        self.detail = False
        self.last_draw = -1000
        self.coarse = bool(window.matchMedia("(pointer: coarse)").matches) if hasattr(window, "matchMedia") else False
        self.resize()
        canvas.bind("pointerdown", self.down)
        canvas.bind("pointermove", self.move)
        canvas.bind("pointerup", self.up)
        for event in ("pointercancel", "lostpointercapture"):
            canvas.bind(event, self.cancel)
        canvas.bind("wheel", self.wheel)
        window.bind("blur", self.reset_pointers)

    def resize(self, _=None):
        bounds = self.canvas.getBoundingClientRect()
        width, height = max(1, number(bounds.width)), max(1, number(bounds.height))
        scale = max(.75, min(1.35, width / 820, height / 490))
        self.w, self.h = round(width / scale), round(height / scale)
        dpr = max(1, min(3, number(window.devicePixelRatio or 1)))
        for key, n in (("width", width), ("height", height)):
            self.canvas.attrs[key] = str(round(n * dpr))
        self.refresh()

    def refresh(self):
        self.last_draw = -1000

    def change_page(self):
        self.scroll = self.maximum = 0
        self.focus = self.hover = None
        self.hits.clear()
        self.refresh()

    def pos(self, e):
        box = self.canvas.getBoundingClientRect()
        return (round((number(e.clientX) - number(box.left)) * self.w / number(box.width)),
                round((number(e.clientY) - number(box.top)) * self.h / number(box.height)))

    def hit(self, x, y, w, h, name, fn=None, kind="action"):
        if self.clip:
            cx, cy, cw, ch = self.clip
            right, bottom = min(x+w, cx+cw), min(y+h, cy+ch)
            x, y = max(x, cx), max(y, cy)
            w, h = right-x, bottom-y
        if w > 0 and h > 0:
            self.hits.append((x, y, w, h, name, fn, kind))

    def at(self, x, y):
        return next((entry for entry in reversed(self.hits)
                     if entry[0] <= x < entry[0]+entry[2] and entry[1] <= y < entry[1]+entry[3]), None)

    def down(self, e):
        if number(e.button) > 0:
            return
        e.preventDefault()
        self.canvas.focus()
        x, y = self.pos(e)
        target = self.at(x, y)
        if not target:
            return
        pid = int(number(e.pointerId))
        self.canvas.setPointerCapture(e.pointerId)
        self.pointer[pid] = (target, x, y, self.position, self.scroll)
        if target[6] == "hold" and not self.app.paused:
            self.app.pointers[pid] = target[4]
            self.app.action(target[4])
        self.refresh()

    def move(self, e):
        x, y = self.pos(e)
        active = self.pointer.get(int(number(e.pointerId)))
        if active:
            target, sx, sy, initial, scroll = active
            if target[6] == "drag" and initial:
                self.position = (initial[0] + x-sx, initial[1] + y-sy)
            elif self.frame_box and self.inside_body(sx, sy) and abs(y-sy) > 5:
                self.scroll = limit(scroll + sy-y, 0, self.maximum)
        target = self.at(x, y)
        self.hover = target[4] if target else None
        self.canvas.style.cursor = "move" if target and target[6] == "drag" else "pointer" if target and target[5] else "default"
        self.refresh()

    def up(self, e):
        pid = int(number(e.pointerId))
        active = self.pointer.pop(pid, None)
        self.app.pointers.pop(pid, None)
        if active:
            target, sx, sy, _, _ = active
            x, y = self.pos(e)
            current = self.at(x, y)
            if current and current[4] == target[4] and abs(sx-x) < 8 and abs(sy-y) < 8 and current[5] and current[6] == "action":
                current[5]()
        self.refresh()

    def cancel(self, e):
        pid = int(number(e.pointerId))
        self.pointer.pop(pid, None)
        self.app.pointers.pop(pid, None)
        self.refresh()

    def reset_pointers(self, _):
        self.pointer.clear()
        self.app.pointers.clear()
        self.refresh()

    def inside_body(self, x, y):
        if not self.frame_box:
            return False
        a, b, w, h = self.frame_box
        return a <= x < a+w and b+24 <= y < b+h

    def wheel(self, e):
        if self.inside_body(*self.pos(e)):
            e.preventDefault()
            self.scroll_by(number(e.deltaY) * (22 if e.deltaMode else 1))

    def scroll_by(self, value):
        self.scroll = limit(round(self.scroll + value), 0, self.maximum)
        self.refresh()

    def navigate(self, key, backwards):
        actions = [entry for entry in self.hits if entry[5] and entry[6] == "action"]
        if not actions:
            return False
        pos = next((i for i, entry in enumerate(actions) if self.focus == entry[4]), -1)
        if key == "Tab":
            entry = actions[(pos + (-1 if backwards else 1)) % len(actions)]
            self.focus = entry[4]
            document["toast"].text = entry[4]
        elif pos >= 0:
            actions[pos][5]()
        else:
            return False
        self.refresh()
        return True

    def box(self, x, y, w, h, color):
        self.ctx.fillStyle = color
        self.ctx.fillRect(round(x), round(y), round(w), round(h))

    def text(self, value, x, y, color=INK, size=13, bold=False, align="left", width=None):
        ctx = self.ctx
        ctx.font = f"{'bold ' if bold else ''}{size}px system-ui, sans-serif"
        ctx.fillStyle, ctx.textAlign, ctx.textBaseline = color, align, "middle"
        text = str(value)
        if width:
            while len(text) > 1 and number(ctx.measureText(text).width) > width:
                text = text[:-2] + "…"
        ctx.fillText(text, round(x), round(y))

    def atlas(self, key, sx, sy, sw, sh, x, y, w, h):
        self.ctx.drawImage(self.app.renderer.images[key], sx, sy, sw, sh, round(x), round(y), round(w), round(h))

    def skin(self, index, x, y, w, h):
        edges = (6, 20, 6)
        dx, dy = (6, w-12, 6), (6, h-12, 6)
        for row, sy in enumerate((0, 6, 26)):
            for col, sx in enumerate((0, 6, 26)):
                self.atlas("interface", 32*index+sx, 32+sy, edges[col], edges[row],
                           x+sum(dx[:col]), y+sum(dy[:row]), dx[col], dy[row])

    def icon(self, key, index, x, y, size):
        cols = 8 if key == "icons" else 9
        self.atlas(key, index % cols*32, index // cols*32, 32, 32, x, y, size, size)

    def pose(self, key, frame, x, y, size):
        spec = SPRITES[key]
        sw, sh = spec["frameWidth"], spec["frameHeight"]
        self.atlas(key, frame % spec["columns"] * sw, frame // spec["columns"] * sh,
                   sw, sh, x, y, size, size)

    def shine(self, x, y, w, h, top, bottom, edge):
        self.box(x, y, w, h, edge)
        self.box(x+1, y+1, w-2, h-2, bottom)
        self.box(x+1, y+1, w-2, max(2, h//2-1), top)

    def button(self, x, y, w, h, label, callback, name=None, selected=False):
        name = name or label
        if callback and (selected or self.hover == name):
            self.skin(4, x, y, w, h)
        else:
            self.shine(x, y, w, h, "#f8fafb" if callback else "#dce0e0",
                       "#bec9d1" if callback else "#c9cdcc", "#74838d")
        self.text(label, x+w/2, y+h/2, INK if callback else "#6d777c", 12, True, "center", w-4)
        if callback:
            self.hit(x, y, w, h, name, callback)

    def meter(self, x, y, w, h, name, value, maximum, colors):
        self.box(x, y, w, h, "#0d1827")
        self.box(x+1, y+1, w-2, h-2, "#333b4a")
        fill = round((w-2)*limit(value / max(1, maximum), 0, 1))
        self.box(x+1, y+1, fill, h-2, colors[1])
        self.box(x+1, y+1, fill, max(1, (h-2)//2), colors[0])
        self.text(name, x+4, y+h/2, WHITE, 10, True)
        self.text(f"{value} / {maximum}", x+w-4, y+h/2, WHITE, 10, True, "right")

    def dock(self):
        game, p = self.app.game, self.app.game.p
        stats = game.stats()
        compact = self.w < 730
        height = 104 if compact else 72
        y = self.h-height
        self.skin(1, 0, y, self.w, height)
        barw = min(182, max(100, self.w-210)) if compact else min(180, round(self.w*.20))
        self.text(f"Lv. {p['level']}   {CLASSES[p['job']]['name']}", 12, y+14, CREAM, 14, True)
        self.text(f"{p['gold']:,} 메소", 8+barw, y+14, "#efcf8a", 10, False, "right", max(36,barw-83))
        self.meter(10, y+25, barw, 15, "HP", p["hp"], stats["hp"], ("#f68987", "#ba3a51"))
        self.meter(10, y+42, barw, 15, "MP", p["mp"], stats["mp"], ("#6dc7ff", "#3571b7"))
        ax = self.w-4*39-12 if compact else barw+24
        for i, action in enumerate(p["hotbar"]):
            x = ax+i*39
            self.skin(2, x, y+9, 37, 43)
            item = {"hp": "potion", "mp": "tonic", "skill": p["equipment"]["weapon"]}.get(action)
            if action:
                self.icon("icons", item_icon(item) if item else 13 if action=="support" else 6, x+4, y+14, 29)
            self.box(x+2, y+10, 10, 12, "#263447")
            self.text(i+1, x+7, y+16, WHITE, 10, True, "center")
            badge = p["pots"] if action=="hp" else p["tonics"] if action=="mp" else ""
            if action == "skill" and game.skill_cd:
                badge = f"{(game.skill_cd+59)//60}s"
            if action == "support":
                badge = "잠김" if not p["skillRanks"]["support"] else f"{(game.support_cd+59)//60}s" if game.support_cd else ""
            if badge != "":
                self.box(x+15, y+38, 20, 12, "#283544")
                self.text(badge, x+33, y+44, WHITE, 10, True, "right")
            self.hit(x, y+9, 37, 43, f"{i+1}번 " + HOTBAR_ACTIONS.get(action, {}).get("name", "빈 슬롯"), lambda i=i: self.app.run_slot(i))
        gap = min(54, (self.w-12)//9) if compact else min(57, (self.w-ax-167)//9)
        mx = (self.w-gap*9)//2 if compact else self.w-7-gap*9
        my = y+59 if compact else y+4
        for i, name in enumerate((*self.menus, "pause")):
            x = mx+i*gap
            label = "계속" if i==8 and self.app.paused else MENU_NAMES[i]
            if self.app.panel and self.app.panel[0] == name or self.hover == label:
                self.shine(x, my, gap-1, 32 if compact else 52, "#547789", "#314c65", "#9cbcc9")
            size = 19 if compact else 27
            self.icon("interface", i, x+(gap-size)//2, my, size)
            self.text(label, x+gap/2, my+size+6, WHITE, 11, True, "center")
            self.hit(x, my, gap-1, size+17, label,
                     self.app.toggle_pause if i==8 else lambda name=name: self.app.show_panel(name))
        self.meter(7, self.h-13, self.w-14, 10, "EXP", p["xp"], game.xp_needed(), ("#e4b833", "#ab7718"))
        return y

    def minimap(self):
        game, p = self.app.game, self.app.game.p
        area = AREAS[area_at(p["x"])]
        w = 153 if self.w < 530 else 188
        x, y = 10, 8
        self.skin(1, x, y, w, 69)
        self.text(area["name"], x+10, y+13, CREAM, 13, True)
        self.text("M", x+w-11, y+13, "#b6cfdf", 10, True, "right")
        self.box(x+6, y+23, w-12, 40, "#1d3848")
        start, end = area["start"], area["end"]
        def sx(world):
            return round(x+9 + (w-18)*(world-start)/(end-start))
        def sy(world):
            return y+27+round(world/16)
        pts = [(start, ground_at(start))] + [(a,b) for a,b in GROUND if start<a<end] + [(end,ground_at(end))]
        ctx = self.ctx
        ctx.beginPath()
        ctx.moveTo(sx(start), y+62)
        for a,b in pts:
            ctx.lineTo(sx(a), sy(b))
        ctx.lineTo(sx(end), y+62)
        ctx.fillStyle = "#56926f"
        ctx.fill()
        for ledge in LEDGES:
            if start <= ledge["x"] < end:
                self.box(sx(ledge["x"]), sy(ledge["y"]), max(2,sx(ledge["x"]+ledge["w"])-sx(ledge["x"])), 2, "#b6dba0")
        for a, _, _ in PORTALS:
            if start<=a<end:
                self.box(sx(a)-1, sy(ground_at(a))-4, 3, 5, "#78dfff")
        self.box(sx(p["x"])-2, sy(p["y"])-4, 5, 5, "#fcdb51")
        self.hit(x,y,w,69,"미니맵",lambda: self.app.show_panel("map"))
        qw = min(251, self.w-w-33)
        self.skin(1, self.w-qw-10, y, qw, 50)
        self.text("퀘스트 알림", self.w-qw, y+13, CREAM, 12, True)
        self.text(game.quest_caption(), self.w-qw, y+33, WHITE, 12, width=qw-18)
        self.hit(self.w-qw-10, y, qw, 50, "퀘스트 알림", lambda: self.app.show_panel("journal"))

    def touch(self, bottom):
        if not self.coarse:
            return
        keys = (("◀","ArrowLeft"),("▶","ArrowRight"),("↓","ArrowDown"),("점프","Space"),
                ("공격","KeyZ"),("스킬","KeyX"),("대화","ArrowUp"))
        for i, (label, key) in enumerate(keys):
            x = 6+i*38 if i<3 else self.w-6-(7-i)*38
            self.skin(1, x, bottom-41, 36, 38)
            self.text(label,x+18,bottom-22,CREAM if key in self.app.pointers.values() else WHITE,13,True,"center")
            self.hit(x,bottom-41,36,38,key,None,"hold")

    def stat_pair(self, x, y, w, label, value, action=None):
        self.shine(x, y, w, 21, "#ffffff", "#ecedeb", "#9caaa9")
        self.shine(x, y, 83, 21, "#d1ef56", "#a9d837", "#779b32")
        self.text(label, x+7, y+10, "#35481d", 12, True)
        self.text(value, x+91, y+10, INK, 13, width=w-96-(29 if action else 0))
        if action:
            self.button(x+w-26, y+1, 24, 19, "+", action, label+" 배분")

    def stats(self, x, y, w):
        game, p = self.app.game, self.app.game.p
        stats = game.stats()
        fields = [("레벨", p["level"]), ("직업", CLASSES[p["job"]]["name"]), ("공격력", stats["attack"]),
                  ("HP", f"{p['hp']} / {stats['hp']}"), ("MP", f"{p['mp']} / {stats['mp']}")]
        for label, value in fields:
            self.stat_pair(x,y,w,label,value)
            y += 22
        self.skin(3, x, y+2, w, 38)
        self.text("ABILITY POINT", x+10, y+16, WHITE, 12, True)
        self.text(f"남은 AP   {game.ap()}", x+w-11, y+21, WHITE, 14, True,"right")
        y += 43
        for code, (key, attr) in zip(STAT_CODES, ATTRIBUTES.items()):
            action = (lambda key=key: self.app.execute(lambda: game.add_attribute(key))) if game.ap() else None
            self.stat_pair(x, y, w, f"{code}  {attr['name']}", p["attributes"][key], action)
            y += 22
        self.button(x+w-96,y+2,96,22,"접기" if self.detail else "자세히 보기", self.toggle_detail)
        y += 27
        if self.detail:
            for label, value in (("방어력",stats["defense"]),("이동 속도",f"{stats['speed']:.2f}"),("처치 수",p["kills"])):
                self.stat_pair(x,y,w,label,value)
                y += 22
        return y

    def toggle_detail(self):
        self.detail = not self.detail
        self.refresh()

    def doll(self, x, y, w):
        p = self.app.game.p
        self.skin(2,x,y,w,130)
        middle = x + w//2
        self.atlas("interface",0,64,120,100,middle-60,y+5,120,120)
        self.ctx.save()
        self.ctx.translate(middle, y+5)
        self.ctx.scale(-1, 1)
        self.pose("hero", idle_pose(self.app.game.tick), -52, 0, 104)
        self.ctx.restore()
        self.box(middle-60,y+106,120,18,"#304965")
        self.text(f"Lv. {p['level']}  {CLASSES[p['job']]['name']}",middle,y+115,WHITE,12,True,"center")
        for i,(slot, label) in enumerate(SLOTS.items()):
            item = p["equipment"][slot]
            left = middle-106 if i < 3 else middle+65
            top = y+4+(i%3)*41
            self.shine(left,top,40,39,"#ebf5c4" if item else "#dce2dd",
                       "#bad076" if item else "#bbc7c6","#8ca14f" if item else "#8f9d9c")
            if item:
                self.icon("icons",item_icon(item),left+6,top+1,28)
                self.hit(left,top,40,39,label+" "+ITEMS[item]["name"],lambda item=item:self.app.select_item(item))
            self.text(label,left+20,top+31,"#415644",10,True,"center")
        return y+134

    def item_grid(self,x,y,w,items,selected):
        cell=38
        columns=max(1,w//cell)
        rows=max(1,(len(items)+columns-1)//columns)
        p=self.app.game.p
        for i in range(rows*columns):
            item=items[i] if i<len(items) else None
            left,top=x+i%columns*cell,y+i//columns*cell
            self.shine(left,top,cell-2,cell-2,"#fffef7" if item else "#e9edeb",
                       "#d8e6b9" if item else "#d8dfdc","#93a83c" if item==selected and item else "#a2b0ad")
            if item:
                self.icon("icons",item_icon(item),left+2,top+1,32)
                if p["bag"][item]>1:
                    self.text(p["bag"][item],left+33,top+29,INK,10,True,"right")
                self.hit(left,top,cell-2,cell-2,ITEMS[item]["name"],lambda item=item:self.app.select_item(item))
        return y+rows*cell+3

    def panel_entries(self, x, y, w):
        for entry in self.app.rows:
            kind = entry[0]
            if kind == "stats":
                y = self.stats(x,y,w)
            elif kind == "tabs":
                _, group, labels, active = entry
                tw = w//len(labels)
                for i,(key,label) in enumerate(labels):
                    self.button(x+i*tw,y,tw-2,23,label,lambda key=key,group=group:self.app.set_tab(group,key),
                                group+" "+label,key==active)
                y += 27
            elif kind == "route":
                for i,area in enumerate(AREAS):
                    self.skin(2,x,y,w,48)
                    image=area.get("image","background")
                    iw,ih=self.app.renderer.sizes[image]
                    sx=round(iw*area["backdrop"][0])
                    self.atlas(image,sx,ih//4,max(1,iw//7),ih//2,x+4,y+4,70,40)
                    self.box(x+80,y+3,2,42,"#839a99")
                    self.box(x+77,y+19,8,8, "#a8ce33" if i==entry[1] else "#68899d")
                    self.text(area["name"],x+94,y+15,INK,14,True)
                    self.text("현재 위치" if i==entry[1] else "포털에서 ↑로 이동", x+94,y+32,"#567342",12)
                    y += 49
            elif kind == "items":
                y = self.item_grid(x,y,w,entry[1],entry[2])
            elif kind == "doll":
                y = self.doll(x,y,w)
            elif kind == "note":
                for line in self.lines(entry[1],w-15):
                    self.text(line,x+5,y+12,"#415565",12)
                    y += 18
                y += 6
            elif kind == "monster":
                _, i, count, detail = entry
                spec = SPECIES[i]
                self.shine(x,y,w,53,"#f6f7f4","#e4e9e6","#a6b4b3")
                self.pose("wildlife",spec["sprite"]*6+((self.app.game.tick//15)%2),x+1,y,51)
                self.text(f"Lv.{spec['level']}  {spec['name']}",x+55,y+15,INK,13,True)
                self.text(detail or "첫 처치 시 전리품 기록", x+55,y+35,"#586579",11,width=w-60)
                y += 56
            else:
                _, title, detail, action, callback, disabled, item = entry
                offset = 39 if item else 7
                button_w = max(51, len(action or "")*11+9) if action else 0
                area_w = w-offset-button_w-14
                lines = self.lines(detail,area_w) if detail else []
                h = max(41, 26+15*len(lines))
                self.shine(x,y,w,h,"#f9faf8","#eaecea","#abb7b8")
                if item:
                    self.icon("icons",item_icon(item),x+4,y+(h-32)//2,32)
                self.text(title,x+offset,y+13,INK,13,True,width=area_w)
                for j,line in enumerate(lines):
                    self.text(line,x+offset,y+30+j*15,"#516071",11)
                if action:
                    self.button(x+w-button_w-4,y+(h-23)//2,button_w,23,action,None if disabled else callback,title+" "+action)
                y += h+3
        return y

    def lines(self, value, width):
        self.ctx.font = "12px system-ui, sans-serif"
        lines, line = [], ""
        for word in value.split():
            candidate = (line+" "+word).strip()
            if line and number(self.ctx.measureText(candidate).width) > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        return lines

    def panel_view(self, bottom):
        key, npc = self.app.panel
        w = min(304 if key=="character" else 352, self.w-14)
        h = min((407 if self.detail else 342) if key=="character" else 355, max(115,bottom-12-(41 if self.coarse else 0)))
        x, y = self.position or (self.w-w-12, min(83, bottom-h-6))
        x = int(limit(x,4,self.w-w-4))
        y = int(limit(y,4,max(4,bottom-h-(41 if self.coarse else 4))))
        self.position = (x,y)
        self.frame_box = (x,y,w,h)
        self.box(x+3,y+4,w,h,"#14232eaa")
        self.skin(0,x,y,w,h)
        self.shine(x+5,y+5,w-10,24,"#4a5767","#222e3e","#131d2a")
        title = npc["name"]+" · "+npc["role"] if npc else self.menus[key]
        english = TITLES.get(key,"NPC TALK")
        self.text(title,x+12,y+16,WHITE,13,True)
        self.text(english,x+w/2+10,y+16,CREAM,10,True,"center")
        self.hit(x,y,w,h,"창",kind="surface")
        self.hit(x+3,y+2,w-33,28,"창 이동",kind="drag")
        self.button(x+w-27,y+7,19,19,"×",self.app.close_panel,"닫기")
        left, top = x+9, y+33
        inner_h, inner_w = h-42, w-32
        self.clip = (left,top,inner_w,inner_h)
        ctx=self.ctx
        ctx.save()
        ctx.beginPath()
        ctx.rect(left,top,inner_w,inner_h)
        ctx.clip()
        start=top-self.scroll
        end=self.panel_entries(left,start,inner_w)
        ctx.restore()
        self.clip=None
        self.maximum=max(0,end-start-inner_h)
        if self.scroll > self.maximum:
            self.scroll = self.maximum
            self.refresh()
        if self.maximum:
            rx = x+w-20
            self.button(rx,top,15,18,"▴",lambda:self.scroll_by(-68),"위로 스크롤")
            self.button(rx,top+inner_h-18,15,18,"▾",lambda:self.scroll_by(68),"아래로 스크롤")
            self.box(rx+5,top+20,5,inner_h-40,"#a1afb5")
            track = inner_h-41
            thumb = max(12,round(track*inner_h/(inner_h+self.maximum)))
            self.box(rx+2,top+20+(track-thumb)*self.scroll/self.maximum,11,thumb,"#6d8291")

    def draw(self, now):
        if now-self.last_draw < 100:
            return
        self.last_draw=now
        self.ctx.setTransform(int(self.canvas.attrs["width"])/self.w,0,0,int(self.canvas.attrs["height"])/self.h,0,0)
        self.ctx.imageSmoothingEnabled=False
        self.ctx.clearRect(0,0,self.w,self.h)
        if not self.app.renderer.ready:
            return
        self.hits=[]
        self.frame_box=None
        self.minimap()
        bottom=self.dock()
        self.touch(bottom)
        now=number(window.performance.now())
        game=self.app.game
        messages=[]
        if now<self.app.notice_end:
            messages.append(self.app.notice_text)
        if now<self.app.loot_end:
            messages.append(self.app.loot_text)
        if game.tick<game.support_until:
            messages.append(SUPPORTS[game.p["job"]]["name"]+f"  {(game.support_until-game.tick+59)//60}초")
        for i,msg in enumerate(messages):
            w=min(self.w-20,max(165,len(msg)*11+24))
            y=bottom-26-i*24-(42 if self.coarse else 0)
            self.box((self.w-w)//2,y,w,21,"#172c3ee8")
            self.text(msg,self.w//2,y+11,WHITE,12,True,"center",w-8)
        if self.app.panel:
            self.panel_view(bottom)
        if self.focus:
            entry = next((e for e in self.hits if e[4]==self.focus),None)
            if entry:
                x,y,w,h=entry[:4]
                self.ctx.strokeStyle="#ffa623"
                self.ctx.lineWidth=2
                self.ctx.strokeRect(x+1,y+1,w-2,h-2)
