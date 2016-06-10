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
        self.player_pos = Pos(0, 0)
        events.events.add_callback(events.EventType.MOVE,
                                   self.handle_move)

    def render(self, world):
        tcod.console_clear(self.map)
        self.draw_level(world.levels[world.player.dungeon_level])
        self.draw_mob(world.player)

        tcod.console_blit(self.map, 0, 0, MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT,
                          0, 0, 0)
        tcod.console_flush()

    def handle_move(self, event):
        if event.info.mob.info["name"] == 'player':
            self.player_pos = event.info.mob.pos
            self.player_moved = True

    def draw_level(self, level):
        for x in range(0, MAP_WINDOW_WIDTH):
            for y in range(0, MAP_WINDOW_HEIGHT):
                window_pos = Pos(x, y)
                map_pos = self.get_map_pos(window_pos)
                tile = level[map_pos]
                if tile.explored:
                    drawables[tile.name].draw(self.map, window_pos)
                    mob = level.get_mob(map_pos)
                    if mob:
                        drawables[mob.info['name']].draw(self.map, window_pos)

    def get_map_window_pos(self, map_pos):
        return map_pos - self.player_pos + \
            Pos(MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT) // 2

    def get_map_pos(self, world_pos):
        return world_pos + self.player_pos - \
            Pos(MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT) // 2

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
