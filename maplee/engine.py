"""Maplee's fixed-step simulation. This module also runs in regular Python."""
from bisect import bisect_right
from math import ceil
from random import random
from .content import (
    AREAS, ATTRIBUTES, CLASSES, DEFAULT_HOTBAR, GROUND, HOTBAR_ACTIONS,
    ITEMS, LEDGES, NPCS, QUESTS, RECIPES, SLOTS, SPECIES, SUPPORTS, WORLD_WIDTH,
)

WIDTH, HEIGHT, STEP = 960, 468, 1000 / 60
SAVE_KEY = "maple-local-world-v1"
START_X = 310
SWING_WINDUP, SWING_END = 5, 22
GROUND_XS = [x for x, _ in GROUND]
AREA_ENDS = [area["end"] for area in AREAS]


def limit(value, low, high):
    return max(low, min(high, value))


def direction(value, fallback=1):
    return 1 if value > 0 else -1 if value < 0 else fallback


def area_at(x):
    return min(bisect_right(AREA_ENDS, x), len(AREAS) - 1)


def ground_at(x):
    index = limit(bisect_right(GROUND_XS, x), 1, len(GROUND) - 1)
    left, y = GROUND[index - 1]
    right, end_y = GROUND[index]
    return y + (end_y - y) * limit((x - left) / (right - left), 0, 1)


PORTALS = []
for i, area in enumerate(AREAS):
    if i:
        PORTALS.append((area["start"] + 65, AREAS[i - 1]["end"] - 155, i - 1))
    if i + 1 < len(AREAS):
        PORTALS.append((area["end"] - 65, AREAS[i + 1]["start"] + 155, i + 1))


def ladder_for(ledge):
    x = ledge["ladderX"]
    bottom = min(
        (other["y"] for other in LEDGES if ledge["y"] < other["y"] < ground_at(x)
         and other["x"] + 8 < x < other["x"] + other["w"] - 8),
        default=ground_at(x),
    )
    return x, ledge["y"], bottom


LADDERS = [ladder_for(ledge) for ledge in LEDGES]


def item_icon(item):
    return ITEMS[item].get("icon", 6) if item in ITEMS and "icon" in ITEMS[item] else {
        "jelly": 8, "spores": 9, "ash": 10, "coral": 11, "potion": 4, "tonic": 5
    }.get(item, 6)


