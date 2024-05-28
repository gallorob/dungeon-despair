from typing import List, Optional

import pygame
from pygame import Rect
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UIImage, UILabel, UIWindow
from PIL import Image

from configs import configs
from heroes_party import Hero, HeroParty
from level import Encounter, Enemy, Room
from utils import img_to_pygame_sprite, rich_entity_description


def scale_and_get_offsets(image, rect):
	image_w, image_h = image.get_width(), image.get_height()
	scale_w = rect.width / image_w
	scale_h = rect.height / image_h
	scale_factor = min(scale_w, scale_h)
	new_width, new_height = int(scale_factor * image_w), int(scale_factor * image_h)
	scaled_image = pygame.transform.scale(image, (new_width, new_height))
	dw, dh = (rect.width - new_width) / 2, (rect.height - new_height) / 2
	
	return scaled_image, dw, dh


class EncounterPreview(UIWindow):
	def __init__(self,
	             rect: Rect,
	             ui_manager: IUIManagerInterface):
		super().__init__(rect, ui_manager, window_display_title='Encounter', resizable=False, draggable=False)
		self.padding = self.get_container().rect.width / 10
		
		self.stress_level: Optional[UILabel] = None
		self.room_image: Optional[UIImage] = None
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
	
	def display_room(self, room: Room):
		# if self.room_image:
		# 	self.room_image.kill()
		# self.room_image = None
		room_image = pygame.image.load(room.sprite)
		room_image, dw, dh = scale_and_get_offsets(room_image, self.get_container().rect)
		
		if self.room_image is None:
			room_rect = Rect(dw, dh,
			                 self.get_container().rect.width - 2 * dw,
			                 self.get_container().rect.height - 2 * dh)
			
			self.room_image = UIImage(relative_rect=room_rect,
			                          image_surface=room_image,
			                          manager=self.ui_manager,
			                          container=self.get_container(),
			                          anchors={'left':   'left',
			                                   'right':  'right',
			                                   'top':    'top',
			                                   'bottom': 'bottom'
			                                   },
			                          starting_height=self.starting_height
			                          )
		
		else:
			self.room_image.set_image(room_image)
	
	def display_encounter(self, encounter: Encounter):
		for enemy in self.enemies:
			enemy.kill()
		self.enemies = []

		# show enemies
		x_offset = self.room_image.rect.width / 2
		y_offset = self.room_image.rect.height / 2
		enemies_width = (x_offset - self.padding) / configs.max_enemies_per_encounter
		cum_padding = self.padding
		for i, enemy in enumerate(encounter.entities.get('enemy', [])):
			enemy_image = pygame.image.load(enemy.sprite)
			# content_rect = enemy_image.get_bounding_rect()
			# enemy_image = enemy_image.subsurface(content_rect)
			r = enemies_width / enemy_image.get_width()
			enemy_sprite = UIImage(
				relative_rect=Rect(
					x_offset + cum_padding,  # x_offset + self.padding + i * enemies_width,
					y_offset - r * enemy_image.get_height(),
					enemies_width,  # r * enemy_image.get_width(),
					r * enemy_image.get_height()
				),
				image_surface=enemy_image, manager=self.ui_manager, container=self.get_container(),
				parent_element=self, anchors={
					'centery': 'centery'
				}, starting_height=self.starting_height + 1
			)
			enemy_sprite.set_tooltip(rich_entity_description(enemy))
			cum_padding += enemies_width  # r * enemy_image.get_width()
			self.enemies.append(enemy_sprite)
	
	def display_heroes(self, heroes: HeroParty):
		for hero in self.heroes:
			hero.kill()
		self.heroes = []
		
		x_offset = self.room_image.rect.width / 2
		y_offset = self.room_image.rect.height / 2
		min_width = (x_offset - self.padding) / 4
		cum_padding = self.padding
		for i, hero in enumerate(heroes.party):
			# print(hero.name, cum_padding, x_offset - cum_padding)
			hero_image = pygame.image.load(hero.sprite)
			# content_rect = hero_image.get_bounding_rect()
			# hero_image = hero_image.subsurface(content_rect)
			r = min_width / hero_image.get_width()
			hero_sprite = UIImage(
				relative_rect=Rect(
					x_offset - cum_padding,#self.padding + i * min_width,
					y_offset - r * hero_image.get_height(),
					min_width,#r * hero_image.get_width(),
					r * hero_image.get_height()
				),
				image_surface=hero_image, manager=self.ui_manager, container=self.get_container(),
				parent_element=self, anchors={
					'centery': 'centery'
				}, starting_height=self.starting_height + 1
			)
			hero_sprite.set_tooltip(rich_entity_description(hero))
			cum_padding += min_width#r * hero_image.get_width()
			self.heroes.append(hero_sprite)
			
	def update(self, time_delta: float):
		super().update(time_delta)
