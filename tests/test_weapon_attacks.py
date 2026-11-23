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

    def test_projectiles_keep_individual_damage(self):
        game = Game()
        game.monsters.clear()
        monster = game.spawn(310, 10, 0)
        game.effects = [
            ("arrow", 0, 310, monster["y"]-20, 5, (1, 41)),
            ("bolt", 0, 310, monster["y"]-20, 5, (1, 58)),
        ]
        impacts = []
        game.hit = lambda target, power, facing: impacts.append((target["kind"], power, facing))
        game.effect_step()
        self.assertEqual(impacts, [(10, 41, 1), (10, 58, 1)])
