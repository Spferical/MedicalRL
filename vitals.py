from events import events, Event, EventType
from events import message as ev_message
from random import random, choice
from collections import namedtuple
from world import Interactions

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
            'HUNGER_PENALTY': 20,
            'LIGHT_HUNGER': 0.8,
            'MEDIUM_HUNGER': 0.7,
            'HEAVY_HUNGER': 0.4,
            'CRITICAL_HUNGER': 0.3,
            'HUNGER_MESSAGE_PROB': 0.05,

            'MAX_SLEEP_TIME': 500,

            'INJURY_MOD': 10,
            'OPEN_DOOR_TIME': 3,
            'EAT_TIME': 5,

            "FASTING_BLOOD_SUGAR": 85,
            "HIGH_CARB_SPIKE": 2.0,
            "MEDIUM_CARB_SPIKE": 1.5,
            "LOW_CARB_SPIKE": 1.3,
            'SUGAR_SPIKE_DURATION': 20,
            'MAX_NATURAL_BLOOD_SUGAR': 200,
            'LOW_BLOOD_SUGAR_OFFSET': 0.2,
            'LOW_BLOOD_SUGAR': 65,
            'BLOOD_SUGAR_SYMPTOM_PROB': 0.1,

            'FAINT_INJURY_PROB': 0.3
        }

        self.conditions = {}
        self.stats = {}
        self.inventory = []
        self.visible = set()
        self.player = player

    def message(self, m):
        if "sleeping" not in self.stats:
            ev_message(m)

    def gs(self, stat_name):
        return self.stats.get(stat_name, None)

    def hs(self, stat_name):
        return stat_name in self.stats

    def ss(self, stat_name, value):
        self.stats[stat_name] = value

    def add(self, obj):
        self.inventory.append(obj)

    def get(self, obj_name):
        return [obj for obj in self.inventory if obj.name == obj_name]

    def gc(self, condition_name):
        return self.conditions.get(condition_name, None)

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
        if not self.hs('sleeping'):
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
        events.send(Event(EventType.PLAYER_STATUS_UPDATE, self.player))

    def sleep(self):
        print("original fatigue: {}".format(self.gs('fatigue')))
        noise = random() * 0.5 - 0.25
        max_ds = self.const('MAX_FATIGUE') - self.const('BASE_FATIGUE')
        hunger_ratio = self.gs('nutrition') / self.const('MAX_NUTRITION')
        ds = self.gs('fatigue') - self.const('BASE_FATIGUE')
        sleep_time = max(min(ds / max_ds + noise, 1.0)
                         * self.const('MAX_SLEEP_TIME'), 0)
        new_fatigue = max(self.const('BASE_FATIGUE') * (1 + noise),
                          self.const('BASE_FATIGUE'))
        additional_fatigue = \
            self.const('HUNGER_PENALTY') if hunger_ratio < self.const(
                'MEDIUM_HUNGER') else 0
        new_fatigue = min(new_fatigue + additional_fatigue, 50)
        print("additional fatigue: {}".format(additional_fatigue))
        print("new fatigue: {}".format(new_fatigue + additional_fatigue))
        self.ss('sleeping', True)
        self.ss('fatigue', new_fatigue)
        print("Sleep time: {}".format(sleep_time))
        return sleep_time

    def on_interact(self, obj):
        ''' Returns the time that it takes the player to interact with obj '''
        action_time = 1
        k = 1

        fails = False
        for name, condition in self.conditions.items():
            can_do_it = condition.on_interact(
                condition, self.turn_number - condition.start_time)
            if not can_do_it:
                fails = True

        if fails:
            return False

        if obj.interaction == Interactions.OPEN_DOOR:
            action_time = self.const('OPEN_DOOR_TIME')
            leg_injury = self.gc('leg_injury')
            arm_injury = self.gc('arm_injury')
            leg_injury = leg_injury if leg_injury != None else 0
            arm_injury = arm_injury if arm_injury != None else 0

            k += (leg_injury + arm_injury) * self.const('INJURY_MOD')
        elif obj.interaction == Interactions.EAT:
            action_time = self.const('EAT_TIME')
        elif obj.interaction == Interactions.SLEEP:
            if self.gs('fatigue') > self.const('LIGHT_FATIGUE'):
                action_time = self.sleep()
            else:
                return -1

        time = int(action_time ** (1 + k * (self.gs('fatigue') /
                                            self.const('MAX_FATIGUE'))))

        print("That action took {} turns".format(time))
        return time

    def on_eat(self, food):
        ''' Called upon ingesting food (includes nutrition calculations) '''
        print("Eating banana")
        new_nutrition = food['nutrition']
        self.ss('nutrition', min(self.gs('nutrition') + new_nutrition,
                                 self.const('MAX_NUTRITION')))
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

        events.send(Event(EventType.PLAYER_STATUS_UPDATE, self.player))

    def handle_fatigue(self):
        if self.gs('fatigue') > self.const('MAX_FATIGUE'):
            self.message("You faint...")
            self.sleep()
            if random() < self.const('FAINT_INJURY_PROB'):
                if random() < 0.5:
                    self.ss('arm_injury', True)
                    self.message(
                        "As you come to, you notice that you injured "
                        "your arm in the fall")
                else:
                    self.ss('leg_injury', True)
                    self.message(
                        "As you come to, you notice that you injured "
                        "your leg in the fall")
            self.message("You groggily awaken and pick yourself up")
        else:
            self.ss('fatigue', self.gs('fatigue') * self.const('FATIGUE_RATE'))
            if random() < self.const('FATIGUE_MESSAGE_PROB'):
                if self.gs('fatigue') > self.const('CRITICAL_FATIGUE'):
                    self.message('You feel like you are about to pass out')
                elif self.gs('fatigue') > self.const('HEAVY_FATIGUE'):
                    self.message('You feel incredibly tired')
                elif self.gs('fatigue') > self.const('MEDIUM_FATIGUE'):
                    self.message('You feel tired')
                elif self.gs('fatigue') > self.const('LIGHT_FATIGUE'):
                    self.message('You feel sleepy')

    def handle_nutrition(self):
        self.ss('nutrition', self.gs('nutrition') - 1)
        if random() < self.const('HUNGER_MESSAGE_PROB'):
            if self.gs('nutrition') / self.const('MAX_NUTRITION') \
               < self.const('CRITICAL_HUNGER'):
                self.message("You are starving to death")
            elif self.gs('nutrition') / self.const('MAX_NUTRITION') \
                    < self.const('HEAVY_HUNGER'):
                self.message("Your belly aches with hunger cramps")
            elif self.gs('nutrition') / self.const('MAX_NUTRITION') \
                    < self.const('MEDIUM_HUNGER'):
                self.message("You feel very hungry")
            elif self.gs('nutrition') / self.const('MAX_NUTRITION') \
                    < self.const('LIGHT_HUNGER'):
                self.message("You feel hungry")

    def handle_blood_sugar(self):
        #print('current blood sugar: {}'.format(self.gs('blood_sugar')))
        noise = (random() - 0.5)
        if 'blood_sugar_spike' not in self.stats:
            nutrition_ratio = self.gs('nutrition') / \
                self.const('MAX_NUTRITION')
            target = self.const('FASTING_BLOOD_SUGAR') * \
                min(self.const('LOW_BLOOD_SUGAR_OFFSET') + nutrition_ratio, 1.0)
            delta = noise + 1
            #print('target blood sugar: {}'.format(target))

        else:
            start_turn = self.gs('blood_sugar_spike').start_turn
            if self.turn_number - start_turn > \
                    self.const('SUGAR_SPIKE_DURATION'):
                del self.stats['blood_sugar_spike']
                return
            target = self.gs('blood_sugar_spike').spike_blood_sugar
            delta = noise + 3

        if self.gs('blood_sugar') < target:
            self.ss('blood_sugar', self.gs('blood_sugar') + delta)
        else:
            self.ss('blood_sugar', self.gs('blood_sugar') - delta)

        if self.gs('blood_sugar') < self.const('LOW_BLOOD_SUGAR') and \
                random() < self.const('BLOOD_SUGAR_SYMPTOM_PROB'):
            symptoms = [('blurry_vision', BlurryVision(), {'duration': 20}),
                        ('tachycardia', Tachycardia(), {'duration': 5}),
                        ('anxiety', Anxiety(), {'duration': 30}),
                        ('headache', Headache(), {'duration': 25}),
                        ('shaking', Shaking(), {'duration': 30}),
                        ('dizziness', Dizziness(), {'duration': 30})]
            name, symptom, details = choice(symptoms)
            self.sc(name, symptom, details)


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

    def is_over(self, time):
        return time > self.details['duration'] \
            if 'duration' in self.details else False


