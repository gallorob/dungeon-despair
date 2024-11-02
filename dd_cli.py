import copy
import json
import os
from enum import Enum, auto
from typing import List, Union, Dict, Any

import fire
from tqdm.auto import tqdm

from configs import configs
from dungeon_despair.domain.configs import config as ddd_config
from dungeon_despair.domain.corridor import Corridor
from dungeon_despair.domain.encounter import Encounter
from dungeon_despair.domain.entities.hero import Hero
from dungeon_despair.domain.level import Level
from dungeon_despair.domain.room import Room
from engine.combat_engine import CombatPhase
from engine.game_engine import GameEngine, GameState
from player.ai_player import AIPlayer
from player.base_player import PlayerType
from player.random_player import RandomPlayer
from utils import get_current_encounter, get_current_room


class RunData:
	def __init__(self):
		self.n_steps = 0
		self.stress_trace: List[float] = []
		self.encounters_stress_delta: List[float] = []
		self.encounters_desc: List[str] = []
		self.termination_condition: str = ''
		
		self.combat_encounter_desc: str = ''
		self.combat_encounter_stress_pre: float = 0.0
	
	@staticmethod
	def get_encounter_desc(area: Union[Room, Corridor],
	                       idx: int,
	                       encounter: Encounter,
	                       encounter_type: str) -> str:
		idx = f' ({idx})' if idx != -1 else ''
		relevant_entities = ', '.join([x.name for x in encounter.entities[encounter_type]])
		desc = f'Encounter {area.name}{idx} {encounter_type} - {relevant_entities}'
		return desc
	
	def info(self) -> Dict[str, Any]:
		return {
			'n_steps': self.n_steps,
			'stress_trace': self.stress_trace,
			'encounters_stress_delta': self.encounters_stress_delta,
			'encounters_desc': self.encounters_desc,
			'termination_condition': self.termination_condition
		}


