"""
Created on Dec 7, 2014

@author: bbuxton
"""

import unittest
from zombiesim.types import Point

from zombiesim.util import xfrange


class UtilTest((unittest.TestCase)):


    def test_xfrange(self):
        result = xfrange(0, 1.0, 0.5)
        self.assertEqual(round(0, 1), round(next(result), 1))
        self.assertEqual(round(0.5, 1), round(next(result), 1))
        self.assertRaises(StopIteration, next, result)

