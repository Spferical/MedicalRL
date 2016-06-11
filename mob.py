import events
import render


class Mob(object):
    def __init__(self, pos, info):
        """
        Creates a mob.
        pos: a tuple (x, y)
        info: a dict with monster-specific info like name, char, color, etc.
        """
        self.pos = pos
        self.info = info
        events.events.do_move_event(self, None)


class Player(Mob):
    dungeon_level = 0
    tiles_in_sight = set()

    def can_see(self, pos):
        return pos in self.tiles_in_sight