class SimulatorJsonLogger:
	def __init__(self,
	             output_filename: str,
	             **kwargs):
		self.output_filename = output_filename.replace('.log', '.json')
		self.simulation_data: List[RunData] = []
		self.configs = ddd_config
		self.level: Level = copy.deepcopy(kwargs['level'])
		self.simulation_type: str = kwargs['simulation_type']
	
	@property
	def current_run(self):
		assert len(self.simulation_data) > 0, f'No run has started yet!'
		return self.simulation_data[-1]
	
	def start_run(self):
		self.simulation_data.append(RunData())
	
	def save_simulation(self):
		with open(self.output_filename, 'w') as f:
			json.dump({
				'simulation_data': [x.info() for x in self.simulation_data],
				'configs': self.configs.__dict__,
				'simulation_type': self.simulation_type,
				'level': self.level.model_dump_json()
			}, f)


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
		logger = SimulatorLogger(output_filename=output_filename)
		logger.start_exp()
		json_logger = SimulatorJsonLogger(output_filename=output_filename,
		                                  **{
			                                  'level': Level.load_as_scenario(scenario_filename),
			                                  'simulation_type': simulation_type
		                                  })
		for run_n in tqdm(range(simulation_runs), desc='Simulating...', position=0):
			# Initialize logger
			logger.start_run(run_n)
			json_logger.start_run()
			# Load the scenario
			scenario = Level.load_as_scenario(scenario_filename)
			# Simulate a random game
			msgs = self.__simulate_scenario(scenario, simulation_type, json_logger.current_run)
			# Log simulation messages
			logger.write(msgs)
		# Save logs
		logger.end()
		json_logger.save_simulation()
	
	def __to_msg(self,
	             strings: List[str],
	             msg_type: MessageType) -> List[Message]:
		return [Message(message=msg,
		                message_type=msg_type) for msg in strings]
	
	def __simulate_scenario(self,
	                        scenario: Level,
	                        simulation_type: str,
	                        run_data: RunData,
	                        max_steps: int = 2000) -> List[Message]:
		msgs = []
		if simulation_type == 'random':
			# Random players
			eng = GameEngine(heroes_player=RandomPlayer(),
			                 enemies_player=RandomPlayer())
		elif simulation_type == 'ai':
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
				if run_data.combat_encounter_desc != '':
					stress_post = eng.stress
					stress_delta = stress_post - run_data.combat_encounter_stress_pre
					run_data.encounters_desc.append(run_data.combat_encounter_desc)
					run_data.encounters_stress_delta.append(stress_delta)
					run_data.combat_encounter_desc = ''
					run_data.combat_encounter_stress_pre = 0.0
				available_destinations = eng.movement_engine.available_destinations(level=eng.game_data)
				if len(available_destinations) > 0:
					destination_room_name, encounter_idx = eng.heroes_player.pick_destination(available_destinations)
					msgs.extend(
						self.__to_msg(eng.move_to_room(room_name=destination_room_name, encounter_idx=encounter_idx),
						              MessageType.ACTION))
					msgs.extend(self.__to_msg(eng.update_state(),
					                          MessageType.EVENT))
			# Loot treasures
			elif eng.state == GameState.INSPECTING_TREASURE:
				curr_encounter = get_current_encounter(level=eng.game_data,
				                                       encounter_idx=eng.movement_engine.encounter_idx)
				encounter_desc = RunData.get_encounter_desc(area=get_current_room(eng.game_data),
				                                            idx=eng.movement_engine.encounter_idx,
				                                            encounter=curr_encounter,
				                                            encounter_type='treasure')
				stress_pre = eng.stress
				do_loot = eng.heroes_player.choose_loot_treasure()
				msgs.extend(self.__to_msg(eng.attempt_looting(choice=0 if do_loot else 1),
				                          MessageType.ACTION))
				# Log stress levels
				msgs.extend(self.__to_msg([f'The heroes stress is at {eng.stress}'],
				                          MessageType.OBSERVATION))
				if do_loot:
					stress_post = eng.stress
					run_data.encounters_stress_delta.append(stress_post - stress_pre)
					run_data.encounters_desc.append(encounter_desc)
			
			# Disarm traps
			elif eng.state == GameState.INSPECTING_TRAP:
				curr_encounter = get_current_encounter(level=eng.game_data,
				                                       encounter_idx=eng.movement_engine.encounter_idx)
				encounter_desc = RunData.get_encounter_desc(area=get_current_room(eng.game_data),
				                                            idx=eng.movement_engine.encounter_idx,
				                                            encounter=curr_encounter,
				                                            encounter_type='trap')
				stress_pre = eng.stress
				do_disarm = eng.heroes_player.choose_disarm_trap()
				msgs.extend(self.__to_msg(eng.attempt_disarm(choice=0 if do_disarm else 1),
				                          MessageType.ACTION))
				# Log stress levels
				msgs.extend(self.__to_msg([f'The heroes stress is at {eng.stress}'],
				                          MessageType.OBSERVATION))
				if do_disarm:
					stress_post = eng.stress
					run_data.encounters_stress_delta.append(stress_post - stress_pre)
					run_data.encounters_desc.append(encounter_desc)
			
			elif eng.state == GameState.IN_COMBAT and eng.combat_engine.state == CombatPhase.CHOOSE_POSITION:
				curr_encounter = get_current_encounter(level=eng.game_data,
				                                       encounter_idx=eng.movement_engine.encounter_idx)
				current_attacker, _ = eng.get_current_attacker_with_idx()
				current_player = eng.heroes_player if isinstance(current_attacker, Hero) else eng.enemies_player
				if current_player.type == PlayerType.AI:
					current_player.game_engine_copy = eng
				idx = current_player.pick_moving(attacker=current_attacker,
				                                 heroes=eng.heroes.party,
				                                 enemies=curr_encounter.entities['enemy'])
				msgs.extend(self.__to_msg(eng.process_move(idx),
				                          MessageType.ACTION))
				msgs.extend(self.__to_msg([f'The heroes stress is at {eng.stress}'],
				                          MessageType.OBSERVATION))
			# Combat enemies
			elif eng.state == GameState.IN_COMBAT and eng.combat_engine.state == CombatPhase.PICK_ATTACK:
				if run_data.combat_encounter_desc == '':
					curr_encounter = get_current_encounter(level=eng.game_data,
					                                       encounter_idx=eng.movement_engine.encounter_idx)
					run_data.combat_encounter_desc = RunData.get_encounter_desc(area=get_current_room(eng.game_data),
					                                                            idx=eng.movement_engine.encounter_idx,
					                                                            encounter=curr_encounter,
					                                                            encounter_type='enemy')
					run_data.combat_encounter_stress_pre = eng.stress
				current_attacker, _ = eng.get_current_attacker_with_idx()
				current_player = eng.heroes_player if isinstance(current_attacker, Hero) else eng.enemies_player
				if current_player.type == PlayerType.AI:
					current_player.game_engine_copy = eng
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
				if eng.state == GameState.IN_COMBAT and eng.combat_engine.state == CombatPhase.PICK_ATTACK:
					msgs.extend(self.__to_msg(eng.next_turn(),
					                          MessageType.EVENT))
			# Check for gameover at end of every step
			game_over_msgs = eng.check_gameover()
			if len(game_over_msgs) > 0:
				run_data.termination_condition = game_over_msgs[0]
			msgs.extend(self.__to_msg(game_over_msgs, MessageType.EVENT))
			# Update steps counter
			n_step += 1
			run_data.n_steps += 1
			run_data.stress_trace.append(eng.stress)
			t.update(n_step)
		# Include message in case max number of steps was reached
		if n_step >= max_steps:
			msgs.append('RUN OVER\tSimulation interrupted: max number of steps reached!')
			run_data.termination_condition = 'Max number of steps reached'
		
		return msgs


if __name__ == "__main__":
	fire.Fire(Simulator)
