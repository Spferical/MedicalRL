from enum import Enum


class EventType(Enum):
    SOUND = 1
    DAMAGE = 2
    MOVE = 3
    TILE_REVEALED = 4


class Event(object):
    def __init__(self, event_type, entity):
        self.event_type = event_type
        self.entity = entity


class EventHandler(object):
    def __init__(self):
        self.callbacks = {event_type: [] for event_type in EventType}

    def add_callback(self, event_type, callback):
        self.callbacks[event_type].append(callback)

    def handle_event(self, event):
        for callback in self.callbacks[event.event_type]:
            callback(event)

events = EventHandler()
