from player.base_player import Player, PlayerType


class HumanPlayer(Player):
	def __init__(self):
		super().__init__(PlayerType.HUMAN)
	
	def pick_attack(self,
	                attacks) -> int:
		pass
	
	def pick_destination(self,
	                     destinations):
		pass
	
	def choose_disarm_trap(self) -> bool:
		pass
	
	def choose_loot_treasure(self) -> bool:
		pass