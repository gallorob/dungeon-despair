import os.path
import time

import pygame
import pygame_gui
from pygame.event import EventType
from pygame_gui import PackageResource
from pygame_gui.elements import UIWindow

from configs import configs
from engine.game_engine import GameEngine, GameState, Turn
from heroes_party import Hero
from level import Room, Enemy
from level_utils import load_level
from player.base_player import PlayerType
from player.human_player import HumanPlayer
from player.random_player import RandomPlayer
from ui_components.action_menu import ActionWindow
from ui_components.encounter_preview import EncounterPreview
from ui_components.events_history import EventsHistory
from ui_components.level_preview import LevelPreview

# clear assets folder on exec
if os.path.exists(os.path.join(configs.assets, 'dungeon_assets')):
	for file in os.listdir(os.path.join(configs.assets, 'dungeon_assets')):
		if os.path.isfile(os.path.join(configs.assets, 'dungeon_assets', file)):
			os.remove(os.path.join(configs.assets, 'dungeon_assets', file))

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

combat_window_height = screen.get_height() / 2
combat_window_width = screen.get_width() * (1 - configs.left_panel_percentage)

events_history_height = screen.get_height() * (1 - configs.topleft_preview_percentage)
events_history_width = screen.get_width() * configs.left_panel_percentage

# Initialize game areas
encounter_preview = EncounterPreview(pygame.Rect(0, 0, room_preview_width, room_preview_height), ui_manager)
events_history = EventsHistory(pygame.Rect(0, room_preview_height, events_history_width, events_history_height),
                               ui_manager)
level_preview = LevelPreview(pygame.Rect(room_preview_width, 0, level_minimap_width, level_minimap_height), ui_manager)
combat_window = ActionWindow(
	pygame.Rect(room_preview_width, level_minimap_height, combat_window_width, combat_window_height), ui_manager)

# Hide game areas on launch
level_preview.hide()
encounter_preview.hide()
combat_window.hide()
events_history.hide()

# Set players
heroes_player = RandomPlayer()
enemies_player = HumanPlayer()

# Create game engine
game_engine: GameEngine = GameEngine(heroes_player=heroes_player,
                                     enemies_player=enemies_player)

# Level selection dialog
file_dlg = pygame_gui.windows.ui_file_dialog.UIFileDialog(
	rect=pygame.Rect(configs.screen_width / 4, configs.screen_height / 4,
	                 configs.screen_width / 2, configs.screen_height / 2),
	manager=None,
	window_title='Choose a level',
	initial_file_path='./my_levels')
file_dlg.show()

# Define a clock to control the frame rate
clock = pygame.time.Clock()
# Main loop
running = True

# Messages for the events history
messages = []


def check_and_start_encounter(game_engine: GameEngine,
                              level_preview: LevelPreview,
                              encounter_preview: EncounterPreview,
                              combat_window: ActionWindow):
	level_preview.set_movement(game_engine.state == GameState.IDLE)
	if game_engine.state == GameState.IN_COMBAT:
		messages.append('<b><i>### NEW ENCOUNTER</i></b>')
		messages.append('<i>Turn 1:</i>')
		
		attacker, attacker_idx = game_engine.get_current_attacker_with_idx()
		pass_attack = game_engine.combat_engine.pass_attack
		
		encounter_preview.display_encounter(game_engine.get_current_encounter())
		combat_window.display_attacks([*attacker.attacks, pass_attack])
		encounter_preview.update_attacking(attacker_idx)
		messages.append(f'Attacking: <b>{attacker.name}</b>')


def check_aftermath(game_engine: GameEngine,
                    level_preview: LevelPreview,
                    encounter_preview: EncounterPreview,
                    combat_window: ActionWindow):
	msgs = game_engine.check_dead_entities()
	messages.extend(msgs)

	combat_window.clear_attacks()
	
	encounter_preview.display_encounter(game_engine.get_current_encounter())
	encounter_preview.display_heroes(game_engine.get_heroes_party())
	encounter_preview.update_targeted([])
	
	game_engine.check_end_encounter()
	level_preview.set_movement(game_engine.state == GameState.IDLE)
	
	if game_engine.state == GameState.IDLE:
		level_preview.update_button_text(game_engine.get_current_encounter(), game_engine.get_current_room().name)
		messages.append('<i><b>### END OF ENCOUNTER</i></b>')
	elif game_engine.state == GameState.IN_COMBAT:
		msg = game_engine.next_turn()
		if msg:
			messages.append(msg)
		combat_window.display_attacks(game_engine.get_attacks())
		attacker, attacker_idx = game_engine.get_current_attacker_with_idx()
		messages.append(f'Attacking: <b>{attacker.name}</b>')
		
		encounter_preview.update_attacking(attacker_idx)
	
	encounter_preview.display_stress_level(game_engine.stress)


def event_in_ui_element(event: EventType,
                        element: UIWindow) -> bool:
	return element.get_abs_rect().collidepoint(event.pos)


