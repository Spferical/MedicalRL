from enum import Enum
import tcod
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, DIRECTION_KEYS, DEBUG, \
    GAME_NAME, MAX_INVENTORY_SIZE
import events
from mob import MobState
from util import Pos
from textwrap import wrap
import vitals
import world


WELCOME = """
You wake up alone in a hospital. You do not feel well.

Arrow keys, numpad, or extended vi keys to move around.
Pick things up with "g" or ",".
Press "i" to see and interact with items in your inventory.
Walk into things to use them.

Good luck.
"""


def init_tcod():
    tcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT,
                           bytes(GAME_NAME, 'utf-8'), False)
    tcod.sys_set_fps(30)


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

    def __init__(self, tile_name, mob=None, item=None):
        self.tile_name = tile_name
        self.mob = mob
        self.item = item


class States(Enum):
    DEFAULT = 1
    EXAMINE = 2
    GAME_OVER = 3


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
            object_drawable = drawables[memory.item.name] if memory.item \
                else None

            visible = map_pos in vision

            tile_drawable.draw(self.console, window_pos, not visible)
            if object_drawable:
                object_drawable.draw(self.console, window_pos, not visible)
            if mob_drawable:
                mob_drawable.draw(self.console, window_pos, not visible)


class MessagesWindow(Window):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_lines = []

    def message(self, message, color=tcod.white):
        self.message_lines.extend((m, color)
                                  for m in wrap(message, self.width))
        while len(self.message_lines) > self.height:
            self.message_lines.pop(0)
        self.draw_messages()

    def draw_messages(self):
        self.clear()
        y = 0
        for (line, color) in self.message_lines:
            tcod.console_set_default_foreground(self.console, color)
            tcod.console_print(self.console, 0, y, line)
            y += 1


