import copy
import json
import os
from enum import Enum, auto
from typing import List, Union, Dict, Any

from dungeon_despair.domain.utils import ActionType, get_enum_by_value
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
from heroes_party import generate_new_party, get_temp_heroes
from player.ai_player import AIPlayer
from player.base_player import PlayerType
from player.random_player import RandomPlayer
from engine.stress_system import stress_system
from engine.message_system import msg_system
from utils import set_ingame_properties


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


class SimulatorLogger:
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


class EventsLogger:
	def __init__(self,
	             output_filename: str):
		self.f = open(output_filename, 'w')
	
	def start_exp(self,
	              **kwargs):
		for k, v in kwargs.items():
			self.f.write(f'\tSETTINGS\t{k}: {v}\n')
	
	def start_run(self,
	              run_n: int) -> None:
		self.f.write(f'\tRUN {run_n}\n')
	
	def end(self) -> None:
		self.f.close()
	
	def write(self) -> None:
		for msg in msg_system.get_queue():
			self.f.write(f'{msg}\n')


class Simulator:
	def run_simulation(self,
	                   scenario_filename: str,
	                   simulation_type: str,
	                   simulation_runs: int,
	                   output_filename: str) -> None:
		# Set assets folder
		ddd_config.temp_dir = configs.assets.dungeon_dir
		events_logger = EventsLogger(output_filename=output_filename)
		events_logger.start_exp()
		simulation_logger = SimulatorLogger(output_filename=output_filename,
		                                    **{
			                                    'level': Level.load_as_scenario(scenario_filename),
			                                    'simulation_type': simulation_type
		                                    })
		for run_n in tqdm(range(simulation_runs), desc='Simulating...', position=0):
			# Initialize logger
			events_logger.start_run(run_n)
			simulation_logger.start_run()
			# Load the scenario
			scenario = Level.load_as_scenario(scenario_filename)
			# Simulate a random game
			self.__simulate_scenario(scenario, simulation_type, simulation_logger.current_run)
			# Log simulation messages
			events_logger.write()
		# Save logs
		events_logger.end()
		simulation_logger.save_simulation()
		
	def __simulate_scenario(self,
	                        scenario: Level,
	                        simulation_type: str,
	                        run_data: RunData,
	                        max_steps: int = 2000) -> None:
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
		heroes = get_temp_heroes()
		set_ingame_properties(game_data=scenario,
		                      heroes=heroes)
		eng.heroes = heroes
		# Set the level
		eng.set_level(level=scenario)
		eng.tick()
		# Simulate until termination or max number of steps is reached
		t = tqdm(total=max_steps, desc='Simulating steps', leave=False, position=1)
		n_step = 0
		while eng.state != GameState.GAME_OVER and n_step < max_steps:
			# Move to a new room
			if eng.state == GameState.IDLE:
				dest = eng.heroes_player.pick_destination(destinations=eng.movement_engine.destinations,
										   				  unk_areas=eng.movement_engine.unk_areas)
				eng.move_to(dest=dest)
			# Loot treasures
			elif eng.state == GameState.INSPECTING_TREASURE:
				choice = eng.player.choose_loot_treasure(**{'game_engine_copy': copy.deepcopy(eng)})
				eng.process_looting(choice=choice)
			# Disarm traps
			elif eng.state == GameState.INSPECTING_TRAP:
				if eng.player.choose_disarm_trap():
					eng.process_disarm()
			# In combat, choosing position
			elif eng.state == GameState.IN_COMBAT and eng.combat_engine.state == CombatPhase.CHOOSE_POSITION:
				entity_idx = eng.player.pick_moving(
					**{'game_engine_copy': copy.deepcopy(eng),
					   'n_heroes': len(eng.heroes.party),
					   'n_enemies': len(eng.current_encounter.enemies)})
				if entity_idx is not None:
					eng.process_move(idx=entity_idx)
				else:
					move_action = [action for action in eng.combat_engine.actions if get_enum_by_value(ActionType, action.type) == ActionType.MOVE][0]
					eng.try_cancel_attack(attack_idx=eng.combat_engine.actions.index(move_action))
			# In combat, choosing attack
			elif eng.state == GameState.IN_COMBAT and eng.combat_engine.state == CombatPhase.PICK_ATTACK:
				action_idx = eng.player.pick_actions(**{'actions': eng.actions,
				                                        'game_engine_copy': copy.deepcopy(eng)})
				eng.process_attack(attack_idx=action_idx)
			# On end of wave, terminate simulation (we only simulate with fixed heroes, so one wave)
			elif eng.state == GameState.WAVE_OVER:
				eng.state = GameState.GAME_OVER
				msgs.append('RUN OVER\tSimulation interrupted: heroes party was wiped out!')
			# Update steps counter
			n_step += 1
			run_data.n_steps += 1
			eng.tick()
			run_data.stress_trace.append(stress_system.stress)
			t.update(n_step)
		# Include message in case max number of steps was reached
		if n_step >= max_steps:
			msgs.append('RUN OVER\tSimulation interrupted: max number of steps reached!')
			run_data.termination_condition = 'Max number of steps reached'


if __name__ == "__main__":
	fire.Fire(Simulator)
