"""Python browser UI, input lifecycle and save persistence."""
import json
from browser import document, window
from .content import AREAS, CLASSES, HOTBAR_ACTIONS, ITEMS, QUESTS, RECIPES, SLOTS, SPECIES, SUPPORTS
from .engine import START_X, STEP, Game, area_at
from .hunting import HUNT_ZONES
from .lobby import Lobby
from .content import STARTER_WEAPONS
from .render import Renderer, number
from .windows import GameInterface

MENUS = {"character": "능력치", "skills": "스킬", "inventory": "장비·가방", "journal": "퀘스트",
         "map": "지도", "bestiary": "도감", "account": "계정", "hotkeys": "설정"}
SHORTCUTS = dict(zip(("KeyC", "KeyS", "KeyI", "KeyQ", "KeyM", "KeyB"), tuple(MENUS)[:6]))
RARITIES = {"uncommon": "고급", "rare": "희귀", "epic": "영웅"}
ACTION_KEYS = {"Space", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "KeyZ", "KeyX", "KeyV",
               "KeyC", "KeyS", "KeyI", "KeyQ", "KeyM", "KeyB", "KeyR", "KeyK", "Digit1", "Digit2", "Digit3", "Digit4"}


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


class App:
    def __init__(self):
        self.game = Game()
        self.profile = None
        self.active = False
        self.portal_until = 0
        self.panel = None
        self.category = {}
        self.rows = []
        self.keys = set()
        self.pointers = {}
        self.paused = False
        self.previous = None
        self.accumulator = 0
        self.sound = False
        self.audio = None
        self.notice_text = ""
        self.notice_end = 0
        self.loot_text = ""
        self.loot_end = 0
        self.renderer = Renderer(document["game-canvas"])
        self.screen = GameInterface(self, document["interface"], MENUS)
        window.bind("resize", self.resize)
        self.bind()
        self.lobby = Lobby(self)
        window.requestAnimationFrame(self.frame)

    def start_character(self, profile, progress):
        self.game = Game(progress)
        self.profile = profile
        if progress is None:
            job = profile["job"]
            weapon = STARTER_WEAPONS[job]
            self.game.p["job"] = job
            self.game.p["bag"] = {weapon:1}
            self.game.p["equipment"]["weapon"] = weapon
            self.game.changed()
            stats = self.game.stats()
            self.game.p.update(hp=stats["hp"],mp=stats["mp"])
        self.active = True
        self.clear_input()
        self.close_panel()
        self.paused = False
        self.previous = None
        self.accumulator = 0
        self.screen.canvas.focus()
        self.toast("방향키 이동 · Space 점프 · Z 공격 · ↑ 포털·대화")
        self.save()

    def leave_character(self):
        self.active = False
        self.profile = None
        self.close_panel()
        self.clear_input()

    def save(self, keepalive=False):
        return self.active and self.lobby.save_progress(self.game.p,keepalive)

    def clear_input(self, _=None):
        self.keys.clear()
        self.pointers.clear()
        if self.game.swing:
            self.game.swing["queued"] = False

    def bind(self):
        window.bind("keydown", self.key_down)
        window.bind("keyup", lambda event: self.keys.discard(event.code))
        window.bind("blur", self.clear_input)
        window.bind("pagehide", lambda _: self.save(True))
        document.bind("visibilitychange", self.visibility_changed)

    def resize(self, _=None):
        self.renderer.resize()
        self.screen.resize()

    def visibility_changed(self, _):
        if document.hidden:
            self.clear_input()
            self.save(True)
        self.previous = None

    def key_down(self, event):
        if not self.active or event.metaKey or event.ctrlKey or event.altKey:
            return
        target = event.target
        if getattr(target, "tagName", "") in ("INPUT", "SELECT", "TEXTAREA"):
            return
        code = event.code
        if code in ("Tab", "Enter") and self.screen.navigate(code, event.shiftKey):
            event.preventDefault()
            return
        if code == "Escape" and self.panel:
            event.preventDefault()
            self.close_panel()
            return
        if code not in ACTION_KEYS:
            return
        event.preventDefault()
        self.keys.add(code)
        if not event.repeat:
            self.action(code)

    def action(self, code):
        if not self.active:
            return
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
            game.press_attack()
        elif code == "KeyX":
            game.start_attack(True)
        elif code == "KeyV":
            game.support()
        elif code == "ArrowUp":
            kind, target = game.nearby()
            if kind == "portal":
                game.travel(target[1])
                self.clear_input()
                area, hunt = AREAS[target[2]], HUNT_ZONES[target[2]]
                self.portal_until = number(window.performance.now())+320
                low, high = hunt["levels"]
                self.toast(f"{area['name']} · {hunt['label']} · Lv. {low}–{high}")
                self.save()
            elif kind == "npc":
                self.show_panel(target["kind"], target)
        elif code == "KeyR":
            self.home()
        elif code == "KeyK":
            self.manual_save()

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
        self.screen.refresh()

    def close_panel(self):
        self.panel = None
        self.screen.change_page()

    def show_panel(self, id, npc=None, toggle=True):
        if toggle and self.panel == (id, npc):
            self.close_panel()
            return
        self.panel = (id, npc)
        if id == "shop":
            self.category["shop"] = "buy"
        self.screen.change_page()
        self.render_panel()

    def set_tab(self, group, value):
        self.category[group] = value
        self.screen.change_page()
        self.render_panel()

    def tabs(self, group, labels, active):
        self.rows.append(("tabs", group, labels, active))

    def note(self, value):
        self.rows.append(("note", value))

    def row(self, title, detail="", action=None, callback=None, disabled=False, item=None):
        self.rows.append(("row", title, detail, action, callback, disabled, item))

    def execute(self, operation, close=False):
        if operation():
            self.save()
            if close:
                self.close_panel()
            elif self.panel:
                self.render_panel()
        self.messages()

    def render_panel(self):
        id, npc = self.panel
        self.rows = []
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
            self.note("출구에서 ↑를 누르면 다음 지역으로 이동해요. 적의 공격 표시를 보고 뒤로 물러나거나 점프하세요.")
        self.screen.refresh()

    def character(self):
        self.rows.append(("stats",))

    def skills(self):
        game, p = self.game, self.game.p
        self.note(f"남은 SP {game.sp()} · 레벨업마다 1점")
        job = CLASSES[p["job"]]
        details = {
            "stab": "앞의 적 하나를 두 번 찔러요.", "kick": "회전하며 주변 적을 최대 여섯 마리 타격해요.",
            "heal": "HP를 회복하고 주변 언데드를 공격해요.", "arc": "앞쪽 적을 넓게 베어요.",
            "arrow": "첫 대상에 맞으면 주변에 폭발해요.", "stars": "주변에 별벼락을 내려요.",
        }
        if job["shape"] in details:
            self.note(details[job["shape"]])
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
            self.note("전직 후 Lv. 7부터 보조 스킬을 배울 수 있어요.")

    def bag(self):
        game, p = self.game, self.game.p
        active = self.category.get("bag", "gear")
        self.tabs("bag", (("gear", "장비"), ("supply", "물약"), ("loot", "전리품")), active)
        if active == "gear":
            self.rows.append(("doll",))
        if active == "supply":
            for id, count, detail in (("potion", p["pots"], "HP 55 회복"), ("tonic", p["tonics"], "MP 35 회복")):
                self.row(f"{ITEMS[id]['name']} ×{count}", detail, "사용",
                         lambda id=id: self.execute(lambda: game.heal(id == "tonic")), not count, id)
            return
        bag = [id for id in p["bag"] if bool(ITEMS[id].get("slot")) == (active == "gear")]
        chosen = self.category.get("selected-item")
        selected = chosen if chosen in bag else next(iter(bag), None)
        self.rows.append(("items", bag, selected))
        if not selected:
            self.note("이 가방 칸에 아이템이 없어요.")
            return
        item = ITEMS[selected]
        if active == "gear":
            equipped = p["equipment"].get(item["slot"]) == selected
            self.row(item["name"], item_details(selected), "해제" if equipped else "장착",
                     lambda: self.execute(lambda: game.toggle_equipment(selected)), not game.can_equip(selected), selected)
        else:
            self.row(item["name"], f"보유 {p['bag'][selected]}개 · 판매 {item['price']//2} 메소", item=selected)

    def select_item(self, item):
        self.category["selected-item"] = item
        self.render_panel()

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
            self.note("표시할 퀘스트가 없어요.")

    def track(self, index):
        self.game.p["trackedQuest"] = index
        self.save()
        self.render_panel()

    def map_panel(self):
        self.note("지역 끝 포털에서 ↑로 다음 지역에 이동해요.")
        self.rows.append(("route",))

    def bestiary(self):
        discovered = self.game.p["bestiary"]
        self.note(f"기록 {len(discovered)}/{len(SPECIES)} · 첫 처치 후 드롭을 확인할 수 있어요.")
        for i, species in enumerate(SPECIES):
            count = discovered.get(str(i), 0)
            detail = f"처치 {count} · {ITEMS[species['loot']]['name']} · {ITEMS[species['rare']]['name']}" if count else ""
            self.rows.append(("monster", i, count, detail))

    def _toggle_sound(self):
        self.sound = not self.sound
        if self.sound:
            self.beep(630)
        self.render_panel()

    def settings(self):
        p = self.game.p
        for i, action in enumerate(p["hotbar"]):
            options = [None] + list(HOTBAR_ACTIONS)
            next_action = options[(options.index(action) + 1) % len(options)]
            self.row(f"{i+1}번 슬롯", HOTBAR_ACTIONS.get(action, {}).get("name", "비우기"),
                     "변경", lambda i=i, value=next_action: self.assign(i, value))
        self.row("효과음", "켜짐" if self.sound else "꺼짐", "끄기" if self.sound else "켜기", self._toggle_sound)

    def assign(self, i, action):
        self.game.p["hotbar"][i] = action if action in HOTBAR_ACTIONS else None
        self.save()
        self.render_panel()

    def account(self):
        self.note(f"{self.lobby.account} · {self.profile['name']} · 슬롯 {self.lobby.slot+1}/4")
        self.row("진행 기록", self.lobby.message, "지금 저장", self.manual_save)
        self.row("캐릭터 선택", "서버에 저장하고 다른 캐릭터로 이동해요.", "목록으로", self.lobby.leave)

    def manual_save(self):
        if self.save():
            self.toast(self.lobby.message)

    def shop(self, npc):
        game, p = self.game, self.game.p
        active = self.category.get("shop", "buy")
        self.tabs("shop", (("buy", "구매"), ("sell", "판매")), active)
        self.note(f"보유 메소 {p['gold']:,}")
        supply = npc["stock"] if active == "buy" else list(p["bag"])
        if not supply:
            self.note("판매할 아이템이 없어요.")
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
        self.note(f"현재 직업 · {CLASSES[p['job']]['name']}")
        self.note("Lv. 5부터 직업을 바꿀 수 있어요. 전용 무기를 받고 기존 장비는 가방에 남아요.")
        for job, support in SUPPORTS.items():
            primary = CLASSES[job]
            self.row(primary["name"], f"X {primary['skill']} · V {support['name']}", "전직",
                     lambda job=job: self.execute(lambda: game.change_job(job)), p["level"] < 5 or p["job"] == job)

    def quest_panel(self, index):
        game = self.game
        quest, progress = QUESTS[index], game.p["quests"][index]
        self.note(quest["detail"])
        detail = f"{progress['count']}/{quest['target']} · {quest['xp']} EXP · {quest['gold']} 메소"
        if progress["state"] == 0:
            self.row(quest["name"], detail, "의뢰 받기", lambda: self.execute(lambda: game.accept_quest(index), True), item=quest["item"])
        elif progress["state"] == 1:
            self.row(quest["name"], detail, "보상 받기", lambda: self.execute(lambda: game.claim_quest(index)),
                     progress["count"] < quest["target"], quest["item"])
        else:
            self.note("의뢰를 완료했어요.")

    def forge(self):
        game = self.game
        for recipe in RECIPES:
            id = recipe["item"]
            ingredients = ", ".join(f"{ITEMS[key]['name']} {game.p['bag'].get(key, 0)}/{value}" for key, value in recipe["ingredients"].items())
            self.row(ITEMS[id]["name"], f"{ingredients} · {recipe['gold']} 메소", "제작",
                     lambda id=id: self.execute(lambda: game.craft(id)), not game.can_craft(recipe), id)

    def hud(self):
        if self.panel:
            self.render_panel()
        self.game.dirty = False
        self.screen.refresh()

    def toast(self, text):
        self.notice_text = text
        self.notice_end = number(window.performance.now()) + 3200
        document["toast"].text = text
        self.screen.refresh()

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
            parts = ([f"+{gold} 메소"] if gold else []) + [ITEMS[id]["name"] for id in items]
            self.loot_text = " · ".join(parts)
            self.loot_end = number(window.performance.now()) + 3600
            self.screen.refresh()

    def frame(self, now):
        now = number(now)
        if self.previous is not None:
            self.accumulator += min(68, now - self.previous)
        self.previous = now
        self.lobby.flush_preview()
        if not self.active:
            self.accumulator = 0
            window.requestAnimationFrame(self.frame)
            return
        game = self.game
        while self.accumulator >= STEP:
            if self.renderer.ready and not self.paused:
                game.step(self.keys | set(self.pointers.values()))
                if game.tick % 300 == 0:
                    self.save()
            self.accumulator -= STEP
        if game.dirty:
            self.hud()
        self.messages()
        self.renderer.draw(game,self.paused,self.profile,max(0,(self.portal_until-now)/320))
        self.screen.draw(now)
        window.requestAnimationFrame(self.frame)
