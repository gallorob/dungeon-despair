import random
from typing import List, Tuple

from dungeon_despair.domain.encounter import Encounter
from heroes_party import HeroParty


class ActionEngine:
	def __init__(self):
		self.trap_disarm_chance = 0.8
		self.trap_disarm_stress = -20
		self.trap_dmg_percentage = 0.1
		
		self.treasure_loot_chance = 0.8
		self.treasure_loot_stress = -15
	
	def init_trap_encounter(self,
	                        encounter: Encounter) -> List[str]:
		trap = encounter.entities['trap'][0]
		return [f'You find <b>{trap.name}</b>!']
	
	def init_treasure_encounter(self,
	                            encounter: Encounter) -> List[str]:
		treasure = encounter.entities['treasure'][0]
		return [f'You find <b>{treasure.name}</b>!']
	
	def resolve_trap_encounter(self,
	                           encounter: Encounter,
	                           heroes: HeroParty) -> Tuple[List[str], int]:
		trap = encounter.entities['trap'][0]
		messages = []
		disarmed = 1
		if random.random() <= self.trap_disarm_chance:
			messages.append(f'You successfully disarm {trap.name}!')
		else:
			messages.append(f'You fail to disarm {trap.name}!')
			hero = random.choice(heroes.party)
			hero.hp -= hero.hp * self.trap_dmg_percentage
			disarmed = -1
		encounter.entities['trap'].pop(0)
		return messages, self.trap_disarm_stress * disarmed
	
	def resolve_treasure_encounter(self,
	                               encounter: Encounter) -> Tuple[List[str], int]:
		treasure = encounter.entities['treasure'][0]
		messages = []
		looted = 1
		if random.random() <= self.treasure_loot_chance:
			messages.append(f'You loot <b>{treasure.name}</b>!')
		else:
			messages.append(f'<b>{treasure.name}</b> is fake!')
			looted = -1
		encounter.entities['treasure'].pop(0)
		return messages, self.treasure_loot_stress * looted