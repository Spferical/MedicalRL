import unittest
from util import Pos


class TestPos(unittest.TestCase):
    def test_constructor(self):
        self.assertEqual(Pos(1, 2), Pos((1, 2)))
        self.assertEqual(Pos(100, 5), Pos((100, 5)))

    def test_add(self):
        self.assertEqual(Pos(1, 2) + Pos(3, 4), Pos(4, 6))
        self.assertEqual(Pos(-5, -1) + Pos(3, 4), Pos(-2, 3))

    def test_sub(self):
        self.assertEqual(Pos(1, 2) - Pos(1, 2), Pos(0, 0))
        self.assertEqual(Pos(5, 5) - Pos(1, 2), Pos(4, 3))
        self.assertEqual(Pos(5, 5) - Pos(6, 6), Pos(-1, -1))

    def test_abs(self):
        self.assertEqual(abs(Pos(1, 2)), 3)
        self.assertEqual(abs(Pos(3, 4)), 7)
        self.assertEqual(abs(Pos(-3, 4)), 7)

    def test_mul(self):
        self.assertEqual(Pos(1, 2) * 3, Pos(3, 6))
        self.assertEqual(Pos(-1, 2) * 3, Pos(-3, 6))

    def test_floordiv(self):
        self.assertEqual(Pos(1, 2) // 2, Pos(0, 1))
        self.assertEqual(Pos(5, 20) // 3, Pos(1, 6))

    def test_repr(self):
        self.assertEqual(repr(Pos(1, 2)), "Pos(1, 2)")
        self.assertEqual(repr(Pos(-20, 2)), "Pos(-20, 2)")

    def test_len(self):
        self.assertEqual(len(Pos(1, 2)), 2)
        self.assertEqual(len(Pos(-1000, 81314)), 2)

    def test_distance(self):
        self.assertEqual(Pos(1, 2).distance(Pos(2, 2)), 1)
        self.assertEqual(Pos(0, 0).distance(Pos(-2, -2)), 4)
