from enum import Enum
import tcod
from constants import MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT, DIRECTION_KEYS, \
    MESSAGE_WINDOW_WIDTH, MESSAGE_WINDOW_HEIGHT
import events
from mob import MobState
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


class States(Enum):
    DEFAULT = 1
    EXAMINE = 2


MOB_STATE_DESCRIPTIONS = {
    MobState.WANDERING: 'wandering',
    MobState.IDLE: 'idle',
}


def get_article(word):
    return 'an' if word[0] in 'aeiou' else 'a'


class UI(object):
    """Handles rendering and input."""
    state = States.DEFAULT

    def __init__(self):
        self.map = tcod.console_new(MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT)
        self.messages_window = tcod.console_new(
            MESSAGE_WINDOW_WIDTH, MESSAGE_WINDOW_HEIGHT)
        self.center_pos = Pos(0, 0)
        events.events.add_callback(events.EventType.MOVE,
                                   self.handle_move)
        events.events.add_callback(events.EventType.TILE_REVEALED,
                                   self.handle_revealed)
        events.events.add_callback(events.EventType.TILE_HIDDEN,
                                   self.handle_hidden)
        self.memory = {}
        self.vision = set()
        self.message_lines = []

    def handle_input(self, game):
        """Returns true if an action was taken."""
        key = tcod.Key()
        mouse = tcod.Mouse()
        tcod.sys_check_for_event(tcod.EVENT_KEY_PRESS | tcod.EVENT_MOUSE,
                                 key, mouse)
        if key.c:
            char = chr(key.c)
            if self.state == States.DEFAULT:
                if char in DIRECTION_KEYS:
                    return game.attempt_player_move(DIRECTION_KEYS[char])
                elif char == 'x':
                    self.state = States.EXAMINE
                    self.center_pos = game.world.player.pos
                    self.draw_cursor(self.center_pos)
                elif char == '.':
                    return True
            elif self.state == States.EXAMINE:
                if char in DIRECTION_KEYS:
                    self.move_examine(DIRECTION_KEYS[char])
                    self.draw_cursor(self.center_pos)
                elif key.vk == tcod.KEY_ESCAPE:
                    self.state = States.DEFAULT
                    self.center_pos = game.world.player.pos
                    self.redraw_level()

    def message(self, message, color=tcod.white):
        self.message_lines.append((message, color))
        if len(self.message_lines) > MESSAGE_WINDOW_HEIGHT:
            self.message_lines.pop(0)
        self.draw_messages()

    def draw_messages(self):
        tcod.console_clear(self.messages_window)
        y = 0
        for (line, color) in self.message_lines:
            tcod.console_set_default_foreground(self.messages_window, color)
            tcod.console_print(self.messages_window, 0, y, line)
            y += 1

    def move_examine(self, direction):
        self.center_pos += direction
        self.redraw_level()
        memory = self.memory.get(self.center_pos, None)
        seen = self.center_pos in self.vision
        if memory:
            start = "You see " if seen else "You remember "
            if memory.mob:
                name = memory.mob.info['name']
                state = MOB_STATE_DESCRIPTIONS[memory.mob.state] + ' ' \
                    if memory.mob.state in MOB_STATE_DESCRIPTIONS else ''
                article = get_article(state if state else name)
                self.message(start + article + ' ' + state + name + '.',
                             tcod.light_grey)
            else:
                self.message(start + memory.tile_name + '.', tcod.light_grey)
        else:
            self.message("You cannot see that location.", tcod.light_grey)

    def draw_cursor(self, map_pos):
        x, y = self.get_map_window_pos(map_pos)
        tcod.console_set_char_background(self.map, x, y, tcod.light_grey)

    def render(self):
        tcod.console_blit(self.map, 0, 0, MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT,
                          0, 0, 0)
        tcod.console_blit(self.messages_window, 0, 0,
                          MESSAGE_WINDOW_WIDTH, MESSAGE_WINDOW_HEIGHT,
                          0, MESSAGE_WINDOW_WIDTH, 0)
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

        if event.info.mob.info["name"] == 'player' \
                and self.state == States.DEFAULT:
            self.center_pos = event.info.mob.pos
            self.redraw_level()

    def handle_revealed(self, event):
        info = event.info
        self.vision.add(info.pos)
        self.memory[info.pos] = TileMemory(info.tile.name, info.mob)
        self.draw_tile(info.pos)

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
        return map_pos - self.center_pos + \
            Pos(MAP_WINDOW_WIDTH, MAP_WINDOW_HEIGHT) // 2

    def get_map_pos(self, world_pos):
        return world_pos + self.center_pos - \
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
    "stone wall": Drawable('#', tcod.grey, bg=tcod.black),
    "stone floor": Drawable('.', tcod.grey, bg=tcod.black),
    "up stairs": Drawable('<', tcod.white, bg=tcod.black),
    "down stairs": Drawable('>', tcod.white, bg=tcod.black),
    "unknown": Drawable(' ', tcod.white, bg=tcod.black),
    "water": Drawable('~', tcod.blue, bg=tcod.darkest_blue),
    "grass": Drawable(',', tcod.green, bg=tcod.darkest_green),
}

drawables["player"] = create_drawable_from_json(world.data["player"])
for info in world.data["mobs"].values():
    drawables[info['name']] = create_drawable_from_json(info)
