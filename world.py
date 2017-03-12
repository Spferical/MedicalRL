import json
from enum import Enum
import math
import random
import constants
import events
import fov
import mob
from util import Pos


with open("data.json") as data:
    data = json.load(data)
    mobinfo = data['mobs']
    objinfo = data['objects']
    player_info = data['player']
    factions = data['factions']


class Tile(object):
    """
    A tile of the map and its properties
    """

    def __init__(self, name, blocked=False, opaque=False, explored=False,
                 room_id=0):
        self.name = name
        self.blocked = blocked
        self.opaque = opaque
        self.explored = explored
        self.room_id = room_id


class TileInfo(object):

    def __init__(self, pos, tile, mob=None, item=None):
        self.pos = Pos(pos)
        self.tile = tile
        self.mob = mob
        self.item = item


class Interactions(Enum):
    NONE = 0
    OPEN_DOOR = 1
    PREGNANCY_TEST = 2
    EAT = 3
    OPEN_CONTAINER = 4


class Object(object):

    def __init__(self, pos, name, passable=True, opaque=False,
                 interaction=Interactions.NONE, pickup=False,
                 consumed_on_use=False, food_info=None):
        """
        pos: a tuple (x, y)
        passable: whether the player can move into the same square as this item
        interaction: enum representing what the player can do with this item
        pickup: whether the player can pick up this item
        """
        self.pos = Pos(pos)
        self.name = name
        self.is_passable = passable
        self.opaque = opaque
        self.interaction = interaction
        self.pickup = pickup
        self.consumed_on_use = consumed_on_use
        self.food_info = food_info
        self.contents = []
        events.events.send(events.Event(events.EventType.BIRTH, self))


class Level(object):

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [[Tile('hospital wall', blocked=True, opaque=True)
                       for y in range(height)]
                      for x in range(width)]
        self.up_stairs_pos = self.down_stairs_pos = None
        self.mobs = {}
        self.rooms = ['']
        self.objects = {}

    def move_mob(self, from_pos, to_pos):
        if from_pos in self.mobs:
            self.mobs[to_pos] = self.mobs.pop(from_pos)

    def add_room(self, room_name):
        self.rooms.append(room_name)
        return len(self.rooms) - 1

    def get_mob(self, pos):
        return self.mobs.get(pos, None)

    def pop_object(self, pos):
        obj = self.objects.pop(pos)
        events.events.send(events.Event(events.EventType.REMOVAL,
                                        obj))
        return obj

    def get_object(self, pos):
        return self.objects.get(pos, None)

    def is_blocked(self, pos):
        return self[pos].blocked or pos in self.mobs or \
            (pos in self.objects and not self.objects[pos].is_passable)

    def is_opaque(self, pos):
        return self[pos].opaque \
                or pos in self.objects and self.objects[pos].opaque

    def __getitem__(self, key):
        x, y = key
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return Tile('hospital wall', blocked=True, opaque=True)
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
    """
    Singleton to store all terrain and mobs.
    """

    def __init__(self, levels):
        self.levels = levels
        self.player = mob.Player(levels[0].up_stairs_pos, 0, player_info)
        self.levels[0].mobs[levels[0].up_stairs_pos] = self.player
        events.events.add_callback(
            events.EventType.MOVE, self.handle_move_event, priority=2)

    def handle_move_event(self, event):
        prev_pos = event.info.prev_pos
        mob = event.info.mob
        self.levels[mob.dlevel].move_mob(prev_pos, mob.pos)

    def __del__(self):
        events.events.remove_callback(
            events.EventType.MOVE, self.handle_move_event)


def generate_world():
    levels = [generate_hospital()]
    return World(levels)


def populate_level(num, level):
    # generate a few groups of mobs
    for i in range(10):
        faction = random.choice(list(factions.keys()))
        groups = factions[faction]['groups']
        group = random.choice(groups)

        # spawn leader at pos, spawn rest of mobs within fov
        leader_info = mobinfo[group[0]]
        leader_pos = get_random_passable_position(level)
        leader = level.mobs[leader_pos] = mob.Mob(leader_pos, num, leader_info)
        tiles_in_sight = list(filter(lambda pos: not level.is_blocked(pos),
                                     fov.calculate_fov(leader_pos, 5, level)))
        for mob_type in group[1:]:
            info = mobinfo[mob_type]
            pos = random.choice(tiles_in_sight)
            tiles_in_sight.remove(pos)
            level.mobs[pos] = mob.Mob(pos, num, info, leader=leader)


def lock_number(x, min_x, max_x):
    return min(max(x, min_x), max_x)


def dig_rect(level, rect, room_id=0):
    x1 = lock_number(rect.left, 0, level.width - 1)
    x2 = lock_number(rect.right, 0, level.width - 1)
    y1 = lock_number(rect.top, 0, level.height - 1)
    y2 = lock_number(rect.bottom, 0, level.height - 1)
    for x in range(x1, x2 + 1):
        for y in range(y1, y2 + 1):
            dig(level, x, y, room_id=room_id)


def rotated90(vec):
    return Pos(vec[1], -vec[0])


def rotated270(vec):
    return Pos(-vec[1], vec[0])


def add(vec1, vec2):
    return (vec1[0] + vec2[0], vec1[1] + vec2[1])


def mul(vec, scalar):
    return tuple(i * scalar for i in vec)