class BlurryVision(Condition):

    prob = 0.3

    def on_start(self):
        self.body.message("Everything looks hazy")

    def on_progression(self, time):
        if random() < self.prob:
            self.body.message("You can barely see anything")

    def on_interact(self, obj, time):
        if random() < self.prob:
            self.body.message("You can't see what you're doing")
            return False
        return True

    def on_completion(self):
        self.body.message("Things don't look as blurry anymore")


class Tachycardia(Condition):

    prob = 0.2

    def on_start(self):
        self.body.message("You feel your heart rapidly beating in your chest")

    def on_progression(self, time):
        if random() < self.prob:
            self.body.message("All you can hear is your racing heartbeat")

    def on_interact(self, obj, time):
        return True

    def on_completion(self):
        pass


class Anxiety(Condition):

    prob = 0.2

    def on_start(self):
        self.body.message("You feel anxious")

    def on_progression(self, time):
        if random() < self.prob:
            self.body.message("You feel really nervous")

    def on_interact(self, obj, time):
        if random() < self.prob:
            self.body.message("You are too anxious to do anything")
            return False
        return True

    def on_completion(self):
        self.body.message("You don't feel as anxious anymore")


class Headache(Condition):

    def on_start(self):
        if 'severe' in self.details:
            self.prob = 0.4
            self.body.message('You have an intense migraine')
        else:
            self.prob = 0.2
            self.body.message('You have a headache')

    def on_progression(self, time):
        if random() < self.prob:
            if random() < 0.5:
                self.body.message("The lights hurt")
            else:
                self.body.message("Your head hurts")

    def on_interact(self, obj, time):
        if random() < self.prob:
            self.body.message("You can't focus on anything")
            return False
        return True

    def on_completion(self):
        self.body.message("You feel your headache pass")