class StatusBar(Window):

    def __init(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update(self, values, background_color=None):
        if background_color is not None:
            tcod.console_set_default_background(self.console, background_color)
            tcod.console_rect(self.console, 0, 0, self.width,
                              self.height, False, tcod.BKGND_SET)
        x = 0
        list_of_statuses = [(k, v) for k, v in values.items()]
        list_of_statuses.sort(key=lambda pair: pair[0])
        for (name, value) in list_of_statuses:
            status, name_color, status_color = value
            tcod.console_set_default_foreground(self.console, name_color)
            name_line = "{}: ".format(name)
            tcod.console_print(self.console, x, 0, name_line)
            x += len(name_line)
            tcod.console_set_default_foreground(self.console, status_color)
            tcod.console_print(self.console, x, 0, status)
            x += len(status)
            tcod.console_set_default_foreground(self.console, tcod.white)
            tcod.console_print(self.console, x, 0, " | ")
            x += 3


class ExamineWindow(Window):

    def examine(self, memory):
        self.clear()
        if memory is None:
            return
        if memory.mob:
            drawables[memory.mob.info['name']].draw(self.console, Pos(1, 1))
            tcod.console_print(self.console, 3, 1,
                               get_short_mob_description(memory.mob))
            tcod.console_set_default_foreground(self.console, tcod.red)
            tcod.console_print(self.console, 3, 2, str(memory.mob.hp))
            tcod.console_set_default_foreground(self.console, tcod.white)
            tcod.console_print(self.console, 4 + len(str(memory.mob.hp)), 2,
                               "hp")
            if DEBUG:
                tcod.console_print(self.console, 3, 3, str(memory.mob.pos))
                tcod.console_print(self.console, 3, 4, str(memory.mob.target))
        elif memory.item:
            drawables[memory.item.name].draw(self.console, Pos(1, 1))
            tcod.console_print(self.console, 3, 1, memory.item.name)
        else:
            drawables[memory.tile_name].draw(self.console, Pos(1, 1))
            tcod.console_print(self.console, 3, 1, memory.tile_name)


class UI(object):
    """Singleton that handles rendering and input."""
    state = States.DEFAULT

    def __init__(self):
        self.map_window = MapWindow(
            0, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 1)
        self.messages_window = MessagesWindow(
            (2 * SCREEN_WIDTH) // 3, 0,
            SCREEN_WIDTH // 3, 3 * (SCREEN_HEIGHT // 4))
        self.examine_window = ExamineWindow(
            SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT * 3 // 4,
            SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4)
        self.status_bar = StatusBar(
            0, SCREEN_HEIGHT - 1, SCREEN_WIDTH, 1)
        events.events.add_callback(events.EventType.MOVE,
                                   self.handle_move)
        events.events.add_callback(events.EventType.BIRTH,
                                   self.handle_birth)
        events.events.add_callback(events.EventType.TILE_REVEALED,
                                   self.handle_revealed)
        events.events.add_callback(events.EventType.TILE_HIDDEN,
                                   self.handle_hidden)
        events.events.add_callback(events.EventType.MESSAGE,
                                   self.handle_message)
        events.events.add_callback(events.EventType.PLAYER_STATUS_UPDATE,
                                   self.handle_player_status_update)
        events.events.add_callback(events.EventType.REMOVAL,
                                   self.handle_removal)
        events.events.add_callback(events.EventType.GAME_OVER,
                                   self.handle_game_over)
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
        else:
            char = None

        if key.vk == tcod.KEY_F11:
            tcod.console_set_fullscreen(not tcod.console_is_fullscreen())
        if (self.state == States.DEFAULT or self.state == States.GAME_OVER) \
                and key.vk == tcod.KEY_ESCAPE:
            result = menu("Escape Menu", ['Resume', 'Quit'], 24)
            if result == 1:
                game.alive = False

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
            elif key.vk in DIRECTION_KEYS:
                return game.attempt_player_move(DIRECTION_KEYS[key.vk])
            elif char == 'i':
                inventory = game.world.player.body.inventory
                if inventory:
                    index = menu("Inventory",
                                 [item.name for item in inventory], 24)
                    if index is not None and index != 'escape':
                        item = inventory[index]
                        turn_used = game.interact_with_object(item)
                        if turn_used and item.consumed_on_use:
                            inventory.remove(item)
                        return turn_used
                else:
                    self.messages_window.message("You have no items.")
            elif char == 'g' or char == ',':
                obj = game.player_level.get_object(game.world.player.pos)
                if obj is not None and obj.pickup:
                    # try to pick it up
                    inventory = game.world.player.body.inventory
                    game.player_level.pop_object(game.world.player.pos)
                    inventory.append(obj)
                    self.messages_window.message("You pick up the " + obj.name
                                                 + '.')
                    if len(inventory) > MAX_INVENTORY_SIZE:
                        drop = inventory.pop(0)
                        self.messages_window.message(
                            "You drop your " + drop.name + '.', tcod.purple)
                        game.player_level.objects[game.world.player.pos] = drop
                        drop.pos = game.world.player.pos
                        events.events.send(
                            events.Event(events.EventType.BIRTH, drop))
                else:
                    self.messages_window.message("There are no items here.")
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
        tcod.console_clear(0)
        self.map_window.blit()
        self.messages_window.blit()
        self.status_bar.blit()
        self.examine_window.blit()
        tcod.console_flush()

    def handle_birth(self, event):
        # new item on level
        memory = self.memory.get(event.info.pos, None)
        if memory and event.info.pos in self.vision:
            memory.item = event.info
            self.draw_tile(event.info.pos)

    def handle_player_status_update(self, event):
        player = event.info
        self.status_bar.update({
        })
        ns = {}
        for st in player.body.visible:
            value = player.body.gs(st)
            if isinstance(value, float):
                value = round(value, 2)
            if player.body.is_critical(st):
                ns[st] = (str(value), tcod.light_grey, tcod.red)
            else:
                ns[st] = (str(value), tcod.light_grey, tcod.light_grey)
        self.status_bar.update(ns, background_color=tcod.dark_grey)

    def handle_removal(self, event):
        # item removed on level
        memory = self.memory.get(event.info.pos, None)
        if memory and event.info.pos in self.vision:
            memory.item = None
            self.draw_tile(event.info.pos)

    def handle_game_over(self, event):
        self.state = States.GAME_OVER
        self.messages_window.message("(Press escape to quit.)")

    def handle_move(self, event):
        # remove mob from previous memory position if we saw him leave
        memory = self.memory.get(event.info.prev_pos, None)
        if memory and event.info.prev_pos in self.vision:
            memory.mob = None
            self.draw_tile(event.info.prev_pos)

        # add mob to new memory position if we saw him enter
        memory = self.memory.get(event.info.mob.pos, None)
        if memory and event.info.mob.pos in self.vision:
            memory.mob = event.info.mob
            self.draw_tile(event.info.mob.pos)

        # recenter/redraw everything if it was the player who moved
        if event.info.mob.info["name"] == 'player' \
                and self.state == States.DEFAULT:
            self.map_window.center(event.info.mob.pos)
            self.map_window.redraw_level(self.memory, self.vision)
            if memory and memory.item:
                self.messages_window.message(
                    "You see a " + memory.item.name + '.')

    def draw_tile(self, pos):
        self.map_window.draw_tile(pos, self.memory, self.vision)

    def handle_revealed(self, event):
        info = event.info
        self.vision.add(info.pos)
        self.memory[info.pos] = TileMemory(info.tile.name, info.mob, info.item)
        self.map_window.draw_tile(info.pos, self.memory, self.vision)

    def handle_hidden(self, event):
        self.vision.remove(event.info.pos)
        self.draw_tile(event.info.pos)

    def handle_message(self, event):
        message, color = event.info
        self.messages_window.message(message, color)


def yes_no_menu(question):
    key = tcod.Key()
    mouse = tcod.Mouse()
    width = SCREEN_HEIGHT // 2
    # calculate total height for the header (after auto-wrap) and one line per
    # option
    text = question + " (y/n)"
    height = tcod.console_get_height_rect(0, 0, 0, width,
                                          SCREEN_HEIGHT, text)
    # create an off-screen console that represents our window
    window = tcod.console_new(width, height)

    tcod.console_set_default_foreground(window, tcod.white)
    tcod.console_print_rect(window, 0, 0, width, height, text)

    # blit the contents of "window" to the root console
    x = SCREEN_WIDTH // 2 - width // 2
    y = SCREEN_HEIGHT // 2 - height // 2
    tcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.9)

    # present the root console to the player and wait for a key-press
    tcod.console_flush()
    tcod.sys_wait_for_event(tcod.EVENT_KEY_PRESS, key, mouse, True)

    # special case: changing to/from fullscreen
    if key.vk == tcod.KEY_F11:
        tcod.console_set_fullscreen(not tcod.console_is_fullscreen())
    return chr(key.c) == 'y'


def choice_menu(title, menu_items):
    chosen = []
    choices = menu_items + ['Done']
    choice = -1
    while choice != len(menu_items):
        tcod.console_clear(0)
        choice = menu(title, choices, SCREEN_WIDTH,
                      highlighted=[choices.index(i) for i in chosen])
        if choice is not None and choice != len(menu_items):
            if choice == 'escape':
                return None
            choice = choices[choice]
            if choice in chosen:
                chosen.remove(choice)
            else:
                chosen.append(choice)
        if tcod.console_is_window_closed():
            return None
    return chosen


def menu(header, options, width, highlighted=[]):
    """Basic, general-purpose menu.
    Allows the user to choose from up to 26 text options."""
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')
    key = tcod.Key()
    mouse = tcod.Mouse()
    # calculate total height for the header (after auto-wrap) and one line per
    # option
    if header == '':
        header_height = 0
    else:
        header_height = tcod.console_get_height_rect(0, 0, 0, width,
                                                     SCREEN_HEIGHT, header)
    height = len(options) + header_height
    # create an off-screen console that represents the menu's window
    window = tcod.console_new(width, height)

    # print the header, with auto-wrap
    tcod.console_set_default_foreground(window, tcod.white)
    tcod.console_print_rect(window, 0, 0, width, height, header)
    # print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        tcod.console_print(window, 0, y, text)
        y += 1
        letter_index += 1
    for index in highlighted:
        w = len(options[index]) + 4
        tcod.console_set_default_background(window, tcod.grey)
        y = index + header_height
        tcod.console_rect(window, 0, y, w, 1, False, flag=tcod.BKGND_SET)
    # blit the contents of "window" to the root console
    x = SCREEN_WIDTH // 2 - width // 2
    y = SCREEN_HEIGHT // 2 - height // 2
    tcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.9)
    # present the root console to the player and wait for a key-press
    tcod.console_flush()
    tcod.sys_wait_for_event(tcod.EVENT_KEY_PRESS, key, mouse, True)

    # special case: changing to/from fullscreen
    if key.vk == tcod.KEY_F11:
        tcod.console_set_fullscreen(not tcod.console_is_fullscreen())
    elif key.vk == tcod.KEY_ESCAPE:
        return 'escape'
    else:
        # convert the ASCII code to an index; if it corresponds to an option,
        # return it
        index = key.c - ord('a')
        if index >= 0 and index < len(options):
            return index
        return None


