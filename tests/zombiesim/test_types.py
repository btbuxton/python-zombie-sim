from unittest import TestCase
from zombiesim.types import Direction, Point


class DirectionTest(TestCase):

    def test_from_points(self):
        result = Direction.from_points(Point(0, 0), Point(1, 1))
        self.assertEqual(round(0.7, 1), round(result.x, 1))
        self.assertEqual(round(0.7, 1), round(result.y, 1))

    def test_reverse(self):
        result = Direction(1, -1).reverse()
        self.assertEqual(-1, result.x)
        self.assertEqual(1, result.y)
