import unittest

from maplee.content import AREAS, BASE_WORLD_WIDTH, HUNT_FIELDS, NPCS, QUESTS, SPECIES, WORLD_WIDTH, map_x
from maplee.engine import Game, PORTALS, area_at, ground_at
from maplee.hunting import HUNT_ZONES, next_hunting_wave


class HuntingTests(unittest.TestCase):
    def test_each_species_has_a_separate_two_way_hunting_field(self):
        self.assertGreater(WORLD_WIDTH,map_x(BASE_WORLD_WIDTH)*1.7)
        game = Game()
        self.assertEqual({field["kind"] for field in HUNT_FIELDS},set(range(len(SPECIES))))
        for field in HUNT_FIELDS:
            region, kind = field["region"], field["kind"]
            self.assertEqual({m["kind"] for m in game.monsters_in_area(region)},{kind})
            entrance = map_x(field["gate"])
            gate = next(p for p in PORTALS if p[0]==entrance)
            self.assertEqual(gate[2], region)
            self.assertTrue(any(area_at(x)==region and dest==entrance and end==field["parent"]
                                for x,dest,end in PORTALS))

    def test_encounters_cover_zones_and_leave_safe_arrivals(self):
        game = Game()
        self.assertEqual(len(AREAS), len(HUNT_ZONES))
        safe_points = [game.p["x"]] + [npc["x"] for npc in NPCS]
        safe_points.extend(x for departure, arrival, _ in PORTALS for x in (departure, arrival))
        for index, zone in enumerate(HUNT_ZONES):
            monsters = [m for m in game.monsters if area_at(m["home"]) == index]
            species = {m["kind"] for m in monsters}
            self.assertEqual(set(zone["species"]), species)
            levels = [SPECIES[kind]["level"] for kind in species]
            self.assertEqual(zone["levels"], (min(levels), max(levels)))
            self.assertTrue(any(m["ledge"] for m in monsters))
            self.assertTrue(any(m["ledge"] is None for m in monsters))
            for m in monsters:
                self.assertLess(m["left"], m["home"])
                self.assertLess(m["home"], m["right"])
                self.assertEqual(area_at(m["left"]), index)
                self.assertEqual(area_at(m["right"]), index)
                if m["ledge"]:
                    self.assertEqual(m["y"], m["ledge"]["y"])
                    self.assertLess(m["y"], ground_at(m["home"]))
                else:
                    reach = 90 if m["spec"].get("elite") else 25
                    self.assertFalse(any(m["left"]-reach <= x <= m["right"]+reach
                                         for x in safe_points), (index, m["home"]))
        available = {m["kind"] for m in game.monsters}
        self.assertEqual(available, set(range(len(SPECIES))))
        for quest in QUESTS:
            self.assertTrue(set(quest["matches"]) & available)

    def test_wave_waits_then_revives_at_home(self):
        game = Game()
        zone = HUNT_ZONES[0]
        first, second = game.monsters[:2]
        for tick, monster in ((63, first), (83, second)):
            game.tick = tick
            game.move_monster(monster, monster["home"] + 50, 50)
            game.hit(monster, monster["hp"], 1)
        due = first["revive_at"]
        self.assertEqual(due, second["revive_at"])
        self.assertEqual(due % zone["wave"], 0)
        for monster in (first, second):
            game.tick = due - 1
            game.monster_step(monster)
            self.assertIsNotNone(monster["dead"])
            game.tick = due
            game.monster_step(monster)
            self.assertIsNone(monster["dead"])
            self.assertEqual(monster["x"], monster["home"])
            self.assertEqual(monster["hp"], monster["spec"]["hp"])
        self.assertGreater(next_hunting_wave(zone, due-1), due)
        boss_zone = HUNT_ZONES[2]
        self.assertGreaterEqual(next_hunting_wave(boss_zone, 3, True)-next_hunting_wave(boss_zone, 3),
                                boss_zone["wave"]*boss_zone["boss_waves"])
