import os.path

import pygame
import pygame_gui
from pygame.event import EventType
from pygame_gui import PackageResource
from pygame_gui.elements import UIWindow

from configs import configs
from dungeon_despair.domain.level import Level
from dungeon_despair.domain.room import Room
from engine.game_engine import GameEngine, GameState
from heroes_party import Hero
from player.base_player import PlayerType
from player.human_player import HumanPlayer
from player.random_player import RandomPlayer
from ui_components.action_menu import ActionWindow
from ui_components.encounter_preview import EncounterPreview
from ui_components.events_history import EventsHistory
from ui_components.gameover_window import GameOver
from ui_components.level_preview import LevelPreview
from utils import get_current_room, get_current_encounter
from dungeon_despair.domain.configs import config as ddd_config

# clear assets folder on exec
if os.path.exists(os.path.join(configs.assets, 'dungeon_assets')):
	for file in os.listdir(os.path.join(configs.assets, 'dungeon_assets')):
		if os.path.isfile(os.path.join(configs.assets, 'dungeon_assets', file)):
			os.remove(os.path.join(configs.assets, 'dungeon_assets', file))
ddd_config.temp_dir = os.path.join(configs.assets, 'dungeon_assets')

pygame.init()

# Initialize the screen
screen = pygame.display.set_mode((configs.screen_width, configs.screen_height))
pygame.display.set_caption("Dungeon Despair")
pygame.display.set_icon(pygame.image.load('./assets/dungeon_despair_logo.png'))

# Create the UI manager
ui_manager = pygame_gui.UIManager((screen.get_width(), screen.get_height()))

# https://pygame-gui.readthedocs.io/en/latest/theme_reference
ui_manager.get_theme().load_theme(PackageResource('assets.themes',
                                                  'despair_theme.json'))
ui_manager.preload_fonts([{'name': 'noto_sans', 'point_size': 14, 'style': 'bold_italic', 'antialiased': '1'},
                          {'name': 'noto_sans', 'point_size': 14, 'style': 'italic', 'antialiased': '1'},
                          {'name': 'noto_sans', 'point_size': 14, 'style': 'bold', 'antialiased': '1'}
                          ])
# Define the sizes
room_preview_height = screen.get_height() * configs.topleft_preview_percentage
room_preview_width = screen.get_width() * configs.left_panel_percentage

level_minimap_height = screen.get_height() / 2
level_minimap_width = screen.get_width() * (1 - configs.left_panel_percentage)

action_window_height = screen.get_height() / 2
action_window_width = screen.get_width() * (1 - configs.left_panel_percentage)

events_history_height = screen.get_height() * (1 - configs.topleft_preview_percentage)
events_history_width = screen.get_width() * configs.left_panel_percentage

# Initialize game areas
encounter_preview = EncounterPreview(pygame.Rect(0, 0, room_preview_width, room_preview_height), ui_manager)
events_history = EventsHistory(pygame.Rect(0, room_preview_height, events_history_width, events_history_height),
                               ui_manager)
level_preview = LevelPreview(pygame.Rect(room_preview_width, 0, level_minimap_width, level_minimap_height), ui_manager)
action_window = ActionWindow(
	pygame.Rect(room_preview_width, level_minimap_height, action_window_width, action_window_height), ui_manager)

# Hide game areas on launch
level_preview.hide()
encounter_preview.hide()
action_window.hide()
events_history.hide()

# Game over window
game_over_window = GameOver(rect=pygame.Rect(configs.screen_width / 4, configs.screen_height / 4,
                                             configs.screen_width / 2, configs.screen_height / 2),
                            ui_manager=ui_manager)
game_over_window.hide()

# Set players
heroes_player = RandomPlayer()
enemies_player = RandomPlayer()

# Create game engine
game_engine: GameEngine = GameEngine(heroes_player=heroes_player,
                                     enemies_player=enemies_player)

# Level selection dialog
file_dlg = pygame_gui.windows.ui_file_dialog.UIFileDialog(
	rect=pygame.Rect(configs.screen_width / 4, configs.screen_height / 4,
	                 configs.screen_width / 2, configs.screen_height / 2),
	manager=None,
	window_title='Choose a scenario',
	initial_file_path='./my_scenarios',
	allow_existing_files_only=False,
	allow_picking_directories=False,
	always_on_top=True)
