import math
import random
import constants
import events


class Tile(object):
    """
    A tile of the map and its properties
    """
    def __init__(self, name, blocked=False, opaque=False, explored=False):
        self.name = name
        self.blocked = blocked
        self.opaque = opaque
        self.explored = explored


class TileInfo(object):
    def __init__(self, x, y, tile):
        self.x = x
        self.y = y
        self.tile = tile


class Level(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [[Tile('wall', blocked=True, opaque=True)
                       for y in range(height)]
                      for x in range(width)]

    def __getitem__(self, key):
        x, y = key
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return Tile('wall', blocked=True, opaque=True)
        return self.tiles[x][y]

    def __setitem__(self, key, value):
        x, y = key
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise IndexError("Out of map bounds")
        self.tiles[x][y] = value

    def __contains__(self, xy):
        x, y = xy
        return 0 <= x < self.width and 0 <= y < self.height


class World(object):
    def __init__(self):
        self.player = None
        self.levels = [generate_level_cellular_automata()]


def lock_number(x, min_x, max_x):
    return min(max(x, min_x), max_x)


def dig_rect(level, x1, y1, x2, y2):
    x1 = lock_number(x1, 0, level.width - 1)
    x2 = lock_number(x2, 0, level.width - 1)
    y1 = lock_number(y1, 0, level.height - 1)
    y2 = lock_number(y2, 0, level.height - 1)
    for x in range(x1, x2 + 1):
        for y in range(y1, y2 + 1):
            dig(level, x, y)


def rotated90(vec):
    return (vec[1], -vec[0])


def rotated270(vec):
    return (-vec[1], vec[0])


def add(vec1, vec2):
    return (vec1[0] + vec2[0], vec1[1] + vec2[1])


def mul(vec, scalar):
    return tuple(i * scalar for i in vec)


def floors_in_or_by_rect(level, x1, y1, x2, y2):
    for x in range(x1 - 1, x2 + 2):
        for y in range(y1 - 1, y2 + 2):
            if level[x, y].name != 'wall':
                return True
    return False


def dig(level, x, y):
    level[x, y] = Tile('floor')
    events.events.handle_event(
        events.Event(
            events.EventType.TILE_REVEALED,
            TileInfo(x, y, level[x, y])))


def undig(level, x, y):
    level[x, y] = Tile('wall', blocked=True, opaque=True)
    events.events.handle_event(
        events.Event(
            events.EventType.TILE_REVEALED,
            TileInfo(x, y, level[x, y])))


def try_to_dig_room(level, entrance, direction, dim1=None, dim2=None):
    if dim1 is None:
        dim1 = random.randint(2, 5)
    if dim2 is None:
        dim2 = random.randint(2, 5)
    perp1 = rotated90(direction)
    perp2 = rotated270(direction)
    corner1 = add(add(entrance, direction), mul(perp1, dim2 // 2))
    corner2 = add(add(entrance, mul(direction, dim1)), mul(perp2,
                  math.ceil(dim2 / 2)))
    x1 = min(corner1[0], corner2[0])
    y1 = min(corner1[1], corner2[1])
    x2 = max(corner1[0], corner2[0])
    y2 = max(corner1[1], corner2[1])
    if (x1, y1) in level and (x2, y2) in level and \
            not floors_in_or_by_rect(level, x1, y1, x2, y2):
        dig_rect(level, x1, y1, x2, y2)
        return True
    return False


def try_to_dig_hallway(level, entrance, direction):
    return try_to_dig_room(level, entrance, direction, dim1=1)


def generate_level():
    width = constants.MAP_WIDTH
    height = constants.MAP_HEIGHT
    level = Level(width, height)
    # randomly place a room
    x = random.randint(2, width-3)
    y = random.randint(2, height-3)
    room_width = random.randint(2, 5)
    room_height = random.randint(2, 5)
    dig_rect(level, x - room_width//2, y - room_height//2,
             x + room_width//2, y + room_height//2)
    for i in range(3000):
        pos = (random.randint(0, width), random.randint(0, height))
        for direction in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            if level[add(pos, direction)].name == 'floor':
                direction = mul(direction, -1)
                if random.random() < 0.5 and \
                        try_to_dig_room(level, pos, direction) or \
                        try_to_dig_hallway(level, pos, direction):
                    dig(level, pos[0], pos[1])


def walls_a_tiles_away(level, x, y, a):
    # manhattan distance
    for x1 in range(x - a, x + a + 1):
        for y1 in (y - a, y + a):
            if level[x1, y1].blocked:
                yield (x1, y1)
    for y1 in range(y - a + 1, y + a):
        for x1 in (x - a, x + a):
            if level[x1, y1].blocked:
                yield (x1, y1)


def reachable_tiles(level, x, y):
    moves = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    return [(x1, y1) for (x1, y1) in (
                (x + m[0], y + m[1]) for m in moves)
            if not level[x1, y1].blocked]


def flood_fill(level, x, y):
    tiles_to_check = {(x, y)}
    checked_tiles = set()
    found_tiles = set()
    while tiles_to_check:
        tile = tiles_to_check.pop()
        checked_tiles.add(tile)
        if not level[tile].blocked:
            found_tiles.add(tile)
            tiles_to_check.update(
                tile for tile in reachable_tiles(level, tile[0], tile[1])
                if tile not in checked_tiles)
    return found_tiles


def generate_level_cellular_automata():
    width = constants.MAP_WIDTH
    height = constants.MAP_HEIGHT
    level = Level(width, height)
    # random initial distribution
    for x in range(level.width):
        for y in range(level.height):
            if random.randint(1, 100) < 45:
                dig(level, x, y)

    # now, apply CA
    for i in range(4):
        new_walls = [[len(list(walls_a_tiles_away(level, x, y, 1))) >= 5 or
                      len(list(walls_a_tiles_away(level, x, y, 3))) <= 1
                      for y in range(level.height)]
                     for x in range(level.width)]
        for x in range(level.width):
            for y in range(level.height):
                if new_walls[x][y]:
                    undig(level, x, y)
                else:
                    dig(level, x, y)

    # detect and delete floors outside of main cavern to prevent inaccessable
    # areas
    x = y = -1
    while level[x, y].blocked:
        x = random.randint(1, level.width - 1)
        y = random.randint(1, level.height - 1)
    tiles = flood_fill(level, x, y)

    if len(tiles) < .45 * level.width * level.height:
        # the cave generated was too small!
        # try again
        return generate_level_cellular_automata()

    for x in range(0, level.width):
        for y in range(0, level.height):
            if (x, y) not in tiles:
                undig(level, x, y)
    return level