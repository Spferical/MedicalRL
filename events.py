from enum import Enum


class EventType(Enum):
    SOUND = 1
    DAMAGE = 2
    MOVE = 3
    TILE_REVEALED = 4
    TILE_HIDDEN = 5
    MESSAGE = 6
    BIRTH = 7


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
        self.send = self.handle_event

    def add_callback(self, event_type, callback, priority=1):
        self.callbacks[event_type].append((callback, priority))
        self.callbacks[event_type].sort(
            key=lambda x: x[1])

    def handle_event(self, event):
        for (callback, priority) in self.callbacks[event.event_type]:
            callback(event)

    def do_move_event(self, mob, prev_pos):
        info = MoveInfo(mob, prev_pos)
        self.handle_event(Event(EventType.MOVE, info))

    def remove_callback(self, event_type, callback):
        for i in range(len(self.callbacks[event_type])):
            if self.callbacks[event_type][i][1] == callback:
                self.callbacks[event_type].pop(i)
                return True
        return False


events = EventHandler()
