import random
from typing import List

from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.entities.entity import Entity
from dungeon_despair.domain.entities.hero import Hero
from player.base_player import Player, PlayerType


class RandomPlayer(Player):
	def __init__(self):
		super().__init__(PlayerType.RANDOM)
	
	def pick_attack(self,
	                attacks) -> int:
		active_attacks = [attack for attack in attacks if attack.active]
		random_attack = random.choice(active_attacks)
		return attacks.index(random_attack)
	
	def pick_moving(self,
	                attacker: Entity,
	                heroes: List[Hero],
	                enemies: List[Enemy]) -> int:
		if isinstance(attacker, Hero):
			idx = random.choice(range(len(heroes)))
			return idx
		else:
			idx = random.choice(range(len(enemies)))
			return idx + len(heroes)
	
	def pick_destination(self,
	                     destinations):
		return random.choice(destinations)
	
	def choose_disarm_trap(self) -> bool:
		return random.random() >= 0.5
	
	def choose_loot_treasure(self) -> bool:
		return random.random() >= 0.5
