import logging
from opentelemetry import trace

import numpy as np
import random

#---------------------------------
# Configure logging
#---------------------------------
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)

#---------------------------------
# Compute Reinforce
class ReinforcedService:

    def __init__(self):
        # --- 1. CONFIGURATION ---
        self.ALPHA = 0.1
        self.GAMMA = 0.9
        self.EPSILON = 0.2
        self.EPOCHS = 5000

        self.MOVE_AMOUNT = 20 
        self.TOTAL_CAPACITY = 100000
        self.TIERS = ['0', '1', '2', '3']
        
        # 3 (idle, balanced, pressure)
        self.STATUS = 3

        self.ACTIONS = {
            0: "Stay",
            1: ("3", "0"), 2: ("2", "0"), 3: ("1", "0"), # Moves to A (tier 3 moves to tier 0, etc.)
            4: ("3", "1"), 5: ("2", "1"), 6: ("0", "1"), # Moves to B (tier 3 moves to tier 1, etc.)
            7: ("3", "2"), 8: ("1", "2"), 9: ("0", "2"), # Moves to C (tier 3 moves to tier 2, etc.)
            10: ("2", "3"), 11: ("1", "3"), 12: ("0", "3") # Moves to D (tier 2 moves to tier 3, etc.)
        }

        self.STATES = [(a, b, c, d) for a in range(self.STATUS) for b in range(self.STATUS) for c in range(self.STATUS) for d in range(self.STATUS)]
        
        self.Q_TABLE = np.zeros((len(self.STATES), len(self.ACTIONS)))

        # Global state memory for Hysteresis
        self.PREV_STATUS = {'0': 1, '1': 1, '2': 1, '3': 1}

    def get_state_index_with_hysteresis(self, usage_dict, limit_dict, verbose=False):
        st = tuple(self.get_state_index_with_hysteresis(t, usage_dict[t], limit_dict[t]) for t in self.TIERS)
        return self.STATES.index(st)

    def get_tier_status_with_hysteresis(self, tier_name, usage, limit):
        ratio = usage / limit
        current_prev = self.PREV_STATUS[tier_name]
        
        # Logic for PRESSURE (State 2)
        if current_prev == 2:
            # If already in Pressure, stay there unless usage drops below 65%
            new_status = 2 if ratio > 0.65 else 1
        elif ratio > 0.75:
            # Enter Pressure only if exceeding 75%
            new_status = 2
        
        # Logic for IDLE (State 0)
        elif current_prev == 0:
            # If already Idle, stay there unless usage climbs above 35%
            new_status = 0 if ratio < 0.35 else 1
        elif ratio < 0.25:
            # Enter Idle only if dropping below 25%
            new_status = 0
        
        else:
            new_status = 1 # Stay Balanced
            
        self.PREV_STATUS[tier_name] = new_status

        return new_status

    def get_tier_status(self, usage, limit):
        ratio = usage / limit
        if ratio > 0.8: return 2   # Under Pressure
        if ratio < 0.4: return 0   # Idle 
        return 1                   # Balanced
        
    def get_state_index(self, usage_dict, limit_dict, verbose=False):
        #logger.debug("get_state_index: %s", usage_dict, limit_dict)

        # 1. Simplify the 4 tiers into statuses (0, 1, or 2)
        statuses = []

        for t in self.TIERS:
            status = self.get_tier_status(usage_dict[t], limit_dict[t])
            statuses.append(status)
        
        # 2. Create the tuple (The 'Snapshot')
        st = tuple(statuses)
        
        # 3. Find the index in our 81-state map
        idx = self.STATES.index(st)
        
        if verbose:
            print(f"   --- Decision Logic ---")
            print(f"   Current Lim:   {limit_dict}")
            print(f"   Current Usage: {usage_dict}")
            print(f"   State Tuple: {st} (Index: {idx})")

            # Translation of the tuple for humans
            status_map = {0: "IDLE", 1: "OK", 2: "PRESSURE"}
            readable = [f"{self.TIERS[i]}:{status_map[st[i]]}" for i in range(4)]
            print(f"   Readable:    {' | '.join(readable)}")
            
        return idx

    def calculate_reward(self, usage, limits):
        reward = 0
        for t in self.TIERS:
            # Penalty for Pressure (>70%)
            if usage[t] / limits[t] > 0.8:
                reward -= 20
            # Penalty for Waste (<30%)
            if usage[t] / limits[t] < 0.4:
                reward -= 10
            # Critical Penalty for Starvation (Usage > Limit)
            if usage[t] > limits[t]:
                reward -= 100
        return reward

    def apply_action(self, action_idx, current_limits):
        new_limits = current_limits.copy()
        if action_idx == 0:
            return new_limits
        
        source, target = self.ACTIONS[action_idx]
        
        # Check if source has enough to give (Minimum floor of 40 RPS per tier)
        if new_limits[source] >= (25 + self.MOVE_AMOUNT):
            new_limits[source] -= self.MOVE_AMOUNT
            new_limits[target] += self.MOVE_AMOUNT
            
        # Validation: Ensure we haven't broken the max RPS total
        #assert sum(new_limits.values()) == self.TOTAL_CAPACITY, "Capacity mismatch!"
        
        return new_limits

    def train_model(self, data) -> dict:
        with tracer.start_as_current_span("service.train_model"):
            logger.info("func.train_model()")
            logger.debug("data: %s", data)

            q_table = np.zeros((len(self.STATES), len(self.ACTIONS)))
            verbose=False

            scenarios = data["scenarios"]
            limit_data = data["limit"]

            print("scenarios:", scenarios)
            print("limit_data:", limit_data)

            for _ in range(self.EPOCHS):
                # choose random from scenario
                choosen_scenario = random.choice(scenarios)
                limit = limit_data

                if verbose:
                    print("choosen_scenario:", choosen_scenario)

                for _step in range(20): # Allow 20 moves per epoch to find balance
                    if verbose:
                        print(".._step:",_step)
   
                    state_idx = self.get_state_index(choosen_scenario, limit, verbose)
                        
                    if verbose:                            
                        print("..state_idx:",state_idx)

                    if random.uniform(0, 1) < self.EPSILON:
                        action = random.randint(0, len(self.ACTIONS)-1)
                        if verbose:
                            print(".. *EXPLORATION*")
                    else:
                        action = np.argmax(q_table[state_idx])

                    # Apply the action (balance rps from tiers)
                    new_limit = self.apply_action(action, limit)

                    # Calc the reward according the new limit
                    reward = self.calculate_reward(choosen_scenario, new_limit)

                    next_s_idx = self.get_state_index(choosen_scenario, new_limit, verbose)

                    # Bellman Equation Update
                    q_table[state_idx, action] += self.ALPHA * (reward + self.GAMMA * np.max(q_table[next_s_idx]) - q_table[state_idx, action])

                    if verbose:        
                        print(f"..q_table[state_idx {state_idx}, action {action}] :", q_table[state_idx, action], q_table[state_idx] )
                    
                    limit = new_limit

            self.Q_TABLE = q_table

            print("Training completed. Final Q-Table:")
            print(self.Q_TABLE)

            return True

    def action(self, data) -> dict:
        logger.info("func.action()")
        print(self.Q_TABLE)

        scenario = data["scenario"]
        limit = data["limit"]
        
        for i in range(30):
            idx = self.get_state_index(scenario, limit)
            best_action = np.argmax(self.Q_TABLE[idx])
            limit = self.apply_action(best_action, limit)
            action_name = self.ACTIONS[best_action]
            print(f"Step {i+1}: Action {action_name} -> New Limits: {limit}")

        return limit