class MainMenuChoice(Enum):
    PLAY = 1
    EXIT = 2


def handle_main_menu():
    """ Returns a MainMenuChoice for the player's choice.
    """
    img = tcod.image_load(b'menu_background.png')
    tcod.console_clear(0)

    while not tcod.console_is_window_closed():
        # show the background image, at twice the regular console resolution
        tcod.image_blit_2x(img, 0, 0, 0)

        # show the game's title
        tcod.console_set_default_foreground(0, tcod.white)
        tcod.console_print_ex(0, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 4,
                              tcod.BKGND_NONE, tcod.CENTER,
                              bytes(GAME_NAME, 'utf-8'))
        tcod.console_print_ex(0, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 2,
                              tcod.BKGND_NONE, tcod.CENTER,
                              b'By Srinivas Kaza and Matthew Pfeiffer')

        # show options and wait for the player's choice
        choice = menu(
            '', ['Play', 'Quit'], 24)

        if choice == 0:  # new game
            return MainMenuChoice.PLAY
        elif choice == 1 or choice == 'escape':  # quit
            return MainMenuChoice.EXIT


def ask_player_for_preexisting_conditions():
    choices = choice_menu(
                'Choose some preexisting conditions for maximum fun...',
                [name for name in vitals.preexisting_conditions.keys()])
    if choices is None:
        return None
    else:
        return {x: vitals.preexisting_conditions[x]()
                for x in choices}


