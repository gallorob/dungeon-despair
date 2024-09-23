from player.base_player import Player, PlayerType


class HumanPlayer(Player):
	def __init__(self):
		super().__init__(PlayerType.HUMAN)
	
	def pick_attack(self,
	                attacker) -> int:
		pass
	
	def pick_destination(self,
	                     destinations):
		pass