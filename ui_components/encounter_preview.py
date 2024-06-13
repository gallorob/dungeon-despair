import os
from typing import List, Optional, Union

import pygame
from pygame import Rect
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UIImage, UILabel, UIWindow

from configs import configs
from heroes_party import HeroParty
from level import Corridor, Encounter, Room
from utils import rich_entity_description


class EncounterPreview(UIWindow):
	def __init__(self,
	             rect: Rect,
	             ui_manager: IUIManagerInterface):
		super().__init__(rect, ui_manager, window_display_title='Encounter', resizable=False, draggable=False)
		self.padding = self.get_container().rect.width / 10
		
		self.stress_level: Optional[UILabel] = None
		self.background_image: Optional[UIImage] = None
		self.enemies: List[UIImage] = []
		self.heroes: List[UIImage] = []
	
	def display_stress_level(self, stress: int):
		if self.stress_level is None:
			self.stress_level = UILabel(relative_rect=Rect(self.get_container().rect.width / 2 - self.get_container().rect.width / 8, 0,
			                                               self.get_container().rect.width / 4, self.get_container().rect.height / 8),
			                            text=f'Current Stress: {stress}',
			                            container=self.get_container(),
			                            manager=self.ui_manager)
		else:
			self.stress_level.text = f'Current Stress: {stress}'
			self.stress_level.rebuild()
	
	def display_corridor_background(self, corridor: Corridor, idx: int):
		if self.background_image:
			self.background_image.kill()
		self.background_image = None
		area_image = pygame.image.load(os.path.join(configs.assets, 'dungeon_assets', corridor.sprite))
		
		scale_factor = self.get_container().rect.height / area_image.get_height()
		new_width, new_height = int(scale_factor * area_image.get_width()), int(scale_factor * area_image.get_height())
		encounter_w = scale_factor * (area_image.get_width() / (corridor.length + 2))
		area_image = pygame.transform.scale(area_image, (new_width, new_height))
		
		diff_w = self.get_container().rect.width - encounter_w
		area_image = area_image.subsurface(Rect(((idx + 1) * encounter_w) - (diff_w / 2), 0,
		                                        encounter_w + diff_w, area_image.get_height()))
		
		corridor_rect = Rect(0, 0,
		                     self.get_container().rect.width,
		                     self.get_container().rect.height)
		
		self.background_image = UIImage(relative_rect=corridor_rect,
		                                image_surface=area_image,
		                                manager=self.ui_manager,
		                                container=self.get_container(),
		                                starting_height=self.starting_height
		                                )
	
	def display_room_background(self, room: Room):
		if self.background_image:
			self.background_image.kill()
		self.background_image = None
		area_image = pygame.image.load(os.path.join(configs.assets, 'dungeon_assets', room.sprite))
		scale_factor = min(self.get_container().rect.width / area_image.get_width(),
		                   self.get_container().rect.height / area_image.get_height())
		area_image = pygame.transform.scale(area_image, (int(scale_factor * area_image.get_width()),
		                                                 int(scale_factor * area_image.get_height())))
		dw, dh = ((self.get_container().rect.width - area_image.get_width()) / 2,
		          (self.get_container().rect.height - area_image.get_height()) / 2)
		room_rect = Rect(dw, dh,
		                 self.get_container().rect.width - dw,
		                 self.get_container().rect.height - dh)
		
		self.background_image = UIImage(relative_rect=room_rect,
		                                image_surface=area_image,
		                                manager=self.ui_manager,
		                                container=self.get_container(),
		                                starting_height=self.starting_height
		                                )
		
	def display_encounter(self, encounter: Encounter):
		for enemy in self.enemies:
			enemy.kill()
		self.enemies = []

		# show enemies
		x_offset = self.background_image.rect.width / 2
		y_offset = self.background_image.rect.height / 2
		enemies_width = (x_offset - self.padding) / configs.max_enemies_per_encounter
		cum_padding = self.padding
		for i, enemy in enumerate(encounter.entities.get('enemy', [])):
			enemy_image = pygame.image.load(os.path.join(configs.assets, 'dungeon_assets', enemy.sprite))
			r = enemies_width / enemy_image.get_width()
			enemy_sprite = UIImage(
				relative_rect=Rect(
					x_offset + cum_padding,
					y_offset - r * enemy_image.get_height(),
					enemies_width,
					r * enemy_image.get_height()
				),
				image_surface=enemy_image, manager=self.ui_manager, container=self.get_container(),
				parent_element=self, anchors={
					'centery': 'centery'
				}, starting_height=self.starting_height + 1
			)
			enemy_sprite.set_tooltip(rich_entity_description(enemy))
			cum_padding += enemies_width
			self.enemies.append(enemy_sprite)
	
	def display_heroes(self, heroes: HeroParty):
		for hero in self.heroes:
			hero.kill()
		self.heroes = []
		
		x_offset = self.background_image.rect.width / 2
		y_offset = self.background_image.rect.height / 2
		min_width = (x_offset - self.padding) / 4
		cum_padding = self.padding
		for i, hero in enumerate(heroes.party):
			hero_image = pygame.image.load(hero.sprite)
			r = min_width / hero_image.get_width()
			hero_sprite = UIImage(
				relative_rect=Rect(
					x_offset - cum_padding,
					y_offset - r * hero_image.get_height(),
					min_width,
					r * hero_image.get_height()
				),
				image_surface=hero_image, manager=self.ui_manager, container=self.get_container(),
				parent_element=self, anchors={
					'centery': 'centery'
				}, starting_height=self.starting_height + 1
			)
			hero_sprite.set_tooltip(rich_entity_description(hero))
			cum_padding += min_width
			self.heroes.append(hero_sprite)
			
	def update(self, time_delta: float):
		super().update(time_delta)
