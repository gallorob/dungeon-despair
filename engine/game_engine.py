from enum import Enum, auto
from typing import List, Optional, Tuple, Union

from engine.combat_engine import CombatEngine
from heroes_party import get_temp_heroes, Hero
from level import Attack, Level, Room, Enemy
from player.base_player import Player


class GameState(Enum):
	LOADING: int = auto()
	IDLE: int = auto()
	IN_COMBAT: int = auto()


class Turn(Enum):
	HEROES: int = auto()
	ENEMIES: int = auto()


class GameEngine:
	def __init__(self,
	             heroes_player: Player,
	             enemies_player: Player):
		self.combat_engine = CombatEngine()
		
		self.heroes_player = heroes_player
		self.heroes = get_temp_heroes()
		self.stress = 0
		
		self.enemies_player = enemies_player
		
		self.state = GameState.LOADING
		self.game_data = None
		self.encounter_idx = -1
	
	def set_level(self, level: Level) -> None:
		self.game_data = level
		self.state = GameState.IDLE
		
		self.move_to_room(self.game_data.current_room, self.encounter_idx)
	
	def get_current_room(self):
		if self.game_data.current_room in self.game_data.rooms:
			return self.game_data.rooms[self.game_data.current_room]
		else:
			return self.game_data.get_corridor(*self.game_data.current_room.split('-'), ordered=False)
	
	def get_current_encounter(self):
		if self.game_data.current_room in self.game_data.rooms:
			return self.game_data.rooms[self.game_data.current_room].encounter
		else:
			return self.game_data.get_corridor(*self.game_data.current_room.split('-'), ordered=False).encounters[
				self.encounter_idx]
	
	def get_heroes_party(self):
		return self.heroes
	
	def move_to_room(self, room_name: str, encounter_idx: int) -> List[Optional[str]]:
		prev_name = self.game_data.current_room
		self.game_data.current_room = room_name
		self.encounter_idx = encounter_idx
		
		if len(self.get_current_encounter().entities.get('enemy', [])) > 0:
			self.state = GameState.IN_COMBAT
			self.init_encounter()
		
		if prev_name != self.game_data.current_room:
			area = self.get_current_room()
			if isinstance(area, Room):
				msg = f'You enter <b>{area.name}</b>: <i>{area.description}</i>'
			else:
				msg = f'You enter the corridor that connects <b>{area.room_from}</b> to <b>{area.room_to}</b>'
			return [msg]
		return []
	
	def init_encounter(self):
		self.combat_engine.start_encounter(self.get_current_encounter())
		self.combat_engine.start_turn(self.heroes, self.game_data)
	
	def get_attacks(self) -> List[Attack]:
		return self.combat_engine.get_attacks(self.heroes, self.game_data)
	
	def get_attacker_idx(self) -> int:
		entity = self.combat_engine.currently_attacking(self.heroes, self.game_data)
		return self.combat_engine.get_entities(self.heroes, self.game_data).index(entity)
	
	def process_attack(self, attack_idx) -> List[str]:
		attack_stress, attack_msgs = self.combat_engine.process_attack(self.heroes, self.game_data, attack_idx)
		self.stress += attack_stress
		return attack_msgs
	
	def get_targeted_idxs(self, attack_idx) -> List[int]:
		positioned_entities = self.combat_engine.get_entities(self.heroes, self.game_data)
		current_attacker = self.combat_engine.currently_attacking(self.heroes, self.game_data)
		attack = current_attacker.attacks[attack_idx] if attack_idx < len(current_attacker.attacks) else self.combat_engine.pass_attack
		attack_mask = self.combat_engine.convert_attack_mask(attack.target_positions)
		if isinstance(current_attacker, Enemy):
			attack_mask = list(reversed(attack_mask))
		attack_offset = 0 if isinstance(current_attacker, Enemy) else len(self.heroes.party)
		target_idxs = [i + attack_offset for i in range(min(len(attack_mask), len(positioned_entities) - attack_offset)) if attack_mask[i]]
		return target_idxs
		
	def check_dead_entities(self):
		dead_stress, dead_msgs = self.combat_engine.process_dead_entities(self.heroes, self.game_data)
		self.stress += dead_stress
		return dead_msgs
	
	def check_end_encounter(self):
		if self.combat_engine.is_encounter_over(self.heroes, self.game_data):
			self.state = GameState.IDLE
	
	def next_turn(self):
		if self.combat_engine.currently_active >= len(self.combat_engine.sorted_entities):
			self.combat_engine.start_turn(self.heroes, self.game_data)
			return f'<i>Turn {self.combat_engine.turn_number}:</i>'
	
	def reachable(self, clicked_room_name: str, idx: int) -> bool:
		# check if current room is a corridor or a room
		if isinstance(self.get_current_room(), Room):
			# check if we are clicking on a connected corridor
			names = clicked_room_name.split('-')
			if len(names) == 2:
				corridor = self.game_data.get_corridor(*names, ordered=False)
				if corridor is not None:
					# make sure the corridor connects this room
					if corridor.room_to == self.get_current_room().name or corridor.room_from == self.get_current_room().name:
						# we can go to a corridor only if idx = 0 or corridor.length - 2
						return idx == 0 or idx == corridor.length - 1
		else:
			# check if we are clicking on the same corridor
			if clicked_room_name == self.get_current_room().name:
				# we can move only by 1 encounter
				return idx in [x + self.encounter_idx for x in [-1, 1]]
			else:
				# check we are moving to a connected room
				if clicked_room_name == self.get_current_room().room_from or clicked_room_name == self.get_current_room().room_to:
					# make sure we are on the edge of the corridor
					return self.encounter_idx == 0 or self.encounter_idx == self.get_current_room().length - 1
		return False
	
	def same_area(self, clicked_room_name, encounter_idx):
		return clicked_room_name == self.game_data.current_room and encounter_idx == self.encounter_idx
	
	def get_current_attacker_with_idx(self) -> Tuple[Union[Hero, Enemy], int]:
		entity = self.combat_engine.currently_attacking(self.heroes, self.game_data)
		return entity, self.combat_engine.get_entities(self.heroes, self.game_data).index(entity)
	
	def available_destinations(self) -> List[Tuple[str, int]]:
		destinations = []
		if isinstance(self.get_current_room(), Room):
			room_name = self.get_current_room().name
			for corridor in self.game_data.corridors:
				if corridor.room_from == room_name:
					destinations.append((corridor.name, 0))
				elif corridor.room_to == room_name:
					destinations.append((corridor.name, corridor.length - 1))
		else:
			corridor = self.get_current_room()
			if self.encounter_idx == 0:
				destinations.append((corridor.name, 1))
				destinations.append((corridor.room_from, -1))
			elif self.encounter_idx == corridor.length - 1:
				destinations.append((corridor.name, corridor.length - 2))
				destinations.append((corridor.room_to, -1))
			else:
				destinations.append((corridor.name, self.encounter_idx + 1))
				destinations.append((corridor.name, self.encounter_idx - 1))
		return destinations
