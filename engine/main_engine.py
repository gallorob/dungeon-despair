from enum import Enum, auto
from typing import List

from engine.combat_engine import CombatEngine
from heroes_party import get_temp_heroes
from level import Attack, Level


class GameState(Enum):
	IDLE: int = auto()
	IN_COMBAT: int = auto()
	

class GameEngine:
	def __init__(self):
		self.combat_engine = CombatEngine()
		
		self.heroes = get_temp_heroes()
		self.stress = 0
		
		self.state = GameState.IDLE
		
		# Load the game level from the saved file
		with open("assets/temp_dungeon/dungeon_data.json", 'r') as f:
			json_data = f.read()
			self.game_data = Level.model_validate_json(json_data, strict=True)
			
		self.move_to_room(self.game_data.current_room)
	
	def get_current_room(self):
		return self.game_data.rooms[self.game_data.current_room]
	
	def get_current_encounter(self):
		return self.game_data.rooms[self.game_data.current_room].encounter
	
	def get_heroes_party(self):
		return self.heroes
	
	def move_to_room(self, room_name: str):
		self.game_data.current_room = room_name
		
		# TODO: Should also handle corridors ;)
		if len(self.get_current_encounter().entities.get('enemy', [])) > 0:
			self.state = GameState.IN_COMBAT
			self.init_encounter()
	
	def init_encounter(self):
		self.combat_engine.start_encounter(game_data=self.game_data)
		self.combat_engine.start_turn(self.heroes, self.game_data)
	
	def get_attacks(self) -> List[Attack]:
		return self.combat_engine.get_attacks(self.heroes, self.game_data)
	
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
	
	def reachable(self, clicked_room_name):
		return self.game_data.get_corridor(self.game_data.current_room, clicked_room_name) is not None
