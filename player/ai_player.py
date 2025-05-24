import copy
import random
from typing import List, Tuple, Optional, Set, Dict

from dungeon_despair.domain.utils import ActionType
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
from configs import configs


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
	
	def pick_destination(self,
	                     **kwargs) -> Destination:
		destinations = kwargs['destinations']
		areas_count = kwargs['unk_areas']
		dest_count = [areas_count[str(destination)] + self.visited_areas.get(str(destination), 0) for destination in destinations]
		destination = destinations[np.argmin(dest_count)]
		return destination
	
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
			# only evaluate active actions
			if action.active:  # pass has 10 stress, move has 0, both are active
				eng_copy.process_attack(i)
				eng_copy.tick()
				stress_diff = stress_system.stress - prev_stress
				stress_system.stress -= stress_diff  # reset stress to before simulation
				# if action is a move, continue the simulation
				if action.type == ActionType.MOVE.value:
					curr_eng_copy = copy.deepcopy(eng_copy)
					idx = self.pick_moving(**{'n_heroes': len(eng_copy.heroes.party),
							 				'n_enemies': len(eng_copy.current_encounter.enemies),
											'game_engine_copy': eng_copy})
					eng_copy = curr_eng_copy
					self.game_engine_copy = kwargs['game_engine_copy']
					del curr_eng_copy
					if idx is not None:
						eng_copy.process_move(idx)
						stress_diff = stress_system.stress - prev_stress
						stress_system.stress -= stress_diff
					else: # cannot move to a better position
						# setting it here because it's 0 in the stress system
						# set it to whatever the stress from passing was, + 1
						stress_diff = stress_diffs[-1] + 1
			else:
				stress_diff = 999999
			stress_diff *= 1 if isinstance(attacker, Hero) else -1  # heroes want to minimize their stress
			stress_diffs.append(stress_diff)
			del eng_copy
		del self.game_engine_copy
		msg_system.queue = curr_msg_queue  # reset messages queue to before simulation
		return stress_diffs.index(min(stress_diffs))
	
	def pick_moving(self,
	                **kwargs) -> Optional[int]:
		n_heroes = kwargs['n_heroes']
		n_enemies = kwargs['n_enemies']
		self.game_engine_copy = kwargs['game_engine_copy']
		curr_msg_queue = msg_system.get_queue()
		# move to maximize number of possible attacks
		n_attacks = sum([1 if x.active else 0 for x in self.game_engine_copy.combat_engine.actions])
		curr_idx = self.game_engine_copy.attacker_and_idx[1]
		idxs_range = range(0, n_heroes) if curr_idx < n_heroes else range(n_heroes, n_heroes + n_enemies)
		for i, idx in enumerate(idxs_range):
			if idx != curr_idx:
				eng_copy = copy.deepcopy(self.game_engine_copy)
				eng_copy.process_move(idx=idx)
				eng_copy.tick()
				new_n_attacks = sum([1 if x.active else 0 for x in self.game_engine_copy.combat_engine.actions])
				if new_n_attacks > n_attacks:
					curr_idx = idx
					n_attacks = new_n_attacks
		# if no movement increases number of possible attacks, cancel the move
		if curr_idx == self.game_engine_copy.attacker_and_idx[1]:
			curr_idx = None
		del self.game_engine_copy
		msg_system.queue = curr_msg_queue  # reset messages queue to before simulation
		return curr_idx
	
	def choose_disarm_trap(self,
	                       **kwargs) -> bool:
		# There is no choice
		return True
	
	def choose_loot_treasure(self,
	                         **kwargs) -> LootingChoice:
		self.game_engine_copy = kwargs['game_engine_copy']
		prev_stress = stress_system.stress
		curr_msg_queue = msg_system.get_queue()
		stress_diffs = []
		for looting_choice in LootingChoice:
			avg_stress_diffs = []
			# Multiple attempts for more informed choice
			for _ in range(configs.game.sim_depth):
				eng_copy = copy.deepcopy(self.game_engine_copy)
				eng_copy.process_looting(choice=looting_choice)
				eng_copy.tick()
				stress_diff = stress_system.stress - prev_stress
				stress_system.stress -= stress_diff  # reset stress to before simulation
				avg_stress_diffs.append(stress_diff)
			stress_diffs.append(np.mean(avg_stress_diffs))
		msg_system.queue = curr_msg_queue  # reset messages queue to before simulation
		return list(LootingChoice)[stress_diffs.index(min(stress_diffs))]