file_dlg.show()

# Define a clock to control the frame rate
clock = pygame.time.Clock()
# Main loop
running = True

# Messages for the events history
messages = []


def update_ui_previews(game_engine: GameEngine,
                       level_preview: LevelPreview,
                       encounter_preview: EncounterPreview):
	curr_room = get_current_room(game_engine.game_data)
	curr_encounter = get_current_encounter(level=game_engine.game_data,
	                                       encounter_idx=game_engine.movement_engine.encounter_idx)
	# update level preview
	level_preview.set_movement(game_engine.state == GameState.IDLE)
	level_preview.update_minimap(game_engine.game_data.current_room,
	                             game_engine.movement_engine.encounter_idx)
	level_preview.update_button_text(encounter=curr_encounter,
	                                 roomcorridor_name=curr_room.name,
	                                 encounter_idx=game_engine.movement_engine.encounter_idx)
	# update encounter preview
	if isinstance(curr_room, Room):
		encounter_preview.display_room_background(curr_room)
	else:
		encounter_preview.display_corridor_background(curr_room,
		                                              idx=game_engine.movement_engine.encounter_idx)
	encounter_preview.display_encounter(curr_encounter)
	encounter_preview.display_heroes(game_engine.get_heroes_party())
	encounter_preview.update_targeted([])
	encounter_preview.display_stress_level(game_engine.stress)


def update_ui_actions(game_engine: GameEngine,
                      action_window: ActionWindow):
	action_window.clear_choices()
	action_window.clear_attacks()
	if game_engine.state == GameState.IN_COMBAT:
		action_window.display_attacks(attacks=game_engine.get_attacks())
	if game_engine.state == GameState.INSPECTING_TRAP:
		action_window.display_trap_choices()
	if game_engine.state == GameState.INSPECTING_TREASURE:
		action_window.display_treasure_choices()


def check_and_start_encounter(game_engine: GameEngine,
                              level_preview: LevelPreview,
                              encounter_preview: EncounterPreview,
                              action_window: ActionWindow):
	update_ui_previews(game_engine=game_engine,
	                   level_preview=level_preview,
	                   encounter_preview=encounter_preview)
	if game_engine.state == GameState.IN_COMBAT or game_engine.state == GameState.INSPECTING_TRAP or game_engine.state == GameState.INSPECTING_TREASURE:
		if game_engine.state == GameState.IN_COMBAT:
			action_window.display_attacks(game_engine.get_attacks())
			attacker, attacker_idx = game_engine.get_current_attacker_with_idx()
			encounter_preview.update_attacking(attacker_idx)
		elif game_engine.state == GameState.INSPECTING_TRAP:
			action_window.display_trap_choices()
		elif game_engine.state == GameState.INSPECTING_TREASURE:
			action_window.display_treasure_choices()


def check_aftermath(game_engine: GameEngine,
                    level_preview: LevelPreview,
                    encounter_preview: EncounterPreview,
                    action_window: ActionWindow):
	msgs = game_engine.check_dead_entities()
	messages.extend(msgs)
	msgs = game_engine.check_end_encounter()
	messages.extend(msgs)
	
	update_ui_previews(game_engine=game_engine,
	                   level_preview=level_preview,
	                   encounter_preview=encounter_preview)
	
	if game_engine.state != GameState.IN_COMBAT:
		level_preview.update_button_text(get_current_encounter(level=game_engine.game_data,
		                                                       encounter_idx=game_engine.movement_engine.encounter_idx),
		                                 get_current_room(level=game_engine.game_data).name,
		                                 encounter_idx=game_engine.movement_engine.encounter_idx)
	elif game_engine.state == GameState.IN_COMBAT:
		msgs = game_engine.next_turn()
		messages.extend(msgs)
		attacker, attacker_idx = game_engine.get_current_attacker_with_idx()
		encounter_preview.update_attacking(attacker_idx)
		
	messages.extend(game_engine.check_gameover())
	
	update_ui_actions(game_engine=game_engine,
	                  action_window=action_window)


