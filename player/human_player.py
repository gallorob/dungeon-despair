from typing import List

from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.entities.entity import Entity
from dungeon_despair.domain.entities.hero import Hero
from player.base_player import Player, PlayerType


class HumanPlayer(Player):
	def __init__(self):
		super().__init__(PlayerType.HUMAN)
	
	def pick_actions(self,
	                 **kwargs) -> int:
		pass
	
	def pick_moving(self,
	                **kwargs) -> int:
		pass
	
	def pick_destination(self,
	                     **kwargs):
		pass
	
	def choose_disarm_trap(self,
	                       **kwargs) -> bool:
		pass
	
	def choose_loot_treasure(self,
	                         **kwargs) -> bool:
		pass