class Shaking(Condition):

    def on_start(self):
        if 'severe' in self.details:
            self.prob = 0.4
            self.body.message('You start shaking')
        else:
            self.prob = 0.2
            self.body.message('You start shaking a little')

    def on_progression(self, time):
        if random() < self.prob:
            if random() < 0.5:
                self.body.message("Your shiver and shake")

    def on_interact(self, obj, time):
        if random() < self.prob:
            self.body.message("Your hands are shaking too much to do anything")
            return False
        return True

    def on_completion(self):
        self.body.message("You feel less shaky")


class Dizziness(Condition):

    def on_start(self):
        if 'severe' in self.details:
            self.prob = 0.4
            self.body.message('You feel very lightheaded')
        else:
            self.prob = 0.2
            self.body.message('You feel dizzy')

    def on_progression(self, time):
        if random() < self.prob:
            self.body.message("Everything swims in front of your eyes")

    def on_interact(self, obj, time):
        if random() < self.prob:
            self.body.message("You are too dizzy to do anything")
            return False
        return True

    def on_completion(self):
        self.body.message("You feel less dizzy")


class Coughing(Condition):

    def on_start(self):
        if 'severe' in self.details:
            self.prob = 0.4
        else:
            self.prob = 0.2

    def on_progression(self, time):
        if random() < self.prob:
            if 'severe' in self.details:
                self.body.message("You cough violently")
                self.ss('fatigue', self.gs('fatigue') * 1.08)
            else:
                self.body.message("You cough")
                self.ss('fatigue', self.gs('fatigue') * 1.02)

    def on_interact(self, obj, time):
        return True

    def on_completion(self):
        pass


class Fever(Condition):

    def on_start(self):
        if 'severe' in self.details:
            self.body.message("You feel very ill")
            self.prob = 0.4
        else:
            self.body.message("You feel ill")
            self.prob = 0.2

    def on_progression(self, time):
        if random() < self.prob:
            if random() < 0.5:
                self.body.message("You have a strong feeling of malaise")
            else:
                self.body.message("Your body is burning up")
            self.ss('fatigue', self.gs('fatigue') * 1.01)

    def on_interact(self, obj, time):
        return True

    def on_completion(self):
        pass


class Chills(Condition):

    def on_start(self):
        if 'severe' in self.details:
            self.prob = 0.4
        else:
            self.prob = 0.2

    def on_progression(self, time):
        if random() < self.prob:
            if random() < 0.5:
                self.body.message("You shiver")
            else:
                self.body.message("Your feel cold")

    def on_interact(self, obj, time):
        if random() < self.prob:
            self.body.message("It's too cold to do anything")
            return False
        return True

    def on_completion(self):
        pass


# Infectious Diseases:


class Pneumonia(Condition):

    def on_start(self):
        self.prob = 0.2
        self.sc('pneumonia_cough', Cough(), {'severe': True})
        self.sc('pneumonia_fever', Feber(), {})

    def on_progression(self, time):
        if random() < self.prob:
            self.body.message("You feel a sharp pain in your chest")

    def on_interact(self, obj, time):
        return True

    def on_completion(self):
        pass