def update_targeted(event,
                    encounter_preview: EncounterPreview,
                    combat_window: ActionWindow):
	attack_idx = combat_window.check_hovered_attack(event.pos)
	if attack_idx is not None:
		idxs = game_engine.get_targeted_idxs(attack_idx)
	else:
		idxs = []
	encounter_preview.update_targeted(idxs)


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
			elif event.type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:  # and event.ui_element == file_dlg:
				selected_file_path = event.text
				level = load_level(selected_file_path)
				game_engine.set_level(level)
				level_preview.show()
				level_preview.create_minimap(game_engine.game_data)
				encounter_preview.show()
				encounter_preview.display_room_background(game_engine.get_current_room())
				encounter_preview.display_heroes(game_engine.get_heroes_party())
				encounter_preview.display_stress_level(game_engine.stress)
				combat_window.show()
				events_history.show()
				check_and_start_encounter(game_engine=game_engine,
				                          level_preview=level_preview,
				                          encounter_preview=encounter_preview,
				                          combat_window=combat_window)
		
		elif game_engine.state == GameState.IDLE:
			# Only human player can choose where to move
			if heroes_player.type == PlayerType.HUMAN:#current_player.type == PlayerType.HUMAN:
				# Process all left mouse button clicks events
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					# level_preview events
					if event_in_ui_element(event, level_preview):
						clicked_room_name, encounter_idx = level_preview.check_clicked_encounter(event.pos)
						if clicked_room_name and (not game_engine.same_area(clicked_room_name, encounter_idx)):
							if game_engine.reachable(clicked_room_name, encounter_idx):
								messages.extend(
									game_engine.move_to_room(room_name=clicked_room_name, encounter_idx=encounter_idx))
								level_preview.update_minimap(clicked_room_name, encounter_idx)
								if isinstance(game_engine.get_current_room(), Room):
									encounter_preview.display_room_background(game_engine.get_current_room())
								else:
									encounter_preview.display_corridor_background(game_engine.get_current_room(),
									                                              idx=game_engine.encounter_idx)
								encounter_preview.display_stress_level(game_engine.stress)
								check_and_start_encounter(game_engine=game_engine,
								                          level_preview=level_preview,
								                          encounter_preview=encounter_preview,
								                          combat_window=combat_window)
							else:
								messages.append(f'You can\'t reach <b>{clicked_room_name}</b> from <b>{game_engine.get_current_room().name}</b>!')
			else:
				available_destinations = game_engine.available_destinations()
				if len(available_destinations) > 0:
					destination_room_name, encounter_idx = current_player.pick_destination(available_destinations)
					messages.extend(game_engine.move_to_room(room_name=destination_room_name, encounter_idx=encounter_idx))
					level_preview.update_minimap(destination_room_name, encounter_idx)
					if isinstance(game_engine.get_current_room(), Room):
						encounter_preview.display_room_background(game_engine.get_current_room())
					else:
						encounter_preview.display_corridor_background(game_engine.get_current_room(),
						                                              idx=game_engine.encounter_idx)
					encounter_preview.display_stress_level(game_engine.stress)
					check_and_start_encounter(game_engine=game_engine,
					                          level_preview=level_preview,
					                          encounter_preview=encounter_preview,
					                          combat_window=combat_window)
				
		elif game_engine.state == GameState.IN_COMBAT:
			current_attacker, _ = game_engine.get_current_attacker_with_idx()
			current_player = game_engine.heroes_player if isinstance(current_attacker, Hero) else game_engine.enemies_player
			# Only human players can choose which attack to execute
			if current_player.type == PlayerType.HUMAN:
				# Process all left mouse button clicks events
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					# combat_window events
					if event_in_ui_element(event, combat_window):
						attack = combat_window.check_clicked_attack(event.pos)
						if attack is not None:
							attack_msgs = game_engine.process_attack(attack)
							messages.extend(attack_msgs)
						check_aftermath(game_engine=game_engine,
						                level_preview=level_preview,
						                encounter_preview=encounter_preview,
						                combat_window=combat_window)
						if game_engine.state == GameState.IN_COMBAT:
							update_targeted(event=event,
							                encounter_preview=encounter_preview,
							                combat_window=combat_window)
				# Moving mouse events
				elif event.type == pygame.MOUSEMOTION:
					# Display targeted entities when hovering over attacks
					update_targeted(event=event,
					                encounter_preview=encounter_preview,
					                combat_window=combat_window)
			else:  # Non-human player
				attack = current_player.pick_attack(current_attacker)
				attack_msgs = game_engine.process_attack(attack)
				messages.extend(attack_msgs)
				check_aftermath(game_engine=game_engine,
				                level_preview=level_preview,
				                encounter_preview=encounter_preview,
				                combat_window=combat_window)
				encounter_preview.update_targeted([])
		
	# Update messages history
	while len(messages) > 0:
		message = messages.pop(0)
		events_history.add_text_and_scroll(message)
	
	ui_manager.update(time_delta)
	screen.fill('#121212')
	
	encounter_preview.update(time_delta)
	level_preview.update(time_delta)
	combat_window.update(time_delta)
	events_history.update(time_delta)
	
	ui_manager.draw_ui(screen)
	pygame.display.update()

pygame.quit()
