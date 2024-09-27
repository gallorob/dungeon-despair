from enum import Enum, auto
from typing import List, Optional, Tuple, Union

from engine.combat_engine import CombatEngine
from engine.movement_engine import MovementEngine
from heroes_party import get_temp_heroes, Hero
from level import Attack, Level, Room, Enemy
from player.base_player import Player
from utils import get_current_encounter


class GameState(Enum):
	LOADING: int = auto()
	IDLE: int = auto()
	IN_COMBAT: int = auto()
	HEROES_WON: int = auto()
	ENEMIES_WON: int = auto()


class GameEngine:
	def __init__(self,
	             heroes_player: Player,
	             enemies_player: Player):
		self.combat_engine = CombatEngine()
		self.movement_engine = MovementEngine()
		
		self.heroes_player = heroes_player
		self.heroes = get_temp_heroes()
		self.stress = 0
		
		self.enemies_player = enemies_player
		
		self.state = GameState.LOADING
		self.game_data = None
		# self.encounter_idx = -1
	
	def set_level(self, level: Level) -> None:
		self.game_data = level
		self.state = GameState.IDLE
		
		self.move_to_room(room_name=self.game_data.current_room)
	
	def get_heroes_party(self):
		return self.heroes
	
	def move_to_room(self, room_name: str, encounter_idx: int = -1) -> List[Optional[str]]:
		msgs = self.movement_engine.move_to_room(level=self.game_data,
		                                         dest_room_name=room_name,
		                                         encounter_idx=encounter_idx)
				
		if len(get_current_encounter(level=self.game_data,
		                             encounter_idx=self.movement_engine.encounter_idx).entities.get('enemy', [])) > 0:
			self.state = GameState.IN_COMBAT
			self.init_encounter()
		
		return msgs
	
	def init_encounter(self):
		self.combat_engine.start_encounter(get_current_encounter(level=self.game_data,
		                                                         encounter_idx=self.movement_engine.encounter_idx))
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
	
	def get_current_attacker_with_idx(self) -> Tuple[Union[Hero, Enemy], int]:
		entity = self.combat_engine.currently_attacking(self.heroes, self.game_data)
		return entity, self.combat_engine.get_entities(self.heroes, self.game_data).index(entity)
	
	def check_gameover(self):
		# game over case #1: all hereoes are dead
		if len(self.heroes.party) == 0:
			self.state = GameState.ENEMIES_WON
		# game over case #2: no more enemies in the level
		else:
			flag = False
			for room in self.game_data.rooms.values():
				flag |= len(room.encounter.entities.get('enemy', [])) > 0
			for corridor in self.game_data.corridors:
				for encounter in corridor.encounters:
					flag |= len(encounter.entities.get('enemy', [])) > 0
			if not flag:
				self.state = GameState.HEROES_WON