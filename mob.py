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
