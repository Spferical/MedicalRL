from enum import Enum
import tcod
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, DIRECTION_KEYS
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


def get_short_mob_description(mob):
    name = mob.info['name']
    state = MOB_STATE_DESCRIPTIONS[mob.state] + ' ' \
        if mob.state in MOB_STATE_DESCRIPTIONS else ''
    article = get_article(state if state else name)
    return article + ' ' + state + name + '.'


def get_article(word):
    return 'an' if word[0] in 'aeiou' else 'a'


class Window(object):
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.console = tcod.console_new(width, height)

    def blit(self):
        tcod.console_blit(self.console, 0, 0,
                          self.width, self.height,
                          0, self.x, self.y)

    def clear(self):
        tcod.console_clear(self.console)

    def draw(self):
        pass


class MapWindow(Window):
    center_pos = Pos(0, 0)

    def __init__(self, *args, **kwargs):
        self.center_pos = Pos(0, 0)
        super().__init__(*args, **kwargs)

    def draw_cursor(self, map_pos):
        x, y = self.get_window_pos(map_pos)
        tcod.console_set_char_background(self.console, x, y,
                                         tcod.light_grey)

    def draw_cursor_at_center(self):
        self.draw_cursor(self.center_pos)

    def move(self, direction):
        self.center_pos += direction

    def center(self, pos):
        self.center_pos = pos

    def get_window_pos(self, map_pos):
        return map_pos - self.center_pos + \
            Pos(self.width, self.height) // 2

    def get_map_pos(self, world_pos):
        return world_pos + self.center_pos - \
            Pos(self.width, self.height) // 2

    def redraw_level(self, memory, vision):
        self.clear()
        map_offset = self.get_map_pos(Pos(0, 0))
        for x in range(0, self.width):
            for y in range(0, self.height):
                window_pos = Pos(x, y)
                map_pos = window_pos + map_offset
                self.draw_tile(map_pos, memory, vision, window_pos=window_pos)

    def draw_tile(self, map_pos, memory, vision, window_pos=None):
        memory = memory.get(map_pos, None)
        if memory:
            if window_pos is None:
                window_pos = self.get_window_pos(map_pos)

            tile_drawable = drawables[memory.tile_name]
            mob_drawable = drawables[memory.mob.info['name']] if memory.mob \
                else None

            visible = map_pos in vision

            tile_drawable.draw(self.console, window_pos, not visible)
            if mob_drawable:
                mob_drawable.draw(self.console, window_pos, not visible)


class MessagesWindow(Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_lines = []

    def message(self, message, color=tcod.white):
        self.message_lines.append((message, color))
        if len(self.message_lines) > self.height:
            self.message_lines.pop(0)
        self.draw_messages()

    def draw_messages(self):
        self.clear()
        y = 0
        for (line, color) in self.message_lines:
            tcod.console_set_default_foreground(self.console, color)
            tcod.console_print(self.console, 0, y, line)
            y += 1


class ExamineWindow(Window):
    def examine(self, memory):
        self.clear()
        if memory is None:
            return
        if memory.mob:
            drawables[memory.mob.info['name']].draw(self.console, Pos(1, 1))
            tcod.console_print(self.console, 3, 1,
                               get_short_mob_description(memory.mob))
        else:
            drawables[memory.tile_name].draw(self.console, Pos(1, 1))
            tcod.console_print(self.console, 3, 1, memory.tile_name)


class UI(object):
    """Handles rendering and input."""
    state = States.DEFAULT

    def __init__(self):
        self.map_window = MapWindow(
            0, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT)
        self.messages_window = MessagesWindow(
            SCREEN_WIDTH // 2, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.examine_window = ExamineWindow(
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        events.events.add_callback(events.EventType.MOVE,
                                   self.handle_move)
        events.events.add_callback(events.EventType.TILE_REVEALED,
                                   self.handle_revealed)
        events.events.add_callback(events.EventType.TILE_HIDDEN,
                                   self.handle_hidden)
        self.memory = {}
        self.vision = set()

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
                    self.map_window.center(game.world.player.pos)
                    self.map_window.draw_cursor_at_center()
                    self.examine_pos(game.world.player.pos)
                elif char == '.':
                    return True
            elif self.state == States.EXAMINE:
                if char in DIRECTION_KEYS:
                    self.map_window.move(DIRECTION_KEYS[char])
                    self.map_window.redraw_level(self.memory, self.vision)
                    self.map_window.draw_cursor_at_center()
                    self.examine_pos(self.map_window.center_pos)
                elif key.vk == tcod.KEY_ESCAPE:
                    self.state = States.DEFAULT
                    self.map_window.center(game.world.player.pos)
                    self.map_window.redraw_level(self.memory, self.vision)
                    self.examine_window.clear()

    def examine_pos(self, pos):
        memory = self.memory.get(pos, None)
        self.examine_window.examine(memory)

    def move_examine(self, direction):
        self.map_window.move(direction)
        self.map_window.redraw_level(self.memory, self.vision)
        memory = self.memory.get(self.center_pos, None)
        seen = self.center_pos in self.vision
        if memory:
            start = "You see " if seen else "You remember "
            if memory.mob:
                description = get_short_mob_description(memory.mob)
                self.message(start + description + '.', tcod.light_grey)
            else:
                self.message(start + memory.tile_name + '.', tcod.light_grey)
        else:
            self.message("You cannot see that location.", tcod.light_grey)

    def render(self):
        self.map_window.blit()
        self.messages_window.blit()
        self.examine_window.blit()
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
            self.map_window.center(event.info.mob.pos)
            self.map_window.redraw_level(self.memory, self.vision)

    def draw_tile(self, pos):
        self.map_window.draw_tile(pos, self.memory, self.vision)

    def handle_revealed(self, event):
        info = event.info
        self.vision.add(info.pos)
        self.memory[info.pos] = TileMemory(info.tile.name, info.mob)
        self.map_window.draw_tile(info.pos, self.memory, self.vision)
        if info.mob:
            self.messages_window.message(
                "You see " + get_short_mob_description(info.mob))

    def handle_hidden(self, event):
        self.vision.remove(event.info.pos)
        self.draw_tile(event.info.pos)


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
