import random
from typing import List, Tuple

from configs import configs
from dungeon_despair.domain.encounter import Encounter
from dungeon_despair.domain.entities.trap import Trap
from dungeon_despair.domain.entities.treasure import Treasure
from heroes_party import HeroParty


class ActionEngine:
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
		trap: Trap = encounter.entities['trap'][0]
		messages = []
		hero = random.choice(heroes.party)
		# in darkest dungeon:
		# chance to disarm: random hero.trap_resist (+40% if trap is spotted) - trap.chance
		p = hero.trap_resist - trap.chance
		if random.random() <= p:
			messages.append(f'<b>{hero.name}</b> successfully disarms {trap.name}!')
			stress_delta = configs.game.stress.disarm_trap
		else:
			dmg_dealt = trap.dmg
			hero.hp -= dmg_dealt
			messages.append(f'<b>{hero.name}</b> fails to disarms {trap.name} and receives <i>{dmg_dealt}</i> damage!')
			# Apply debuffs to the hero here if there are any from the trap...
			stress_delta = configs.game.stress.trigger_trap + dmg_dealt
		if stress_delta < 0: stress_delta *= (1 - hero.stress_resist)
		encounter.entities['trap'].pop(0)
		return messages, int(stress_delta)
	
	def resolve_treasure_encounter(self,
	                               encounter: Encounter,
	                               heroes: HeroParty,
	                               do_inspect: bool) -> Tuple[List[str], int]:
		treasure: Treasure = encounter.entities['treasure'][0]
		messages = []
		hero = random.choice(heroes.party)
		# in darkest dungeon:
		# curios have a ~75% chance of containing loot and ~25% chance of being empty
		# plus other effects, so... we do what we want here
		if random.random() <= treasure.trapped_chance:
			if random.random() <= (hero.trap_resist if do_inspect else 1.0):
				messages.append(f'<b>{hero.name}</b> successfully disarms the trap in {treasure.name} and loots it!')
				stress_delta = configs.game.stress.loot_treasure + configs.game.stress.disarm_trap
				stress_delta += configs.game.stress.no_inspect_treasure if not do_inspect else 0
			else:
				messages.append(f'<b>{hero.name}</b> triggers the trap in {treasure.name}!')
				dmg_dealt = treasure.dmg
				hero.hp -= dmg_dealt
				stress_delta = configs.game.stress.trigger_trapped_treasure + dmg_dealt
				stress_delta -= configs.game.stress.no_inspect_treasure if not do_inspect else 0
		else:
			messages.append(f'<b>{hero.name}</b> loots {treasure.name}!')
			stress_delta = configs.game.stress.loot_treasure
			stress_delta += configs.game.stress.no_inspect_treasure if not do_inspect else 0
		if stress_delta < 0: stress_delta *= (1 - hero.stress_resist)
		stress_delta = int(stress_delta)
		encounter.entities['treasure'].pop(0)
		return messages, stress_delta
