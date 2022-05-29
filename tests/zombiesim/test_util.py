"""
Created on Dec 7, 2014

@author: bbuxton
"""

import unittest

from zombiesim.util import distance, dir_to, opposite_dir, xfrange, \
    add_points, diff_points


class UtilTest((unittest.TestCase)):
    def test_distance(self):
        self.assertEqual(3, distance((0, 0), (3, 0)))
        self.assertEqual(2, distance((1, 1), (1, 3)))

    def test_dir_to(self):
        result = dir_to((0, 0), (1, 1))
        self.assertEqual(round(0.7, 1), round(result[0], 1))
        self.assertEqual(round(0.7, 1), round(result[1], 1))

    def test_opposite_dir(self):
        result = opposite_dir((1, -1))
        self.assertEqual(-1, result[0])
        self.assertEqual(1, result[1])

    def test_xfrange(self):
        result = xfrange(0, 1.0, 0.5)
        self.assertEqual(round(0, 1), round(next(result), 1))
        self.assertEqual(round(0.5, 1), round(next(result), 1))
        self.assertRaises(StopIteration, next, result)

    def test_add_points(self):
        result = add_points((1, 1), (3, 4))
        self.assertEqual((4, 5), result)

    def test_diff_points(self):
        result = diff_points((1, 1), (3, 4))
        self.assertEqual((-2, -3), result)
