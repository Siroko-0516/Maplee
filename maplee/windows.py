"""Pixel-atlas game HUD and live windows. Coordinates are logical screen pixels."""
from browser import document, window
from .classic_skin import CLASSIC_REGIONS
from .content import AREAS, ATTRIBUTES, CLASSES, EXPANSION_ICON_COLUMNS, GROUND, HOTBAR_ACTIONS, ITEMS, LEDGES, PANORAMA_Y, SLOTS, SPECIES, SUPPORTS, monster_art
from .hunting import HUNT_ZONES
from .engine import HEIGHT, PORTALS, area_at, ground_at, item_icon, limit
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
        ctx.font = f"{'bold ' if bold else ''}{size}px Gulim, Dotum, Arial, sans-serif"
        ctx.fillStyle, ctx.textAlign, ctx.textBaseline = color, align, "middle"
        text = str(value)
        if width:
            while len(text) > 1 and number(ctx.measureText(text).width) > width:
                text = text[:-2] + "…"
        ctx.fillText(text, round(x), round(y))

    def atlas(self, key, sx, sy, sw, sh, x, y, w, h):
        self.ctx.drawImage(self.app.renderer.images[key], sx, sy, sw, sh, round(x), round(y), round(w), round(h))

    def classic(self, name, x, y, w=None, h=None, crop=None):
        sx,sy,sw,sh = CLASSIC_REGIONS[name]
        if crop:
            dx,dy,sw,sh = crop
            sx,sy = sx+dx,sy+dy
        if min(sw,sh) > 0:
            self.atlas("classic_ui",sx,sy,sw,sh,x,y,sw if w is None else w,sh if h is None else h)

    def bezel(self, name, x, y, w, h, sides=(6,6,6,6)):
        _,_,sw,sh = CLASSIC_REGIONS[name]
        left,top,right,bottom = sides
        sx,sy = (0,left,sw-right), (0,top,sh-bottom)
        ws,hs = (left,sw-left-right,right),(top,sh-top-bottom,bottom)
        widths,heights = (left,w-left-right,right),(top,h-top-bottom,bottom)
        for row,yy in enumerate((y,y+top,y+h-bottom)):
            for col,xx in enumerate((x,x+left,x+w-right)):
                if widths[col] > 0 and heights[row] > 0:
                    self.classic(name,xx,yy,widths[col],heights[row],(sx[col],sy[row],ws[col],hs[row]))

    def picture_button(self, normal, x, y, w, h, name, callback):
        self.classic(normal,x,y,w,h)
        if callback:
            self.hit(x-2,y-2,w+4,h+4,name,callback)

    def icon(self, key, index, x, y, size):
        if key == "icons" and index in EXPANSION_ICON_COLUMNS:
            key, index = "expansion_icons", EXPANSION_ICON_COLUMNS[index]
        cols = 8 if key in ("icons","expansion_icons") else 9
        self.atlas(key, index % cols*32, index // cols*32, 32, 32, x, y, size, size)

    def shine(self, x, y, w, h, top, bottom, edge):
        self.box(x, y, w, h, edge)
        self.box(x+1, y+1, w-2, h-2, bottom)
        self.box(x+1, y+1, w-2, max(2, h//2-1), top)

    def button(self, x, y, w, h, label, callback, name=None, selected=False):
        name = name or label
        self.bezel("button" if callback else "tab_off", x, y, w, h, (4,4,5,4))
        if selected or self.hover == name:
            self.box(x+4,y+h-3,w-9,1,"#fff8af")
        self.text(label, x+w/2+1, y+h/2+1, "#496017" if callback else "#69767c", 12, True, "center", w-5)
        self.text(label, x+w/2, y+h/2, "#fbffef" if callback else "#eef2f0", 12, True, "center", w-5)
        if callback:
            self.hit(x, y, w, h, name, callback)

    def dock(self):
        game, p = self.app.game, self.app.game.p
        stats = game.stats()
        compact = self.w < 730
        height = 104 if compact else 72
        y = self.h-height
        barw = min(197, max(120, self.w-187)) if compact else min(204, round(self.w*.24))
        hx,hy = 5,y+1
        def ux(n):
            return round(barw*n/204)
        for stat,yy in (("hp",28),("mp",44)):
            gx,gw = hx+ux(25),ux(171)
            self.box(gx,hy+yy,gw,13,"#2a2830")
            amount = limit(p[stat]/max(1,stats[stat]),0,1)
            source_w = round(amount*171)
            if source_w:
                self.classic("hud_"+stat,gx,hy+yy,round(gw*amount),13,(0,0,source_w,13))
        self.classic("hud",hx,hy,barw,64,crop=(0,0,204,64))
        self.classic("lv",hx+6,hy+7)
        self.text(p["level"],hx+24,hy+12,CREAM,13,True)
        self.text(CLASSES[p["job"]]["name"],hx+46,hy+12,WHITE,13,True,width=barw//2-27)
        self.text(f"{p['gold']:,} 메소",hx+barw-6,hy+13,"#ffe6a0",10,True,"right",barw//2-4)
        for key,cy in (("hp",35),("mp",51)):
            txt=f"{p[key]} / {stats[key]}"
            self.text(txt,hx+barw//2+9,hy+cy+1,"#442f39",10,True,"center")
            self.text(txt,hx+barw//2+9,hy+cy,WHITE,10,True,"center")
        ax = self.w-4*39-8 if compact else barw+14
        self.bezel("chrome",ax-3,y+5,159,54,(6,8,6,6))
        for i, action in enumerate(p["hotbar"]):
            x = ax+i*39
            self.classic("quick_cell",x,y+9,37,43)
            item = {"hp": "potion", "mp": "tonic", "skill": p["equipment"]["weapon"]}.get(action)
            if action:
                self.icon("icons", item_icon(item) if item else 13 if action=="support" else 6, x+4, y+14, 29)
            self.box(x+1,y+10,11,12,"#242b35")
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
        my = y+64 if compact else y+6
        self.bezel("chrome",mx-3,my-3,gap*9+6,(34 if compact else 52)+4,(5,7,5,5))
        for i, name in enumerate((*self.menus, "pause")):
            x = mx+i*gap
            label = "계속" if i==8 and self.app.paused else MENU_NAMES[i]
            if self.app.panel and self.app.panel[0] == name or self.hover == label:
                self.shine(x, my, gap-1, 32 if compact else 52, "#547789", "#314c65", "#9cbcc9")
            size = 19 if compact else 29
            ix=x+(gap-size)//2
            plate={0:"hud_character",6:"hud_account",7:"hud_setting"}.get(i,"hud_plate")
            self.classic(plate,ix,my,size,size)
            if plate == "hud_plate":
                self.icon("interface",i,ix+1,my,size-3)
            self.text(label, x+gap/2, my+size+6, WHITE, 11, True, "center")
            self.hit(x, my, gap-1, size+17, label,
                     self.app.toggle_pause if i==8 else lambda name=name: self.app.show_panel(name))
        self.box(0,self.h-9,self.w,9,"#242323")
        expw=round(self.w*min(1,p["xp"]/max(1,game.xp_needed())))
        if expw:
            self.classic("exp_strip",0,self.h-8,expw,7)
        self.text(f"EXP   {p['xp']} / {game.xp_needed()}",self.w//2,self.h-5,WHITE,9,True,"center")
        return y

    def minimap(self):
        game, p = self.app.game, self.app.game.p
        area = AREAS[area_at(p["x"])]
        w = 153 if self.w < 530 else 188
        x, y = 10, 8
        # The minimap has its own nine asymmetric pieces in the game atlas.
        for r,(cy,ch) in enumerate(((y,29),(y+29,28),(y+57,12))):
            for c,(cx,cw) in enumerate(((x,42),(x+42,w-84),(x+w-42,42))):
                name = (("nw","n","ne"),("w","c","e"),("sw","s","se"))[r][c]
                self.classic("mini_"+name,cx,cy,cw,ch)
        self.text(area["name"],x+8,y+19,WHITE,12,True,width=w-30)
        self.text("M",x+w-9,y+13,CREAM,10,True,"right")
        self.box(x+5,y+27,w-10,35,"#26323bbf")
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
        qx=self.w-qw-10
        self.classic("quest_top",qx,y,qw,22)
        self.box(qx+2,y+22,qw-4,23,"#192632e8")
        self.classic("quest_body",qx,y+22,qw,22)
        self.classic("quest_end",qx,y+44,qw,6)
        self.text("퀘스트 알림",qx+11,y+12,CREAM,12,True)
        self.text(game.quest_caption(),qx+11,y+32,WHITE,12,True,width=qw-20)
        self.hit(self.w-qw-10, y, qw, 50, "퀘스트 알림", lambda: self.app.show_panel("journal"))

    def touch(self, bottom):
        if not self.coarse:
            return
        keys = (("◀","ArrowLeft"),("▶","ArrowRight"),("↓","ArrowDown"),("점프","Space"),
                ("공격","KeyZ"),("스킬","KeyX"),("대화","ArrowUp"))
        for i, (label, key) in enumerate(keys):
            x = 6+i*38 if i<3 else self.w-6-(7-i)*38
            self.bezel("chrome",x,bottom-41,36,38,(5,7,5,5))
            self.text(label,x+18,bottom-22,CREAM if key in self.app.pointers.values() else WHITE,13,True,"center")
            self.hit(x,bottom-41,36,38,key,None,"hold")

    def stat_pair(self, x, y, w, label, value, action=None, attr=False):
        # Stretch the white value field only. The lime label keeps its original
        # nine-pixel Korean lettering, corner highlights and stipple.
        self.classic("stat_row",x,y,60,20,(0,0,60,18))
        self.classic("stat_row",x+60,y,w-66,20,(60,0,124,18))
        self.classic("stat_row",x+w-6,y,6,20,(184,0,6,18))
        names = {"직업":"job","레벨":"level","경험치":"exp","HP":"hp","MP":"mp"}
        if label in names:
            self.classic(names[label]+"_label",x+2,y+1,45,17)
        else:
            self.text(label,x+5,y+11,"#436b13",12,True)
            self.text(label,x+4,y+10,"#fcffdf",12,True)
        self.text(value,x+67,y+10,INK,12,width=w-74-(18 if attr else 0))
        if attr:
            self.picture_button("up" if action else "up_off",x+w-18,y+3,14,14,label+" 배분",action)

    def stats(self, x, y, w):
        game, p = self.app.game, self.app.game.p
        stats = game.stats()
        fields = (("레벨",p["level"]),("직업",CLASSES[p["job"]]["name"]),
                  ("경험치",f"{p['xp']} / {game.xp_needed()}"),("공격력",stats["attack"]),
                  ("HP",f"{p['hp']} / {stats['hp']}"),("MP",f"{p['mp']} / {stats['mp']}"))
        for label,value in fields:
            self.stat_pair(x,y,w,label,value)
            y += 21
        self.classic("ap",x,y+2,w,46)
        self.text(game.ap(),x+w*75/198,y+33,INK,13,True,"center")
        y += 51
        for code,(key,attr) in zip(STAT_CODES,ATTRIBUTES.items()):
            action=(lambda key=key:self.app.execute(lambda:game.add_attribute(key))) if game.ap() else None
            self.stat_pair(x,y,w,f"{code}  {attr['name']}",p["attributes"][key],action,True)
            y += 21
        caption="접기" if self.detail else "자세히 보기"
        self.picture_button("detail_close" if self.detail else "detail_open",x+w-79,y+5,78,19,caption,self.toggle_detail)
        y += 28
        if self.detail:
            for label,value in (("방어력",stats["defense"]),("이동 속도",f"{stats['speed']:.2f}"),("처치 수",p["kills"])):
                self.stat_pair(x,y,w,label,value)
                y += 21
        return y

    def toggle_detail(self):
        self.detail = not self.detail
        self.refresh()

    def doll(self, x, y, w):
        p = self.app.game.p
        self.bezel("paper",x,y,w,146)
        middle = x+w//2
        self.shine(middle-62,y+4,124,137,"#7f94a5","#c2d2da","#75838d")
        self.atlas("interface",0,64,120,100,middle-60,y+6,120,113)
        equipment=p["equipment"]
        self.app.renderer.avatar(self.ctx,equipment,equipment.get("weapon"),idle_pose(self.app.game.tick),
                                 middle,y+114,115,-1,job=p["job"])
        self.box(middle-60,y+119,120,19,"#374e68")
        self.text(f"Lv. {p['level']}  {CLASSES[p['job']]['name']}",middle,y+128,WHITE,12,True,"center")
        for i,(slot,label) in enumerate(SLOTS.items()):
            item=equipment[slot]
            left=middle-114 if i<3 else middle+67
            top=y+4+(i%3)*46
            self.box(left,top,46,44,"#a1bb31" if item else "#b0b6bb")
            self.classic("cell",left+1,top+1,44,42)
            if item:
                self.icon("icons",item_icon(item),left+7,top+1,32)
                self.hit(left,top,46,44,label+" "+ITEMS[item]["name"],lambda item=item:self.app.select_item(item))
            self.text(label,left+23,top+37,"#5b6575",10,True,"center")
        return y+149

    def item_grid(self,x,y,w,items,selected):
        cell=36
        columns=max(1,w//cell)
        rows=max(2,(len(items)+columns-1)//columns)
        p=self.app.game.p
        for i in range(rows*columns):
            item=items[i] if i<len(items) else None
            left,top=x+(w-columns*cell)//2+i%columns*cell,y+i//columns*cell
            self.box(left,top,cell-1,cell-1,"#dea528" if item and item==selected else "#a3abb0")
            self.classic("cell",left+1,top+1,cell-3,cell-3)
            if item:
                self.icon("icons",item_icon(item),left+1,top+1,32)
                if p["bag"][item]>1:
                    self.text(p["bag"][item],left+32,top+28,INK,10,True,"right")
                self.hit(left,top,cell-1,cell-1,ITEMS[item]["name"],lambda item=item:self.app.select_item(item))
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
                    left=x+i*tw
                    current=key==active
                    self.bezel("tab_on" if current else "tab_off",left,y+(0 if current else 2),tw-1,23 if current else 21,(4,4,3,3))
                    self.text(label,left+tw/2+1,y+13,"#83582c" if current else "#58606b",12,True,"center")
                    self.text(label,left+tw/2,y+12,WHITE,12,True,"center")
                    self.hit(left,y,tw-1,23,group+" "+label,lambda key=key,group=group:self.app.set_tab(group,key))
                self.box(x,y+23,w,2,"#eb8d31")
                y += 27
            elif kind == "route":
                player = self.app.game.p["x"]
                current = area_at(player)
                for i,area in enumerate(AREAS):
                    self.bezel("paper",x,y,w,48)
                    image=area["image"]
                    iw,_=self.app.renderer.sizes[image]
                    sx=min(area["view"],iw-iw//5)
                    self.atlas(image,sx,PANORAMA_Y+HEIGHT//4,max(1,iw//5),HEIGHT//2,x+4,y+4,70,40)
                    self.box(x+80,y+3,2,42,"#839a99")
                    self.box(x+77,y+19,8,8, "#a8ce33" if i==current else "#68899d")
                    self.text(area["name"],x+94,y+15,INK,14,True)
                    low, high = HUNT_ZONES[i]["levels"]
                    desc = f"현재 위치 · Lv. {low}–{high}" if i==current else f"포털 이동 · Lv. {low}–{high}"
                    self.text(desc,x+94,y+32,"#567342",12)
                    self.text(HUNT_ZONES[i]["label"],x+94,y+45,"#3a5364",10)
                    y += 53
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
                self.classic("book_paper",x,y,w,54)
                self.classic("book_edge",x,y,6,54)
                sx,sy,sw,sh,_,_=monster_art(spec,"stand",self.app.game.tick)
                scale=min(1,44/max(sw,sh))
                self.atlas(spec.get("image","wildlife"),sx,sy,sw,sh,x+31-sw*scale/2,y+47-sh*scale,sw*scale,sh*scale)
                self.text(f"Lv.{spec['level']}  {spec['name']}",x+60,y+15,"#5e4736",13,True)
                self.text(detail or "첫 처치 시 전리품 기록",x+60,y+35,"#715f4c",11,width=w-65)
                y += 56
            else:
                _, title, detail, action, callback, disabled, item = entry
                offset = 39 if item else 7
                button_w = max(51, len(action or "")*11+9) if action else 0
                area_w = w-offset-button_w-14
                lines = self.lines(detail,area_w) if detail else []
                h = max(41, 26+15*len(lines))
                if item:
                    self.classic("panel_card",x,y,37,h,crop=(0,0,37,35))
                    self.classic("panel_card",x+37,y,w-37,h,crop=(37,0,103,35))
                    self.icon("icons",item_icon(item),x+2,y+(h-32)//2,32)
                else:
                    self.bezel("paper",x,y,w,h,(3,3,3,3))
                self.text(title,x+offset,y+13,INK,13,True,width=area_w)
                for j,line in enumerate(lines):
                    self.text(line,x+offset,y+30+j*15,"#516071",11)
                if action:
                    self.button(x+w-button_w-4,y+(h-23)//2,button_w,23,action,None if disabled else callback,title+" "+action)
                y += h+3
        return y

    def lines(self, value, width):
        self.ctx.font = "12px Gulim, Dotum, Arial, sans-serif"
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
        w=min(249 if key=="character" else 352,self.w-14)
        h=min((398 if self.detail else 337) if key=="character" else 379,
              max(115,bottom-12-(41 if self.coarse else 0)))
        x,y=self.position or (self.w-w-12,min(83,bottom-h-6))
        x=int(limit(x,4,self.w-w-4))
        y=int(limit(y,4,max(4,bottom-h-(41 if self.coarse else 4))))
        self.position=(x,y)
        self.frame_box=(x,y,w,h)
        self.box(x+3,y+4,w-2,h-1,"#18202a77")
        self.bezel("chrome",x,y,w,h,(8,23,8,8))
        self.bezel("paper",x+6,y+22,w-12,h-28,(5,5,5,8))
        title_key=key+"_title"
        if title_key in CLASSIC_REGIONS and not npc:
            self.classic(title_key,x+(w-128)//2,y+3,128,20)
        else:
            name=npc["name"]+" · "+npc["role"] if npc else TITLES.get(key,self.menus.get(key,"NPC TALK"))
            self.text(name,x+w//2+1,y+13,"#3a2e1b",11,True,"center")
            self.text(name,x+w//2,y+12,CREAM,11,True,"center")
        self.hit(x,y,w,h,"창",kind="surface")
        self.hit(x+3,y+2,w-32,24,"창 이동",kind="drag")
        self.picture_button("close",x+w-23,y+5,16,16,"닫기",self.app.close_panel)
        left,top=x+11,y+28
        inner_h,inner_w=h-38,w-34
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
            self.picture_button("prev",rx,top,15,16,"위로 스크롤",lambda:self.scroll_by(-68))
            self.picture_button("next",rx,top+inner_h-16,15,16,"아래로 스크롤",lambda:self.scroll_by(68))
            self.box(rx+4,top+17,7,inner_h-34,"#b3b2b0")
            track=inner_h-35
            thumb=max(16,round(track*inner_h/(inner_h+self.maximum)))
            self.classic("thumb",rx,top+17+(track-thumb)*self.scroll/self.maximum,15,thumb)


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
