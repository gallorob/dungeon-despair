import random
from typing import List, Tuple, Union, Optional

from heroes_party import Hero, HeroParty
from level import Attack, Enemy, Level, Encounter


# Refer to:
# https://darkestdungeon.fandom.com/wiki/Getting_Started#The_Basics
# https://www.reddit.com/r/darkestdungeon/comments/3iyyvs/how_does_combat_work/


class CombatEngine:
	def __init__(self):
		self.turn_number = 0
		self.currently_active = 0
		self.sorted_entities = []
		self.current_encounter: Optional[Encounter] = None
		
		self.pass_attack = Attack(name='Pass',
		                          description='Pass the current turn.',
		                          starting_positions='XXXX',
		                          target_positions='OOOO',
		                          base_dmg=0)
	
	def start_encounter(self, encounter):
		self.turn_number = 0
		self.current_encounter = encounter
	
	def is_encounter_over(self, heroes: HeroParty, game_data: Level):
		return len(heroes.party) == 0 or len(self.current_encounter.entities.get('enemy', [])) == 0
	
	def sort_entities(self, entities: List[Union[Hero, Enemy]]) -> List[int]:
		# Turn order is determined semi-randomly: 1d10+Speed.
		modified_speed = [entity.spd + random.randint(1, 10) for entity in entities]
		sorted_entities = [i for i, _ in sorted(enumerate(modified_speed), key=lambda x: x[1])]
		return sorted_entities
	
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
		positioned_entities = self.get_entities(heroes, game_data)
		current_attacker = positioned_entities[self.sorted_entities[self.currently_active]]
		return current_attacker
	
	def get_attacks(self, heroes: HeroParty, game_data: Level) -> List[Attack]:
		positioned_entities = self.get_entities(heroes, game_data)
		current_attacker = positioned_entities[self.sorted_entities[self.currently_active]]
		
		possible_attacks = current_attacker.attacks.copy()
		possible_attacks.append(self.pass_attack)
		# disable attacks that cannot be executed
		attacker_idx = positioned_entities.index(current_attacker)
		attacker_idx -= 0 if attacker_idx <= len(heroes.party) - 1 else len(heroes.party)
		
		for attack in possible_attacks:
			attack_mask = self.convert_attack_mask(attack.starting_positions)
			if isinstance(current_attacker, Hero):
				attack_mask = list(reversed(attack_mask))
			attack.active = attack_mask[attacker_idx] == 1
		
		return possible_attacks
	
	def process_attack(self, heroes: HeroParty, game_data: Level, attack_idx: int) -> Tuple[int, List[str]]:
		stress = 0
		attack_msgs = []
		
		positioned_entities = self.get_entities(heroes, game_data)
		current_attacker = positioned_entities[self.sorted_entities[self.currently_active]]
		attack = current_attacker.attacks[attack_idx] if attack_idx < len(current_attacker.attacks) else self.pass_attack
	
		if attack == self.pass_attack:
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
		
		for i in reversed(dead_entities):
			if i > len(heroes.party) - 1:
				j = i - len(heroes.party)
				game_data.rooms[game_data.current_room].encounter.entities.get('enemy', []).pop(j)
			else:
				heroes.party.pop(i)
			self.sorted_entities.pop(self.sorted_entities.index(i))
		
		for i in reversed(dead_entities):
			for j, v in enumerate(self.sorted_entities):
				if v > i:
					self.sorted_entities[j] = v - 1
		
		return stress, messages
