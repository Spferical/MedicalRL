import random
import tcod
import ui
from constants import FOV_RADIUS
import events
import fov
from mob import MobState
import path
import world


class Game(object):
    """Manages a single play of the game."""
    alive = True

    def __init__(self):
        self.ui = ui.UI()
        self.world = world.generate_world()
        events.events.add_callback(
            events.EventType.TILE_REVEALED, self.handle_tile_reveal)
        self.update_fov()
        events.events.do_move_event(self.world.player, None)
        self.ui.render()

    @property
    def player_level(self):
        return self.world.levels[self.world.player.dlevel]

    def update_fov(self):
        player = self.world.player
        pos = self.world.player.pos
        level = self.world.levels[player.dlevel]
        new_fov = set(fov.calculate_fov(pos, FOV_RADIUS, level))

        for pos in player.tiles_in_sight.difference(new_fov):
            tile_info = world.TileInfo(pos, level[pos.x, pos.y])
            events.events.handle_event(
                events.Event(
                    events.EventType.TILE_HIDDEN, tile_info))

        for pos in new_fov.difference(player.tiles_in_sight):
            world.reveal_tile(level, pos)

        player.tiles_in_sight = new_fov

    def update_mobs(self):
        level = self.player_level
        for mob in level.mobs.values():
            if mob != self.world.player:
                self.update_mob(mob, level)

    def update_mob(self, mob, level):
        if mob.state == MobState.WANDERING:
            if mob.target is None or \
                    mob.target == mob.pos:
                if mob.leader and mob.leader.target:
                    mob.target = mob.leader.target
                else:
                    potential_targets = list(
                        pos for pos in fov.calculate_fov(mob.pos, 5, level)
                        if not level[pos].blocked)
                    mob.target = random.choice(potential_targets)
            wander_path = path.get_path(
                mob.pos, mob.target, level)
            if wander_path:
                mob.move_to(wander_path[0])
                if mob.pos.distance(mob.target) <= 1:
                    mob.state = MobState.IDLE
        elif mob.state == MobState.IDLE:
            if mob.leader is None:
                if random.randint(1, 10) == 1:
                    mob.state = MobState.WANDERING
            else:
                if mob.leader and mob.leader.state != MobState.IDLE:
                    mob.state = mob.leader.state

    def handle_tile_reveal(self, event):
        level = self.world.levels[self.world.player.dlevel]
        level[event.info.pos].explored = True

    def attempt_player_move(self, direction):
        """Returns True if player successfully moved."""
        player = self.world.player
        old_pos = player.pos
        new_pos = player.pos + direction
        # check for item in spot
        obj = self.player_level.get_object(new_pos)
        if obj and not obj.is_passable \
                and obj.interaction != world.Interactions.NONE:
            # we want to interact with this object
            # maybe open up a gui, or something
            if obj.interaction == world.Interactions.OPEN_DOOR:
                # the object is a closed door
                # replace it with an open door
                self.player_level.objects[new_pos] = \
                        world.create_open_door(new_pos)
        elif not self.player_level.is_blocked(new_pos) \
                and player.can_move(new_pos):
            # message if we entered a new room
            old_room_id = self.player_level[old_pos].room_id
            new_room_id = self.player_level[new_pos].room_id
            if new_room_id != 0 and new_room_id != old_room_id:
                self.ui.messages_window.message(
                        "You enter a " + self.player_level.rooms[new_room_id] +
                        '.')

            # do the actual move
            player.pos = new_pos
            events.events.do_move_event(player, old_pos)

            self.update_fov()
            return True

    def run(self):
        while self.alive and not tcod.console_is_window_closed():
            if self.ui.handle_input(self):
                self.update_mobs()
            self.ui.render()
