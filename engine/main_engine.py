from enum import Enum, auto
from typing import List, Optional

from engine.combat_engine import CombatEngine
from heroes_party import get_temp_heroes
from level import Attack, Level, Room


class GameState(Enum):
	IDLE: int = auto()
	IN_COMBAT: int = auto()


class GameEngine:
	def __init__(self,
	             level: Level):
		self.combat_engine = CombatEngine()
		
		self.heroes = get_temp_heroes()
		self.stress = 0
		
		self.encounter_idx = -1
		
		self.state = GameState.IDLE
		
		self.game_data = level
		
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
		self.combat_engine.start_encounter(game_data=self.game_data)
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
