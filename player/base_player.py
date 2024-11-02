from enum import auto, Enum
from typing import List

from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.entities.entity import Entity
from dungeon_despair.domain.entities.hero import Hero


class PlayerType(Enum):
	HUMAN: int = auto()
	RANDOM: int = auto()
	LLM: int = auto()
	AI: int = auto()


class Player:
	def __init__(self,
	             player_type: PlayerType):
		self.type = player_type
	
	def pick_attack(self,
	                attacks) -> int:
		pass
	
	def pick_moving(self,
	                attacker: Entity,
	                heroes: List[Hero],
	                enemies: List[Enemy]) -> int:
		pass
	
	def pick_destination(self,
	                     destinations):
		pass
	
	def choose_disarm_trap(self) -> bool:
		pass
	
	def choose_loot_treasure(self) -> bool:
		pass
