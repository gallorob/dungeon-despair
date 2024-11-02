import random
from enum import auto, Enum
from typing import List, Tuple, Union, Optional

from dungeon_despair.domain.attack import Attack
from dungeon_despair.domain.encounter import Encounter
from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.level import Level
from heroes_party import Hero, HeroParty

# Refer to:
# https://darkestdungeon.fandom.com/wiki/Getting_Started#The_Basics
# https://www.reddit.com/r/darkestdungeon/comments/3iyyvs/how_does_combat_work/


class CombatPhase(Enum):
	PICK_ATTACK = auto()
	CHOOSE_POSITION = auto()


class CombatEngine:
	def __init__(self):
		self.turn_number = 0
		self.currently_active = 0
		self.sorted_entities = []
		self.current_encounter: Optional[Encounter] = None
		
		self.extra_actions = [
			Attack(name='Pass',
			       description='Pass the current turn.',
			       starting_positions='XXXX',
			       target_positions='OOOO',
			       base_dmg=0),
			Attack(name='Move',
			       description='Move to another hero\'s position.',
			       starting_positions='XXXX',
			       target_positions='OOOO',
			       base_dmg=0)
		]
		
		self.state = CombatPhase.PICK_ATTACK
	
	def start_encounter(self, encounter, heroes: HeroParty, game_data: Level) -> List[str]:
		msgs = ['<b><i>### NEW ENCOUNTER</i></b>', '<i>Turn 1:</i>']
		self.turn_number = 0
		self.current_encounter = encounter
		self.start_turn(heroes, game_data)
		msgs.append(f'Attacking: <b>{self.currently_attacking(heroes, game_data).name}</b>')
		return msgs
	
	def is_encounter_over(self, heroes: HeroParty, game_data: Level):
		return len(heroes.party) == 0 or len(self.current_encounter.entities.get('enemy', [])) == 0
	
	def sort_entities(self, entities: List[Union[Hero, Enemy]]) -> List[Union[Hero, Enemy]]:
		# Turn order is determined semi-randomly: 1d10+Speed.
		modified_speed = [(entity.spd * 10) + random.randint(1, 10) for entity in entities]
		sorted_entities = [i for i, _ in sorted(enumerate(modified_speed), key=lambda x: x[1])]
		# return sorted_entities
		return [entities[i] for i in sorted_entities]
	
	def get_entities(self, heroes: HeroParty, game_data: Level) -> List[Union[Hero, Enemy]]:
		return [*heroes.party, *self.current_encounter.entities.get('enemy', [])]
	
	def start_turn(self, heroes: HeroParty, game_data: Level):
		self.turn_number += 1
		self.currently_active = 0
		# Everyone takes a move during the turn, then the turn advances and everyone rerolls turn order and goes again.
		self.sorted_entities = self.sort_entities(self.get_entities(heroes, game_data))
	
	def convert_attack_mask(self, mask: str):
		return [1 if x == 'X' else 0 for x in mask]
	
	def currently_attacking(self, heroes: HeroParty, game_data: Level) -> Union[Hero, Enemy]:
		current_attacker = self.sorted_entities[self.currently_active]
		return current_attacker
	
	def get_attacks(self, heroes: HeroParty, game_data: Level) -> List[Attack]:
		positioned_entities = self.get_entities(heroes, game_data)
		current_attacker = self.sorted_entities[self.currently_active]
		
		possible_attacks = current_attacker.attacks.copy()
		possible_attacks.extend(self.extra_actions)
		attacker_idx = positioned_entities.index(current_attacker)
		attacker_idx -= 0 if attacker_idx <= len(heroes.party) - 1 else len(heroes.party)
		
		# disable attacks that cannot be executed
		for attack in possible_attacks:
			if attack.name == 'Move':
				# Move should be disabled if there are no other entities to change place with
				if isinstance(current_attacker, Hero):
					attack.active = len(heroes.party) > 1
				else:
					attack.active = len(self.current_encounter.entities['enemy']) > 1
			elif attack.name != 'Pass':
				# Disable attacks that cannot be executed from the current attacker position
				attack_mask = self.convert_attack_mask(attack.starting_positions)
				if isinstance(current_attacker, Hero):
					attack_mask = list(reversed(attack_mask))
				attack.active = attack_mask[attacker_idx] == 1
				# Disable attacks that do not have a target in a valid position
				target_mask = self.convert_attack_mask(attack.target_positions)
				if isinstance(current_attacker, Enemy):
					target_mask = list(reversed(target_mask))
				targets_n = len(positioned_entities) - len(heroes.party) if positioned_entities.index(
					current_attacker) <= len(heroes.party) - 1 else len(heroes.party)
				targets = [1 if i < targets_n else 0 for i in range(len(target_mask))]
				if isinstance(current_attacker, Enemy):
					targets = list(reversed(targets))
				target_and = [1 if i == 1 and j == 1 else 0 for i, j in zip(target_mask, targets)]
				attack.active &= sum(target_and) > 0
		
		return possible_attacks
	
	def process_attack(self, heroes: HeroParty, game_data: Level, attack_idx: int) -> Tuple[int, List[str]]:
		stress = 0
		attack_msgs = []
		
		positioned_entities = self.get_entities(heroes, game_data)
		current_attacker = self.sorted_entities[self.currently_active]
		attack = current_attacker.attacks[attack_idx] if attack_idx < len(
			current_attacker.attacks) else self.extra_actions[attack_idx - len(current_attacker.attacks)]
		
		if attack.name == 'Move':
			self.state = CombatPhase.CHOOSE_POSITION
		else:
			if attack.name == 'Pass':
				attack_msgs.append(f'<b>{current_attacker.name}</b> passes!')
				stress += 10 * (1 if isinstance(current_attacker, Hero) else -1)
			else:
				base_dmg = attack.base_dmg
				attack_mask = self.convert_attack_mask(attack.target_positions)
				if isinstance(current_attacker, Enemy):
					attack_mask = list(reversed(attack_mask))
				attack_offset = 0 if isinstance(current_attacker, Enemy) else len(heroes.party)
				
				for i in range(min(len(attack_mask), len(positioned_entities) - attack_offset)):
					if attack_mask[i]:
						target_entity = positioned_entities[attack_offset + i]
						dmg_taken = int(base_dmg * (1 - target_entity.prot)) * attack_mask[i]
						target_entity.hp -= dmg_taken
						attack_msgs.append(
							f'<b>{current_attacker.name}</b>: {attack.description} <i>{dmg_taken}</i> damage dealt to <b>{target_entity.name}</b>!')
						
						stress += dmg_taken * (-1 if isinstance(current_attacker, Hero) else 1)
			
			self.currently_active += 1
		
		return stress, attack_msgs
	
	def process_move(self, heroes: HeroParty, game_data: Level, idx: int) -> Tuple[int, List[str]]:
		positioned_entities = self.get_entities(heroes, game_data)
		current_attacker = self.sorted_entities[self.currently_active]
		
		curr_idx = positioned_entities.index(current_attacker)
		
		if isinstance(current_attacker, Hero):
			if idx < len(heroes.party) and idx != curr_idx:
				move_msg = f"<b>{current_attacker.name}</b> moves in <b>{heroes.party[idx].name}</b> position!"
				heroes.party.insert(idx, heroes.party.pop(curr_idx))
				self.state = CombatPhase.PICK_ATTACK
				self.currently_active += 1
			else:
				move_msg = f"<b>{current_attacker.name}</b> can only move within its party!"
		else:
			curr_idx -= len(heroes.party)
			if idx >= len(heroes.party):
				idx -= len(heroes.party)
				move_msg = f"<b>{current_attacker.name}</b> moves in <b>{self.current_encounter.entities['enemy'][idx].name}</b> position!"
				self.current_encounter.entities['enemy'].insert(idx, self.current_encounter.entities['enemy'].pop(curr_idx))
				self.state = CombatPhase.PICK_ATTACK
				self.currently_active += 1
			else:
				move_msg = f"<b>{current_attacker.name}</b> can only move within its group!"
		
		return 0, [move_msg]
	
	def process_dead_entities(self, heroes: HeroParty, game_data: Level) -> Tuple[int, List[str]]:
		stress = 0
		dead_entities = []
		messages = []
		
		positioned_entities = self.get_entities(heroes, game_data)
		for i, entity in enumerate(positioned_entities):
			if entity.hp <= 0:
				dead_entities.append(i)
				stress += 100 * (1 if isinstance(entity, Hero) else -1)
				messages.append(f'<b>{entity.name}</b> is dead!')
				self.sorted_entities.remove(entity)
		
		for i in reversed(dead_entities):
			if i > len(heroes.party) - 1:
				j = i - len(heroes.party)
				self.current_encounter.entities.get('enemy', []).pop(j)
			else:
				heroes.party.pop(i)
		
		return stress, messages
