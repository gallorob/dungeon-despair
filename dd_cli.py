import copy
import os
from enum import Enum, auto
from typing import List

from tqdm.auto import tqdm

import fire

from dungeon_despair.domain.entities.hero import Hero
from dungeon_despair.domain.configs import config as ddd_config
from dungeon_despair.domain.level import Level

from engine.game_engine import GameEngine, GameState
from player.base_player import PlayerType
from player.random_player import RandomPlayer
from player.ai_player import AIPlayer
from configs import configs


class MessageType(Enum):
	ACTION = auto()
	EVENT = auto()
	OBSERVATION = auto()


class Message:
	def __init__(self, message_type: MessageType, message: str):
		self.type = message_type
		self.message = message
	
	def __str__(self):
		if self.type == MessageType.ACTION:
			return f'ACTION\t{self.message}'
		elif self.type == MessageType.EVENT:
			return f'EVENT\t{self.message}'
		elif self.type == MessageType.OBSERVATION:
			return f'OBSERVATION\t{self.message}'
		else:
			raise ValueError(f'Unknown message type: {self.type}')

class SimulatorLogger:
	def __init__(self,
	             output_filename: str):
		self.f = open(output_filename, 'w')
	
	def start_exp(self,
	              **kwargs):
		for k, v in kwargs.items():
			self.f.write(f'SETTINGS\t{k}: {v}\n')
	
	def start_run(self,
	              run_n: int) -> None:
		self.f.write(f'RUN\t{run_n}\n')
	
	def end(self) -> None:
		self.f.close()
	
	def write(self,
	          msgs: List[Message]) -> None:
		for msg in msgs:
			self.f.write(f'{str(msg)}\n')


class Simulator:
	def run_simulation(self,
	                   scenario_filename: str,
	                   simulation_type: str,
	                   simulation_runs: int,
	                   output_filename: str) -> None:
		# Set assets folder
		ddd_config.temp_dir = os.path.join(configs.assets, 'dungeon_assets')
		logger = SimulatorLogger(output_filename)
		logger.start_exp(**{'simulation_type': simulation_type})
		for run_n in tqdm(range(simulation_runs), desc='Simulating...', position=0):
			# Initialize logger
			logger.start_run(run_n)
			# Load the scenario
			scenario = Level.load_as_scenario(scenario_filename)
			# Simulate a random game
			msgs = self.__simulate_scenario(scenario, simulation_type)
			# Log simulation messages
			logger.write(msgs)
		# Save logs
		logger.end()
	
	def __to_msg(self,
	             strings: List[str],
	             msg_type: MessageType) -> List[Message]:
		return [Message(message=msg,
		                message_type=msg_type) for msg in strings]
	
	def __simulate_scenario(self,
                            scenario: Level,
                            simulation_type: str,
                            max_steps: int = 2000) -> List[Message]:
		msgs = []
		if simulation_type == 'random':
			# Random players
			eng = GameEngine(heroes_player=RandomPlayer(),
			                 enemies_player=RandomPlayer())
		if simulation_type == 'ai':
			# Greedy AI players
			eng = GameEngine(heroes_player=AIPlayer(),
			                 enemies_player=AIPlayer())
		else:
			raise NotImplementedError(f'{simulation_type} is not implemented yet!')
		# Set the level
		eng.set_level(level=scenario)
		# Initialize by moving to the current room
		msgs.extend(self.__to_msg(eng.move_to_room(room_name=eng.game_data.current_room,
		                                           encounter_idx=-1),
		                          MessageType.EVENT))
		msgs.extend(self.__to_msg(eng.update_state(),
		                          MessageType.EVENT))
		# Simulate until termination or max number of steps is reached
		t = tqdm(total=max_steps, desc='Simulating steps', leave=False, position=1)
		n_step = 0
		while (eng.state != GameState.ENEMIES_WON and eng.state != GameState.HEROES_WON) and n_step < max_steps:
			# Move to a new room
			if eng.state == GameState.IDLE:
				available_destinations = eng.movement_engine.available_destinations(level=eng.game_data)
				if len(available_destinations) > 0:
					destination_room_name, encounter_idx = eng.heroes_player.pick_destination(available_destinations)
					msgs.extend(self.__to_msg(eng.move_to_room(room_name=destination_room_name, encounter_idx=encounter_idx),
					                          MessageType.ACTION))
					msgs.extend(self.__to_msg(eng.update_state(),
					                          MessageType.EVENT))
			# Loot treasures
			elif eng.state == GameState.INSPECTING_TREASURE:
				do_loot = eng.heroes_player.choose_loot_treasure()
				msgs.extend(self.__to_msg(eng.attempt_looting(choice=0 if do_loot else 1),
				                          MessageType.ACTION))
				# Log stress levels
				msgs.extend(self.__to_msg([f'The heroes stress is at {eng.stress}'],
				                          MessageType.OBSERVATION))
			# Disarm traps
			elif eng.state == GameState.INSPECTING_TRAP:
				do_disarm = eng.heroes_player.choose_disarm_trap()
				msgs.extend(self.__to_msg(eng.attempt_disarm(choice=0 if do_disarm else 1),
				                          MessageType.ACTION))
				# Log stress levels
				msgs.extend(self.__to_msg([f'The heroes stress is at {eng.stress}'],
				                          MessageType.OBSERVATION))
			# Combat enemies
			elif eng.state == GameState.IN_COMBAT:
				current_attacker, _ = eng.get_current_attacker_with_idx()
				current_player = eng.heroes_player if isinstance(current_attacker, Hero) else eng.enemies_player
				if current_player.type == PlayerType.AI:
					current_player.game_engine_copy = copy.deepcopy(eng)
				attack = current_player.pick_attack(eng.get_attacks())
				msgs.extend(self.__to_msg(eng.process_attack(attack),
				                          MessageType.ACTION))
				msgs.extend(self.__to_msg(eng.check_dead_entities(),
				                          MessageType.EVENT))
				msgs.extend(self.__to_msg(eng.check_end_encounter(),
				                          MessageType.EVENT))
				# Log stress levels
				msgs.extend(self.__to_msg([f'The heroes stress is at {eng.stress}'],
				                          MessageType.OBSERVATION))
				# Set new turn
				if eng.state == GameState.IN_COMBAT:
					msgs.extend(self.__to_msg(eng.next_turn(),
					                          MessageType.EVENT))
			# Check for gameover at end of every step
			msgs.extend(self.__to_msg(eng.check_gameover(),
			                          MessageType.EVENT))
			# Update steps counter
			n_step += 1
			t.update(n_step)
		# Include message in case max number of steps was reached
		if n_step >= max_steps:
			msgs.append('RUN OVER\tSimulation interrupted: max number of steps reached!')
		
		return msgs


if __name__ == "__main__":
	fire.Fire(Simulator)