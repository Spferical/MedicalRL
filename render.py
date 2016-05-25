import tcod
import time
from constants import MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT
import events


class Drawable(object):
    """Thing that can be drawn with libtcod."""
    def __init__(self, char, fg, bg=None):
        self.char = char
        self.fg = fg
        self.bg = bg

    def draw(self, con, x, y):
        if self.bg:
            tcod.console_set_char_background(con, x, y, self.bg)
        tcod.console_set_char_foreground(con, x, y, self.fg)
        tcod.console_set_char(con, x, y, self.char)


class Renderer(object):
    """Renders everything."""
    def __init__(self):
        self.map = tcod.console_new(MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT)
        events.events.add_callback(events.EventType.TILE_REVEALED,
                                   self.handle_tile_reveal)

    def render(self):
        tcod.console_blit(self.map, 0, 0, MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT,
                          0, 0, 0)
        tcod.console_flush()

    def handle_tile_reveal(self, event):
        (x, y) = event.entity.x, event.entity.y
        drawables[event.entity.tile.name].draw(self.map, x, y)


drawables = {
    "player": Drawable('@', tcod.white),
    "wall": Drawable('#', tcod.white),
    "floor": Drawable('.', tcod.white),
}