def create_drawable_from_json(info):
    bg_color = info.get("bg_color", None)
    return Drawable(info["char"],
                    getattr(tcod, info["fg_color"]),
                    getattr(tcod, bg_color) if bg_color is not None else None)


def draw_cell(con, pos, char, fg, bg=None):
    x, y = pos
    if bg:
        tcod.console_set_char_background(con, x, y, bg)
    tcod.console_set_char_foreground(con, x, y, fg)
    tcod.console_set_char(con, x, y, char)


def text_popup(text):
    key = tcod.Key()
    mouse = tcod.Mouse()
    width = SCREEN_WIDTH // 2
    # calculate total height for the header (after auto-wrap) and one line per
    # option
    height = tcod.console_get_height_rect(0, 0, 0, width,
                                          SCREEN_HEIGHT, text)
    # create an off-screen console that represents our window
    window = tcod.console_new(width, height)

    tcod.console_set_default_foreground(window, tcod.white)
    tcod.console_print_rect(window, 1, 0, width - 2, height, text)

    # blit the contents of "window" to the root console
    x = SCREEN_WIDTH // 2 - width // 2
    y = SCREEN_HEIGHT // 2 - height // 2
    tcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.9)

    # present the root console to the player and wait for a key-press
    tcod.console_flush()
    tcod.sys_wait_for_event(tcod.EVENT_KEY_PRESS, key, mouse, True)

    # special case: changing to/from fullscreen
    if key.vk == tcod.KEY_F11:
        tcod.console_set_fullscreen(not tcod.console_is_fullscreen())


def do_welcome():
    text_popup(WELCOME)


drawables = {
    "player": Drawable('@', tcod.white),
    "hospital wall": Drawable('#', tcod.white, bg=tcod.black),
    "tile floor": Drawable('.', tcod.white, bg=tcod.black),
    "up stairs": Drawable('<', tcod.white, bg=tcod.black),
    "down stairs": Drawable('>', tcod.white, bg=tcod.black),
    "unknown": Drawable(' ', tcod.white, bg=tcod.black),
    "water": Drawable('~', tcod.blue, bg=tcod.darkest_blue),
    "grass": Drawable(',', tcod.green, bg=tcod.darkest_green),
}

drawables["player"] = create_drawable_from_json(world.data["player"])
for info in world.data["mobs"].values():
    drawables[info['name']] = create_drawable_from_json(info)
for name, info in world.data["objects"].items():
    drawables[name] = create_drawable_from_json(info)
