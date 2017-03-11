Fatigue algorithm:

- Fatigue is set to $BASE_FATIGUE + DISEASE_FATIGUE$.
- Every action increases fatigue by a certain percentage of the previous fatigue.
- Every action takes $BASE_ACTION_TIME ^ (1 + k * (CURRENT_FATIGUE / MAX_FATIGUE))$ seconds. (where $k$ is affected by other injuries)
- If fatigue is greater than $MAX_FATIGUE$, the player falls unconscious
- Sleeping reduces fatigue at $BASE_FATIGUE_RECOVER_RATE * DISEASE_FATIGUE_REGEN_PENALTY$.
- Sleeping lasts for $RAND(0.8, 1.2) * REQUIRED_SLEEP_TIME$. If fatigue is greater than $VERY_FATIGUED$, then sleeping lasts for $RAND(1.0, 1.5) * REQUIRED_SLEEP_TIME$.

Nutrition algorithm:
- Nutrition starts at $BASE_NUTRITION$
- Food increases nutrition by the amount of nutrition of the food
- Every turn, nutrition goes down by 1
- Nutrition acts as an additional source of base fatigue: $1 - (BASE_NUTRITION / MAX_NUTRITION) * HUNGER_PENALTY$.

Blood sugar algorithm:

- Blood sugar during fasting is normally at 85 mg/dl.
- Eating food with the "high carb" trait will cause the blood sugar to double over the course of the next hour, and then go down linearly.
- Eating food with the "medium carb" trait will cause the blood sugar to increase 1.5x over the course of the next hour, and then go down linearly.
- Eating food with the "low carb" trait will cause blood sugar to increase 1.3x over the course of the next hour, and then go down linearly.
- Low blood sugar randomly causes some of the following symptoms:
  - Blurry vision: "Things look hazy"
  - Rapid heartbeat
  - Anxiety
  - Fatigue increases by factor 0.3
  - Headache: "You get a minor headache"
