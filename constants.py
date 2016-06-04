import tcod


# window dimensions
MAP_WINDOW_WIDTH = 40
MAP_WINDOW_HEIGHT = 40
SCREEN_WIDTH = MAP_WINDOW_WIDTH
SCREEN_HEIGHT = MAP_WINDOW_HEIGHT

MAP_WIDTH = 100
MAP_HEIGHT = 100

NUM_LEVELS = 27

DIRECTION_KEYS = {
    # arrow keys
    tcod.KEY_UP: (0, -1),
    tcod.KEY_DOWN: (0, 1),
    tcod.KEY_LEFT: (-1, 0),
    tcod.KEY_RIGHT: (1, 0),
    # numpad keys
    tcod.KEY_KP1: (-1, 1),
    tcod.KEY_KP2: (0, 1),
    tcod.KEY_KP3: (1, 1),
    tcod.KEY_KP4: (-1, 0),
    tcod.KEY_KP6: (1, 0),
    tcod.KEY_KP7: (-1, -1),
    tcod.KEY_KP8: (0, -1),
    tcod.KEY_KP9: (1, -1),
    # vi keys
    'h': (-1, 0),
    'j': (0, 1),
    'k': (0, -1),
    'l': (1, 0),
    'y': (-1, -1),
    'u': (1, -1),
    'b': (-1, 1),
    'n': (1, 1)
}
