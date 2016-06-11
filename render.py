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

    def draw(self, con, pos):
        x, y = pos.x, pos.y
        if self.bg:
            tcod.console_set_char_background(con, x, y, self.bg)
        tcod.console_set_char_foreground(con, x, y, self.fg)
        tcod.console_set_char(con, x, y, self.char)


class TileMemory(object):
    def __init__(self, tile_name, mob=None):
        print(mob)
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
        if event.info.mob.info["name"] == 'player':
            self.player_pos = event.info.mob.pos

        memory = self.memory.get(event.info.prev_pos, None)
        if memory:
            memory.mob = None

        memory = self.memory.get(event.info.mob.pos, None)
        if memory:
            memory.mob = event.info.mob

        self.redraw_level()

    def handle_revealed(self, event):
        info = event.info
        self.vision.add(info.pos)
        self.memory[info.pos] = TileMemory(info.tile.name, info.mob)
        self.draw_tile(info.pos)

    def handle_hidden(self, event):
        self.vision.remove(event.info.pos)

    def redraw_level(self):
        tcod.console_clear(self.map)
        for x in range(0, MAP_WINDOW_WIDTH):
            for y in range(0, MAP_WINDOW_HEIGHT):
                window_pos = Pos(x, y)
                map_pos = self.get_map_pos(window_pos)
                if map_pos in self.memory:
                    memory = self.memory[map_pos]
                    drawables[memory.tile_name].draw(self.map, window_pos)
                    if memory.mob and map_pos in self.vision:
                        drawables[memory.mob.info['name']].draw(self.map,
                                                                window_pos)

    def get_map_window_pos(self, map_pos):
        return map_pos - self.player_pos + \
            Pos(MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT) // 2

    def get_map_pos(self, world_pos):
        return world_pos + self.player_pos - \
            Pos(MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT) // 2

    def draw_mob(self, mob):
        window_pos = self.get_map_window_pos(mob.pos)
        drawables[mob.info['name']].draw(self.map, window_pos)

    def draw_tile(self, map_pos):
        if map_pos in self.memory:
            memory = self.memory[map_pos]
            window_pos = self.get_map_window_pos(map_pos)
            drawables[memory.tile_name].draw(self.map, window_pos)


def create_drawable_from_json(info):
    return Drawable(info["char"], getattr(tcod, info["color"]))


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
