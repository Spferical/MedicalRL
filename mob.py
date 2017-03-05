from enum import Enum
import events
from vitals import Body


class MobState(Enum):
    WANDERING = 1
    IDLE = 2


class Mob(object):

    def __init__(self, pos, dlevel, info,
                 state=MobState.WANDERING, leader=None):
        """
        Creates a mob.
        pos: a tuple (x, y)
        info: a dict with monster-specific info like name, char, color, etc.
        state: MobState that indicates what the mob's current intention is
        target: pos the mob is trying to get to, if any
        leader: mob this mob is subordinate to
        """
        self.pos = pos
        self.dlevel = dlevel
        self.info = info
        self.state = state
        self.target = None
        self.leader = leader
        self.hp = self.info['hp']
        events.events.do_move_event(self, None)

    def move_to(self, pos):
        old_pos = self.pos
        self.pos = pos
        events.events.do_move_event(self, old_pos)


class Player(Mob):
    tiles_in_sight = set()

    def __init__(self, pos, dlevel, info):
        super().__init__(pos, dlevel, info)
        self.body = Body(info)

    def can_move(self, pos):
        return True

    def can_see(self, pos):
        return pos in self.tiles_in_sight
