import os
from typing import List

from tqdm.auto import tqdm

import fire

from dungeon_despair.domain.entities.hero import Hero
from dungeon_despair.domain.configs import config as ddd_config
from dungeon_despair.domain.level import Level

from engine.game_engine import GameEngine, GameState
from player.random_player import RandomPlayer
from configs import configs


class SimulatorLogger:
	def __init__(self,
	             output_filename: str):
		self.f = open(output_filename, 'w')
	
	def start(self,
	          run_n: int) -> None:
		self.f.write(f'### {run_n}\n')
	
	def end(self) -> None:
		self.f.close()
	
	def write(self,
	          msgs: List[str]) -> None:
		for msg in msgs:
			self.f.write(f'{msg}\n')


class Simulator:
	def run_simulation(self,
	                   scenario_filename: str,
	                   simulation_type: str,
	                   simulation_runs: int,
	                   output_filename: str) -> None:
		# Set assets folder
		ddd_config.temp_dir = os.path.join(configs.assets, 'dungeon_assets')
		logger = SimulatorLogger(output_filename)
		for run_n in tqdm(range(simulation_runs), desc='Simulating...', position=0):
			# Initialize logger
			logger.start(run_n)
			# Load the scenario
			scenario = Level.load_as_scenario(scenario_filename)
			# Simulate a random game
			msgs = self.simulate_scenario(scenario, simulation_type)
			# Log simulation messages
			logger.write(msgs)
		# Save logs
		logger.end()
	
	def simulate_scenario(self,
	                      scenario: Level,
	                      simulation_type: str,
	                      max_steps: int = 2000) -> List[str]:
		msgs = []
		if simulation_type == 'random':
			# Random players
			eng = GameEngine(heroes_player=RandomPlayer(),
			                 enemies_player=RandomPlayer())
		else:
			raise NotImplementedError(f'{simulation_type} is not implemented yet!')
		# Set the level
		eng.set_level(level=scenario)
		# Initialize by moving to the current room
		msgs.extend(eng.move_to_room(room_name=eng.game_data.current_room,
		                             encounter_idx=-1))
		msgs.extend(eng.update_state())
		# Simulate until termination or max number of steps is reached
		t = tqdm(total=max_steps, desc='Simulating steps', leave=False, position=1)
		n_step = 0
		while (eng.state != GameState.ENEMIES_WON or eng.state != GameState.HEROES_WON) and n_step < max_steps:
			# Move to a new room
			if eng.state == GameState.IDLE:
				available_destinations = eng.movement_engine.available_destinations(level=eng.game_data)
				if len(available_destinations) > 0:
					destination_room_name, encounter_idx = eng.heroes_player.pick_destination(available_destinations)
					msgs.extend(eng.move_to_room(room_name=destination_room_name, encounter_idx=encounter_idx))
					msgs.extend(eng.update_state())
			# Loot treasures
			elif eng.state == GameState.INSPECTING_TREASURE:
				do_loot = eng.heroes_player.choose_loot_treasure()
				msgs.extend(eng.attempt_looting(choice=0 if do_loot else 1))
			# Disarm traps
			elif eng.state == GameState.INSPECTING_TRAP:
				do_disarm = eng.heroes_player.choose_disarm_trap()
				msgs.extend(eng.attempt_disarm(choice=0 if do_disarm else 1))
			# Combat enemies
			elif eng.state == GameState.IN_COMBAT:
				current_attacker, _ = eng.get_current_attacker_with_idx()
				current_player = eng.heroes_player if isinstance(current_attacker, Hero) else eng.enemies_player
				attack = current_player.pick_attack(eng.get_attacks())
				msgs.extend(eng.process_attack(attack))
				msgs.extend(eng.check_dead_entities())
				msgs.extend(eng.check_end_encounter())
				# Set new turn
				if eng.state == GameState.IN_COMBAT:
					msgs.extend(eng.next_turn())
			# Check for gameover at end of every step
			msgs.extend(eng.check_gameover())
			# Update steps counter
			n_step += 1
			t.update(n_step)
		# Include message in case max number of steps was reached
		if n_step >= max_steps:
			msgs.append('Simulation interrupted: max number of steps reached!')
		
		return msgs


if __name__ == "__main__":
	fire.Fire(Simulator)