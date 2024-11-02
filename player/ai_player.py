import copy
from typing import List, Tuple, Optional

import numpy as np

from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.entities.entity import Entity
from dungeon_despair.domain.entities.hero import Hero
from engine.game_engine import GameEngine
from player.base_player import Player, PlayerType


# TODO: Adding a simulation depth would allows heroes to move "tactfully"


class AIPlayer(Player):
	def __init__(self):
		super().__init__(PlayerType.AI)
		self.visited_areas = {}
		self.game_engine_copy: Optional[GameEngine] = None
	
	def pick_attack(self,
	                attacks) -> int:
		curr_stress = self.game_engine_copy.stress
		stress_diffs = []
		attacker, _ = self.game_engine_copy.get_current_attacker_with_idx()
		for i, attack in enumerate(attacks):
			eng_copy = copy.deepcopy(self.game_engine_copy)
			_ = eng_copy.process_attack(i)
			_ = eng_copy.check_dead_entities()
			new_stress = eng_copy.stress
			mult = -1 if isinstance(attacker, Hero) else 1
			stress_diffs.append(mult * (new_stress - curr_stress))
		# print(f'AIPlayer.pick_attack - attacks={[attack.name for attack in attacks]} {stress_diffs=} - Picked: {attacks[stress_diffs.index(max(stress_diffs))].name}')
		return stress_diffs.index(max(stress_diffs))
	
	def pick_moving(self,
	                attacker: Entity,
	                heroes: List[Hero],
	                enemies: List[Enemy]) -> int:
		if isinstance(attacker, Hero):
			idx = np.random.choice(range(len(heroes)))
			return idx
		else:
			idx = np.random.choice(range(len(enemies)))
			return idx + len(heroes)
	
	def pick_destination(self,
	                     destinations: List[Tuple[str, int]]) -> Tuple[str, int]:
		verbose_destinations = [f'{x}_{idx}' for (x, idx) in destinations]
		probs = np.ones(len(verbose_destinations)) * (1 / len(verbose_destinations))
		for i, destination in enumerate(verbose_destinations):
			if destination in self.visited_areas.keys():
				probs[i] /= self.visited_areas[destination]
		probs /= np.sum(probs)
		idx = np.random.choice(range(len(verbose_destinations)), p=probs)
		destination, encounter_idx = destinations[idx]
		# print(f'AIPlayer.pick_destination - {destinations=} {probs=} - Picked: {destination} {encounter_idx}')
		return destination, encounter_idx
	
	def choose_disarm_trap(self) -> bool:
		p = np.random.rand() < 0.5
		# print(f'AIPlayer.choose_disarm_trap - {p=}')
		return p
	
	def choose_loot_treasure(self) -> bool:
		p = np.random.rand() < 0.5
		# print(f'AIPlayer.choose_loot_treasure - {p=}')
		return p
