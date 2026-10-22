"""
Pruebas de las funciones de colisión por distancia (game/systems/collisions.py).

No abren ninguna ventana: usan objetos simples con x, y y radius.
"""

import unittest
from types import SimpleNamespace

from game.systems.collisions import circles_overlap, distance, is_within, point_distance


def circle(x, y, radius=0):
    """Crea un objeto con x, y y radius, como las entidades del juego."""
    return SimpleNamespace(x=x, y=y, radius=radius)


class PointDistanceTest(unittest.TestCase):

    def test_3_4_5_triangle(self):
        self.assertEqual(point_distance(0, 0, 3, 4), 5)

    def test_same_point(self):
        self.assertEqual(point_distance(7, -2, 7, -2), 0)

    def test_order_does_not_matter(self):
        self.assertEqual(point_distance(1, 2, 10, 14), point_distance(10, 14, 1, 2))


class DistanceTest(unittest.TestCase):

    def test_distance_between_objects(self):
        self.assertEqual(distance(circle(0, 0), circle(6, 8)), 10)


class IsWithinTest(unittest.TestCase):

    def test_inside_reach(self):
        self.assertTrue(is_within(circle(0, 0), circle(3, 4), 6))

    def test_exact_edge_does_not_count(self):
        # La comparación es "menor que", igual que en el juego.
        self.assertFalse(is_within(circle(0, 0), circle(3, 4), 5))

    def test_outside_reach(self):
        self.assertFalse(is_within(circle(0, 0), circle(30, 40), 10))


class CirclesOverlapTest(unittest.TestCase):

    def test_touching_circles(self):
        self.assertTrue(circles_overlap(circle(0, 0, 10), circle(15, 0, 10)))

    def test_separate_circles(self):
        self.assertFalse(circles_overlap(circle(0, 0, 10), circle(25, 0, 10)))

    def test_circles_barely_touching(self):
        # Distancia 20 = suma de radios: todavía no chocan.
        self.assertFalse(circles_overlap(circle(0, 0, 10), circle(20, 0, 10)))

    def test_circle_inside_another(self):
        self.assertTrue(circles_overlap(circle(0, 0, 50), circle(5, 5, 2)))


if __name__ == '__main__':
    unittest.main()
