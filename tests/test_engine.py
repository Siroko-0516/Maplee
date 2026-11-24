import json
import unittest
from maplee.content import AREAS, ITEMS, LEDGES, LEDGE_DEPTH, QUESTS, RECIPES, SPECIES, WORLD_LAYOUT, WORLD_WIDTH, map_x
from maplee.engine import LADDERS, PORTALS, SWING_WINDUP, Game, area_at, ground_at, monster_bounds, monster_feet_y


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
        self.assertEqual(game.camera, AREAS[0]["end"] - 960)
        game.travel(PORTALS[0][0])
        kind, portal = game.nearby()
        self.assertEqual(kind, "portal")
        game.travel(portal[1])
        self.assertEqual(area_at(game.p["x"]), 1)

    def test_each_region_border_requires_portal_in_both_directions(self):
        for x, destination, index in PORTALS:
            game = self.sandbox(x)
            origin = area_at(x)
            direction = "ArrowRight" if index>origin else "ArrowLeft"
            self.step(game, 40, direction)
            self.assertEqual(area_at(game.p["x"]),origin)
            game.travel(x)
            self.assertEqual(game.nearby(),("portal",(x,destination,index)))
            game.travel(destination)
            self.assertEqual(area_at(game.p["x"]),index)
            self.assertEqual(game.p["y"],ground_at(game.p["x"]))
        self.assertEqual(len(PORTALS),2*(len(AREAS)-1))

    def test_legacy_position_migrates_once(self):
        game = Game({"level":8,"x":9120,"gold":470})
        self.assertEqual(game.p["x"],map_x(9120))
        self.assertEqual(game.p["worldLayout"],WORLD_LAYOUT)
        self.assertEqual(game.p["gold"],470)
        self.assertEqual(Game(game.p).p["x"],game.p["x"])

    def test_previous_layout_positions_follow_shortened_forest(self):
        forest = AREAS[1]
        self.assertAlmostEqual(forest["end"]-forest["start"], (11375-3062)*.75, delta=1)
        for authored in (1750, 5750, 13900, 28800, 33400):
            restored = Game({"level":14, "worldLayout":2, "x":round(authored*1.25)})
            self.assertAlmostEqual(restored.p["x"], map_x(authored), delta=1)
            self.assertEqual(Game(restored.p).p["x"], restored.p["x"])

    def test_platform_surfaces_have_separate_bodies(self):
        for i, ledge in enumerate(LEDGES):
            for other in LEDGES[:i]:
                overlap = min(ledge["x"]+ledge["w"],other["x"]+other["w"]) - max(ledge["x"],other["x"])
                if overlap > 0:
                    self.assertGreaterEqual(abs(ledge["y"]-other["y"]),LEDGE_DEPTH,(ledge,other))
        x = map_x(5500)
        self.assertEqual(Game({"level":8,"x":x,"worldLayout":3}).p["x"],x)

    def test_ladder_reaches_floating_ledge_and_returns_to_ground(self):
        x, top, bottom = LADDERS[0]
        game = self.sandbox(x)
        self.assertEqual(game.p["y"],bottom)
        self.step(game,1,"ArrowUp")
        self.assertTrue(game.ladder)
        self.step(game,100,"ArrowUp")
        self.assertEqual(game.p["y"],top)
        self.step(game,100,"ArrowDown")
        self.assertIsNone(game.ladder)
        self.assertEqual(game.p["y"],bottom)

    def test_camera_follows_jump_and_portal_with_narrow_view(self):
        game = self.sandbox(map_x(1150))
        game.set_camera_view(320,468)
        self.assertEqual(game.camera,game.p["x"]-160)
        ground_top = game.camera_y
        game.jump()
        self.step(game,20,"ArrowRight")
        self.assertLess(game.camera_y,ground_top-60)
        self.assertGreater(game.camera, map_x(1150)-160)
        self.step(game,90)
        self.assertAlmostEqual(game.camera_y,game.camera_vertical_target(),places=1)
        _, destination, _ = PORTALS[0]
        game.travel(destination)
        self.assertEqual(game.camera,game.camera_target())
        self.assertEqual(game.camera_y,game.camera_vertical_target())

    def assert_climb_route(self, authored_x, from_ledge=False):
        route = [next(ladder for ladder in LADDERS if ladder[0] == map_x(x))
                 for x in authored_x]
        game = self.sandbox(route[0][0])
        game.set_camera_view(1040, 585)
        if from_ledge:
            game.p["y"] = route[0][2]
            game.surface = "ladder"
        for x, top, bottom in route:
            for _ in range(280):
                if abs(game.p["x"] - x) <= 8:
                    break
                key = "ArrowRight" if game.p["x"] < x else "ArrowLeft"
                self.step(game, 1, key)
            self.assertLessEqual(abs(game.p["x"] - x), 8)
            self.assertAlmostEqual(game.p["y"], bottom, delta=3)
            self.step(game, 50, "ArrowUp")
            self.assertEqual(game.p["y"], top)
        self.assertLess(route[-1][1], 0)
        self.assertGreater(game.p["y"] - game.camera_y, 80)

    def test_canopy_stairs_connect_ground_to_the_top_platform(self):
        self.assert_climb_route((26205, 26520, 26700, 27000))

    def test_bellflower_routes_reach_high_ledges(self):
        self.assert_climb_route((3450, 3680, 4135), from_ledge=True)
        self.assert_climb_route((5356, 5580, 5840, 6100), from_ledge=True)

    def test_reclass_from_existing_save_retains_items_and_health(self):
        game = self.sandbox(saved={"level":14,"job":"guardian","hp":22,"mp":10,
                                   "bag":{"blade":1},"equipment":{"weapon":"blade"}})
        for job, equipment in (("thief","dagger"),("pirate","knuckle"),("cleric","chimewand"),("thief","dagger")):
            self.assertTrue(game.change_job(job))
            self.assertEqual(game.p["equipment"]["weapon"],equipment)
            self.assertEqual(game.p["bag"][equipment],1)
            self.assertEqual((game.p["hp"],game.p["mp"]),(22,10))
        self.assertEqual(game.p["bag"]["blade"],1)

    def test_thief_strikes_the_nearest_target_twice(self):
        game = self.sandbox(18630,saved={"level":12,"job":"thief"})
        far = game.spawn(18682,11,0)
        near = game.spawn(18650,11,1)
        self.assertTrue(game.start_attack(True))
        hit = []
        game.hit = lambda target,*_: hit.append(target)
        for tick in range(1,game.swing["duration"]):
            game.tick=tick
            game.update_attack()
        self.assertEqual(hit,[near,near])
        self.assertNotIn(far,hit)

    def test_heal_restores_hp_and_hits_undead_only(self):
        game = self.sandbox(19150,saved={"level":12,"job":"cleric","hp":5})
        ghost = game.spawn(19140,11,0)
        live = game.spawn(19170,0,1)
        self.assertTrue(game.start_attack(True))
        hit=[]
        game.hit = lambda target,*_: hit.append(target)
        game.tick = game.swing["impact"]
        game.update_attack()
        self.assertGreater(game.p["hp"],5)
        self.assertEqual(hit,[ghost])
        self.assertNotIn(live,hit)

    def test_attack_frame_landing_and_pickup(self):
        game = self.sandbox(2690)
        target = game.spawn(2727, 0, 0)
        initial_hp = target["hp"]
        self.assertTrue(game.start_attack())
        self.step(game, game.swing["impact"] - 1)
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
        x = map_x(12670)
        game = self.sandbox(x)
        enemy = game.spawn(x+80, 5, 0)
        self.step(game, 4)
        self.assertEqual(enemy["state"], "pursuit")
        self.assertLess(enemy["x"], enemy["home"])
        game.travel(x+320)
        self.step(game, 1)
        self.assertEqual(enemy["state"], "return")
        self.step(game, 50)
        self.assertEqual(enemy["state"], "patrol")

    def test_star_pixie_hovers_and_hitbox_follows(self):
        game = Game()
        pixies = [m for m in game.monsters if m["spec"]["name"] == "스타픽시"]
        for habitat in (True, False):
            monster = next(m for m in pixies if bool(m["ledge"]) == habitat)
            for tick in (0, 17, 51):
                feet = monster_feet_y(monster, tick)
                self.assertIn(round(monster["y"]-feet), range(21, 28))
                self.assertEqual(monster_bounds(monster, tick)[3], feet)

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
