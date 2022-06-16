"""
Created on Dec 7, 2014

@author: bbuxton
"""

import unittest
from zombiesim.types import Point

from zombiesim.util import distance, xfrange, add_points, diff_points


class UtilTest((unittest.TestCase)):
    def test_distance(self):
        self.assertEqual(3, distance(Point(0, 0), Point(3, 0)))
        self.assertEqual(2, distance(Point(1, 1), Point(1, 3)))

    def test_xfrange(self):
        result = xfrange(0, 1.0, 0.5)
        self.assertEqual(round(0, 1), round(next(result), 1))
        self.assertEqual(round(0.5, 1), round(next(result), 1))
        self.assertRaises(StopIteration, next, result)

    def test_add_points(self):
        result = add_points(Point(1, 1), Point(3, 4))
        self.assertEqual(Point(4, 5), result)

    def test_diff_points(self):
        result = diff_points(Point(1, 1), Point(3, 4))
        self.assertEqual(Point(-2, -3), result)
