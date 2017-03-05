import tcod
from util import Pos

DEBUG = True

# window dimensions
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 40

MAP_WIDTH = 200
MAP_HEIGHT = 200

NUM_LEVELS = 27

DIRECTION_KEYS = {
    # arrow keys
    tcod.KEY_UP: Pos(0, -1),
    tcod.KEY_DOWN: Pos(0, 1),
    tcod.KEY_LEFT: Pos(-1, 0),
    tcod.KEY_RIGHT: Pos(1, 0),
    # numpad keys
    tcod.KEY_KP1: Pos(-1, 1),
    tcod.KEY_KP2: Pos(0, 1),
    tcod.KEY_KP3: Pos(1, 1),
    tcod.KEY_KP4: Pos(-1, 0),
    tcod.KEY_KP6: Pos(1, 0),
    tcod.KEY_KP7: Pos(-1, -1),
    tcod.KEY_KP8: Pos(0, -1),
    tcod.KEY_KP9: Pos(1, -1),
    # vi keys
    'h': Pos(-1, 0),
    'j': Pos(0, 1),
    'k': Pos(0, -1),
    'l': Pos(1, 0),
    'y': Pos(-1, -1),
    'u': Pos(1, -1),
    'b': Pos(-1, 1),
    'n': Pos(1, 1)
}

DIRECTIONS = set(DIRECTION_KEYS.values())

FOV_RADIUS = 40
