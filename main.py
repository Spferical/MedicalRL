import tcod
import render
import world
from constants import SCREEN_HEIGHT, SCREEN_WIDTH, DIRECTION_KEYS
import events


class Game(object):
    alive = True

    def __init__(self):
        self.render = render.Renderer()
        self.world = world.World()
        self.render.render()

    def handle_input(self):
        key = tcod.Key()
        mouse = tcod.Mouse()
        tcod.sys_check_for_event(tcod.EVENT_KEY_PRESS | tcod.EVENT_MOUSE,
                                 key, mouse)
        if key.c:
            char = chr(key.c)
            if char in DIRECTION_KEYS:
                self.attempt_player_move(DIRECTION_KEYS[char])

    def attempt_player_move(self, direction):
        # TODO
        player = self.world.player
        pos = self.world.player.pos

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
