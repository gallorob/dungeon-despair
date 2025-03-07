import os
from typing import List, Optional, Union
from dungeon_despair.domain.level import Level
from pygame import Rect
import pygame
import pygame_gui
from pygame_gui.core.gui_type_hints import RectLike, Coordinate
from pygame_gui.core.interfaces import IUIManagerInterface, IContainerLikeInterface
from pygame_gui.elements import UIWindow, UIImage, UILabel, UIButton, UIPanel
from engine.game_engine import GameEngine, GameState
from engine.stress_system import stress_system
from engine.message_system import msg_system
from configs import configs
from utils import get_entities_differences, reset_entity

class Checkbox(UIButton):
	def __init__(self,
				 relative_rect: Union[RectLike, Coordinate], 
				 manager: Optional[IUIManagerInterface] = None, 
				 container: Optional[IContainerLikeInterface] = None):
		super().__init__(text='',
				   		 relative_rect=relative_rect,
				   		 manager=manager,
						 container=container)
		self.enable()
		self.ticked = 'X'
		self.unticked = ' '
		self.set_text(self.unticked)

	def process_event(self, event):
		if self.is_enabled and event.type == pygame.MOUSEBUTTONDOWN and self.get_abs_rect().collidepoint(event.pos):
			self.set_text(self.ticked if self.text == self.unticked else self.unticked)
		return super().process_event(event)

class RegenPicker(UIWindow):
	def __init__(self,
				 rect: Rect,
				 ui_manager: IUIManagerInterface,
				 level_copy: Level,
				 game_engine: GameEngine):
		super().__init__(rect, ui_manager, window_display_title='Pick Regenerables', resizable=False, draggable=False,
						 always_on_top=True)
		
		self.level_copy = level_copy
		self.game_engine = game_engine

		self.stress_label: Optional[UILabel] = None
		self.make_stress_label(amount=stress_system.stress)
		
		self.diff_entities, self.locations = get_entities_differences(ref_level=level_copy, curr_level=game_engine.scenario)
		
		self.panel = UIPanel(Rect(0, self.get_container().rect.height / 10, self.get_relative_rect().width, self.get_relative_rect().height - self.get_container().rect.height / 5), 
							 starting_height=1, 
							 manager=self.ui_manager, 
							 container=self)
		
		self.checkboxes: List[Checkbox] = []
		self.create_entity_grid()

		self.spending: int = 0

		self.regen_button = UIButton(Rect(0, self.get_relative_rect().height - self.get_container().rect.height / 5, self.get_relative_rect().width, self.get_relative_rect().height / 10), 
									 'Regenerate', 
									 self.ui_manager, 
									 container=self)
		self.regen_button.set_tooltip('Regenerate selected entities')
		self.regen_button.disable()

	def make_stress_label(self, amount: int):
		if self.stress_label is None:
			self.stress_label = UILabel(
				relative_rect=Rect(self.get_container().rect.width / 2 - self.get_container().rect.width / 8, 0,
								   self.get_container().rect.width / 4, self.get_container().rect.height / 10),
				text=f'Available Stress: {amount}',
				container=self.get_container(),
				manager=self.ui_manager)
		else:
			self.stress_label.text = f'Available Stress: {amount}'
			self.stress_label.rebuild()

	def create_entity_grid(self):
		y_offset = self.get_container().rect.height / 15
		for i, (entity, location) in enumerate(zip(self.diff_entities, self.locations)):
			entity_image = pygame.image.load(os.path.join(configs.assets.dungeon_dir, entity.sprite))
			ratio = self.get_container().rect.height / 10 / entity_image.get_height()
			entity_image = pygame.transform.scale(entity_image, (entity_image.get_width() * ratio, entity_image.get_height() * ratio))
			image_label = UIImage(Rect((40, y_offset + i * entity_image.get_height()), (entity_image.get_width(), entity_image.get_height())), entity_image, self.ui_manager, container=self.panel)
			
			name_label = UILabel(Rect((90, y_offset + i * entity_image.get_height()), (200, 40)), f'{entity.name}', self.ui_manager, container=self.panel)
			location_label = UILabel(Rect((300, y_offset + i * entity_image.get_height()), (200, 40)), f'{location}', self.ui_manager, container=self.panel)
			cost_label = UILabel(Rect((510, y_offset + i * entity_image.get_height()), (100, 40)), f'Cost: {entity.cost}', self.ui_manager, container=self.panel)
			
			checkbox = Checkbox(Rect((10, y_offset + i * entity_image.get_height() + (entity_image.get_height() / 2)), (20, 20)), self.ui_manager, container=self.panel)
			self.checkboxes.append(checkbox)

	def process_event(self, event):
		super().process_event(event)
		if event.type == pygame_gui.UI_BUTTON_PRESSED:
			self.spending = 0
			for i, checkbox in enumerate(self.checkboxes):
				if checkbox.text == checkbox.ticked:
					self.spending += self.diff_entities[i].cost
			self.make_stress_label(amount=stress_system.stress - self.spending)
			if self.spending > 0:
				self.regen_button.enable()
			else:
				self.regen_button.disable()
			for i, checkbox in enumerate(self.checkboxes):
				if checkbox.text == checkbox.unticked:
					if stress_system.stress < self.spending + self.diff_entities[i].cost:
						checkbox.disable()
					else:
						checkbox.enable()
			if event.ui_element == self.regen_button:
				self.regenerate_entities()

	def regenerate_entities(self):
		max_cost = sum([x.cost for x in self.diff_entities])
		for i, (entity, location) in enumerate(zip(self.diff_entities, self.locations)):
			if self.checkboxes[i].text == self.checkboxes[i].ticked:
				reset_entity(ref_level=self.level_copy, curr_level=self.game_engine.scenario, entity=entity, location=location)
				stress_system.stress -= entity.cost
		
		if self.spending == max_cost:
			msg_system.add_msg('The dungeon has been fully regenerated!')
		else:
			msg_system.add_msg('The dungeon has been partially regenerated...')
		
		self.game_engine.state = GameState.NEXT_WAVE
		self.kill()