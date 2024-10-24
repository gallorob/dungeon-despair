from enum import Enum, auto
from typing import List, Optional, Tuple, Union

from dungeon_despair.domain.attack import Attack
from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.level import Level
from engine.actions_engine import ActionEngine
from engine.combat_engine import CombatEngine
from engine.movement_engine import MovementEngine
from heroes_party import get_temp_heroes, Hero
from player.base_player import Player
from utils import get_current_encounter


class GameState(Enum):
	LOADING: int = auto()
	IDLE: int = auto()
	IN_COMBAT: int = auto()
	INSPECTING_TRAP: int = auto()
	INSPECTING_TREASURE: int = auto()
	HEROES_WON: int = auto()
	ENEMIES_WON: int = auto()


class GameEngine:
	def __init__(self,
	             heroes_player: Player,
	             enemies_player: Player):
		self.combat_engine = CombatEngine()
		self.movement_engine = MovementEngine()
		self.actions_engine = ActionEngine()
		
		self.heroes_player = heroes_player
		self.heroes = get_temp_heroes()
		self.stress = 0
		
		self.enemies_player = enemies_player
		
		self.state = GameState.LOADING
		self.game_data = None
	
	def set_level(self, level: Level) -> None:
		self.game_data = level
		self.state = GameState.IDLE
		
		self.move_to_room(room_name=self.game_data.current_room)
	
	def get_heroes_party(self):
		return self.heroes
	
	def update_state(self) -> List[str]:
		current_encounter = get_current_encounter(level=self.game_data,
		                                          encounter_idx=self.movement_engine.encounter_idx)
		if len(current_encounter.entities.get('enemy', [])) > 0:
			self.state = GameState.IN_COMBAT
			return self.combat_engine.start_encounter(current_encounter, self.heroes, self.game_data)
		elif len(current_encounter.entities.get('trap', [])) > 0:
			self.state = GameState.INSPECTING_TRAP
			return self.actions_engine.init_trap_encounter(current_encounter)
		elif len(current_encounter.entities.get('treasure', [])) > 0:
			self.state = GameState.INSPECTING_TREASURE
			return self.actions_engine.init_treasure_encounter(current_encounter)
		else:
			self.state = GameState.IDLE
		
		return []
	
	def move_to_room(self, room_name: str, encounter_idx: int = -1) -> List[str]:
		msgs = self.movement_engine.move_to_room(level=self.game_data,
		                                         dest_room_name=room_name,
		                                         encounter_idx=encounter_idx)
		return msgs
		
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
	
	def check_end_encounter(self) -> List[str]:
		if self.combat_engine.is_encounter_over(self.heroes, self.game_data):
			msgs = ['<i><b>### END OF ENCOUNTER</i></b>']
			msgs.extend(self.update_state())
			return msgs
		return []
	
	def next_turn(self) -> List[str]:
		msgs = []
		if self.combat_engine.currently_active >= len(self.combat_engine.sorted_entities):
			self.combat_engine.start_turn(self.heroes, self.game_data)
			msgs.append(f'<i>Turn {self.combat_engine.turn_number}:</i>')
		attacker = self.combat_engine.currently_attacking(self.heroes, self.game_data)
		msgs.append(f'Attacking: <b>{attacker.name}</b>')
		return msgs
	
	def get_current_attacker_with_idx(self) -> Tuple[Union[Hero, Enemy], int]:
		entity = self.combat_engine.currently_attacking(self.heroes, self.game_data)
		return entity, self.combat_engine.get_entities(self.heroes, self.game_data).index(entity)
	
	def check_gameover(self) -> List[str]:
		# TODO: The game over check for heroes should depend on the scenario objective
		# game over case #1: all hereoes are dead
		if len(self.heroes.party) == 0:
			self.state = GameState.ENEMIES_WON
			return ['<i><b>GAME OVER</i></b>: Enemies won!']
		# game over case #2: no more enemies in the level
		else:
			flag = False
			for room in self.game_data.rooms.values():
				flag |= len(room.encounter.entities.get('enemy', [])) > 0
			for corridor in self.game_data.corridors.values():
				for encounter in corridor.encounters:
					flag |= len(encounter.entities.get('enemy', [])) > 0
			if not flag:
				self.state = GameState.HEROES_WON
				return ['<i><b>GAME OVER</i></b>: Heroes won!']
		return []
	
	def attempt_looting(self,
	                    choice: int) -> List[str]:
		if choice == 0:
			encounter = get_current_encounter(level=self.game_data,
			                                  encounter_idx=self.movement_engine.encounter_idx)
			msgs, stress_diff = self.actions_engine.resolve_treasure_encounter(encounter)
			self.stress += stress_diff
		else:
			msgs = ['You ignore the treasure... For now.']
		self.state = GameState.IDLE
		return msgs
	
	def attempt_disarm(self,
	                   choice: int) -> List[str]:
		if choice == 0:
			encounter = get_current_encounter(level=self.game_data,
			                                  encounter_idx=self.movement_engine.encounter_idx)
			msgs, stress_diff = self.actions_engine.resolve_trap_encounter(encounter=encounter,
			                                                               heroes=self.heroes)
			self.stress += stress_diff
		else:
			msgs = ['You ignore the trap... For now.']
		self.state = GameState.IDLE
		return msgs