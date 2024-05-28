import pygame
import pygame_gui
from pygame_gui import PackageResource

from configs import configs
from engine.main_engine import GameEngine, GameState
from ui_components.action_menu import ActionWindow
from ui_components.encounter_preview import EncounterPreview
from ui_components.events_history import EventsHistory
from ui_components.level_preview import LevelPreview

pygame.init()

# Initialize the screen
screen = pygame.display.set_mode((configs.screen_width, configs.screen_height))
pygame.display.set_caption("Dungeon Despair")

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

game_engine = GameEngine()

level_preview.create_minimap(game_engine.game_data)
encounter_preview.display_room(game_engine.get_current_room())
encounter_preview.display_heroes(game_engine.get_heroes_party())
encounter_preview.display_stress_level(game_engine.stress)

# Define a clock to control the frame rate
clock = pygame.time.Clock()
# Main loop
running = True


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
		
		# TODO: Fix this patchwork :)
		events_history.add_text_and_scroll(
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
	
	encounter_preview.display_stress_level(game_engine.stress)


check_and_start_encounter(game_engine=game_engine,
                          level_preview=level_preview,
                          encounter_preview=encounter_preview,
                          events_history=events_history,
                          combat_window=combat_window)

while running:
	time_delta = clock.tick(60) / 1000.0
	
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
		
		elif event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 1:  # Left mouse button
				if level_preview.get_abs_rect().collidepoint(event.pos):
					clicked_room_name = level_preview.check_clicked_encounter(event.pos)
					if clicked_room_name and clicked_room_name != game_engine.get_current_room().name and game_engine.reachable(
						clicked_room_name):
						game_engine.move_to_room(room_name=clicked_room_name)
						level_preview.shift_minimap(clicked_room_name)
						encounter_preview.display_room(game_engine.get_current_room())
						encounter_preview.display_stress_level(game_engine.stress)
						encounter_preview.display_encounter(game_engine.get_current_encounter())
						check_and_start_encounter(game_engine=game_engine,
						                          level_preview=level_preview,
						                          encounter_preview=encounter_preview,
						                          events_history=events_history,
						                          combat_window=combat_window)
				
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
	
	ui_manager.update(time_delta)
	screen.fill('#121212')
	
	encounter_preview.update(time_delta)
	level_preview.update(time_delta)
	combat_window.update(time_delta)
	
	ui_manager.draw_ui(screen)
	pygame.display.update()

pygame.quit()
