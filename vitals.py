from events import events, message, Event, EventType
from random import random, choice
from collections import namedtuple

blood_sugar_spike = namedtuple('blood_sugar_spike',
                               ['current_blood_sugar',
                                'spike_blood_sugar',
                                'start_turn'])


class Body(object):

    def __init__(self, info, player):
        self.constants = {
            'BASE_FATIGUE': 10,
            'MAX_FATIGUE': 100,
            'FATIGUE_RATE': 1.003,
            'LIGHT_FATIGUE': 20,
            'MEDIUM_FATIGUE': 40,
            'HEAVY_FATIGUE': 60,
            'CRITICAL_FATIGUE': 70,
            'FATIGUE_MESSAGE_PROB': 0.05,

            'MAX_NUTRITION': 2000,
            'BASE_NUTRITION': 1900,
            'HUNGER_PENALTY': 50,
            'LIGHT_HUNGER': 0.8,
            'MEDIUM_HUNGER': 0.7,
            'HEAVY_HUNGER': 0.4,
            'CRITICAL_HUNGER': 0.3,
            'HUNGER_MESSAGE_PROB': 0.05,

            'INJURY_MOD': 10,
            'OPEN_DOOR_TIME': 3,
            'EAT_TIME': 20,

            "FASTING_BLOOD_SUGAR": 85,
            "HIGH_CARB_SPIKE": 2.0,
            "MEDIUM_CARB_SPIKE": 1.5,
            "LOW_CARB_SPIKE": 1.3,
            'SUGAR_SPIKE_DURATION': 20,
            'MAX_NATURAL_BLOOD_SUGAR': 200,
            'LOW_BLOOD_SUGAR_OFFSET': 0.2,
            'LOW_BLOOD_SUGAR': 65,
            'BLOOD_SUGAR_SYMPTOM_PROB': 0.1
        }

        self.nutrition_lookup_table = {
            'coffee_food': {'nutrition': 50},
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

    def sc(self, condition_name, condition_value, duration={}):
        condition_value.configure(self,
                                  self.turn_number,
                                  duration)
        condition_value.on_start()
        self.conditions[condition_name] = condition_value

    def const(self, constant_name):
        return self.constants[constant_name]

    def on_game_start(self, character_info):
        ''' Called when the game starts '''

        self.turn_number = 0
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

        # Set blood sugar
        self.ss('blood_sugar', self.const('FASTING_BLOOD_SUGAR'))

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
        self.handle_blood_sugar()

        for condition in self.conditions.values():
            condition.on_progression(self.turn_number - condition.start_time)

        for name, condition in self.conditions.items():
            if condition.is_over(self.turn_number - condition.start_time):
                condition.on_completion()

        self.conditions = {k: v for k, v in self.conditions.items()
                           if not v.is_over(self.turn_number - v.start_time)}

        self.turn_number += 1

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
        elif obj.name.contains('food'):
            new_nutrition = self.nutrition_lookup_table[obj.name]["nutrition"]
            self.ss('nutrition', self.gs('nutrition') + new_nutrition)
            self.on_eat(self.nutrition_lookup_table[obj.name])
            action_time = self.const['EAT_TIME']

        for name, condition in self.conditions.items():
            condition.on_interact(condition,
                                  self.turn_number - condition.start_time)

        time = int(action_time ** (1 + k * (self.gs('fatigue') /
                                            self.const('MAX_FATIGUE'))))

        events.send(Event(EventType.PLAYER_STATUS_UPDATE, self.player))

        return time

    def on_eat(self, food):
        ''' Called upon ingesting food (do not include nutrition
        calculations here) '''
        current_blood_sugar = self.gs('blood_sugar')
        spike = lambda multiplier: min(current_blood_sugar * multiplier,
                                       self.const('MAX_NATURAL_BLOOD_SUGAR'))
        if 'high_carb' in food:
            self.ss('blood_sugar_spike',
                    blood_sugar_spike(
                        current_blood_sugar,
                        spike(self.const('HIGH_CARB_SPIKE')),
                        self.turn_number))
        elif 'medium_carb' in food:
            self.ss('blood_sugar_spike',
                    blood_sugar_spike(
                        current_blood_sugar,
                        spike(self.const('MEDIUM_CARB_SPIKE')),
                        self.turn_number))
        elif 'low_carb' in food:
            self.ss('blood_sugar_spike',
                    blood_sugar_spike(
                        current_blood_sugar,
                        spike(self.const('LOW_CARB_SPIKE')),
                        self.turn_number))

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

    def handle_blood_sugar(self):
        print('current blood sugar: {}'.format(self.gs('blood_sugar')))
        noise = (random() - 0.5)
        if 'blood_sugar_spike' not in self.stats:
            nutrition_ratio = self.gs('nutrition') / \
                self.const('MAX_NUTRITION')
            target = self.const('FASTING_BLOOD_SUGAR') * \
                min(self.const('LOW_BLOOD_SUGAR_OFFSET') + nutrition_ratio, 1.0)
            delta = noise + 1
            print('target blood sugar: {}'.format(target))

        else:
            start_turn = self.gs('blood_sugar_spike')
            if self.turn_number - start_turn > \
               self.const('SUGAR_SPIKE_DURATION'):
                del self.stats['blood_sugar_spike']
                return
            target = self.gs('blood_sugar_spike').spike_blood_sugar
            delta = noise + 4

        if self.gs('blood_sugar') < target:
            self.ss('blood_sugar', self.gs('blood_sugar') + delta)
        else:
            self.ss('blood_sugar', self.gs('blood_sugar') - delta)

        if self.gs('blood_sugar') < self.const('LOW_BLOOD_SUGAR') and \
           random() < self.const('BLOOD_SUGAR_SYMPTOM_PROB'):
            symptoms = ['blurry_vision',
                        'rapid_heartbeat',
                        'anxiety',
                        'irritability',
                        'headache',
                        'shaking',
                        'dizziness',
                        'focus_issues']
            symptom = choice(symptoms)
            self.sc("blurry_vision",
                    BlurryVision(),
                    {"duration": 20})


class Condition(object):

    def configure(self, body, time, details):
        self.body = body
        self.start_time = time
        self.details = details

    def on_start(self):
        pass

    def on_progression(self, time):
        pass

    def on_interact(self, obj, time):
        pass

    def on_completion(self):
        pass

    def is_over(self):
        pass


class BlurryVision(Condition):

    prob = 0.3

    def on_start(self):
        message("Everything looks hazy")

    def on_progression(self, time):
        if random() < self.prob:
            message("You can barely see anything")

    def on_interact(self, obj, time):
        if random() < self.prob:
            message("You can't see what you're doing")
            return False
        return True

    def on_completion(self):
        message("Things don't look as blurry anymore")

    def is_over(self, time):
        return time > self.details['duration']
