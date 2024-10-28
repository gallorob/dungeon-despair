from typing import List

from dungeon_despair.domain.encounter import Encounter
from engine.game_engine import GameEngine
from utils import get_current_encounter


class CombatContext:
	heroes_status: str
	enemies_status: str
	attacking: str
	attacks: List[str]
	targeted: List[List[str]]
	expected_dmg: List[List[float]]
	stress: int
	combat_history: List[str]


class TreasureContext:
	heroes_status: str
	stress: int
	desc: str
	outcome: str


class TrapContext:
	heroes_status: str
	stress: int
	desc: str
	outcome: str


class MovementContext:
	heroes_status: str
	stress: int
	destinations: List[str]
	descriptions: List[str]
	encounters_desc: List[List[str]]
	


class ContextManager:
	def __init__(self):
		self.history_n = 10
	
	def get_combat_context(self,
	                       game_engine: GameEngine,
	                       events_history: List[str]) -> CombatContext:
		curr_encounter = get_current_encounter(level=game_engine.game_data,
		                                       encounter_idx=game_engine.movement_engine.encounter_idx)
		context = CombatContext()
		# get heroes status
		context.heroes_status = game_engine.heroes.get_party_status()
		# get enemies status
		enemies_status = 'This is the current enemies status:'
		for enemy in curr_encounter.entities['enemy']:
			enemies_status += f'\n{enemy.name}: {enemy.hp} HP'
		enemies_status += '\n'
		context.enemies_status = enemies_status
		# get attacker name
		context.attacking = game_engine.get_current_attacker_with_idx()[0].name
		# get attacks, targeted, and expected_dmg
		attacks_names, targeted, expected_dmg = [], [], []
		attacks = game_engine.get_attacks()
		positioned_entities = game_engine.combat_engine.get_entities(game_engine.heroes, game_engine.game_data)
		context.attacks = [attack.name for attack in attacks]
		for i, attack in enumerate(attacks):
			targ, dmgs = [], []
			targeted_idxs = game_engine.get_targeted_idxs(attack_idx=i)
			for targeted_idx in targeted_idxs:
				target_entity = positioned_entities[targeted_idx]
				targ.append(target_entity.name)
				dmg = attack.base_dmg * (1 - target_entity.prot)
				dmgs.append(dmg)
			targeted.append(targ)
			expected_dmg.append(dmgs)
		context.targeted = targeted
		context.expected_dmg = expected_dmg
		# get stress
		context.stress = game_engine.stress
		# get combat history
		try:
			soe_idx = events_history.index('<b><i>### NEW ENCOUNTER</i></b>')
			events_history = events_history[soe_idx:]
		except ValueError as e:
			pass
		context.combat_history = events_history
		return context
	
	def get_treasure_context(self,
	                         game_engine: GameEngine) -> TreasureContext:
		curr_encounter = get_current_encounter(level=game_engine.game_data,
		                                       encounter_idx=game_engine.movement_engine.encounter_idx)
		context = TreasureContext()
		# get heroes status
		context.heroes_status = game_engine.heroes.get_party_status()
		# get stress
		context.stress = game_engine.stress
		# get treasure description
		treasure = curr_encounter.entities['treasure'][0]
		context.desc = f'{treasure.name}: {treasure.description} (loot: {treasure.loot})'
		context.outcome = f'Successfully looting this treasure will reduce stress by -15 point. Failing to do so will increase the stress by 15 points.'  # TODO: From config
		return context
		
	def get_trap_context(self,
	                     game_engine: GameEngine) -> TrapContext:
		curr_encounter = get_current_encounter(level=game_engine.game_data,
		                                       encounter_idx=game_engine.movement_engine.encounter_idx)
		context = TrapContext()
		# get heroes status
		context.heroes_status = game_engine.heroes.get_party_status()
		# get stress
		context.stress = game_engine.stress
		# get trap description
		trap = curr_encounter.entities['trap'][0]
		context.desc = f'{trap.name}: {trap.description} (effect: {trap.effect})'
		context.outcome = f'Successfully disarming this trap will reduce stress by -20 point. Failing to do so will increase the stress by 20 points and inflict damage equal to 10% of one of the heroes HP.'  # TODO: From config
		return context
	
	@staticmethod
	def __get_encounter_description(encounter: Encounter) -> str:
		desc = ''
		if len(encounter.entities['enemy']) > 0:
			desc += 'There seems to be enemies present here. '
		else:
			desc += 'There seems to be no enemies present. '
		if len(encounter.entities['trap']) > 0:
			desc += 'There seems to be a trap nearby here. '
		else:
			desc += 'There does not seem to be any traps nearby. '
		if len(encounter.entities['treasure']) > 0:
			desc += 'There seems to be a treasure nearby here.'
		else:
			desc += 'There does not seem to be any treasures nearby.'
		return desc
		
	def get_movement_context(self,
	                         game_engine: GameEngine) -> MovementContext:
		context = MovementContext()
		# get heroes status
		context.heroes_status = game_engine.heroes.get_party_status()
		# get stress
		context.stress = game_engine.stress
		available_destinations = game_engine.movement_engine.available_destinations(level=game_engine.game_data)
		for (name, idx) in available_destinations:
			if name in game_engine.game_data.rooms.keys():
				area = game_engine.game_data.rooms[name]
				context.encounters_desc.append([ContextManager.__get_encounter_description(area.encounter)])
			elif name in game_engine.game_data.corridors.keys():
				area = game_engine.game_data.corridors[name]
				context.encounters_desc.append([ContextManager.__get_encounter_description(encounter) for encounter in area.encounters])
			else:
				raise ValueError(f'Unrecognized destination type: {name}')
			context.destinations.append(f'{name}_{idx}')
			context.descriptions.append(area.description)
		return context