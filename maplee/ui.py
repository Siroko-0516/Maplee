"""Python browser UI, input lifecycle and save persistence."""
import json
from browser import document, html, timer, window
from .content import AREAS, ATTRIBUTES, CLASSES, GROUND, HOTBAR_ACTIONS, IMAGES, ITEMS, LEDGES, NPCS, QUESTS, RECIPES, SLOTS, SPECIES, SUPPORTS
from .engine import PORTALS, SAVE_KEY, START_X, STEP, Game, area_at, ground_at, item_icon
from .render import Renderer, number

SITE = "https://maplee-pixel-world.jisung-20090725.chatgpt.site"
MENUS = {"character": "능력치", "skills": "스킬", "inventory": "장비·가방", "journal": "퀘스트",
         "map": "지도", "bestiary": "도감", "account": "계정", "hotkeys": "설정"}
SHORTCUTS = dict(zip(("KeyC", "KeyS", "KeyI", "KeyQ", "KeyM", "KeyB"), tuple(MENUS)[:6]))
RARITIES = {"uncommon": "고급", "rare": "희귀", "epic": "영웅"}
ACTION_KEYS = {"Space", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "KeyZ", "KeyX", "KeyV",
               "KeyC", "KeyS", "KeyI", "KeyQ", "KeyM", "KeyB", "KeyR", "KeyK", "Digit1", "Digit2", "Digit3", "Digit4"}


def set_text(id, value):
    value = str(value)
    node = document[id]
    if node.text != value:
        node.text = value


def art(node, index):
    node.classList.add("pixel-icon")
    node.style.backgroundPosition = f"{100 * (index % 8) / 7}% {100 * (index // 8) / 3}%"
    node.attrs["aria-hidden"] = "true"
    return node


def icon(index, classes=""):
    return art(html.SPAN(Class=classes), index)


def item_details(id):
    item = ITEMS[id]
    parts = []
    if item.get("rarity"):
        parts.append(RARITIES[item["rarity"]])
    if item.get("slot"):
        parts.extend((SLOTS[item["slot"]], f"Lv. {item['level']}"))
    if item.get("job"):
        parts.append(CLASSES[item["job"]]["name"])
    for stat, label in (("attack", "공격"), ("defense", "방어"), ("hp", "HP"), ("mp", "MP")):
        if item.get(stat):
            parts.append(f"{label} +{item[stat]}")
    return " · ".join(parts)


def button(label, callback, disabled=False, pressed=None):
    node = html.BUTTON(label, type="button")
    node.disabled = bool(disabled)
    if pressed is not None:
        node.attrs["aria-pressed"] = "true" if pressed else "false"
    node.bind("click", lambda ev: callback())
    return node