def floors_in_or_by_rect(level, rect):
    for x in range(rect.left - 1, rect.right + 2):
        for y in range(rect.top - 1, rect.bottom + 2):
            if level[x, y].name != 'hospital wall':
                return True
    return False


def reveal_tile(level, pos):
    events.events.handle_event(
        events.Event(
            events.EventType.TILE_REVEALED,
            TileInfo(pos,
                     level[pos],
                     level.get_mob(pos),
                     level.get_object(pos))))


def dig(level, x, y, room_id=0):
    level[x, y] = Tile('tile floor', room_id=room_id)


def undig(level, x, y):
    level[x, y] = Tile('hospital wall', blocked=True, opaque=True)


class Rect(object):
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom


def rect_in_level(level, rect):
    return (rect.left, rect.top) in level \
            and (rect.right, rect.bottom) in level


def try_to_dig_room(level, entrance, direction, dim1=None, dim2=None,
                    name=None):
    if dim1 is None:
        dim1 = random.randint(2, 5)
    if dim2 is None:
        dim2 = random.randint(2, 5)
    perp1 = rotated90(direction)
    perp2 = rotated270(direction)
    corner1 = add(add(entrance, direction), mul(perp1, dim2 // 2))
    corner2 = add(
            add(entrance, mul(direction, dim1)),
            mul(perp2, math.ceil(dim2 / 2)))
    x1 = min(corner1[0], corner2[0])
    y1 = min(corner1[1], corner2[1])
    x2 = max(corner1[0], corner2[0])
    y2 = max(corner1[1], corner2[1])
    rect = Rect(x1, y1, x2, y2)
    if rect_in_level(level, rect) and \
            not floors_in_or_by_rect(level, rect):
        room_id = level.add_room(name) if name is not None else 0
        dig_rect(level, rect, room_id=room_id)
        return rect
    return None


def try_to_dig_hallway(level, entrance, direction):
    return try_to_dig_room(level, entrance, direction, dim1=1)


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


def get_random_passable_position(level):
    pos = Pos(-1, -1)
    while level.is_blocked(pos):
        x = random.randint(1, level.width - 1)
        y = random.randint(1, level.height - 1)
        pos = Pos(x, y)
    return pos


def filled_a_tiles_away(grid, x, y, a, outside_filled=False):
    def outside(x, y):
        return not 0 <= x < len(grid) or not 0 <= y < len(grid[0])
    # manhattan distance
    for x1 in range(x - a, x + a + 1):
        for y1 in (y - a, y + a):
            if outside(x1, y1):
                if outside_filled:
                    yield(x1, y1)
            elif grid[x1][y1]:
                yield (x1, y1)
    for y1 in range(y - a + 1, y + a):
        for x1 in (x - a, x + a):
            if outside(x1, y1):
                if outside_filled:
                    yield(x1, y1)
            elif grid[x1][y1]:
                yield (x1, y1)


def create_object(pos, name):
    assert name in objinfo
    json = objinfo[name]
    default = objinfo['default']
    return Object(pos, name,
                  json.get("passable", default['passable']),
                  json.get("opaque", default['opaque']),
                  getattr(Interactions,
                          json.get("interaction", default['interaction'])),
                  json.get("pickup", default['pickup']),
                  json.get("consumed_on_use", default['consumed_on_use']),
                  json.get("food_info", default['food_info']))


def try_to_dig_hospital_room(level, entrance, direction):
    rect = try_to_dig_room(level, entrance, direction, 3, 3,
                           name='hospital room')
    if rect:
        # room was successfully dug
        # add the door
        dig(level, entrance.x, entrance.y)
        level.objects[entrance] = create_object(entrance, "closed door")

        # stick a bed across from the entrance
        corners = (Pos(rect.left, rect.top), Pos(rect.right, rect.bottom))
        bed_corner = max(corners, key=lambda pos: entrance.distance(pos))
        level.objects[bed_corner] = Object(bed_corner, 'bed', passable=False)

        # populate the room with items
        for i in range(3):
            x = random.randint(rect.left, rect.right)
            y = random.randint(rect.top, rect.bottom)
            pos = Pos(x, y)
            if not level.get_object(pos):
                name = random.choice(
                    ("banana", "pregnancy test", "cabinet"))
                item = create_object(pos, name)
                if name == 'cabinet':
                    item.contents.append(
                        create_object(pos, "banana"))
                level.objects[pos] = item


def generate_hospital():
    width = constants.MAP_WIDTH
    height = constants.MAP_HEIGHT
    level = Level(width, height)

    # dig a long corridor
    pos = Pos(width // 2, height // 2)
    direction = Pos(1, 0)
    walls = []
    for i in range(12):
        direction = random.choice((
            rotated90(direction), rotated270(direction)))
        right = rotated90(direction)
        left = rotated270(direction)
        for num in range(random.randint(10, 15)):
            pos += direction
            pos2 = pos + right
            dig(level, pos.x, pos.y)
            dig(level, pos2.x, pos2.y)
            walls.append((pos + left, left))
            walls.append((pos + right * 2, right))
        pos -= direction

    # go through walls next to corridor and try to dig rooms from them
    while walls:
        wall, direction = walls.pop()
        try_to_dig_hospital_room(level, wall, direction)

    # up stairs
    x, y = get_random_passable_position(level)
    level.up_stairs_pos = Pos(x, y)

    return level
