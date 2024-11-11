import copy
import random
from typing import List, Tuple, Optional, Set, Dict

import numpy as np

from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.entities.entity import Entity
from dungeon_despair.domain.entities.hero import Hero
from engine.actions_engine import LootingChoice
from engine.game_engine import GameEngine
from engine.message_system import msg_system
from engine.movement_engine import Destination
from engine.stress_system import stress_system
from player.base_player import Player, PlayerType
from ui_components.action_menu import treasure_choices


# TODO: Adding a simulation depth would allows heroes to move "tactfully"


class AIPlayer(Player):
	def __init__(self):
		super().__init__(PlayerType.AI)
		self.visited_areas: Dict[str, int] = {}
		self.game_engine_copy: Optional[GameEngine] = None
	
	def update_visited_areas(self,
	                         dest: Destination) -> None:
		k = str(dest)
		if k in self.visited_areas.keys():
			self.visited_areas[k] += 1
		else:
			self.visited_areas[k] = 1
	
	def simulate_combat(self,
	                    depth: int):
		pass
	
	def pick_actions(self,
	                 **kwargs) -> int:
		self.game_engine_copy = kwargs['game_engine_copy']
		actions = kwargs['actions']
		prev_stress = stress_system.stress
		curr_msg_queue = msg_system.get_queue()
		stress_diffs = []
		attacker, _ = self.game_engine_copy.attacker_and_idx
		for i, action in enumerate(actions):
			eng_copy = copy.deepcopy(self.game_engine_copy)
			eng_copy.process_attack(i)
			eng_copy.tick()
			stress_diff = stress_system.stress - prev_stress
			stress_system.stress -= stress_diff  # reset stress to before simulation
			stress_diff *= 1 if isinstance(attacker, Hero) else -1  # heroes want to minimize their stress
			stress_diffs.append(stress_diff)
			del eng_copy
		del self.game_engine_copy
		msg_system.queue = curr_msg_queue  # reset messages queue to before simulation
		return stress_diffs.index(min(stress_diffs))
	
	def pick_moving(self,
	                **kwargs) -> int:
		# TODO: Decide what to optimize when moving
		attacker_type = kwargs['attacker_type']
		n_heroes = kwargs['n_heroes']
		n_enemies = kwargs['n_enemies']
		if attacker_type == Hero:
			idx = random.choice(range(n_heroes))
			return idx
		else:
			idx = random.choice(range(n_enemies))
			return idx + n_heroes
	
	def pick_destination(self,
	                     **kwargs) -> Destination:
		destinations = kwargs['destinations']
		probs = np.ones(len(destinations)) * (1 / len(destinations))
		for i, destination in enumerate(destinations):
			if str(destination) in self.visited_areas.keys():
				probs[i] /= self.visited_areas[str(destination)]
		probs /= np.sum(probs)
		idx = np.random.choice(range(len(destinations)), p=probs)
		destination = destinations[idx]
		return destination
	
	def choose_disarm_trap(self,
	                       **kwargs) -> bool:
		return True
	
	def choose_loot_treasure(self,
	                         **kwargs) -> Optional[LootingChoice]:
		self.game_engine_copy = kwargs['game_engine_copy']
		prev_stress = stress_system.stress
		curr_msg_queue = msg_system.get_queue()
		stress_diffs = []
		for looting_choice in LootingChoice:
			eng_copy = copy.deepcopy(self.game_engine_copy)
			eng_copy.process_looting(choice=looting_choice)
			eng_copy.tick()
			stress_diff = stress_system.stress - prev_stress
			stress_system.stress -= stress_diff  # reset stress to before simulation
			stress_diffs.append(stress_diff)
		msg_system.queue = curr_msg_queue  # reset messages queue to before simulation
		return list(LootingChoice)[stress_diffs.index(min(stress_diffs))]