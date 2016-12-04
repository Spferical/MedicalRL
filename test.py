import unittest
from mob import Mob
from util import Pos
from world import mobinfo, Level, World


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

    def test_as_tuple(self):
        x, y = Pos(1, 2)
        self.assertEquals(x, 1)
        self.assertEquals(y, 2)
        self.assertEquals(Pos(1, 2), (1, 2))


class WorldTest(unittest.TestCase):
    def test_out_of_bounds(self):
        level = Level(100, 100)

        self.assertNotIn((100, 100), level)
        self.assertNotIn((-1, -1), level)
        self.assertIn((50, 50), level)

        self.assertEquals(level[(-1, -1)].name, 'stone wall')
        self.assertTrue(level[(-1, -1)].blocked)
        self.assertTrue(level[(-1, -1)].opaque)
        self.assertFalse(level[(-1, -1)].explored)

        self.assertEquals(level[(101, 101)].name, 'stone wall')
        self.assertTrue(level[(101, 101)].blocked)
        self.assertTrue(level[(101, 101)].opaque)
        self.assertFalse(level[(101, 101)].explored)

    def test_mobs(self):
        level = Level(25, 25)
        level.up_stairs_pos = Pos(1, 1)
        world = World([level])

        mob = level.mobs[2, 2] = Mob(Pos(2, 2), 0, mobinfo['orc'])
        mob.move_to(Pos(3, 3))
        self.assertNotIn((2, 2), level.mobs)
        self.assertEquals(mob, level.mobs.get((3, 3)))

        self.assertEquals(level.mobs.get(world.levels[0].up_stairs_pos),
                          world.player)
