import random
from enum import auto, Enum
from typing import List, Tuple, Union, Optional

from dungeon_despair.domain.attack import Attack
from dungeon_despair.domain.encounter import Encounter
from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.level import Level
from dungeon_despair.domain.utils import AttackType, get_enum_by_value
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
			       type=AttackType.PASS,
			       starting_positions='XXXX',
			       target_positions='OOOO',
			       base_dmg=0, accuracy=0.0),
			Attack(name='Move',
			       description='Move to another hero\'s position.',
			       type=AttackType.MOVE,
			       starting_positions='XXXX',
			       target_positions='OOOO',
			       base_dmg=0, accuracy=0.0)
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
			attack_type = get_enum_by_value(AttackType, attack.type)
			if attack_type == AttackType.MOVE:
				# Move should be disabled if there are no other entities to change place with
				if isinstance(current_attacker, Hero):
					attack.active = len(heroes.party) > 1
				else:
					attack.active = len(self.current_encounter.entities['enemy']) > 1
			elif attack_type != AttackType.PASS:
				# Disable attacks that cannot be executed from the current attacker position
				attack_mask = self.convert_attack_mask(attack.starting_positions)
				if isinstance(current_attacker, Hero):
					attack_mask = list(reversed(attack_mask))
				attack.active = attack_mask[attacker_idx] == 1
				# Disable attacks that do not have a target in a valid position
				target_mask = self.convert_attack_mask(attack.target_positions)
				if attack_type == AttackType.DAMAGE:
					if isinstance(current_attacker, Enemy):
						target_mask = list(reversed(target_mask))
					targets_n = len(positioned_entities) - len(heroes.party) if positioned_entities.index(
						current_attacker) <= len(heroes.party) - 1 else len(heroes.party)
					targets = [1 if i < targets_n else 0 for i in range(len(target_mask))]
					if isinstance(current_attacker, Enemy):
						targets = list(reversed(targets))
				elif attack_type == AttackType.HEAL:
					targets_n = len(heroes.party) if positioned_entities.index(current_attacker) <= len(heroes.party) - 1 else len(positioned_entities) - len(heroes.party)
					targets = [1 if i < targets_n else 0 for i in range(len(target_mask))]
					if isinstance(current_attacker, Hero):
						targets = list(reversed(targets))
				else:
					raise NotImplementedError(f'Unknown attack type: {attack.type.value}')
				target_and = [1 if i == 1 and j == 1 else 0 for i, j in zip(target_mask, targets)]
				attack.active &= sum(target_and) > 0
		
		return possible_attacks
	
	def process_attack(self, heroes: HeroParty, game_data: Level, attack_idx: int) -> Tuple[int, List[str]]:
		stress = 0
		action_msgs = []
		
		positioned_entities = self.get_entities(heroes, game_data)
		current_attacker = self.sorted_entities[self.currently_active]
		attack = current_attacker.attacks[attack_idx] if attack_idx < len(
			current_attacker.attacks) else self.extra_actions[attack_idx - len(current_attacker.attacks)]
		
		attack_type = get_enum_by_value(AttackType, attack.type)
		
		if attack_type == AttackType.MOVE:
			self.state = CombatPhase.CHOOSE_POSITION
		else:
			if attack_type == AttackType.PASS:
				action_msgs.append(f'<b>{current_attacker.name}</b> passes!')
				stress += 10 * (1 if isinstance(current_attacker, Hero) else -1)
			elif attack_type == AttackType.DAMAGE:
				base_dmg = attack.base_dmg
				attack_mask = self.convert_attack_mask(attack.target_positions)
				if isinstance(current_attacker, Enemy):
					attack_mask = list(reversed(attack_mask))
				attack_offset = 0 if isinstance(current_attacker, Enemy) else len(heroes.party)
				
				for i in range(min(len(attack_mask), len(positioned_entities) - attack_offset)):
					if attack_mask[i]:
						target_entity = positioned_entities[attack_offset + i]
						do_hit = 1 if random.random() < max(0.0, (attack.accuracy * 2) - target_entity.dodge) else 0
						if do_hit:
							dmg_taken = int(base_dmg * (1 - target_entity.prot))
							target_entity.hp -= dmg_taken
							action_msgs.append(
								f'<b>{current_attacker.name}</b>: {attack.description} <i>{dmg_taken}</i> damage dealt to <b>{target_entity.name}</b>!')
							stress += int(dmg_taken * (-1 if isinstance(current_attacker, Hero) else 1))
						else:
							action_msgs.append(
								f'<b>{current_attacker.name}</b>: {attack.description} but misses!')
							stress += int(10 * (-1 if isinstance(current_attacker, Enemy) else 1))
			elif attack_type == AttackType.HEAL:
				heal = -attack.base_dmg
				heal_mask = self.convert_attack_mask(attack.target_positions)
				if isinstance(current_attacker, Hero):
					heal_mask = list(reversed(heal_mask))
				heal_offset = 0 if isinstance(current_attacker, Hero) else len(positioned_entities) - len(heroes.party)
				
				for i in range(min(len(heal_mask), len(positioned_entities) - heal_offset)):
					if heal_mask[i]:
						target_entity = positioned_entities[heal_offset + i]
						target_entity.hp += heal
						action_msgs.append(f'<b>{current_attacker.name}</b>: {attack.description} <i>{heal}</i> heals <b>{target_entity.name}</b>!')
						stress -= int(heal * (1 if isinstance(current_attacker, Hero) else -1))
			else:
				raise NotImplementedError(f'Unknown attack type: {attack_type.value}.')
			
			self.currently_active += 1
		
		return stress, action_msgs
	
	def try_cancel_move(self,
	                    attacker: Union[Hero, Enemy],
	                    idx: int) -> None:
		attack = attacker.attacks[idx] if idx < len(
			attacker.attacks) else self.extra_actions[idx - len(attacker.attacks)]
		attack_type = get_enum_by_value(AttackType, attack.type)
		if attack_type == AttackType.MOVE:
			self.state = CombatPhase.PICK_ATTACK
	
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
