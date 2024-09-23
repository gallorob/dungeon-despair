import random

from player.base_player import Player, PlayerType


class RandomPlayer(Player):
	def __init__(self):
		super().__init__(PlayerType.RANDOM)
	
	def pick_attack(self,
	                attacker) -> int:
		return random.randint(0, len(attacker.attacks))
	
	def pick_destination(self,
	                     destinations):
		return random.choice(destinations)