"""
Pruebas de las reglas de las noches (game/systems/levels.py): metas,
dificultad y multiplicador de entrega.

No abren ninguna ventana: LevelManager no usa Kivy.
"""

import unittest

from game.config import BAT_BASE_SPEED, BAT_MAX_SPEED_FACTOR
from game.systems.levels import LevelManager, delivery_multiplier


class GoalTest(unittest.TestCase):

    def test_goal_for_each_night(self):
        self.assertEqual(LevelManager.goal_for(1), 10)
        self.assertEqual(LevelManager.goal_for(2), 15)
        self.assertEqual(LevelManager.goal_for(3), 20)
        self.assertEqual(LevelManager.goal_for(10), 55)

    def test_game_starts_on_night_1(self):
        levels = LevelManager()
        self.assertEqual(levels.night, 1)
        self.assertEqual(levels.goal, 10)


class DifficultyTest(unittest.TestCase):

    def setUp(self):
        self.levels = LevelManager()

    def test_bats_per_night(self):
        self.assertEqual(self.levels.bat_count, 2)
        self.levels.next_night()
        self.assertEqual(self.levels.bat_count, 3)

    def test_bats_get_faster(self):
        first = self.levels.bat_speed
        self.assertEqual(first, BAT_BASE_SPEED)
        self.levels.next_night()
        self.assertGreater(self.levels.bat_speed, first)

    def test_speed_has_a_cap(self):
        self.levels.night = 100
        self.assertAlmostEqual(self.levels.bat_speed, BAT_BASE_SPEED * BAT_MAX_SPEED_FACTOR)

    def test_fleeting_from_night_4(self):
        for night, expected in ((1, False), (3, False), (4, True), (7, True)):
            self.levels.night = night
            self.assertEqual(self.levels.allows_fleeting, expected, f'noche {night}')

    def test_max_free_fireflies(self):
        self.assertEqual(self.levels.max_free_fireflies, 8)
        self.levels.night = 50
        self.assertEqual(self.levels.max_free_fireflies, 14)


class DeliveryTest(unittest.TestCase):

    def test_reaching_the_goal(self):
        levels = LevelManager()
        self.assertFalse(levels.register_delivery(4))
        self.assertTrue(levels.register_delivery(6))  # 4 + 6 = 10 = meta
        self.assertEqual(levels.delivered_total, 10)

    def test_next_night_resets_count(self):
        levels = LevelManager()
        levels.register_delivery(10)
        levels.next_night()
        self.assertEqual(levels.night, 2)
        self.assertEqual(levels.delivered_tonight, 0)
        self.assertEqual(levels.delivered_total, 10)  # el total se mantiene

    def test_reset_goes_back_to_start(self):
        levels = LevelManager()
        levels.register_delivery(12)
        levels.next_night()
        levels.reset()
        self.assertEqual((levels.night, levels.delivered_tonight, levels.delivered_total),
                         (1, 0, 0))


class MultiplierTest(unittest.TestCase):

    def test_multipliers(self):
        self.assertEqual(delivery_multiplier(1), 1)
        self.assertEqual(delivery_multiplier(4), 1)
        self.assertEqual(delivery_multiplier(5), 2)
        self.assertEqual(delivery_multiplier(9), 2)
        self.assertEqual(delivery_multiplier(10), 3)
        self.assertEqual(delivery_multiplier(15), 3)


if __name__ == '__main__':
    unittest.main()
