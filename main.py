import tcod
import render
from constants import SCREEN_HEIGHT, SCREEN_WIDTH, DIRECTION_KEYS, FOV_RADIUS
import events
import fov
from util import Pos
import world


class Game(object):
    alive = True

    def __init__(self):
        self.render = render.Renderer()
        self.world = world.World()
        events.events.add_callback(
            events.EventType.TILE_REVEALED, self.handle_tile_reveal)
        self.update_fov()
        events.events.do_move_event(self.world.player, None)
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

    def update_fov(self):
        player = self.world.player
        pos = self.world.player.pos
        level = self.world.levels[player.dungeon_level]
        new_fov = set(fov.calculate_fov(pos, FOV_RADIUS, level))

        for pos in player.tiles_in_sight.difference(new_fov):
            tile_info = world.TileInfo(pos, level[pos.x, pos.y])
            events.events.handle_event(
                events.Event(
                    events.EventType.TILE_HIDDEN, tile_info))
        for pos in new_fov.difference(player.tiles_in_sight):
            world.reveal_tile(level, pos)

        player.tiles_in_sight = new_fov

    def handle_tile_reveal(self, event):
        level = self.world.levels[self.world.player.dungeon_level]
        level[event.info.pos].explored = True

    def attempt_player_move(self, direction):
        player = self.world.player
        old_pos = player.pos
        new_pos = player.pos + Pos(direction)
        if not self.world.levels[player.dungeon_level][new_pos].blocked:
            player.pos = new_pos
            events.events.do_move_event(player, old_pos)
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
