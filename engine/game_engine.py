from enum import Enum, auto
import random
from typing import List, Tuple, Union, Optional

from dungeon_despair.domain.attack import Attack
from dungeon_despair.domain.entities.entity import Entity
from dungeon_despair.domain.level import Level
from engine.actions_engine import ActionEngine, LootingChoice
from engine.combat_engine import CombatEngine, CombatPhase
from engine.message_system import msg_system
from engine.modifier_system import ModifierSystem
from engine.movement_engine import MovementEngine, Destination
from engine.stress_system import stress_system
from heroes_party import get_temp_heroes, Hero, HeroParty
from player.base_player import Player, PlayerType


class GameState(Enum):
	LOADING: int = auto()
	IDLE: int = auto()
	IN_COMBAT: int = auto()
	INSPECTING_TRAP: int = auto()
	INSPECTING_TREASURE: int = auto()
	WAVE_OVER: int = auto()
	GAME_OVER: int = auto()


class GameEngine:
	def __init__(self,
	             heroes_player: Player,
	             enemies_player: Player):
		self.heroes_player = heroes_player
		self.enemies_player = enemies_player
		
		self.combat_engine = CombatEngine()
		self.movement_engine = MovementEngine()
		self.actions_engine = ActionEngine()
		
		self.heroes: Optional[HeroParty] = None
		
		self.state = GameState.LOADING
		self.scenario = None

		self.wave = 0
	
	def set_level(self, level: Level) -> None:
		'''Set the scenario and prepare to play'''
		self.scenario = level
		self.state = GameState.IDLE

		# TODO: Temporary fix, should be reset individually
		self.combat_engine = CombatEngine()
		self.movement_engine = MovementEngine()
		self.actions_engine = ActionEngine()

		self.move_to(dest=Destination(to=self.scenario.current_room,
		                              idx=-1))
	
	def tick(self):
		'''Update the state of the game based on the current scenario state'''
		def try_combat():
			if len(self.movement_engine.current_encounter.enemies) > 0:
				self.state = GameState.IN_COMBAT
				ModifierSystem.apply_and_tick_modifiers(self.heroes.party)  # Apply now in case there is a stun
				self.combat_engine.start_encounter(encounter=self.movement_engine.current_encounter,
				                                   heroes=self.heroes)  # TODO
				self.combat_engine.start_turn(heroes=self.heroes,
				                              enemies=self.movement_engine.current_encounter.enemies)
		
		def try_trap():
			if len(self.movement_engine.current_encounter.traps) > 0:
				self.state = GameState.INSPECTING_TRAP
				ModifierSystem.apply_and_tick_modifiers(self.heroes.party)
				trap = self.movement_engine.current_encounter.traps[0]
				msg_system.add_msg(f'You find <b>{trap.name}</b>!')
		
		def try_treasure():
			if len(self.movement_engine.current_encounter.treasures) > 0:
				self.state = GameState.INSPECTING_TREASURE
				ModifierSystem.apply_and_tick_modifiers(self.heroes.party)
				treasure = self.movement_engine.current_encounter.treasures[0]
				msg_system.add_msg(f'You find <b>{treasure.name}</b>!')
		
		# Check for dead entities
		self.check_for_dead()
		if self.state == GameState.IDLE:
			try_combat()
			if self.state == GameState.IDLE: try_trap()
			if self.state == GameState.IDLE: try_treasure()
		# Update the game state, if possible
		elif self.state == GameState.INSPECTING_TRAP:
			try_treasure()
			if self.state == GameState.INSPECTING_TRAP: self.state = GameState.IDLE
		elif self.state == GameState.INSPECTING_TREASURE:
			try_trap()
			if self.state == GameState.INSPECTING_TREASURE: self.state = GameState.IDLE
		if self.state == GameState.IN_COMBAT:
			if self.combat_engine.state == CombatPhase.PICK_ATTACK:
				self.combat_engine.tick(heroes=self.heroes)
			if self.combat_engine.state == CombatPhase.END_OF_TURN:
				# Apply and tick down modifiers that are still active to heroes
				ModifierSystem.apply_and_tick_modifiers(self.heroes.party)
				# Apply modifiers that are still active to enemies, if there are any
				ModifierSystem.apply_and_tick_modifiers(self.movement_engine.current_encounter.enemies)
				# Check for dead entities
				self.check_for_dead()
				self.combat_engine.start_turn(heroes=self.heroes,
				                              enemies=self.movement_engine.current_encounter.enemies)
				self.combat_engine.tick(self.heroes)
			elif self.combat_engine.state == CombatPhase.END_OF_COMBAT:
				self.state = GameState.IDLE
				self.check_for_dead()
				self.check_wave_over()
				if self.state == GameState.IDLE:
					try_trap()
				if self.state == GameState.IDLE:
					try_treasure()
		if self.state == GameState.IDLE:
			ModifierSystem.apply_and_tick_modifiers(self.heroes.party)
			self.check_wave_over()
			# Check for dead entities
			self.check_for_dead()
			self.check_game_over()
		
	def move_to(self,
	            dest: Destination):
		'''Move the hero party to another area of the level'''
		if self.movement_engine.current_room is None or \
				self.movement_engine.reachable(level=self.scenario,
				                               dest=dest):
			self.movement_engine.move_to(level=self.scenario,
			                             dest=dest)
			if self.heroes_player.type == PlayerType.AI:
				self.heroes_player.update_visited_areas(dest)
	
	@property
	def current_room(self):
		return self.movement_engine.current_room
	
	@property
	def current_encounter(self):
		return self.movement_engine.current_encounter
	
	@property
	def actions(self) -> List[Attack]:
		'''Get the current attacker's attacks'''
		return self.combat_engine.actions
	
	@property
	def attacker_and_idx(self) -> Tuple[Union[Hero, Entity], int]:
		'''Get the current attacker and its index in the positioned entities in the current encounter'''
		entity = self.combat_engine.attacker
		return entity, [*self.heroes.party, *self.movement_engine.current_encounter.enemies].index(entity)
	
	@property
	def player(self) -> Player:
		if self.state == GameState.IN_COMBAT:
			return self.heroes_player if isinstance(self.combat_engine.attacker, Hero) else self.enemies_player
		else:
			return self.heroes_player
	
	def process_attack(self,
	                   attack_idx: int) -> None:
		'''Process the attack with the provided index'''
		self.combat_engine.process_attack(heroes=self.heroes,
		                                  idx=attack_idx)
	
	def try_cancel_attack(self,
	                  attack_idx: int) -> None:
		'''Attempt to cancel the attack with the provided index'''
		self.combat_engine.try_cancel_move(action_idx=attack_idx)
	
	def process_move(self,
	                 idx) -> None:
		'''Move the current attacker to the specified position'''
		self.combat_engine.process_move(heroes=self.heroes,
		                                target_idx=idx)
	
	def check_for_dead(self) -> None:
		'''Process dead heroes and enemies'''
		dead_entities = []
		for hero in self.heroes.party:
			if hero.hp <= 0:
				dead_entities.append(self.heroes.party.pop(self.heroes.party.index(hero)))
		for enemy in self.movement_engine.current_encounter.enemies:
			if enemy.hp <= 0:
				dead_entities.append(self.movement_engine.current_encounter.enemies.pop(self.movement_engine.current_encounter.enemies.index(enemy)))
		if self.state == GameState.IN_COMBAT:
			self.combat_engine.process_dead(dead_entities=dead_entities)
		stress_system.process_dead(dead_entities)
		msg_system.process_dead(dead_entities)
	
	def process_disarm(self) -> None:
		'''Process disarming a trap'''
		self.actions_engine.resolve_trap_encounter(encounter=self.movement_engine.current_encounter,
		                                           heroes=self.heroes)
	
	def process_looting(self,
	                    choice: LootingChoice) -> None:
		'''Process looting a treasure'''
		encounter = self.movement_engine.current_encounter
		treasure = encounter.treasures[0]
		hero = random.choice(self.heroes.party)
		if choice == LootingChoice.LOOT or choice == LootingChoice.INSPECT_AND_LOOT:
			self.actions_engine.resolve_treasure_encounter(treasure=treasure,
			                                               hero=hero,
			                                               encounter=encounter,
			                                               choice=choice)
		else:
			msg_system.ignore_looting(hero=hero, treasure=treasure)
			stress_system.process_ignore_looting(hero=hero, treasure=treasure)
	
	def targeted(self,
	             idx: int) -> List[int]:
		'''Get the indices of the positioned entities currently targeted'''
		return self.combat_engine.targets_by_action[idx]
	
	def check_wave_over(self) -> None:
		if len(self.heroes.party) == 0:
			self.state = GameState.WAVE_OVER
			msg_system.add_msg(f'<b>Wave #{self.wave + 1} is over</b>: all heroes are dead!')

	def check_game_over(self) -> None:
		'''Check if the game is over (based on the scenario objective)'''
		# TODO: The game over check for heroes should depend on the scenario objective
		n_enemies_left = 0
		for room in self.scenario.rooms.values():
			n_enemies_left += len(room.encounter.enemies)
		for corridor in self.scenario.corridors.values():
			for encounter in corridor.encounters:
				n_enemies_left += len(encounter.enemies)
		if n_enemies_left == 0:
			self.state = GameState.GAME_OVER
			stress_system.score += stress_system.stress
			msg_system.add_msg(f'<b>Game over</b>: dungeon has been cleared!')