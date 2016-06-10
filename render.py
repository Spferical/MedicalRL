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


class Renderer(object):
    """Renders everything."""
    def __init__(self):
        self.map = tcod.console_new(MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT)
        self.tile_data = {}
        self.mob_data = {}
        self.player_pos = Pos(0, 0)
        events.events.add_callback(events.EventType.TILE_REVEALED,
                                   self.handle_tile_reveal)
        events.events.add_callback(events.EventType.MOVE,
                                   self.handle_move)
        self.revealed_tiles = set()

    def render(self):
        tcod.console_blit(self.map, 0, 0, MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT,
                          0, 0, 0)
        tcod.console_flush()

    def handle_tile_reveal(self, event):
        pos = Pos(event.info.x, event.info.y)
        self.tile_data[pos] = event.info.tile
        self.draw_tile(pos, new=True)
        self.revealed_tiles.add(pos)

    def handle_move(self, event):
        self.mob_data[event.info.mob.pos] = event.info.mob
        if event.info.prev_pos:
            self.mob_data[event.info.prev_pos] = None
        if event.info.mob.info["name"] == 'player':
            self.player_pos = event.info.mob.pos
            self.redraw_tiles()
        self.draw_mob(event.info.mob)

    def redraw_tiles(self):
        for x in range(0, MAP_WINDOW_WIDTH):
            for y in range(0, MAP_WINDOW_HEIGHT):
                window_pos = Pos(x, y)
                map_pos = self.get_map_pos(window_pos)
                self.draw_tile(map_pos)

    def get_map_window_pos(self, map_pos):
        return map_pos - self.player_pos + \
            Pos(MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT) // 2

    def get_map_pos(self, world_pos):
        return world_pos + self.player_pos - \
            Pos(MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT) // 2

    def draw_tile(self, pos, new=False):
        tile = self.tile_data.get(pos, world.Tile('unknown'))
        window_pos = self.get_map_window_pos(pos)
        drawables[tile.name].draw(self.map, window_pos)
        if new:
            tcod.console_set_char_background(self.map, window_pos.x,
                                             window_pos.y, tcod.darkest_grey)
        if pos in self.revealed_tiles:
            mob = self.mob_data.get(pos, None)
            if mob:
                self.draw_mob(mob)

    def draw_mob(self, mob):
        window_pos = self.get_map_window_pos(mob.pos)
        drawables[mob.info['name']].draw(self.map, window_pos)


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
