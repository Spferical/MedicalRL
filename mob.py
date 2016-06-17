from enum import Enum
import events


class MobState(Enum):
    WANDERING = 1
    IDLE = 2


class Mob(object):
    def __init__(self, pos, info, state=MobState.WANDERING):
        """
        Creates a mob.
        pos: a tuple (x, y)
        info: a dict with monster-specific info like name, char, color, etc.
        """
        self.pos = pos
        self.info = info
        self.state = state
        self.wander_destination = None
        events.events.do_move_event(self, None)

    def move_to(self, pos):
        old_pos = self.pos
        self.pos = pos
        events.events.do_move_event(self, old_pos)


class Player(Mob):
    dungeon_level = 0
    tiles_in_sight = set()

    def can_see(self, pos):
        return pos in self.tiles_in_sight
