import os
from typing import List, Optional

import pygame
from dungeon_despair.domain.corridor import Corridor
from dungeon_despair.domain.encounter import Encounter
from dungeon_despair.domain.room import Room
from pygame import Rect
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UIImage, UILabel, UIWindow

from configs import configs
from heroes_party import HeroParty
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
		self.traps: List[UIImage] = []
		self.treasures: List[UIImage] = []
		self.heroes: List[UIImage] = []
		self.attacking: Optional[UIImage] = None
		self.targeted: List[UIImage] = []
	
	def display_stress_level(self, stress: int):
		if self.stress_level is None:
			self.stress_level = UILabel(
				relative_rect=Rect(self.get_container().rect.width / 2 - self.get_container().rect.width / 8, 0,
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
		
		before_image = pygame.image.load(os.path.join(configs.assets, 'dungeon_assets', corridor.sprites[idx]))
		area_image = pygame.image.load(os.path.join(configs.assets, 'dungeon_assets', corridor.sprites[idx + 1]))
		after_image = pygame.image.load(os.path.join(configs.assets, 'dungeon_assets', corridor.sprites[idx + 2]))
		
		scale_factor = self.get_container().rect.height / area_image.get_height()
		new_width, new_height = int(scale_factor * area_image.get_width()), int(scale_factor * area_image.get_height())
		encounter_w = scale_factor * (area_image.get_width() / (corridor.length + 2))
		
		before_image = pygame.transform.scale(before_image, (new_width, new_height))
		area_image = pygame.transform.scale(area_image, (new_width, new_height))
		after_image = pygame.transform.scale(after_image, (new_width, new_height))
		
		diff_w = self.get_container().rect.width - encounter_w
		before_image = before_image.subsurface(
			Rect(diff_w / 2, 0, before_image.get_width() - (diff_w / 2), before_image.get_height()))
		after_image = after_image.subsurface(Rect(0, 0, diff_w / 2, after_image.get_height()))
		
		combined_surface = pygame.Surface((before_image.get_width() + area_image.get_width() + after_image.get_width(),
		                                   area_image.get_height()))
		combined_surface.blit(before_image, (0, 0))
		combined_surface.blit(area_image, (before_image.get_width(), 0))
		combined_surface.blit(after_image, (before_image.get_width() + area_image.get_width(), 0))
		
		corridor_rect = Rect(0, 0,
		                     self.get_container().rect.width,
		                     self.get_container().rect.height)
		
		self.background_image = UIImage(relative_rect=corridor_rect,
		                                image_surface=combined_surface,
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
		
		def __add_and_show_entities(max_n: int,
		                            entity_type: str,
		                            height_diff: int,
		                            additional_x_offset: float) -> List[UIImage]:
			sprites = []
			x_offset = self.background_image.rect.width / 2
			y_offset = self.background_image.rect.height / 2
			entity_width = (x_offset - self.padding) / max_n
			cum_padding = self.padding
			for i, entity in enumerate(encounter.entities[entity_type]):
				entity_image = pygame.image.load(os.path.join(configs.assets, 'dungeon_assets', entity.sprite))
				r = entity_width / entity_image.get_width()
				entity_sprite = UIImage(
					relative_rect=Rect(
						additional_x_offset + x_offset + cum_padding,
						y_offset - r * entity_image.get_height(),
						entity_width,
						r * entity_image.get_height()
					),
					image_surface=entity_image, manager=self.ui_manager, container=self.get_container(),
					parent_element=self, anchors={
						'centery': 'centery'
					}, starting_height=self.starting_height + height_diff
				)
				entity_sprite.set_tooltip(rich_entity_description(entity))
				cum_padding += entity_width
				sprites.append(entity_sprite)
			return sprites
		
		for enemy in self.enemies:
			enemy.kill()
		for trap in self.traps:
			trap.kill()
		for treasure in self.treasures:
			treasure.kill()
		self.enemies = []
		self.traps = []
		self.treasures = []
		
		# show enemies
		self.enemies = __add_and_show_entities(max_n=configs.max_enemies_per_encounter,
		                                       entity_type='enemy',
		                                       height_diff=1,
		                                       additional_x_offset=0)
		# show traps
		self.traps = __add_and_show_entities(max_n=4,#configs.max_traps_per_encounter,
		                                     entity_type='trap',
		                                     height_diff=0,
		                                     additional_x_offset=-self.padding)
		# show treasures
		self.treasures = __add_and_show_entities(max_n=4,#configs.max_treasures_per_encounter,
		                                         entity_type='treasure',
		                                         height_diff=0,
		                                         additional_x_offset=-self.padding)
	
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
	
	def update_attacking(self, idx: int):
		if self.attacking is not None:
			self.attacking.kill()
		
		ref_sprite = [*self.heroes, *self.enemies][idx]
		self.attacking = UIImage(
			relative_rect=Rect(
				ref_sprite.relative_rect.x + ref_sprite.relative_rect.width / 2 - self.padding / 4,
				0,
				self.padding / 2, self.padding / 2),
			image_surface=pygame.image.load('assets/attacking_icon.png'),
			manager=self.ui_manager, container=self.get_container(),
			parent_element=self, anchors={
				'centery': 'centery'
			}, starting_height=self.starting_height + 1
		)
	
	def update_targeted(self, idxs: List[int]):
		if self.targeted:
			for target in self.targeted:
				target.kill()
		
		for idx in idxs:
			ref_sprite = [*self.heroes, *self.enemies][idx]
			self.targeted.append(UIImage(
				relative_rect=Rect(
					ref_sprite.relative_rect.x + ref_sprite.relative_rect.width / 2 - self.padding / 4,
					0,
					self.padding / 2, self.padding / 2),
				image_surface=pygame.image.load('assets/targeting_icon.png'),
				manager=self.ui_manager, container=self.get_container(),
				parent_element=self, anchors={
					'centery': 'centery'
				}, starting_height=self.starting_height + 1
			))
	
	def update(self, time_delta: float):
		super().update(time_delta)