class Game:
    def __init__(self, saved=None):
        self.p = {
            "x": START_X, "y": ground_at(START_X), "hp": 100, "mp": 35, "level": 1, "xp": 0,
            "gold": 0, "kills": 0, "pots": 5, "tonics": 1, "job": "beginner", "bag": {"twig": 1},
            "equipment": {"weapon": "twig", "armor": None, "charm": None},
            "quests": [{"state": 0, "count": 0} for _ in QUESTS],
            "attributes": dict.fromkeys(ATTRIBUTES, 0), "skillRanks": {"primary": 1, "support": 0},
            "hotbar": DEFAULT_HOTBAR[:], "trackedQuest": None, "bestiary": {},
        }
        self.tick = 0
        self.vy = 0
        self.facing = 1
        self.surface = "ground"
        self.ladder = None
        self.walk = 0
        self.land_until = 0
        self.jump_tick = -100
        self.swing = None
        self.inv_until = self.hurt_until = self.support_until = 0
        self.skill_cd = self.support_cd = 0
        self.drops, self.effects, self.monsters = [], [], []
        self.notice, self.loot, self.sound = "", None, None
        self.dirty = True
        self._stats_cache = None
        self.restore(saved)
        self.camera = self.camera_target()
        self.populate()

    def restore(self, saved):
        if not isinstance(saved, dict) or not isinstance(saved.get("level"), (int, float)):
            return
        p = self.p
        for key in ("x", "hp", "mp", "level", "xp", "gold", "kills", "pots", "tonics"):
            value = saved.get(key)
            if isinstance(value, (int, float)) and 0 <= value <= 10**9:
                p[key] = int(value)
        p["level"] = limit(p["level"], 1, 200)
        p["x"] = limit(p["x"], 24, WORLD_WIDTH - 24)
        p["y"] = ground_at(p["x"])
        if saved.get("job") in CLASSES:
            p["job"] = saved["job"]
        bag = saved.get("bag")
        if isinstance(bag, dict):
            p["bag"] = {id: count for id, count in bag.items()
                        if id in ITEMS and isinstance(count, int) and 0 < count <= 10**9
                        and id not in ("potion", "tonic")}
            p["equipment"]["weapon"] = None
        equipped = saved.get("equipment") or {}
        for slot in SLOTS:
            id = equipped.get(slot, p["equipment"][slot])
            if id is None or (id in p["bag"] and self.can_equip(id) and ITEMS[id]["slot"] == slot):
                p["equipment"][slot] = id
        if isinstance(saved.get("quests"), list):
            for index, entry in enumerate(saved["quests"][:len(QUESTS)]):
                if isinstance(entry, dict) and entry.get("state") in (0, 1, 2) and isinstance(entry.get("count"), int):
                    p["quests"][index] = {"state": entry["state"], "count": limit(entry["count"], 0, QUESTS[index]["target"])}
        elif isinstance(saved.get("quest"), int) and saved["quest"] > 0:
            p["quests"][0] = {"state": 2 if saved["quest"] >= 2 else 1, "count": min(p["kills"], QUESTS[0]["target"])}
            if saved["quest"] >= 4:
                p["quests"][1] = {"state": 2, "count": 1}
        for id in ATTRIBUTES:
            count = (saved.get("attributes") or {}).get(id)
            if isinstance(count, int):
                p["attributes"][id] = limit(count, 0, self.ap())
        ranks = saved.get("skillRanks") or {}
        for id, maximum in (("primary", 5), ("support", 3)):
            current = p["skillRanks"][id]
            if id == "support" and p["job"] not in SUPPORTS:
                continue
            count = ranks.get(id)
            if isinstance(count, int):
                for rank in range(current + 1, min(count, maximum) + 1):
                    if self.sp() and p["level"] >= self.rank_level(id, rank):
                        p["skillRanks"][id] = rank
        slots = saved.get("hotbar")
        if isinstance(slots, list):
            for index, id in enumerate(slots[:4]):
                if id is None or isinstance(id, str) and id in HOTBAR_ACTIONS:
                    p["hotbar"][index] = id
        tracked = saved.get("trackedQuest")
        if isinstance(tracked, int) and 0 <= tracked < len(QUESTS) and p["quests"][tracked]["state"] == 1:
            p["trackedQuest"] = tracked
        bestiary = saved.get("bestiary") or {}
        p["bestiary"] = {str(i): n for i in range(len(SPECIES)) if isinstance(n := bestiary.get(str(i)), int) and n > 0}
        self.changed()
        stats = self.stats()
        p["hp"] = limit(p["hp"], 1, stats["hp"])
        p["mp"] = limit(p["mp"], 0, stats["mp"])

    def changed(self):
        self.dirty = True
        self._stats_cache = None

    def stats(self):
        if self._stats_cache is not None:
            return self._stats_cache
        p = self.p
        level = p["level"] - 1
        job = CLASSES[p["job"]]
        result = {
            "hp": 100 + 10 * level + job["hp"], "mp": 35 + 4 * level + job["mp"],
            "attack": 4 + 2 * level + job["attack"], "defense": level // 2, "speed": 4.2,
        }
        for id in p["equipment"].values():
            for key in result:
                result[key] += ITEMS.get(id, {}).get(key, 0)
        for id, count in p["attributes"].items():
            for key in result:
                result[key] += ATTRIBUTES[id].get(key, 0) * count
        result["speed"] = min(7, result["speed"])
        self._stats_cache = result
        return result

    def ap(self):
        return max(0, 3 * (self.p["level"] - 1) - sum(self.p["attributes"].values()))

    def sp(self):
        return max(0, self.p["level"] - sum(self.p["skillRanks"].values()))

    @staticmethod
    def rank_level(id, rank):
        return rank * 2 - 1 if id == "primary" else 5 + rank * 2

    def add_attribute(self, id):
        if id not in ATTRIBUTES or not self.ap():
            return False
        self.p["attributes"][id] += 1
        self.p["hp"] += ATTRIBUTES[id].get("hp", 0)
        self.p["mp"] += ATTRIBUTES[id].get("mp", 0)
        self.changed()
        return True

    def raise_skill(self, id):
        ranks = self.p["skillRanks"]
        if id not in ranks or not self.sp() or id == "support" and self.p["job"] not in SUPPORTS:
            return False
        rank = ranks[id] + 1
        if rank > (5 if id == "primary" else 3) or self.p["level"] < self.rank_level(id, rank):
            return False
        ranks[id] = rank
        self.changed()
        return True

    def xp_needed(self):
        return 45 + (self.p["level"] - 1) * 28

    def gain_xp(self, amount):
        p = self.p
        p["xp"] += amount
        old = p["level"]
        while p["xp"] >= self.xp_needed():
            p["xp"] -= self.xp_needed()
            p["level"] += 1
        self.changed()
        if old < p["level"]:
            stats = self.stats()
            p["hp"], p["mp"] = stats["hp"], stats["mp"]
            self.text("LEVEL UP!", p["x"], p["y"] - 76, "#ffe8a0")
            self.notice = f"Lv. {p['level']} 달성! " + ("다온에게 전직할 수 있어요." if old < 5 <= p["level"] else "C 능력치 · S 스킬")
            self.sound = 840

    def can_equip(self, id):
        item = ITEMS.get(id, {})
        return item.get("slot") and self.p["level"] >= item["level"] and item.get("job", self.p["job"]) == self.p["job"]

    def add_item(self, id):
        if id in ("potion", "tonic"):
            self.p["pots" if id == "potion" else "tonics"] += 1
        else:
            bag = self.p["bag"]
            bag[id] = bag.get(id, 0) + 1
        self.changed()

    def toggle_equipment(self, id):
        p = self.p
        if not p["bag"].get(id) or not self.can_equip(id):
            return False
        slot = ITEMS[id]["slot"]
        p["equipment"][slot] = None if p["equipment"][slot] == id else id
        self.changed()
        stats = self.stats()
        p["hp"], p["mp"] = min(p["hp"], stats["hp"]), min(p["mp"], stats["mp"])
        return True

    def heal(self, mana=False):
        key, count, amount = ("mp", "tonics", 35) if mana else ("hp", "pots", 55)
        if not self.p[count] or self.p[key] >= self.stats()[key]:
            self.notice = "물약이 부족하거나 이미 가득 차 있어요."
            return False
        self.p[count] -= 1
        self.p[key] = min(self.p[key] + amount, self.stats()[key])
        self.dirty = True
        self.sound = 620
        return True

    def change_job(self, id):
        if self.p["level"] < 5 or self.p["job"] != "beginner" or id not in SUPPORTS:
            return False
        weapon = {"guardian": "blade", "ranger": "bow", "mage": "wand"}[id]
        self.p["job"] = id
        self.add_item(weapon)
        self.p["equipment"]["weapon"] = weapon
        self.changed()
        self.p["hp"], self.p["mp"] = self.stats()["hp"], self.stats()["mp"]
        self.notice = f"{CLASSES[id]['name']}로 전직했어요."
        return True

    def buy(self, id, stock):
        if id not in stock or self.p["gold"] < ITEMS[id]["price"]:
            return False
        self.p["gold"] -= ITEMS[id]["price"]
        self.add_item(id)
        return True

    def sellable(self, id):
        count = self.p["bag"].get(id, 0)
        return count > (1 if id in self.p["equipment"].values() else 0)

    def sell(self, id):
        if not self.sellable(id):
            return False
        self.remove_item(id, 1)
        self.p["gold"] += ITEMS[id]["price"] // 2
        self.dirty = True
        return True

    def remove_item(self, id, count):
        bag = self.p["bag"]
        bag[id] -= count
        if not bag[id]:
            del bag[id]

    def can_craft(self, recipe):
        return self.p["gold"] >= recipe["gold"] and all(
            self.p["bag"].get(id, 0) >= count for id, count in recipe["ingredients"].items())

    def craft(self, id):
        recipe = next((entry for entry in RECIPES if entry["item"] == id), None)
        if not recipe or not self.can_craft(recipe):
            return False
        for material, count in recipe["ingredients"].items():
            self.remove_item(material, count)
        self.p["gold"] -= recipe["gold"]
        self.add_item(id)
        self.loot = (0, [id])
        return True

    def accept_quest(self, index):
        entry = self.p["quests"][index]
        if entry["state"]:
            return False
        entry["state"] = 1
        self.p["trackedQuest"] = index
        self.dirty = True
        return True

    def claim_quest(self, index):
        entry, quest = self.p["quests"][index], QUESTS[index]
        if entry["state"] != 1 or entry["count"] < quest["target"]:
            return False
        entry["state"] = 2
        if self.p["trackedQuest"] == index:
            self.p["trackedQuest"] = None
        self.p["gold"] += quest["gold"]
        self.add_item(quest["item"])
        self.gain_xp(quest["xp"])
        self.loot = (quest["gold"], [quest["item"]])
        return True

    def tracked_quest(self):
        p = self.p
        index = p["trackedQuest"]
        if index is not None and p["quests"][index]["state"] == 1:
            return index
        return next((i for i, entry in enumerate(p["quests"]) if entry["state"] == 1), None)

    def quest_caption(self):
        index = self.tracked_quest()
        if index is None:
            return "마을의 리나와 대화" if not self.p["quests"][0]["state"] else "퀘스트 기록 열기"
        quest = QUESTS[index]
        count = self.p["quests"][index]["count"]
        return f"{quest['who']}에게 보고" if count >= quest["target"] else f"{quest['name']} {count}/{quest['target']}"

    def camera_target(self):
        area = AREAS[area_at(self.p["x"])]
        return limit(self.p["x"] - WIDTH / 2, area["start"], area["end"] - WIDTH)

    def travel(self, x):
        if area_at(x) != area_at(self.p["x"]):
            self.effects.clear()
        self.p["x"], self.p["y"] = x, ground_at(x)
        self.camera = self.camera_target()
        self.vy, self.surface, self.ladder, self.swing, self.walk = 0, "ground", None, None, 0
        self.land_until = 0
        self.dirty = True

    def nearby(self):
        x, y = self.p["x"], self.p["y"]
        for portal in PORTALS:
            if abs(portal[0] - x) <= 42 and abs(ground_at(portal[0]) - y) <= 28:
                return ("portal", portal)
        for npc in NPCS:
            if abs(npc["x"] - x) <= 58 and abs(ground_at(npc["x"]) - y) <= 29:
                return ("npc", npc)
        return (None, None)

    def jump(self, down=False):
        if self.surface is None and self.ladder is None:
            return
        self.jump_tick = self.tick
        if down and isinstance(self.surface, dict):
            self.p["y"] += 2
            self.vy = 1
        else:
            self.vy = -11.2
            self.sound = 300
            self.effects.append(("dust", self.tick, self.p["x"], self.p["y"], 13, self.facing))
        self.surface = self.ladder = None

    def primary(self):
        return CLASSES[self.p["job"]]

    def support_value(self, stat):
        support = SUPPORTS.get(self.p["job"])
        return support["power"] * (1 + .35 * (self.p["skillRanks"]["support"] - 1)) if (
            self.tick < self.support_until and support and support["stat"] == stat) else 0

    def support(self):
        rank = self.p["skillRanks"]["support"]
        support = SUPPORTS.get(self.p["job"])
        if not rank or not support or self.support_cd or self.tick < self.hurt_until:
            return False
        if self.p["mp"] < support["cost"]:
            self.notice = "마력이 부족해요."
            return False
        self.p["mp"] -= support["cost"]
        self.support_until = self.tick + 420 + 90 * (rank - 1)
        self.support_cd = 720
        self.text(support["name"], self.p["x"], self.p["y"] - 65, "#b7ffd3")
        self.sound = 690
        self.dirty = True
        return True

    def start_attack(self, skill=False):
        if self.swing or self.ladder or self.tick < self.hurt_until:
            return False
        job = self.primary()
        if skill and (self.skill_cd or self.p["mp"] < job["cost"]):
            return False
        if skill:
            self.p["mp"] -= job["cost"]
            self.skill_cd = job["cooldown"]
            self.dirty = True
        self.swing = {"start": self.tick, "dir": self.facing, "skill": skill}
        self.sound = 380
        return True

    def text(self, text, x, y, color="#ffe381"):
        self.effects.append(("text", self.tick, x, y, 42, (str(text), color)))

    def update_attack(self):
        if not self.swing:
            return
        elapsed = self.tick - self.swing["start"]
        if elapsed >= SWING_END:
            self.swing = None
            return
        if elapsed != SWING_WINDUP:
            return
        skill, facing = self.swing["skill"], self.swing["dir"]
        p = self.p
        job = self.primary()
        shape = job["shape"] if skill else "slash"
        power = self.stats()["attack"] + self.support_value("attack")
        power = ceil(power * (job["power"] + .25 * (p["skillRanks"]["primary"] - 1))) if skill else round(power)
        self.sound = 740 if skill else 505
        if shape == "arrow":
            self.effects.append(("arrow", self.tick, p["x"] + facing * 15, p["y"] - 22, ceil(job["reach"] / 15), facing))
            self.arrow_damage = power
            return
        radius = job["reach"] if skill else 54
        self.effects.append((shape, self.tick, p["x"], p["y"] - 24, 17 if skill else 11, facing))
        for monster in self.monsters:
            if monster["dead"] is not None or area_at(monster["x"]) != area_at(p["x"]):
                continue
            dx, dy = monster["x"] - p["x"], abs(monster["y"] - p["y"])
            if abs(dx) <= radius and dy <= (92 if shape == "stars" else 51 if skill else 31):
                if shape not in ("slash", "arc") or dx * facing >= -8:
                    self.hit(monster, power + (int(random() * 3) if not skill else 0), direction(dx, facing))

    def spawn(self, x, kind, index, ledge=None):
        spec = SPECIES[kind]
        area = AREAS[area_at(x)]
        stride = 134 if spec.get("elite") else 86
        low = ledge["x"] + 16 if ledge else max(area["start"] + 24, x - stride)
        high = ledge["x"] + ledge["w"] - 16 if ledge else min(area["end"] - 24, x + stride)
        monster = {"x": x, "y": ledge["y"] if ledge else ground_at(x), "home": x, "kind": kind, "spec": spec,
                   "left": low, "right": high, "dir": 1 if index % 2 else -1, "hp": spec["hp"], "dead": None,
                   "state": "patrol", "hurt": 0, "windup": 0, "strike": -100, "next": 0, "ledge": ledge, "phase": index * 31}
        self.monsters.append(monster)
        return monster

    def populate(self):
        def kind(x, i):
            if x < 3780:
                return 0
            if x < 6100:
                return 1
            if x < 9100:
                return 2
            if x < 12000:
                return 3 if i % 2 else 5
            if x < 13040:
                return 5 if i % 2 else 6
            if x < 14900:
                return 6 if i % 3 else 7
            return 8 if i % 2 else 9
        for i, x in enumerate(range(2580, 18070, 213)):
            if not (9290 <= x <= 10810 or 11520 < x < 12500 or 14900 < x < 15500):
                self.spawn(x, kind(x, i), i)
        for i, ledge in enumerate(LEDGES):
            x = ledge["x"]
            if x >= 2450 and i % 3 and not 9100 <= x <= 10900:
                self.spawn(x + int(.6 * ledge["w"]), kind(x, i), i, ledge)
        self.spawn(11780, 4, 1)
        self.spawn(18120, 10, 1)

    def hit(self, monster, power, facing):
        spec = monster["spec"]
        monster["hp"] -= power
        monster["hurt"] = self.tick + 10
        monster["hit_dir"] = facing
        if not spec.get("elite"):
            monster["windup"] = 0
            monster["next"] = max(monster["next"], self.tick + 13)
        if spec.get("aggro") and monster["state"] != "return":
            monster["state"] = "pursuit"
        self.move_monster(monster, monster["x"] + facing * 8, 8)
        self.text(power, monster["x"], monster["y"] - 48)
        self.effects.append(("impact", self.tick, monster["x"], monster["y"] - 22, 13, facing))
        if monster["hp"] <= 0:
            self.reward(monster)

    def reward(self, monster):
        spec = monster["spec"]
        monster["dead"] = self.tick
        monster["windup"] = 0
        p = self.p
        p["kills"] += 1
        key = str(monster["kind"])
        p["bestiary"][key] = p["bestiary"].get(key, 0) + 1
        self.gain_xp(spec["xp"])
        for quest, entry in zip(QUESTS, p["quests"]):
            if entry["state"] == 1 and monster["kind"] in quest["matches"]:
                entry["count"] = min(quest["target"], entry["count"] + 1)
        items = [spec["loot"]]
        if spec.get("elite") or random() < .16:
            items.append(spec["rare"])
        if random() < .18:
            items.append("tonic" if monster["kind"] % 2 else "potion")
        self.drops.append({"x": monster["x"], "y": monster["y"], "start": self.tick, "items": items, "gold": spec["gold"]})

    def collect(self):
        kept = []
        p = self.p
        for drop in self.drops:
            age = self.tick - drop["start"]
            if age > 1000:
                continue
            if age < 12 or abs(drop["x"] - p["x"]) > 34 or abs(drop["y"] - p["y"]) > 30:
                kept.append(drop)
                continue
            p["gold"] += drop["gold"]
            for id in drop["items"]:
                self.add_item(id)
            self.loot = (drop["gold"], drop["items"])
            self.effects.append(("pickup", self.tick, drop["x"], drop["y"] - 12, 16,
                                 (item_icon(drop["items"][-1]), p["x"], p["y"] - 38)))
        self.drops = kept

    def move_monster(self, monster, x, speed):
        delta = limit(x - monster["x"], -speed, speed)
        if delta:
            monster["dir"] = direction(delta)
        monster["x"] = limit(monster["x"] + delta, monster["left"], monster["right"])
        if not monster["ledge"]:
            monster["y"] = ground_at(monster["x"])

    def monster_step(self, monster):
        tick, p, spec = self.tick, self.p, monster["spec"]
        if monster["dead"] is not None:
            if tick - monster["dead"] >= (900 if spec.get("elite") else 340):
                monster.update(dead=None, hp=spec["hp"], state="patrol", next=tick + 40)
                self.move_monster(monster, monster["home"], 500)
            return
        if area_at(monster["home"]) != area_at(p["x"]):
            if monster["state"] != "patrol" or monster["windup"]:
                monster.update(state="patrol", windup=0)
                self.move_monster(monster, monster["home"], 500)
            return
        offset = p["x"] - monster["x"]
        same_height = abs(monster["y"] - p["y"]) < 37
        elite = spec.get("elite")
        enraged = elite and monster["hp"] <= spec["hp"] / 2
        reach = 90 if enraged else 60 if elite else 25
        if monster["windup"]:
            if tick < monster["windup"]:
                return
            monster.update(windup=0, strike=tick, next=tick + (46 if enraged else 64))
            reach = monster["range"]
            if elite:
                self.effects.append(("wave", tick, monster["x"] + monster["dir"] * reach / 2, monster["y"] - 10, 20, reach / 2))
            if same_height and -12 <= offset * monster["dir"] <= reach:
                self.take_damage(ceil(spec["attack"] * (1.2 if enraged else 1)))
            return
        if tick < monster["hurt"]:
            return
        aggro = spec.get("aggro", 0)
        near_home = abs(p["x"] - monster["home"]) <= aggro + 70
        if monster["state"] == "pursuit" and (not same_height or not near_home or abs(offset) > aggro + 80):
            monster["state"] = "return"
        if monster["state"] == "patrol" and aggro and same_height and near_home and abs(offset) <= aggro:
            monster["state"] = "pursuit"
        if monster["state"] != "return" and same_height and abs(offset) <= reach and tick >= monster["next"]:
            monster.update(dir=direction(offset, monster["dir"]), range=reach, windup=tick + (24 if enraged else 34 if elite else 17))
        elif monster["state"] == "return":
            self.move_monster(monster, monster["home"], spec["speed"] * 1.6)
            if monster["x"] == monster["home"]:
                monster["state"] = "patrol"
        elif monster["state"] == "pursuit":
            if abs(offset) > reach - 2:
                self.move_monster(monster, p["x"], spec["speed"] * (2.35 if enraged else 1.9))
        else:
            target = monster["right"] if monster["dir"] > 0 else monster["left"]
            self.move_monster(monster, target, spec["speed"])
            if monster["x"] == target:
                monster["dir"] *= -1

    def take_damage(self, amount):
        if self.tick < self.inv_until:
            return
        p, stats = self.p, self.stats()
        lost = max(1, amount - int(stats["defense"] + self.support_value("defense")))
        p["hp"] -= lost
        self.inv_until, self.hurt_until = self.tick + 55, self.tick + 10
        self.swing = self.ladder = self.surface = None
        self.vy = -3.4
        self.text("-" + str(lost), p["x"], p["y"] - 52, "#ffab95")
        self.dirty = True
        if p["hp"] <= 0:
            self.travel(START_X)
            p["hp"], p["mp"] = stats["hp"], stats["mp"]
            self.notice = "솔방울 마을에서 회복했어요."

    def effect_step(self):
        live = []
        impacts = []
        for effect in self.effects:
            shape, start, x, y, duration, data = effect
            age = self.tick - start
            if age >= duration:
                continue
            if shape == "arrow":
                arrow_x = x + data * 15 * age
                monster = next((m for m in self.monsters if m["dead"] is None
                                and area_at(m["x"]) == area_at(self.p["x"])
                                and abs(m["x"] - arrow_x) <= 18 and abs(y - (m["y"] - 18)) <= 22), None)
                if monster:
                    impacts.append((monster, data))
                    continue
            live.append(effect)
        self.effects = live
        for monster, facing in impacts:
            if monster["dead"] is None:
                self.hit(monster, self.arrow_damage, facing)

    def move_player(self, dx, dy):
        p = self.p
        if dx:
            self.ladder = None
        if not self.ladder and not dx and not self.swing and dy and self.vy >= 0:
            self.ladder = next((ladder for ladder in LADDERS if abs(p["x"] - ladder[0]) <= 11 and (
                ladder[1] < p["y"] <= ladder[2] + 2 if dy < 0 else ladder[1] - 1 <= p["y"] < ladder[2] - 1)), None)
        if self.ladder:
            x, top, bottom = self.ladder
            p["x"], p["y"] = x, limit(p["y"] + dy * 3.2, top, bottom)
            self.vy, self.surface = 0, None
            if p["y"] in (top, bottom):
                self.ladder, self.surface = None, "ladder"
            return
        old_x, old_y, previous_surface = p["x"], p["y"], self.surface
        area = AREAS[area_at(old_x)]
        speed = self.stats()["speed"] + self.support_value("speed")
        p["x"] = limit(old_x + dx * speed * (.58 if self.swing and self.surface else 1), area["start"] + 24, area["end"] - 24)
        floor = ground_at(p["x"])
        if self.surface == "ground":
            p["y"] = floor
        else:
            self.vy += .5
            p["y"] += self.vy
            self.surface = None
            if self.vy >= 0:
                landing = floor if p["y"] >= floor else float("inf")
                selected = "ground"
                for ledge in LEDGES:
                    if old_y <= ledge["y"] <= p["y"] and ledge["y"] < landing and ledge["x"] - 3 <= p["x"] <= ledge["x"] + ledge["w"] + 3:
                        landing, selected = ledge["y"], ledge
                if landing < float("inf"):
                    p["y"], self.surface, self.vy = landing, selected, 0
                    if previous_surface is None:
                        self.land_until = self.tick + 5
                        self.effects.append(("dust", self.tick, p["x"], landing, 12, self.facing))
        self.walk = self.walk + abs(p["x"] - old_x) if self.surface and dx else 0

    def step(self, keys):
        self.tick += 1
        self.skill_cd = max(0, self.skill_cd - 1)
        self.support_cd = max(0, self.support_cd - 1)
        dx = int("ArrowRight" in keys) - int("ArrowLeft" in keys)
        dy = int("ArrowDown" in keys) - int("ArrowUp" in keys)
        if dx and not self.swing:
            self.facing = dx
        if "KeyX" in keys:
            self.start_attack(True)
        if "KeyZ" in keys:
            self.start_attack()
        self.move_player(dx, dy)
        self.update_attack()
        self.effect_step()
        for monster in self.monsters:
            self.monster_step(monster)
        self.collect()
        if self.tick % 90 == 0 and self.p["mp"] < self.stats()["mp"]:
            self.p["mp"] += 1
            self.dirty = True
        target = self.camera_target()
        self.camera += (target - self.camera) * .19
        if abs(target - self.camera) < .1:
            self.camera = target
