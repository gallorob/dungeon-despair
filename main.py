import os.path
from shutil import rmtree
from typing import Optional

import pygame
import pygame_gui
from pygame_gui import PackageResource

from configs import configs
from engine.main_engine import GameEngine, GameState
from level import Level, Room
from level_utils import load_level
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

encounter_preview = EncounterPreview(pygame.Rect(0, 0, room_preview_width, room_preview_height), ui_manager)
events_history = EventsHistory(pygame.Rect(0, room_preview_height, events_history_width, events_history_height),
                               ui_manager)
level_preview = LevelPreview(pygame.Rect(room_preview_width, 0, level_minimap_width, level_minimap_height), ui_manager)
combat_window = ActionWindow(
	pygame.Rect(room_preview_width, level_minimap_height, combat_window_width, combat_window_height), ui_manager)

game_engine: Optional[GameEngine] = None

level_preview.hide()
encounter_preview.hide()
combat_window.hide()
events_history.hide()


def show_level(level: Level):
	global game_engine
	
	game_engine = GameEngine(level=level)
	
	level_preview.create_minimap(game_engine.game_data)
	encounter_preview.display_room_background(game_engine.get_current_room())
	encounter_preview.display_heroes(game_engine.get_heroes_party())
	encounter_preview.display_stress_level(game_engine.stress)
	
	check_and_start_encounter(game_engine=game_engine,
	                          level_preview=level_preview,
	                          encounter_preview=encounter_preview,
	                          events_history=events_history,
	                          combat_window=combat_window)


# select the level
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

messages = []


def check_and_start_encounter(game_engine: GameEngine,
                              level_preview: LevelPreview,
                              encounter_preview: EncounterPreview,
                              events_history: EventsHistory,
                              combat_window: ActionWindow):
	if game_engine.state != GameState.IDLE:
		level_preview.toggle_movement()
	if game_engine.state == GameState.IN_COMBAT:
		events_history.new_encounter()  # TODO: Change
		encounter_preview.display_encounter(game_engine.get_current_encounter())
		combat_window.display_attacks(game_engine.get_attacks())
		
		encounter_preview.update_attacking(game_engine.get_attacker_idx())
		
		# TODO: Fix this patchwork :)
		# events_history.add_text_and_scroll(
		messages.append(
			f'Attacking: <b>{game_engine.combat_engine.currently_attacking(game_engine.heroes, game_engine.game_data).name}</b>')


def check_aftermath(game_engine: GameEngine,
                    level_preview: LevelPreview,
                    encounter_preview: EncounterPreview,
                    events_history: EventsHistory,
                    combat_window: ActionWindow):
	msgs = game_engine.check_dead_entities()
	for msg in msgs:
		events_history.add_text_and_scroll(msg)
	
	encounter_preview.display_heroes(game_engine.get_heroes_party())
	encounter_preview.display_encounter(game_engine.get_current_encounter())
	
	combat_window.clear_attacks()
	
	game_engine.check_end_encounter()
	if game_engine.state == GameState.IDLE:
		level_preview.update_button_text(game_engine.get_current_encounter(), game_engine.get_current_room().name)
		level_preview.toggle_movement()
		events_history.add_text_and_scroll('<i><b>### END OF ENCOUNTER</i></b>')
	elif game_engine.state == GameState.IN_COMBAT:
		msg = game_engine.next_turn()
		if msg:
			events_history.add_text_and_scroll(msg)
		combat_window.display_attacks(game_engine.get_attacks())
		events_history.add_text_and_scroll(
			f'Attacking: <b>{game_engine.combat_engine.currently_attacking(game_engine.heroes, game_engine.game_data).name}</b>')
		
		encounter_preview.update_attacking(game_engine.get_attacker_idx())
	
	encounter_preview.display_stress_level(game_engine.stress)


while running:
	time_delta = clock.tick(60) / 1000.0
	
	for event in pygame.event.get():
		
		if event.type == pygame.QUIT:
			running = False
		
		ui_manager.process_events(event)
		
		# Check if the event is a file dialog selection event
		if event.type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED and event.ui_element == file_dlg:
			selected_file_path = event.text
			level = load_level(selected_file_path)
			level_preview.show()
			encounter_preview.show()
			combat_window.show()
			events_history.show()
			show_level(level)
		
		if event.type == pygame_gui.UI_WINDOW_CLOSE and event.ui_element == file_dlg:
			if game_engine is None:
				# no level was picked, so close the application
				running = False
		
		elif event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 1:  # Left mouse button
				if level_preview.get_abs_rect().collidepoint(event.pos):
					clicked_room_name, encounter_idx = level_preview.check_clicked_encounter(event.pos)
					if clicked_room_name and (not game_engine.same_area(clicked_room_name, encounter_idx)):
						if game_engine.reachable(clicked_room_name, encounter_idx):
							messages.extend(
								game_engine.move_to_room(room_name=clicked_room_name, encounter_idx=encounter_idx))
							level_preview.shift_minimap(clicked_room_name)
							if isinstance(game_engine.get_current_room(), Room):
								encounter_preview.display_room_background(game_engine.get_current_room())
							else:
								encounter_preview.display_corridor_background(game_engine.get_current_room(),
								                                              idx=game_engine.encounter_idx)
							encounter_preview.display_stress_level(game_engine.stress)
							encounter_preview.display_encounter(game_engine.get_current_encounter())
							check_and_start_encounter(game_engine=game_engine,
							                          level_preview=level_preview,
							                          encounter_preview=encounter_preview,
							                          events_history=events_history,
							                          combat_window=combat_window)
						else:
							messages.append(
								f'You can\'t reach <b>{clicked_room_name}</b> from <b>{game_engine.get_current_room().name}</b>!')
				
				elif combat_window.get_abs_rect().collidepoint(event.pos):
					attack = combat_window.check_clicked_attack(event.pos)
					if attack is not None:
						for attack_msg in game_engine.process_attack(attack):
							events_history.add_text_and_scroll(attack_msg)
						
						check_aftermath(game_engine=game_engine,
						                level_preview=level_preview,
						                encounter_preview=encounter_preview,
						                events_history=events_history,
						                combat_window=combat_window)
		
		while len(messages) > 0:
			message = messages.pop(0)
			events_history.add_text_and_scroll(message)
	
	ui_manager.update(time_delta)
	screen.fill('#121212')
	
	encounter_preview.update(time_delta)
	level_preview.update(time_delta)
	combat_window.update(time_delta)
	
	ui_manager.draw_ui(screen)
	pygame.display.update()

pygame.quit()
