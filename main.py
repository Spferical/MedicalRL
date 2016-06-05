import tcod
import render
from constants import SCREEN_HEIGHT, SCREEN_WIDTH, DIRECTION_KEYS
import events
from util import Pos
import world


class Game(object):
    alive = True

    def __init__(self):
        self.render = render.Renderer()
        self.world = world.World()
        self.render.render()
        self.update_fov()

    def handle_input(self):
        key = tcod.Key()
        mouse = tcod.Mouse()
        tcod.sys_check_for_event(tcod.EVENT_KEY_PRESS | tcod.EVENT_MOUSE,
                                 key, mouse)
        if key.c:
            char = chr(key.c)
            if char in DIRECTION_KEYS:
                self.attempt_player_move(DIRECTION_KEYS[char])

    def update_fov(self):
        # TODO: actual fov
        pos = self.world.player.pos
        level = self.world.levels[self.world.player.dungeon_level]
        for x in range(pos.x - 10, pos.x + 10 + 1):
            for y in range(pos.y - 10, pos.y + 10 + 1):
                if not (x == pos.x and y == pos.y):
                    tile_info = world.TileInfo(x, y, level[x, y])
                    events.events.handle_event(
                        events.Event(
                            events.EventType.TILE_REVEALED, tile_info))

    def attempt_player_move(self, direction):
        player = self.world.player
        self.world.player.pos += Pos(direction)
        events.events.handle_event(
            events.Event(events.EventType.MOVE, self.world.player))
        self.update_fov()

    def run(self):
        while self.alive and not tcod.console_is_window_closed():
            self.handle_input()
            self.render.render()


def main():
    tcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, b"Frogue", False)
    tcod.sys_set_fps(30)
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
