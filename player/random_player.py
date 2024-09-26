import random

from player.base_player import Player, PlayerType


class RandomPlayer(Player):
	def __init__(self):
		super().__init__(PlayerType.RANDOM)
	
	def pick_attack(self,
	                attacks) -> int:
		active_attacks = [attack for attack in attacks if attack.active]
		random_attack = random.choice(active_attacks)
		return attacks.index(random_attack)
	
	def pick_destination(self,
	                     destinations):
		return random.choice(destinations)