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
        self.accum = 1
        self.ui = ui.UI()
        self.world = world.generate_world()
        events.events.add_callback(
            events.EventType.TILE_REVEALED, self.handle_tile_reveal)
        self.update_fov()
        events.events.do_move_event(self.world.player, None)
        self.update_player_status()
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
        for i in range(self.accum):
            self.world.player.body.on_tick()
        self.accum = 1

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

    def update_player_status(self):
        events.events.send(events.Event(
            events.EventType.PLAYER_STATUS_UPDATE, self.world.player))

    def interact_with_object(self, obj):
        """
        Returns whether an action took place.
        """
        self.accum += self.world.player.body.get_interaction_time(obj)
        if obj.interaction == world.Interactions.OPEN_DOOR:
            # the object is a closed door
            # replace it with an open door
            self.player_level.objects[obj.pos] = \
                world.create_object(obj.pos, "open door")
            self.update_fov()
            return True
        elif obj.interaction == world.Interactions.OPEN_CONTAINER:
            if not obj.contents:
                self.ui.messages_window.message(
                    "The " + obj.name + " is empty.")
                return
            # let the player pick an item
            index = ui.menu(obj.name,
                            [item.name for item in obj.contents], 24)
            if index is not None and index != 'escape':
                item = obj.contents.pop(index)
                self.world.player.body.inventory.append(item)
                self.ui.messages_window.message(
                    "You take the " + item.name
                    + " out of the " + obj.name + ".")
        elif obj.interaction == world.Interactions.PREGNANCY_TEST:
            self.ui.messages_window.message(
                "You perform a pregnancy test on yourself...")
            if random.random() < 0.01:
                self.ui.messages_window.message(
                    "You are pregnant!", tcod.pink)
            else:
                self.ui.messages_window.message(
                    "You are not pregnant.", tcod.pink)
            return True
        elif obj.interaction == world.Interactions.EAT:
            self.world.player.body.on_eat(obj.food_info)
            self.ui.messages_window.message(
                    "You eat the " + obj.name + ".", tcod.light_blue)
            return True
        elif obj.interaction == world.Interactions.SLEEP:
            if ui.yes_no_menu("Sleep in the bed?") is True:
                self.ui.messages_window.message(
                    "You sleep for a while.")

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
            if self.interact_with_object(obj):
                return True

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
            self.update_player_status()
            return True

    def run(self, character_info={'ADDITONAL_FATIGUE': []}):
        self.world.player.body.on_game_start(character_info)
        while self.alive and not tcod.console_is_window_closed():
            if self.ui.handle_input(self):
                self.update_mobs()
            self.ui.render()