class App:
    def __init__(self):
        try:
            saved = json.loads(window.localStorage.getItem(SAVE_KEY) or "null")
        except Exception:
            saved = None
        self.game = Game(saved)
        self.panel = None
        self.pane = document["panel"]
        self.modal = document["game-modal"]
        self.category = {}
        self.focus_before = None
        self.keys = set()
        self.pointers = {}
        self.paused = False
        self.previous = None
        self.accumulator = 0
        self.last_area = None
        self.last_hud_tick = -1
        self.notice_timer = None
        self.loot_timer = None
        self.sound = False
        self.audio = None
        root = document.documentElement.style
        root.setProperty("--item-art", f"url('assets/{IMAGES['icons']}')")
        root.setProperty("--frame-art", f"url('assets/{IMAGES['frame']}')")
        root.setProperty("--hero-art", f"url('assets/{IMAGES['hero']}')")
        self.renderer = Renderer(document["game-canvas"])
        window.bind("resize", self.renderer.resize)
        self.bind()
        self.hud()
        self.toast("방향키 이동 · Z 공격 · X 스킬 · ↑ 대화·출구")
        window.requestAnimationFrame(self.frame)

    def save(self):
        try:
            window.localStorage.setItem(SAVE_KEY, json.dumps(self.game.p, ensure_ascii=False))
            return True
        except Exception:
            return False

    def clear_input(self, _=None):
        self.keys.clear()
        self.pointers.clear()

    def bind(self):
        for id in MENUS:
            document[id].bind("click", lambda event, id=id: self.show_panel(id))
        document["minimap-button"].bind("click", lambda _: self.show_panel("map"))
        document["quest-button"].bind("click", lambda _: self.show_panel("journal"))
        document["pause"].bind("click", lambda _: self.toggle_pause())
        for i in range(4):
            document[f"slot-{i}"].bind("click", lambda event, i=i: self.run_slot(i))
        for node in document.select("[data-key]"):
            code = node.attrs["data-key"]
            node.bind("pointerdown", lambda event, node=node, code=code: self.pointer_down(event, node, code))
            for name in ("pointerup", "pointercancel", "lostpointercapture"):
                node.bind(name, self.pointer_up)
            node.bind("click", lambda event, code=code: self.action(code) if not event.detail else None)
        window.bind("keydown", self.key_down)
        window.bind("keyup", lambda event: self.keys.discard(event.code))
        window.bind("blur", self.clear_input)
        window.bind("pagehide", lambda _: self.save())
        document.bind("visibilitychange", self.visibility_changed)
        self.modal.bind("focusin", self.clear_input)
        self.modal.bind("cancel", self.cancel_dialog)
        self.modal.bind("click", lambda event: self.close_panel() if event.target == self.modal else None)

    def visibility_changed(self, _):
        if document.hidden:
            self.clear_input()
            self.save()
        self.previous = None

    def pointer_down(self, event, node, code):
        if number(event.button) > 0 or self.paused:
            return
        event.preventDefault()
        self.pointers[int(number(event.pointerId))] = code
        node.setPointerCapture(event.pointerId)
        self.action(code)

    def pointer_up(self, event):
        self.pointers.pop(int(number(event.pointerId)), None)

    def key_down(self, event):
        if event.metaKey or event.ctrlKey or event.altKey:
            return
        target = event.target
        if getattr(target, "tagName", "") in ("INPUT", "SELECT", "TEXTAREA"):
            return
        code = event.code
        if code == "Escape" and self.panel:
            event.preventDefault()
            self.close_panel()
            return
        if code not in ACTION_KEYS:
            return
        if code == "Space" and self.panel and getattr(target, "tagName", "") == "BUTTON":
            return
        event.preventDefault()
        self.keys.add(code)
        if not event.repeat:
            self.action(code)

    def action(self, code):
        if code in SHORTCUTS:
            self.show_panel(SHORTCUTS[code])
            return
        if self.paused or not self.renderer.ready:
            return
        game = self.game
        if code.startswith("Digit"):
            self.run_slot(int(code[-1]) - 1)
        elif code == "Space":
            game.jump("ArrowDown" in self.keys or "ArrowDown" in self.pointers.values())
        elif code == "KeyZ":
            game.start_attack()
        elif code == "KeyX":
            game.start_attack(True)
        elif code == "KeyV":
            game.support()
        elif code == "ArrowUp":
            kind, target = game.nearby()
            if kind == "portal":
                game.travel(target[1])
                self.clear_input()
                self.toast(AREAS[target[2]]["name"])
                self.save()
            elif kind == "npc":
                self.show_panel(target["kind"], target)
        elif code == "KeyR":
            self.home()
        elif code == "KeyK":
            self.toast("모험을 저장했어요." if self.save() else "저장 공간을 사용할 수 없어요.")

    def home(self):
        self.game.travel(START_X)
        self.game.notice = "솔방울 마을로 돌아왔어요."
        self.save()

    def run_slot(self, i):
        if self.paused or not self.renderer.ready:
            return
        action = self.game.p["hotbar"][i]
        if action in ("hp", "mp"):
            if self.game.heal(action == "mp"):
                self.save()
        elif action == "skill":
            self.game.start_attack(True)
        elif action == "support":
            self.game.support()
        elif action == "home":
            self.home()

    def toggle_pause(self):
        self.clear_input()
        self.paused = not self.paused
        set_text("pause", "계속하기" if self.paused else "일시정지")

    def cancel_dialog(self, event):
        event.preventDefault()
        self.close_panel()

    def close_panel(self):
        if not self.panel:
            return
        self.panel = None
        self.clear_input()
        self.modal.close()
        if self.focus_before is not None:
            self.focus_before.focus()
        self.focus_before = None
        self.previous = None

    def show_panel(self, id, npc=None, toggle=True):
        if toggle and self.panel and self.panel == (id, npc):
            self.close_panel()
            return
        opening = not self.panel
        if opening:
            self.focus_before = document.activeElement
        self.clear_input()
        self.panel = (id, npc)
        if id == "shop":
            self.category["shop"] = "buy"
        self.render_panel()
        if opening:
            self.modal.show()
            self.pane.select_one(".close-panel").focus()

    def set_tab(self, group, value):
        self.category[group] = value
        self.render_panel()

    def tabs(self, group, labels, active):
        row = html.NAV(Class="panel-tabs")
        for id, label in labels:
            row <= button(label, lambda id=id: self.set_tab(group, id), pressed=id == active)
        self.pane <= row

    def row(self, title, detail="", action=None, callback=None, disabled=False, item=None):
        row = html.DIV(Class="panel-row")
        if item:
            row <= icon(item_icon(item), "row-icon")
        label = html.DIV(Class="row-label")
        name = html.B(title)
        if item and ITEMS[item].get("rarity"):
            name.attrs["data-rarity"] = ITEMS[item]["rarity"]
        label <= name
        if detail:
            label <= html.SMALL(detail)
        row <= label
        if action:
            row <= button(action, callback, disabled)
        self.pane <= row

    def execute(self, operation, close=False):
        if operation():
            self.save()
            self.hud()
            if close:
                self.close_panel()
            elif self.panel:
                self.render_panel()
        self.messages()

    def render_panel(self):
        id, npc = self.panel
        previous = self.pane.scrollTop
        old_buttons = list(self.pane.select("button"))
        active = document.activeElement
        focused = next((i for i, node in enumerate(old_buttons) if node == active), None)
        self.pane.clear()
        title = f"{npc['name']} · {npc['role']}" if npc else MENUS[id]
        head = html.HEADER(Class="panel-heading")
        head <= html.H2(title, id="panel-title")
        close = button("닫기", self.close_panel)
        close.className = "close-panel"
        head <= close
        self.pane <= head
        if id in MENUS:
            links = html.NAV(Class="panel-tabs")
            for target, label in MENUS.items():
                links <= button(label, lambda target=target: self.show_panel(target, toggle=False), pressed=id == target)
            self.pane <= links
        if id == "character":
            self.character()
        elif id == "skills":
            self.skills()
        elif id == "inventory":
            self.bag()
        elif id == "journal":
            self.journal()
        elif id == "map":
            self.map_panel()
        elif id == "bestiary":
            self.bestiary()
        elif id == "account":
            self.account()
        elif id == "hotkeys":
            self.settings()
        elif id == "shop":
            self.shop(npc)
        elif id == "trainer":
            self.trainer()
        elif id in ("quest", "harbor"):
            self.quest_panel(npc.get("quest", 1 if id == "harbor" else 0))
        elif id == "forge":
            self.forge()
        else:
            self.pane <= html.P("출구에서 ↑를 누르면 다음 지역으로 이동해요. 적의 공격 표시를 보고 뒤로 물러나거나 점프하세요.")
        self.pane.scrollTop = previous
        if focused is not None:
            new_buttons = self.pane.select("button")
            if focused < len(new_buttons) and not new_buttons[focused].disabled:
                new_buttons[focused].focus()
            else:
                close.focus()

    def character(self):
        game = self.game
        stats = game.stats()
        p = game.p
        sheet = html.DIV(Class="stat-sheet")
        for id, label, value in (
            ("level", "레벨", p["level"]), ("job", "직업", CLASSES[p["job"]]["name"]),
            ("attack", "공격력", stats["attack"]), ("defense", "방어력", stats["defense"]),
            ("hp", "체력", f"{p['hp']} / {stats['hp']}"), ("mp", "마력", f"{p['mp']} / {stats['mp']}"),
            ("speed", "이동 속도", f"{stats['speed']:.2f}"), ("kills", "처치 수", p["kills"])
        ):
            sheet <= html.DIV(html.B(label) + html.SPAN(str(value), id="detail-" + id), Class="stat-field")
        self.pane <= sheet
        points = html.DIV(html.B("능력치 포인트") + html.SPAN(str(game.ap())), Class="points-summary")
        self.pane <= points
        for id, attr in ATTRIBUTES.items():
            self.row(f"{attr['name']} · {game.p['attributes'][id]}", attr["detail"], "+1",
                     lambda id=id: self.execute(lambda: game.add_attribute(id)), not game.ap())

    def skills(self):
        game, p = self.game, self.game.p
        self.pane <= html.P(f"남은 SP {game.sp()} · 레벨업마다 1점")
        job = CLASSES[p["job"]]
        rank = p["skillRanks"]["primary"]
        self.row(f"{job['skill']} · 랭크 {rank}/5", f"X · MP {job['cost']} · 피해 {round(100 * (job['power'] + .25 * (rank - 1)))}%",
                 "강화", lambda: self.execute(lambda: game.raise_skill("primary")),
                 rank == 5 or p["level"] < game.rank_level("primary", rank + 1) or not game.sp(), p["equipment"]["weapon"])
        if p["job"] in SUPPORTS:
            support = SUPPORTS[p["job"]]
            rank = p["skillRanks"]["support"]
            self.row(f"{support['name']} · 랭크 {rank}/3", f"V · MP {support['cost']} · {support['summary']}",
                     "강화" if rank else "배우기", lambda: self.execute(lambda: game.raise_skill("support")),
                     rank == 3 or p["level"] < game.rank_level("support", rank + 1) or not game.sp())
        else:
            self.pane <= html.P("전직 후 Lv. 7부터 보조 스킬을 배울 수 있어요.")

    def bag(self):
        game, p = self.game, self.game.p
        active = self.category.get("bag", "gear")
        self.tabs("bag", (("gear", "장비"), ("supply", "물약"), ("loot", "전리품")), active)
        if active == "gear":
            grid = html.DIV(Class="paper-doll")
            portrait = html.DIV(Class="equipment-portrait")
            avatar = html.SPAN(Class="portrait-sprite")
            avatar.attrs["aria-hidden"] = "true"
            portrait <= avatar
            portrait <= html.B(f"Lv. {p['level']} · {CLASSES[p['job']]['name']}")
            for slot, label in SLOTS.items():
                id = p["equipment"][slot]
                card = html.DIV(Class=f"doll-slot doll-{slot}")
                card <= html.SMALL(label)
                card <= icon(item_icon(id), "equip-icon" if id else "equip-icon empty-icon")
                card <= html.B(ITEMS[id]["name"] if id else "비어 있음")
                grid <= card
            grid <= portrait
            self.pane <= grid
        if active == "supply":
            for id, count, detail in (("potion", p["pots"], "HP 55 회복"), ("tonic", p["tonics"], "MP 35 회복")):
                self.row(f"{ITEMS[id]['name']} ×{count}", detail, "사용",
                         lambda id=id: self.execute(lambda: game.heal(id == "tonic")), not count, id)
            return
        shown = 0
        for id, count in p["bag"].items():
            item = ITEMS[id]
            slot = item.get("slot")
            if bool(slot) != (active == "gear"):
                continue
            shown += 1
            details = item_details(id) if slot else f"판매 {item['price']//2} 메소"
            action = "해제" if id == p["equipment"].get(slot) else "장착"
            self.row(f"{item['name']} ×{count}", details, action if slot else None,
                     lambda id=id: self.execute(lambda: game.toggle_equipment(id)), not game.can_equip(id), id)
        if not shown:
            self.pane <= html.P("이 가방 칸에 아이템이 없어요.")

    def journal(self):
        game, p = self.game, self.game.p
        active = self.category.get("quest", "active")
        self.tabs("quest", (("active", "진행 중"), ("available", "받을 수 있음"), ("done", "완료")), active)
        status = {"active": 1, "available": 0, "done": 2}[active]
        count = 0
        for i, (quest, entry) in enumerate(zip(QUESTS, p["quests"])):
            if entry["state"] != status:
                continue
            count += 1
            detail = f"{AREAS[quest['area']]['name']} · {quest['who']} · {entry['count']}/{quest['target']}"
            tracked = i == game.tracked_quest()
            self.row(quest["name"], detail, ("추적 중" if tracked else "추적") if status == 1 else None,
                     lambda i=i: self.track(i), tracked, quest["item"])
        if not count:
            self.pane <= html.P("표시할 퀘스트가 없어요.")

    def track(self, index):
        self.game.p["trackedQuest"] = index
        self.save()
        self.hud()
        self.render_panel()

    def map_panel(self):
        current = area_at(self.game.p["x"])
        for i, area in enumerate(AREAS):
            self.row(area["name"], "현재 위치" if i == current else "출구에서 ↑로 이동")

    def bestiary(self):
        discovered = self.game.p["bestiary"]
        self.pane <= html.P(f"기록 {len(discovered)}/{len(SPECIES)} · 첫 처치 후 드롭을 확인할 수 있어요.")
        for i, species in enumerate(SPECIES):
            count = discovered.get(str(i), 0)
            detail = f"처치 {count} · {ITEMS[species['loot']]['name']} · {ITEMS[species['rare']]['name']}" if count else ""
            self.row(f"Lv. {species['level']} · " + (species["name"] if count else "미발견"), detail,
                     item=species["loot"] if count else None)

    def _toggle_sound(self):
        self.sound = not self.sound
        if self.sound:
            self.beep(630)
        self.render_panel()

    def settings(self):
        p = self.game.p
        for i, action in enumerate(p["hotbar"]):
            row = html.LABEL(Class="panel-row")
            row <= html.B(f"{i+1}번 슬롯")
            select = html.SELECT()
            select.attrs["aria-label"] = f"{i+1}번 슬롯"
            select <= html.OPTION("비우기", value="")
            for id, info in HOTBAR_ACTIONS.items():
                select <= html.OPTION(info["name"], value=id)
            select.value = action or ""
            select.bind("change", lambda event, i=i: self.assign(i, event.target.value))
            row <= select
            self.pane <= row
        self.row("효과음", "켜짐" if self.sound else "꺼짐", "끄기" if self.sound else "켜기", self._toggle_sound)

    def assign(self, i, action):
        self.game.p["hotbar"][i] = action if action in HOTBAR_ACTIONS else None
        self.save()
        self.hud()

    def account(self):
        hosted = window.location.origin == SITE
        self.pane <= html.P("웹 버전은 ChatGPT 계정으로 인증합니다. 캐릭터 진행은 이 브라우저에 저장됩니다.")
        entry = html.A("ChatGPT 로그아웃" if hosted else "웹에서 ChatGPT 로그인",
                       href="/signout-with-chatgpt" if hosted else SITE, target="_top", Class="account-link")
        entry.bind("click", lambda _: self.save())
        self.pane <= entry
        self.row("진행 기록", f"Lv. {self.game.p['level']} · {AREAS[area_at(self.game.p['x'])]['name']}", "저장",
                 lambda: self.toast("모험을 저장했어요." if self.save() else "저장 공간을 사용할 수 없어요."))

    def shop(self, npc):
        game, p = self.game, self.game.p
        active = self.category.get("shop", "buy")
        self.tabs("shop", (("buy", "구매"), ("sell", "판매")), active)
        self.pane <= html.P(f"보유 메소 {p['gold']:,}")
        supply = npc["stock"] if active == "buy" else list(p["bag"])
        if not supply:
            self.pane <= html.P("판매할 아이템이 없어요.")
        for id in supply:
            item = ITEMS[id]
            if active == "buy":
                self.row(item["name"], item_details(id), f"{item['price']} 메소",
                         lambda id=id: self.execute(lambda: game.buy(id, npc["stock"])), p["gold"] < item["price"], id)
            else:
                self.row(f"{item['name']} ×{p['bag'][id]}", item_details(id), f"판매 {item['price']//2}",
                         lambda id=id: self.execute(lambda: game.sell(id)), not game.sellable(id), id)

    def trainer(self):
        game, p = self.game, self.game.p
        if p["job"] != "beginner":
            self.pane <= html.P(f"현재 직업은 {CLASSES[p['job']]['name']}입니다.")
            return
        self.pane <= html.P("Lv. 5부터 전직할 수 있어요. 전직하면 전용 무기를 받아요.")
        for id, support in SUPPORTS.items():
            self.row(CLASSES[id]["name"], f"X {CLASSES[id]['skill']} · V {support['name']}", "전직",
                     lambda id=id: self.execute(lambda: game.change_job(id)), p["level"] < 5)

    def quest_panel(self, index):
        game = self.game
        quest, progress = QUESTS[index], game.p["quests"][index]
        self.pane <= html.P(quest["detail"])
        detail = f"{progress['count']}/{quest['target']} · {quest['xp']} EXP · {quest['gold']} 메소"
        if progress["state"] == 0:
            self.row(quest["name"], detail, "의뢰 받기", lambda: self.execute(lambda: game.accept_quest(index), True), item=quest["item"])
        elif progress["state"] == 1:
            self.row(quest["name"], detail, "보상 받기", lambda: self.execute(lambda: game.claim_quest(index)),
                     progress["count"] < quest["target"], quest["item"])
        else:
            self.pane <= html.P("의뢰를 완료했어요.")

    def forge(self):
        game = self.game
        for recipe in RECIPES:
            id = recipe["item"]
            ingredients = ", ".join(f"{ITEMS[key]['name']} {game.p['bag'].get(key, 0)}/{value}" for key, value in recipe["ingredients"].items())
            self.row(ITEMS[id]["name"], f"{ingredients} · {recipe['gold']} 메소", "제작",
                     lambda id=id: self.execute(lambda: game.craft(id)), not game.can_craft(recipe), id)

    def minimap(self):
        game = self.game
        index = area_at(game.p["x"])
        area = AREAS[index]
        start, end = area["start"], area["end"]
        def scale(x):
            return 6 + (x - start) * 188 / (end - start)
        if self.last_area != index:
            self.last_area = index
            set_text("region", area["name"])
            ctx = document["minimap"].getContext("2d")
            ctx.clearRect(0, 0, 200, 46)
            ctx.strokeStyle = "#91c5a9"
            ctx.fillStyle = "#294e52"
            ctx.beginPath()
            ctx.moveTo(6, 41)
            ctx.lineTo(6, ground_at(start)/20 + 12)
            for x, y in GROUND:
                if start < x < end:
                    ctx.lineTo(scale(x), y/20 + 12)
            ctx.lineTo(194, ground_at(end)/20 + 12)
            ctx.lineTo(194, 41)
            ctx.closePath()
            ctx.fill()
            ctx.stroke()
            ctx.fillStyle = "#96b5a6"
            for ledge in LEDGES:
                if start <= ledge["x"] < end:
                    ctx.fillRect(scale(ledge["x"]), ledge["y"]/20 + 10, max(3, ledge["w"] * 188 / (end-start)), 1)
            ctx.fillStyle = "#9feafa"
            for x, _, _ in PORTALS:
                if start <= x < end:
                    ctx.fillRect(scale(x)-2, ground_at(x)/20 + 6, 4, 7)
            ctx.fillStyle = "#f2bb78"
            for npc in NPCS:
                if start <= npc["x"] < end:
                    ctx.fillRect(scale(npc["x"])-1, ground_at(npc["x"])/20 + 8, 3, 3)
        player = document["minimap-player"]
        player.style.left = f"{scale(game.p['x']) / 2}%"
        player.style.top = f"{(game.p['y']/20 + 10) * 100 / 46}%"

    def hud(self):
        game, p = self.game, self.game.p
        stats = game.stats()
        set_text("lv", f"Lv. {p['level']}")
        set_text("job", CLASSES[p["job"]]["name"])
        set_text("gold", f"{p['gold']:,} 메소")
        for key in ("hp", "mp", "xp"):
            maximum = game.xp_needed() if key == "xp" else stats[key]
            percentage = min(100, 100 * p[key] / maximum)
            set_text(key, f"{p[key]} / {maximum}")
            document[key + "bar"].style.width = f"{percentage:.1f}%"
            if key == "xp":
                set_text("xp-percent", f"{percentage:.0f}%")
        if self.panel and self.panel[0] == "character":
            set_text("detail-hp", f"{p['hp']} / {stats['hp']}")
            set_text("detail-mp", f"{p['mp']} / {stats['mp']}")
            set_text("detail-level", p["level"])
            set_text("detail-kills", p["kills"])
            set_text("detail-attack", stats["attack"])
            set_text("detail-defense", stats["defense"])
        set_text("point-badge", game.ap() or "")
        set_text("skill-point-badge", game.sp() or "")
        set_text("quest", game.quest_caption())
        if game.tick < game.support_until:
            set_text("buff-status", f"{SUPPORTS[p['job']]['name']} · {(game.support_until-game.tick+59)//60}초")
        else:
            set_text("buff-status", "")
        for i, id in enumerate(p["hotbar"]):
            node = document[f"slot-{i}"]
            symbol = document[f"slot-symbol-{i}"]
            if id:
                target = p["equipment"]["weapon"] if id == "skill" else {"hp": "potion", "mp": "tonic"}.get(id)
                art(symbol, item_icon(target) if target else 13 if id == "support" else 6)
                symbol.text = ""
            else:
                symbol.classList.remove("pixel-icon")
                symbol.text = "–"
            label = HOTBAR_ACTIONS.get(id, {}).get("name", "빈 슬롯")
            node.attrs["aria-label"] = f"{i+1}번 · {label}"
            node.attrs["title"] = label
            node.attrs["data-color"] = HOTBAR_ACTIONS.get(id, {}).get("color", "empty")
            badge = ""
            if id in ("hp", "mp"):
                badge = p["pots" if id == "hp" else "tonics"]
            elif id == "skill" and game.skill_cd:
                badge = f"{(game.skill_cd+59)//60}초"
            elif id == "support":
                badge = "잠김" if not p["skillRanks"]["support"] else f"{(game.support_cd+59)//60}초" if game.support_cd else ""
            node.attrs["data-unavailable"] = str(id is None or badge == 0 or badge == "잠김" or isinstance(badge, str) and badge.endswith("초")).lower()
            set_text(f"slot-count-{i}", badge)
        self.minimap()
        game.dirty = False

    def toast(self, text):
        set_text("toast", text)
        document["toast"].style.opacity = "1"
        if self.notice_timer is not None:
            timer.clear_timeout(self.notice_timer)
        self.notice_timer = timer.set_timeout(lambda: document["toast"].style.setProperty("opacity", "0"), 3600)

    def beep(self, hz):
        if not self.sound:
            return
        try:
            if self.audio is None:
                self.audio = window.AudioContext.new()
            oscillator = self.audio.createOscillator()
            gain = self.audio.createGain()
            begin = self.audio.currentTime
            oscillator.type = "triangle"
            oscillator.frequency.value = hz
            gain.gain.setValueAtTime(.035, begin)
            gain.gain.exponentialRampToValueAtTime(.001, begin + .14)
            oscillator.connect(gain)
            gain.connect(self.audio.destination)
            oscillator.start()
            oscillator.stop(begin + .15)
        except Exception:
            pass

    def messages(self):
        game = self.game
        if game.notice:
            self.toast(game.notice)
            game.notice = ""
        if game.sound:
            self.beep(game.sound)
            game.sound = None
        if game.loot:
            gold, items = game.loot
            game.loot = None
            feed = document["loot-feed"]
            feed.clear()
            line = html.DIV(Class="loot-line")
            if gold:
                line <= icon(7)
                line <= html.B(f"+{gold} 메소")
            for id in items:
                line <= icon(item_icon(id))
                label = html.SPAN(ITEMS[id]["name"])
                label.attrs["data-rarity"] = ITEMS[id].get("rarity", "")
                line <= label
            feed <= line
            feed.hidden = False
            if self.loot_timer is not None:
                timer.clear_timeout(self.loot_timer)
            self.loot_timer = timer.set_timeout(lambda: setattr(feed, "hidden", True), 3900)

    def frame(self, now):
        now = number(now)
        if self.previous is not None:
            self.accumulator += min(68, now - self.previous)
        self.previous = now
        game = self.game
        while self.accumulator >= STEP:
            if self.renderer.ready and not self.paused:
                game.step(self.keys | set(self.pointers.values()))
                if game.tick % 600 == 0:
                    self.save()
            self.accumulator -= STEP
        if game.dirty or game.tick % 6 == 0 and self.last_hud_tick != game.tick:
            self.hud()
            self.last_hud_tick = game.tick
        self.messages()
        self.renderer.draw(game, self.paused)
        window.requestAnimationFrame(self.frame)