def event_in_ui_element(event: EventType,
                        element: UIWindow) -> bool:
	return element.get_abs_rect().collidepoint(event.pos)


def update_targeted(event,
                    encounter_preview: EncounterPreview,
                    action_window: ActionWindow):
	attack_idx = action_window.check_hovered_attack(event.pos)
	if attack_idx is not None:
		idxs = game_engine.get_targeted_idxs(attack_idx)
	else:
		idxs = []
	encounter_preview.update_targeted(idxs)


def move_to_room(room_name: str,
                 encounter_idx: int,
                 game_engine: GameEngine,
                 level_preview: LevelPreview,
                 encounter_preview: EncounterPreview):
	messages.extend(game_engine.move_to_room(room_name=room_name, encounter_idx=encounter_idx))
	messages.extend(game_engine.update_state())
	check_and_start_encounter(game_engine=game_engine,
	                          level_preview=level_preview,
	                          encounter_preview=encounter_preview,
	                          action_window=action_window)
	update_ui_actions(game_engine=game_engine,
	                  action_window=action_window)


while running:
	time_delta = clock.tick(60) / 1000.0
	
	for event in pygame.event.get():
		ui_manager.process_events(event)
		
		# Closing the application
		if event.type == pygame.QUIT:
			running = False
		
		# Check only events when the level loading dialog is shown
		elif game_engine.state == GameState.LOADING:
			# Closing the level loading dialog will close the application
			if event.type == pygame_gui.UI_WINDOW_CLOSE and event.ui_element == file_dlg:
				# no level was picked, so close the application
				running = False
			# Selecting a level
			elif event.type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:
				selected_file_path = event.text
				level = Level.load_as_scenario(selected_file_path)
				game_engine.set_level(level)
				level_preview.show()
				level_preview.create_minimap(game_engine.game_data)
				encounter_preview.show()
				encounter_preview.display_room_background(get_current_room(game_engine.game_data))
				encounter_preview.display_heroes(game_engine.get_heroes_party())
				action_window.show()
				events_history.show()
				move_to_room(room_name=game_engine.game_data.current_room,
				             encounter_idx=-1,
				             game_engine=game_engine,
				             level_preview=level_preview,
				             encounter_preview=encounter_preview)
		
		elif game_engine.state == GameState.IDLE:
			# Only human player can choose where to move
			if heroes_player.type == PlayerType.HUMAN:
				# Process all left mouse button clicks events
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					# level_preview events
					if event_in_ui_element(event, level_preview):
						clicked_room_name, encounter_idx = level_preview.check_clicked_encounter(event.pos)
						if clicked_room_name and (not game_engine.movement_engine.same_area(level=game_engine.game_data,
						                                                                    room_name=clicked_room_name,
						                                                                    encounter_idx=encounter_idx)):
							is_reachable, err_msg = game_engine.movement_engine.reachable(level=game_engine.game_data,
							                                                              room_name=clicked_room_name,
							                                                              idx=encounter_idx)
							if is_reachable:
								move_to_room(room_name=clicked_room_name,
								             encounter_idx=encounter_idx,
								             game_engine=game_engine,
								             level_preview=level_preview,
								             encounter_preview=encounter_preview)
							else:
								messages.append(err_msg)
			else:
				available_destinations = game_engine.movement_engine.available_destinations(level=game_engine.game_data)
				if len(available_destinations) > 0:
					destination_room_name, encounter_idx = heroes_player.pick_destination(available_destinations)
					move_to_room(room_name=destination_room_name,
					             encounter_idx=encounter_idx,
					             game_engine=game_engine,
					             level_preview=level_preview,
					             encounter_preview=encounter_preview)
		
		elif game_engine.state == GameState.INSPECTING_TREASURE:
			# Only human players can choose whether to loot treasures
			if heroes_player.type == PlayerType.HUMAN:
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					if event_in_ui_element(event, action_window):
						choice = action_window.check_clicked_choice(event.pos)
						if choice is not None:
							outcome_action = game_engine.attempt_looting(choice)
							messages.extend(outcome_action)
							action_window.clear_choices()
							update_ui_previews(game_engine=game_engine,
							                   level_preview=level_preview,
							                   encounter_preview=encounter_preview)
			else:
				do_loot = heroes_player.choose_loot_treasure()
				outcome_action = game_engine.attempt_looting(choice=0 if do_loot else 1)
				messages.extend(outcome_action)
				action_window.clear_choices()
				update_ui_previews(game_engine=game_engine,
				                   level_preview=level_preview,
				                   encounter_preview=encounter_preview)
		
		elif game_engine.state == GameState.INSPECTING_TRAP:
			# Only human players can choose whether to disarm traps
			if heroes_player.type == PlayerType.HUMAN:
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					if event_in_ui_element(event, action_window):
						choice = action_window.check_clicked_choice(event.pos)
						if choice is not None:
							outcome_action = game_engine.attempt_disarm(choice)
							messages.extend(outcome_action)
							game_engine.state = GameState.IDLE
							action_window.clear_choices()
							update_ui_previews(game_engine=game_engine,
							                   level_preview=level_preview,
							                   encounter_preview=encounter_preview)
			else:
				do_disarm = heroes_player.choose_disarm_trap()
				outcome_action = game_engine.attempt_disarm(choice=0 if do_disarm else 1)
				messages.extend(outcome_action)
				game_engine.state = GameState.IDLE
				action_window.clear_choices()
				update_ui_previews(game_engine=game_engine,
				                   level_preview=level_preview,
				                   encounter_preview=encounter_preview)
			
		
		elif game_engine.state == GameState.IN_COMBAT:
			current_attacker, _ = game_engine.get_current_attacker_with_idx()
			current_player = game_engine.heroes_player if isinstance(current_attacker,
			                                                         Hero) else game_engine.enemies_player
			# Only human players can choose which attack to execute
			if current_player.type == PlayerType.HUMAN:
				# Process all left mouse button clicks events
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					# action_window events
					if event_in_ui_element(event, action_window):
						attack = action_window.check_clicked_attack(event.pos)
						if attack is not None:
							attack_msgs = game_engine.process_attack(attack)
							messages.extend(attack_msgs)
							encounter_preview.display_stress_level(game_engine.stress)
							check_aftermath(game_engine=game_engine,
							                level_preview=level_preview,
							                encounter_preview=encounter_preview,
							                action_window=action_window)
							if game_engine.state == GameState.IN_COMBAT:
								update_targeted(event=event,
								                encounter_preview=encounter_preview,
								                action_window=action_window)
				# Moving mouse events
				elif event.type == pygame.MOUSEMOTION:
					# Display targeted entities when hovering over attacks
					update_targeted(event=event,
					                encounter_preview=encounter_preview,
					                action_window=action_window)
			else:  # Non-human player
				attack = current_player.pick_attack(game_engine.get_attacks())
				attack_msgs = game_engine.process_attack(attack)
				messages.extend(attack_msgs)
				encounter_preview.display_stress_level(game_engine.stress)
				check_aftermath(game_engine=game_engine,
				                level_preview=level_preview,
				                encounter_preview=encounter_preview,
				                action_window=action_window)
				encounter_preview.update_targeted([])
	
	# Update messages history
	while len(messages) > 0:
		message = messages.pop(0)
		events_history.add_text_and_scroll(message)
	
	ui_manager.update(time_delta)
	screen.fill('#121212')
	
	encounter_preview.update(time_delta)
	level_preview.update(time_delta)
	action_window.update(time_delta)
	events_history.update(time_delta)
	game_over_window.update(time_delta)
	
	if game_engine.state == GameState.HEROES_WON:
		if game_over_window.img_idx == -1:
			game_over_window.img_idx = 0
			game_over_window.show()
	elif game_engine.state == GameState.ENEMIES_WON:
		if game_over_window.img_idx == -1:
			game_over_window.img_idx = 1
			game_over_window.show()
	
	ui_manager.draw_ui(screen)
	
	pygame.display.update()

pygame.quit()
