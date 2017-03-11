from events import events, message, Event, EventType


class Body:

    def __init__(self, info, player):
        self.constants = {
            'BASE_FATIGUE': 10,
            'MAX_FATIGUE': 100,
            'FATIGUE_RATE': 1.006,
            'CRITICAL_FATIGUE': 70,
            'INJURY_MOD': 10,
            'OPEN_DOOR_TIME': 3
        }

        self.conditions = {}
        self.stats = {}
        self.inventory = []
        self.visible = set()
        self.player = player

    def gs(self, stat_name):
        return self.stats[stat_name] if stat_name in self.stats else None

    def ss(self, stat_name, value):
        self.stats[stat_name] = value

    def add(self, obj):
        self.inventory.append(obj)

    def get(self, obj_name):
        return [obj for obj in self.inventory if obj.name == obj_name]

    def gc(self, condition_name):
        return self.conditions[condition_name] if condition_name in self.conditions \
            else None

    def hc(self, condition_name):
        return condition_name in self.conditions

    def sc(self, condition_name, condition_value):
        self.inventory[condition_name] = condition_value

    def const(self, constant_name):
        return self.constants[constant_name]

    def on_game_start(self, character_info):
        ''' Called when the game starts '''

        # Base Fatigue for character
        base_fatigue = self.const('BASE_FATIGUE')

        # Additional Fatigue for character
        additional_fatigue = sum(character_info['ADDITONAL_FATIGUE'])

        # Set fatigue value
        self.ss('fatigue', base_fatigue + additional_fatigue)

        self.visible = set(('fatigue',))

    def is_critical(self, stat_name):
        ''' Returns True if a stat is critical '''
        if stat_name == 'fatigue':
            if self.gs(stat_name) > self.const('CRITICAL_FATIGUE'):
                return True

    def on_tick(self):
        ''' Called every action in game '''
        self.handle_fatigue()

    def on_interact(self, obj):
        ''' Called upon interacting with objects '''
        action_time = 1
        k = 1
        if obj.name == 'closed door':
            action_time = self.const('OPEN_DOOR_TIME')
            leg_injury = self.gc('leg_injury')
            arm_injury = self.gc('arm_injury')
            leg_injury = leg_injury if leg_injury != None else 0
            arm_injury = arm_injury if arm_injury != None else 0

            k += (leg_injury + arm_injury) * self.const('INJURY_MOD')

        time = int(action_time ** (1 + k * (self.gs('fatigue') /
                                            self.const('MAX_FATIGUE'))))

        events.send(Event(EventType.PLAYER_STATUS_UPDATE, self.player))

        return time

    def handle_fatigue(self):
        if self.gs('fatigue') > self.const('MAX_FATIGUE'):
            pass
        else:
            self.ss('fatigue', self.gs('fatigue') * self.const('FATIGUE_RATE'))
