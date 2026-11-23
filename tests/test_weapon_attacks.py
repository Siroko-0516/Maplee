import unittest

from maplee.engine import Game, SWING_WINDUP


class WeaponAttacks(unittest.TestCase):
    def test_ranged_basic_attack_uses_equipped_weapon_and_lands_at_range(self):
        for job, weapon, shape in (("ranger", "bow", "arrow"), ("mage", "wand", "bolt")):
            with self.subTest(weapon=weapon):
                game = Game({"level": 7, "job": job, "bag": {weapon: 1},
                             "equipment": {"weapon": weapon}})
                game.travel(2720)
                game.facing = 1
                game.monsters.clear()
                target = game.spawn(2830, 1, 0)
                initial = target["hp"]
                self.assertTrue(game.start_attack())
                self.assertTrue(game.toggle_equipment(weapon))
                self.assertEqual(game.swing["weapon"], weapon)
                game.tick = SWING_WINDUP
                game.update_attack()
                self.assertEqual(game.effects[-1][0], shape)
                self.assertEqual(initial, target["hp"])
                for _ in range(8):
                    game.tick += 1
                    game.effect_step()
                self.assertLess(target["hp"], initial)
                hp = target["hp"]
                game.effect_step()
                self.assertEqual(target["hp"], hp)

    def test_continuous_melee_contact_and_recovery_inputs(self):
        for weapon in ("twig", None):
            game = Game()
            game.monsters.clear()
            game.p["equipment"]["weapon"] = weapon
            game.press_attack()
            self.assertEqual((game.swing["impact"], game.swing["duration"]), (8, 24))
            for _ in range(19):
                game.step(set())
            game.press_attack()
            game.press_attack()
            for _ in range(5):
                game.step({"ArrowRight"})
            self.assertEqual((game.swing["start"], game.swing["dir"]), (24, 1))
            for _ in range(24):
                game.step(set())
            self.assertIsNone(game.swing)
            for _ in range(49):
                game.step({"KeyZ"})
            self.assertEqual(game.swing["start"], 97)

    def test_blade_contacts_a_body_entering_the_sweep_only_once(self):
        game = Game()
        game.monsters.clear()
        game.facing = 1
        target = game.spawn(game.p["x"] + 100, 0, 0)
        target["spec"] = dict(target["spec"], body_size=(32, 38))
        game.start_attack()
        game.tick = game.swing["impact"]
        hits = []
        game.hit = lambda *args: hits.append(args)
        game.update_attack()
        self.assertFalse(hits)
        target["x"] = game.p["x"] + game.swing["reach"] + 12
        for _ in range(4):
            game.tick += 1
            game.update_attack()
        self.assertEqual(len(hits), 1)

    def test_projectile_selects_first_body_on_travel_path(self):
        for facing in (-1, 1):
            game = Game()
            game.monsters.clear()
            x, y = game.p["x"], game.p["y"]
            far = game.spawn(x + 14*facing, 0, 0)
            near = game.spawn(x + 5*facing, 0, 1)
            for m in (far, near):
                m["spec"] = dict(m["spec"], body_size=(4, 32))
            game.tick = 1
            game.effects = [("arrow", 0, x, y-20, 10, (facing, 4))]
            hits = []
            game.hit = lambda target, *args: hits.append(target)
            game.effect_step()
            self.assertEqual(hits, [near])

    def test_projectiles_keep_individual_damage(self):
        game = Game()
        game.monsters.clear()
        monster = game.spawn(310, 10, 0)
        game.effects = [
            ("arrow", 0, 310, monster["y"]-20, 5, (1, 41)),
            ("bolt", 0, 310, monster["y"]-20, 5, (1, 58)),
        ]
        impacts = []
        game.hit = lambda target, power, facing, impact: impacts.append((target["kind"], power, facing, impact))
        game.effect_step()
        self.assertEqual(impacts, [(10, 41, 1, "arrow_hit"), (10, 58, 1, "bolt_hit")])
