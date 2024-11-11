import copy
import os.path
from enum import Enum, auto
from typing import Union, Optional

import pygame
import pygame_gui
from pygame.event import EventType
from pygame_gui import PackageResource
from pygame_gui.elements import UIWindow

from configs import configs
from context_manager import ContextManager
from dungeon_despair.domain.attack import Attack
from dungeon_despair.domain.configs import config as ddd_config
from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.level import Level
from dungeon_despair.domain.room import Room
from engine.actions_engine import LootingChoice
from engine.combat_engine import CombatPhase
from engine.game_engine import GameEngine, GameState
from engine.message_system import msg_system
from engine.movement_engine import Destination
from engine.stress_system import stress_system
from heroes_party import Hero, get_temp_heroes
from player.ai_player import AIPlayer
from player.base_player import PlayerType, Player
from player.human_player import HumanPlayer
from player.random_player import RandomPlayer
from ui_components.action_menu import ActionWindow, trap_choices, treasure_choices
from ui_components.encounter_preview import EncounterPreview
from ui_components.events_history import EventsHistory
from ui_components.gameover_window import GameOver
from ui_components.level_preview import LevelPreview
from utils import set_ingame_properties

# clear assets folder on exec
if os.path.exists(configs.assets.dungeon_dir):
	for file in os.listdir(configs.assets.dungeon_dir):
		if os.path.isfile(os.path.join(configs.assets.dungeon_dir, file)):
			os.remove(os.path.join(configs.assets.dungeon_dir, file))
ddd_config.temp_dir = configs.assets.dungeon_dir

pygame.init()

# Initialize the screen
screen = pygame.display.set_mode((configs.ui.screen_width, configs.ui.screen_height))
pygame.display.set_caption("Dungeon Despair")
pygame.display.set_icon(pygame.image.load(configs.assets.logo))

background_image = pygame.image.load(configs.assets.screens.background)
screen.blit(background_image,
            dest=pygame.Rect(0, 0, configs.ui.screen_width, configs.ui.screen_height))  # TODO: Scale the background correctly and blur it a bit

# TODO: Add all the other main menu things (logo, title, load scenario button, quit button)

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
room_preview_height = screen.get_height() * configs.ui.topleft_preview_percentage
room_preview_width = screen.get_width() * configs.ui.left_panel_percentage

level_minimap_height = screen.get_height() / 2
level_minimap_width = screen.get_width() * (1 - configs.ui.left_panel_percentage)

action_window_height = screen.get_height() / 2
action_window_width = screen.get_width() * (1 - configs.ui.left_panel_percentage)

events_history_height = screen.get_height() * (1 - configs.ui.topleft_preview_percentage)
events_history_width = screen.get_width() * configs.ui.left_panel_percentage

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
game_over_window = GameOver(rect=pygame.Rect(configs.ui.screen_width / 4, configs.ui.screen_height / 4,
                                             configs.ui.screen_width / 2, configs.ui.screen_height / 2),
                            ui_manager=ui_manager)
game_over_window.hide()

# Set players
heroes_player = AIPlayer()
enemies_player = HumanPlayer()

# Create game engine
game_engine: GameEngine = GameEngine(heroes_player=heroes_player,
                                     enemies_player=enemies_player)

# Level selection dialog
file_dlg = pygame_gui.windows.ui_file_dialog.UIFileDialog(
	rect=pygame.Rect(configs.ui.screen_width / 4, configs.ui.screen_height / 4,
	                 configs.ui.screen_width / 2, configs.ui.screen_height / 2),
	manager=ui_manager,
	window_title='Choose a scenario',
	initial_file_path='./my_scenarios',
	allow_existing_files_only=False,
	allow_picking_directories=False,
	always_on_top=True)
file_dlg.show()

# Exit game dialog
exit_dlg = None
def get_exit_dlg():
	return pygame_gui.windows.UIConfirmationDialog(
	rect=pygame.Rect(configs.ui.screen_width / 4, configs.ui.screen_height / 4,
	                 configs.ui.screen_width / 4, configs.ui.screen_height / 6),
	manager=ui_manager,
    window_title="Exit Confirmation",
    action_long_desc="Do you really want to close the game?",
    action_short_name="Yes",
    blocking=True,
	always_on_top=True)

# Define a clock to control the frame rate
clock = pygame.time.Clock()
# Main loop
running = True

