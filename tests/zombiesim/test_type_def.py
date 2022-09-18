from unittest import TestCase
from zombiesim.type_def import Direction, Point


class DirectionTest(TestCase):

    def test_from_points(self):
        result = Direction.from_points(Point(0, 0), Point(1, 1))
        self.assertEqual(round(0.7, 1), round(result.x, 1))
        self.assertEqual(round(0.7, 1), round(result.y, 1))

    def test_reverse(self):
        result = -Direction(1, -1)
        self.assertEqual(-1, result.x)
        self.assertEqual(1, result.y)

class PointTest(TestCase):
    def test_distance(self):
        self.assertEqual(3, Point(0, 0).distance(Point(3, 0)))
        self.assertEqual(2, Point(1, 1).distance(Point(1, 3)))

    def test_add_points(self):
        result = Point(1, 1) + Point(3, 4)
        self.assertEqual(Point(4, 5), result)

    def test_diff_points(self):
        result = Point(1, 1) - Point(3, 4)
        self.assertEqual(Point(-2, -3), result)
