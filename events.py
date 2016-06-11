from enum import Enum


class EventType(Enum):
    SOUND = 1
    DAMAGE = 2
    MOVE = 3
    TILE_REVEALED = 4
    TILE_HIDDEN = 5


class MoveInfo(object):
    def __init__(self, mob, prev_pos):
        self.mob = mob
        self.prev_pos = prev_pos


class Event(object):
    def __init__(self, event_type, info):
        self.event_type = event_type
        self.info = info


class EventHandler(object):
    def __init__(self):
        self.callbacks = {event_type: [] for event_type in EventType}

    def add_callback(self, event_type, callback):
        self.callbacks[event_type].append(callback)

    def handle_event(self, event):
        for callback in self.callbacks[event.event_type]:
            callback(event)

    def do_move_event(self, mob, prev_pos):
        info = MoveInfo(mob, prev_pos)
        self.handle_event(Event(EventType.MOVE, info))

events = EventHandler()