# Messages for the events history
messages = []

# Context manager for the LLM player
cntxt_mngr = ContextManager()

# TODO: Make a main menu, scenario selection, buttons etc...
class AppState(Enum):
	IN_MAIN_MENU = auto()
	IN_LOADING_SCENARIO = auto()
	IN_GAME = auto()
appstate = AppState.IN_LOADING_SCENARIO

def event_in_ui_element(event: EventType,
                        element: UIWindow) -> bool:
	return element.get_abs_rect().collidepoint(event.pos)

def update_ui_elements():
	if isinstance(game_engine.current_room, Room):
		encounter_preview.display_room_background(room=game_engine.current_room)
	else:
		encounter_preview.display_corridor_background(corridor=game_engine.current_room,
		                                              idx=game_engine.movement_engine.encounter_idx)
	encounter_preview.display_heroes(game_engine.heroes)
	encounter_preview.display_encounter(game_engine.current_encounter)
	encounter_preview.display_stress_level(stress_system.stress)
	encounter_preview.update_modifiers(heroes=game_engine.heroes,
	                                   enemies=game_engine.current_encounter.enemies)
	level_preview.update_button_text(encounter=game_engine.current_encounter,
	                                 roomcorridor_name=game_engine.current_room.name,
	                                 encounter_idx=game_engine.movement_engine.encounter_idx)
	
	if game_engine.state == GameState.IN_COMBAT:
		if level_preview.allow_movement: level_preview.set_movement(allowed=False)
		encounter_preview.update_attacking(idx=game_engine.attacker_and_idx[1])
		action_window.display_actions(actions=game_engine.actions,
		                              disable_not_moving=game_engine.combat_engine.state == CombatPhase.CHOOSE_POSITION)
	elif game_engine.state == GameState.INSPECTING_TRAP:
		if level_preview.allow_movement: level_preview.set_movement(allowed=False)
		action_window.display_actions(actions=trap_choices)
	elif game_engine.state == GameState.INSPECTING_TREASURE:
		if level_preview.allow_movement: level_preview.set_movement(allowed=False)
		action_window.display_actions(actions=treasure_choices)
	elif game_engine.state == GameState.IDLE:
		action_window.display_actions(actions=[])
		if encounter_preview.attacking: encounter_preview.attacking.kill()
		if not level_preview.allow_movement: level_preview.set_movement(allowed=True)
	
	if game_engine.combat_engine.state != CombatPhase.CHOOSE_POSITION:
		if encounter_preview.moving_to: encounter_preview.moving_to.kill()

