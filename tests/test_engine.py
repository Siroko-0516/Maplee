import json
import unittest
from maplee.content import AREAS, ITEMS, QUESTS, RECIPES, SPECIES
from maplee.engine import PORTALS, SWING_WINDUP, Game, area_at, ground_at


class WorldTests(unittest.TestCase):
    def sandbox(self, x=310, saved=None):
        game = Game(saved)
        game.monsters.clear()
        game.travel(x)
        game.facing = 1
        return game

    def step(self, game, count, *keys):
        for _ in range(count):
            game.step(set(keys))

    def test_ground_portals_and_area_limits(self):
        game = self.sandbox(390)
        previous = game.p["y"]
        for _ in range(70):
            self.step(game, 1, "ArrowRight")
            self.assertLess(abs(game.p["y"] - previous), 2)
            self.assertEqual(game.p["y"], ground_at(game.p["x"]))
            previous = game.p["y"]
        game.travel(2400)
        self.step(game, 90, "ArrowRight")
        self.assertEqual(area_at(game.p["x"]), 0)
        self.assertEqual(game.p["x"], AREAS[0]["end"] - 24)
        game.travel(PORTALS[0][0])
        kind, portal = game.nearby()
        self.assertEqual(kind, "portal")
        game.travel(portal[1])
        self.assertEqual(area_at(game.p["x"]), 1)

    def test_attack_frame_landing_and_pickup(self):
        game = self.sandbox(2690)
        target = game.spawn(2727, 0, 0)
        initial_hp = target["hp"]
        self.assertTrue(game.start_attack())
        self.step(game, SWING_WINDUP - 1)
        self.assertEqual(target["hp"], initial_hp)
        self.step(game, 1)
        self.assertLess(target["hp"], initial_hp)
        hp = target["hp"]
        self.step(game, 15)
        self.assertEqual(target["hp"], hp)
        game.hit(target, target["hp"], 1)
        game.travel(target["x"])
        self.step(game, 11)
        self.assertEqual(game.p["gold"], 0)
        self.step(game, 1)
        self.assertEqual(game.p["gold"], SPECIES[0]["gold"])
        self.assertGreater(game.p["bag"]["jelly"], 0)
        self.assertTrue(any(effect[0] == "pickup" for effect in game.effects))

    def test_progression_and_save_recovery(self):
        game = self.sandbox(saved={"level": 4, "xp": 9, "hp": 62, "gold": 120, "quest": 1, "kills": 3})
        self.assertEqual(game.p["quests"][0]["count"], 3)
        game.add_attribute("strength")
        self.assertEqual(game.ap(), 8)
        self.assertFalse(game.change_job("guardian"))
        game.gain_xp(game.xp_needed())
        self.assertTrue(game.change_job("guardian"))
        game.raise_skill("primary")
        self.assertTrue(game.sell("twig"))
        restored = Game(json.loads(json.dumps(game.p)))
        self.assertEqual(restored.p["equipment"]["weapon"], "blade")
        self.assertEqual(restored.p["skillRanks"]["primary"], 2)
        self.assertEqual(restored.p["attributes"]["strength"], 1)
        self.assertNotIn("twig", restored.p["bag"])
        self.assertEqual(restored.p["job"], "guardian")

    def test_monster_pursues_and_returns(self):
        game = self.sandbox(12670)
        enemy = game.spawn(12750, 5, 0)
        self.step(game, 4)
        self.assertEqual(enemy["state"], "pursuit")
        self.assertLess(enemy["x"], enemy["home"])
        game.travel(12990)
        self.step(game, 1)
        self.assertEqual(enemy["state"], "return")
        self.step(game, 50)
        self.assertEqual(enemy["state"], "patrol")

    def test_economy_quest_boss_and_crafting(self):
        game = self.sandbox(18135, saved={"level": 13, "gold": 525})
        self.assertTrue(game.accept_quest(6))
        self.assertFalse(game.claim_quest(6))
        boss = game.spawn(18120, 10, 0)
        game.hit(boss, boss["hp"], 1)
        self.assertEqual(game.p["quests"][6]["count"], 1)
        self.assertEqual(game.p["bestiary"]["10"], 1)
        self.assertIn("moonseal", game.drops[0]["items"])
        self.assertTrue(game.claim_quest(6))
        recipe = next(r for r in RECIPES if r["item"] == "glasscoat")
        self.assertFalse(game.craft("glasscoat"))
        game.p["bag"].update(recipe["ingredients"])
        self.assertTrue(game.craft("glasscoat"))
        self.assertTrue(game.toggle_equipment("glasscoat"))
        self.assertFalse(game.sell("glasscoat"))

    def test_landing_recovery_and_projectile(self):
        game = self.sandbox(2720, saved={"level": 7, "job": "ranger"})
        target = game.spawn(2842, 0, 0)
        self.assertTrue(game.start_attack(True))
        self.step(game, SWING_WINDUP + 10)
        self.assertIsNotNone(target["dead"])
        self.step(game, 15)
        game.jump()
        self.assertIsNone(game.surface)
        self.step(game, 3)
        self.assertLess(game.vy, 0)
        self.step(game, 43)
        self.assertIsNotNone(game.surface)


if __name__ == "__main__":
    unittest.main()
