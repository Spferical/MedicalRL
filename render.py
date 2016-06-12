import tcod
import time
from constants import MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT
import events
from util import Pos
import world


class Drawable(object):
    """Thing that can be drawn with libtcod."""
    def __init__(self, char, fg, bg=None):
        self.char = char
        self.fg = fg
        self.bg = bg

    def draw(self, con, pos, memory=False):
        if memory:
            draw_cell(con, pos, self.char, self.fg * .5,
                      self.bg * .5 if self.bg else None)
        else:
            draw_cell(con, pos, self.char, self.fg, self.bg)


class TileMemory(object):
    def __init__(self, tile_name, mob=None):
        self.tile_name = tile_name
        self.mob = mob


class Renderer(object):
    """Renders everything."""
    def __init__(self):
        self.map = tcod.console_new(MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT)
        self.player_pos = Pos(0, 0)
        events.events.add_callback(events.EventType.MOVE,
                                   self.handle_move)
        events.events.add_callback(events.EventType.TILE_REVEALED,
                                   self.handle_revealed)
        events.events.add_callback(events.EventType.TILE_HIDDEN,
                                   self.handle_hidden)
        self.memory = {}
        self.vision = set()

    def render(self):
        tcod.console_blit(self.map, 0, 0, MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT,
                          0, 0, 0)
        tcod.console_flush()

    def handle_move(self, event):
        memory = self.memory.get(event.info.prev_pos, None)
        if memory:
            memory.mob = None
        if event.info.prev_pos in self.vision:
            self.draw_tile(event.info.prev_pos)

        memory = self.memory.get(event.info.mob.pos, None)
        if memory:
            memory.mob = event.info.mob
        if event.info.mob.pos in self.vision:
            self.draw_tile(event.info.mob.pos)

        if event.info.mob.info["name"] == 'player':
            self.player_pos = event.info.mob.pos
            self.redraw_level()

    def handle_revealed(self, event):
        info = event.info
        self.vision.add(info.pos)
        self.memory[info.pos] = TileMemory(info.tile.name, info.mob)
        self.draw_tile(info.pos)
        window_pos = self.get_map_window_pos(info.pos)

    def handle_hidden(self, event):
        self.vision.remove(event.info.pos)
        self.draw_tile(event.info.pos)

    def redraw_level(self):
        tcod.console_clear(self.map)
        map_offset = self.get_map_pos(Pos(0, 0))
        for x in range(0, MAP_WINDOW_WIDTH):
            for y in range(0, MAP_WINDOW_HEIGHT):
                window_pos = Pos(x, y)
                map_pos = window_pos + map_offset
                self.draw_tile(map_pos, window_pos)

    def get_map_window_pos(self, map_pos):
        return map_pos - self.player_pos + \
            Pos(MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT) // 2

    def get_map_pos(self, world_pos):
        return world_pos + self.player_pos - \
            Pos(MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT) // 2

    def draw_mob(self, mob):
        window_pos = self.get_map_window_pos(mob.pos)
        drawables[mob.info['name']].draw(self.map, window_pos)

    def draw_tile(self, map_pos, window_pos=None):
        memory = self.memory.get(map_pos, None)
        if memory:
            if window_pos is None:
                window_pos = self.get_map_window_pos(map_pos)

            tile_drawable = drawables[memory.tile_name]
            mob_drawable = drawables[memory.mob.info['name']] if memory.mob \
                else None

            visible = map_pos in self.vision

            tile_drawable.draw(self.map, window_pos, not visible)
            if mob_drawable:
                mob_drawable.draw(self.map, window_pos, not visible)


def create_drawable_from_json(info):
    return Drawable(info["char"], getattr(tcod, info["color"]))


def draw_cell(con, pos, char, fg, bg=None):
    x, y = pos
    if bg:
        tcod.console_set_char_background(con, x, y, bg)
    tcod.console_set_char_foreground(con, x, y, fg)
    tcod.console_set_char(con, x, y, char)


drawables = {
    "player": Drawable('@', tcod.white),
    "wall": Drawable('#', tcod.white, bg=tcod.black),
    "floor": Drawable('.', tcod.white, bg=tcod.black),
    "up stairs": Drawable('<', tcod.white, bg=tcod.black),
    "down stairs": Drawable('>', tcod.white, bg=tcod.black),
    "unknown": Drawable(' ', tcod.white, bg=tcod.black)
}

drawables["player"] = create_drawable_from_json(world.data["player"])
for mob in world.data["mobs"]:
    drawables[mob["name"]] = create_drawable_from_json(mob)