while running:
	time_delta = clock.tick(60) / 1000.0
	
	for event in pygame.event.get():
		ui_manager.process_events(event)
		
		if event.type == pygame.QUIT:
			running = False
		
		elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
			exit_dlg = get_exit_dlg()
		
		if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
			if event.ui_element == exit_dlg:
				running = False
		
		elif event.type == pygame_gui.UI_WINDOW_CLOSE and event.ui_element == exit_dlg:
				exit_dlg = None
		
		elif game_engine.state == GameState.LOADING:
			# Closing the level loading dialog will close the application
			if event.type == pygame_gui.UI_WINDOW_CLOSE and event.ui_element == file_dlg:
				# no level was picked, so close the application
				running = False
			# Selecting a level
			if event.type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:
				selected_file_path = event.text
				level = Level.load_as_scenario(selected_file_path)
				heroes = get_temp_heroes()
				set_ingame_properties(game_data=level,
				                      heroes=heroes)
				game_engine.heroes = heroes
				game_engine.set_level(level)
				appstate = AppState.IN_GAME
				# Initialize in-game screens
				level_preview.show()
				level_preview.create_minimap(game_data=game_engine.scenario)
				encounter_preview.show()
				action_window.show()
				events_history.show()
				# Update UI elements
				update_ui_elements()
		
		elif game_engine.state == GameState.IDLE:
			dest: Optional[Destination] = None
			if heroes_player.type == PlayerType.HUMAN:
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					if event_in_ui_element(event, level_preview):
						dest = level_preview.check_clicked_encounter(event.pos)
			else:
				dest = heroes_player.pick_destination(destinations=game_engine.movement_engine.destinations)
			if dest is not None:
				game_engine.move_to(dest=dest)
				game_engine.tick()
				# Update UI elements
				update_ui_elements()
				level_preview.update_minimap(game_engine.current_room.name, game_engine.movement_engine.encounter_idx)
			
		elif game_engine.state == GameState.INSPECTING_TRAP:
			idx = None
			if heroes_player.type == PlayerType.HUMAN:
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					if event_in_ui_element(event, action_window):
						idx = action_window.check_colliding_action(pos=event.pos)
			else:
				idx = game_engine.player.choose_disarm_trap()
			if idx is not None:
				game_engine.process_disarm()
				game_engine.tick()
				update_ui_elements()
		
		elif game_engine.state == GameState.INSPECTING_TREASURE:
			choice: Optional[LootingChoice] = None
			if heroes_player.type == PlayerType.HUMAN:
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					if event_in_ui_element(event, action_window):
						idx = action_window.check_colliding_action(pos=event.pos)
						if idx is not None:
							choice = treasure_choices[idx].looting_choice
			else:
				choice = game_engine.player.choose_loot_treasure(**{'game_engine_copy': copy.deepcopy(game_engine)})
			if choice is not None:
				game_engine.process_looting(choice=choice)
				game_engine.tick()
				update_ui_elements()
		
		elif game_engine.state == GameState.IN_COMBAT:
			# if game_engine.player.type == PlayerType.HUMAN:
			if game_engine.combat_engine.state == CombatPhase.PICK_ATTACK:
				if game_engine.player.type == PlayerType.HUMAN:
					action_idx: Optional[int] = None
					if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
						if event_in_ui_element(event, action_window):
							action_idx = action_window.check_colliding_action(pos=event.pos)
					elif event.type == pygame.MOUSEMOTION:
						if event_in_ui_element(event, action_window):
							hovered_action = action_window.check_colliding_action(pos=event.pos)
							if hovered_action is not None:
								encounter_preview.update_targeted(idxs=game_engine.targeted(idx=hovered_action))
				else:  # Other player types
					action_idx = game_engine.player.pick_actions(**{'actions': game_engine.actions,
					                                                'game_engine_copy': copy.deepcopy(game_engine)})
				if action_idx is not None:
					game_engine.process_attack(attack_idx=action_idx)
					game_engine.tick()
					update_ui_elements()
					# TODO: This currently removes the targeted icons, but we could instead show the new attack's
					#  targeted if we're hovering over, without waiting for the next mouse movement
					encounter_preview.update_targeted([])
				
			elif game_engine.combat_engine.state == CombatPhase.CHOOSE_POSITION:
				sprite_idx: Optional[int] = None
				if game_engine.player.type == PlayerType.HUMAN:
					if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
						if event_in_ui_element(event, encounter_preview):
							sprite_idx = encounter_preview.check_colliding_entity(pos=event.pos)
						elif event_in_ui_element(event, action_window):
							action_idx = action_window.check_colliding_action(pos=event.pos)
							if action_idx is not None:
								game_engine.combat_engine.try_cancel_move(
									action_idx=action_idx)  # TODO: Should be exposed by game_engine
								update_ui_elements()
							sprite_idx = None
					elif event.type == pygame.MOUSEMOTION:
						if event_in_ui_element(event, encounter_preview):
							hovered_sprite_idx = encounter_preview.check_colliding_entity(pos=event.pos)
							if hovered_sprite_idx is not None:
								encounter_preview.update_moving_to(sprite_idx=hovered_sprite_idx,
								                                   attacker=game_engine.attacker_and_idx[0])
				else:
					sprite_idx = game_engine.player.pick_moving(
						**{'attacker_type': game_engine.attacker_and_idx[0].__class__,
						   'n_heroes': len(game_engine.heroes.party),
						   'n_enemies': len(game_engine.current_encounter.enemies)})
				if sprite_idx is not None:
					game_engine.process_move(idx=sprite_idx)
					game_engine.tick()
					update_ui_elements()
					
	for msg in msg_system.get_queue():
		events_history.add_text_and_scroll(msg)
		
	ui_manager.update(time_delta)
	if appstate == AppState.IN_GAME:
		screen.fill('#121212')  # TODO: Fill once game has started
	
	if game_engine.state == GameState.GAME_OVER:
		if game_over_window.background_image is None:
			encounter_preview.stress_level.kill()
			action_window.clear_actions()
			game_over_window.toggle()
	
	ui_manager.draw_ui(screen)
	pygame.display.update()

pygame.quit()

pygame.quit()
