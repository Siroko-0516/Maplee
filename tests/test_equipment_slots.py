import unittest

from maplee.engine import Game


class EquipmentMigrationTest(unittest.TestCase):
    def test_old_hat_and_ring_keep_their_stats_and_new_slots(self):
        saved = {"level": 4, "bag": {"twig": 1, "cap": 1, "dew": 1},
                 "equipment": {"weapon": "twig", "armor": "cap", "charm": "dew"}}
        game = Game(saved)
        self.assertEqual(game.p["equipment"]["head"], "cap")
        self.assertEqual(game.p["equipment"]["ring"], "dew")
        self.assertIsNone(game.p["equipment"]["armor"])
        self.assertEqual(Game(game.p).stats(), game.stats())
