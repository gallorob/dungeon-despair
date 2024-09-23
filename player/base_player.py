from enum import auto, Enum


class PlayerType(Enum):
	HUMAN: int = auto()
	RANDOM: int = auto()


class Player:
	def __init__(self,
	             player_type: PlayerType):
		self.type = player_type
	
	def pick_attack(self,
	                attacker) -> int:
		pass
	
	def pick_destination(self,
	                     destinations):
		pass