from events import events, message, Event, EventType
from random import random


class Body:

    def __init__(self, info, player):
        self.constants = {
            'BASE_FATIGUE': 10,
            'MAX_FATIGUE': 100,
            'FATIGUE_RATE': 1.006,
            'LIGHT_FATIGUE': 20,
            'MEDIUM_FATIGUE': 40,
            'HEAVY_FATIGUE': 60,
            'CRITICAL_FATIGUE': 70,
            'FATIGUE_MESSAGE_PROB': 0.05,

            'MAX_NUTRITION': 1000,
            'BASE_NUTRITION': 900,
            'HUNGER_PENALTY': 50,
            'LIGHT_HUNGER': 0.8,
            'MEDIUM_HUNGER': 0.7,
            'HEAVY_HUNGER': 0.4,
            'CRITICAL_HUNGER': 0.3,
            'HUNGER_MESSAGE_PROB': 0.05,

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

        self.ss('nutrition', self.const('BASE_NUTRITION'))

        # Base Fatigue for character
        base_fatigue = self.const('BASE_FATIGUE')

        # Additional Fatigue for character
        additional_fatigue = sum(character_info['ADDITONAL_FATIGUE'])

        # Add hunger induced-fatigue
        additional_fatigue += \
            (1 - self.gs('nutrition') / self.const('MAX_NUTRITION')) * \
            self.const('HUNGER_PENALTY')

        # Set fatigue value
        self.ss('fatigue', base_fatigue + additional_fatigue)

        self.visible = set(('fatigue', 'nutrition'))

    def is_critical(self, stat_name):
        ''' Returns True if a stat is critical '''
        if stat_name == 'fatigue':
            if self.gs(stat_name) > self.const('CRITICAL_FATIGUE'):
                return True
        if stat_name == 'nutrition':
            if self.gs(stat_name) / self.const('MAX_NUTRITION') \
               < self.const('CRITICAL_HUNGER'):
                return True

    def on_tick(self):
        ''' Called every action in game '''
        self.handle_fatigue()
        self.handle_nutrition()

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
            if random() < self.const('FATIGUE_MESSAGE_PROB'):
                if self.gs('fatigue') > self.const('CRITICAL_FATIGUE'):
                    message('You feel like you are about to pass out')
                elif self.gs('fatigue') > self.const('HEAVY_FATIGUE'):
                    message('You feel incredibly tired')
                elif self.gs('fatigue') > self.const('MEDIUM_FATIGUE'):
                    message('You feel tired')
                elif self.gs('fatigue') > self.const('LIGHT_FATIGUE'):
                    message('You feel sleepy')

    def handle_nutrition(self):
        self.ss('nutrition', self.gs('nutrition') - 1)
        if random() < self.const('HUNGER_MESSAGE_PROB'):
            if self.gs('nutrition') / self.const('MAX_NUTRITION') \
               < self.const('CRITICAL_HUNGER'):
                message("You are starving to death")
            elif self.gs('nutrition') / self.const('MAX_NUTRITION') \
                    < self.const('HEAVY_HUNGER'):
                message("Your belly aches with hunger cramps")
            elif self.gs('nutrition') / self.const('MAX_NUTRITION') \
                    < self.const('MEDIUM_HUNGER'):
                message("You feel very hungry")
            elif self.gs('nutrition') / self.const('MAX_NUTRITION') \
                    < self.const('LIGHT_HUNGER'):
                message("You feel hungry")
