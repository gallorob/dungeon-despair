import random
from enum import auto, Enum

from dungeon_despair.domain.encounter import Encounter
from dungeon_despair.domain.entities.hero import Hero
from dungeon_despair.domain.entities.treasure import Treasure
from engine.message_system import msg_system
from engine.modifier_system import ModifierSystem
from engine.stress_system import stress_system
from heroes_party import HeroParty


class LootingChoice(Enum):
	IGNORE = auto()
	INSPECT_AND_LOOT = auto()
	LOOT = auto()


class ActionEngine:
	
	def resolve_trap_encounter(self,
	                           encounter: Encounter,
	                           heroes: HeroParty) -> None:
		trap = encounter.traps[0]
		hero = random.choice(heroes.party)
		# in darkest dungeon:
		# chance to disarm: random hero.trap_resist (+40% if trap is spotted) - trap.chance
		p = hero.trap_resist - trap.chance
		if random.random() <= p:
			msg_system.add_msg(f'<b>{hero.name}</b> successfully disarms {trap.name}!')
			stress_system.process_trap(hero=hero, disarmed=True)
		else:
			dmg_dealt = min(hero.hp, trap.dmg)
			hero.hp -= dmg_dealt
			msg_system.add_msg(f'<b>{hero.name}</b> fails to disarms {trap.name} and receives <i>{dmg_dealt}</i> damage!')
			stress_system.process_trap(hero=hero, dmg_dealt=dmg_dealt, disarmed=False)
			ModifierSystem.try_add_modifier(target=hero,
			                                modifier=trap.modifier)
		encounter.entities['trap'].pop(0)
	
	def resolve_treasure_encounter(self,
	                               treasure: Treasure,
	                               hero: Hero,
	                               encounter: Encounter,
	                               choice: LootingChoice) -> None:
		# in darkest dungeon:
		# curios have a ~75% chance of containing loot and ~25% chance of being empty
		# plus other effects, so... we do what we want here
		if random.random() <= treasure.trapped_chance:
			if random.random() <= (hero.trap_resist if choice == LootingChoice.INSPECT_AND_LOOT else 1.0):
				msg_system.add_msg(f'<b>{hero.name}</b> successfully disarms the trap in {treasure.name} and loots it!')
				stress_system.process_disarmed_treasure(inspected=choice == LootingChoice.INSPECT_AND_LOOT)
			else:
				msg_system.add_msg(f'<b>{hero.name}</b> triggers the trap in {treasure.name}!')
				dmg_dealt = min(hero.hp, treasure.dmg)
				hero.hp -= dmg_dealt
				stress_system.process_triggered_treasure(hero=hero, dmg_dealt=dmg_dealt,
				                                         inspected=choice == LootingChoice.INSPECT_AND_LOOT)
				ModifierSystem.try_add_modifier(target=hero, modifier=treasure.modifier)
		else:
			msg_system.add_msg(f'<b>{hero.name}</b> loots {treasure.name}!')
			stress_system.process_safe_treasure(inspected=choice == LootingChoice.INSPECT_AND_LOOT)
		encounter.entities['treasure'].pop(0)
