import os
from typing import List, Optional, Union

import pygame
from pygame import Rect
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UIImage, UILabel, UIWindow

from configs import configs
from dungeon_despair.domain.corridor import Corridor
from dungeon_despair.domain.encounter import Encounter
from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.entities.hero import Hero
from dungeon_despair.domain.room import Room
from dungeon_despair.domain.configs import config as ddd_config
from dungeon_despair.domain.utils import ModifierType, get_enum_by_value
from heroes_party import HeroParty
from utils import rich_entity_description


class EncounterPreview(UIWindow):
	def __init__(self,
	             rect: Rect,
	             ui_manager: IUIManagerInterface):
		super().__init__(rect, ui_manager, window_display_title='Encounter', resizable=False, draggable=False)
		self.padding = self.get_container().rect.width / 10
		
		self.stats_level: Optional[UILabel] = None
		self.background_image: Optional[UIImage] = None
		self.enemies: List[UIImage] = []
		self.traps: List[UIImage] = []
		self.treasures: List[UIImage] = []
		self.heroes: List[UIImage] = []
		self.attacking: Optional[UIImage] = None
		self.targeted: List[UIImage] = []
		self.moving_to: UIImage = None
		self.modifiers: List[UIImage] = []
	
	def display_stats_level(self, stress: int, wave: int):
		if self.stats_level is None:
			self.stats_level = UILabel(
				relative_rect=Rect(self.get_container().rect.width / 2 - self.get_container().rect.width / 8, 0,
				                   self.get_container().rect.width / 4, self.get_container().rect.height / 8),
				text=f'Current Stress: {stress} | Wave #{wave + 1}',
				container=self.get_container(),
				manager=self.ui_manager)
		else:
			self.stats_level.text = f'Current Stress: {stress} | Wave #{wave + 1}'
			self.stats_level.rebuild()
	
	def display_corridor_background(self, corridor: Corridor, idx: int):
		if self.background_image:
			self.background_image.kill()
		if self.stats_level:
			self.stats_level.kill()
		self.background_image = None
		self.stats_level = None
		
		before_image = pygame.image.load(os.path.join(configs.assets.dungeon_dir, corridor.sprites[idx]))
		area_image = pygame.image.load(os.path.join(configs.assets.dungeon_dir, corridor.sprites[idx + 1]))
		after_image = pygame.image.load(os.path.join(configs.assets.dungeon_dir, corridor.sprites[idx + 2]))
		
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
		if self.stats_level:
			self.stats_level.kill()
		self.background_image = None
		self.stats_level = None
		area_image = pygame.image.load(os.path.join(configs.assets.dungeon_dir, room.sprite))
		scale_factor = min(self.get_container().rect.width / area_image.get_width(),
		                   self.get_container().rect.height / area_image.get_height())
		area_image = pygame.transform.scale(area_image, (int(scale_factor * area_image.get_width()),
		                                                 int(scale_factor * area_image.get_height())))
		room_rect = Rect(0, 0,
		                 self.get_container().rect.width,
		                 self.get_container().rect.height)
		
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
				entity_image = pygame.image.load(os.path.join(configs.assets.dungeon_dir, entity.sprite))
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
		self.enemies = __add_and_show_entities(max_n=ddd_config.max_enemies_per_encounter,
		                                       entity_type='enemy',
		                                       height_diff=1,
		                                       additional_x_offset=0)
		# show traps
		self.traps = __add_and_show_entities(max_n=4,  # ddd_config.max_traps_per_encounter,
		                                     entity_type='trap',
		                                     height_diff=1,
		                                     additional_x_offset=-self.padding)
		# show treasures
		self.treasures = __add_and_show_entities(max_n=4,  # ddd_config.max_treasures_per_encounter,
		                                         entity_type='treasure',
		                                         height_diff=1,
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
			hero_image = pygame.image.load(os.path.join(configs.assets.dungeon_dir, hero.sprite))
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
		y_offset = self.background_image.rect.height / 2
		self.attacking = UIImage(
			relative_rect=Rect(
				ref_sprite.relative_rect.x + ref_sprite.relative_rect.width / 2 - self.padding / 4,
				y_offset - (ref_sprite.relative_rect.height / 2) / 2 - self.padding / 4,
				self.padding / 2,
				self.padding / 2),
			image_surface=pygame.image.load(configs.assets.icons.combat.attacking),
			manager=self.ui_manager, container=self.get_container(),
			parent_element=self,
			starting_height=self.starting_height + 1
		)
	
	def update_targeted(self, idxs: List[int]):
		if self.targeted:
			for target in self.targeted:
				target.kill()
		
		for idx in idxs:
			ref_sprite = [*self.heroes, *self.enemies][idx]
			# not sure why the +1, but it works this way :/
			attacking_x = int(self.attacking.rect.x - ref_sprite.relative_rect.width / 2 + self.padding / 4) + 1
			y_offset = (self.background_image.rect.height / 2) - (ref_sprite.relative_rect.height / 2) / 2 - self.padding / 4
			self.targeted.append(UIImage(
				relative_rect=Rect(
					ref_sprite.relative_rect.x + ref_sprite.relative_rect.width / 2 - self.padding / 4,
					y_offset if (attacking_x != ref_sprite.rect.x) else y_offset - self.padding / 2,
					self.padding / 2, self.padding / 2),
				image_surface=pygame.image.load(configs.assets.icons.combat.targeted),
				manager=self.ui_manager, container=self.get_container(),
				parent_element=self,
				starting_height=self.starting_height + 1
			))
	
	def update(self, time_delta: float):
		super().update(time_delta)
	
	def check_colliding_entity(self, pos):
		for i, sprite in enumerate([*self.heroes, *self.enemies]):
			if sprite.rect.collidepoint(pos):
				return i
		return None
	
	def update_moving_to(self, sprite_idx, attacker: Union[Hero, Enemy]):
		if self.moving_to:
			self.moving_to.kill()
		
		if (sprite_idx < len(self.heroes) and isinstance(attacker, Hero)) or \
		   (sprite_idx >= len(self.heroes) and isinstance(attacker, Enemy)):
			ref_sprite = [*self.heroes, *self.enemies][sprite_idx]
			# not sure why the +1, but it works this way :/
			attacking_x = int(self.attacking.rect.x - ref_sprite.relative_rect.width / 2 + self.padding / 4) + 1
			y_offset = (self.background_image.rect.height / 2) - (ref_sprite.relative_rect.height / 2) / 2 - self.padding / 4
			self.moving_to = UIImage(
				relative_rect=Rect(
					ref_sprite.relative_rect.x + ref_sprite.relative_rect.width / 2 - self.padding / 4,
					y_offset if (attacking_x != ref_sprite.rect.x) else y_offset - self.padding / 2,
					self.padding / 2, self.padding / 2),
				image_surface=pygame.image.load(configs.assets.icons.combat.moving),
				manager=self.ui_manager, container=self.get_container(),
				parent_element=self,
				starting_height=self.starting_height + 1
			)
	
	def update_modifiers(self, heroes: HeroParty, enemies: List[Enemy]):
		def get_icon(modifier_type: ModifierType):
			if modifier_type == ModifierType.BLEED:
				return configs.assets.icons.modifiers.bleed
			elif modifier_type == ModifierType.HEAL:
				return configs.assets.icons.modifiers.heal
			elif modifier_type == ModifierType.SCARE:
				return configs.assets.icons.modifiers.scare
			elif modifier_type == ModifierType.STUN:
				return configs.assets.icons.modifiers.stun
			else:
				raise ValueError(f'Unknown modifier type: {modifier_type.value}')
		
		for modifier in self.modifiers:
			modifier.kill()
		
		for i, hero in enumerate(heroes.party):
			for j, modifier in enumerate(hero.modifiers):
				ref_sprite = self.heroes[i]
				y_offset = (self.background_image.rect.height / 2) + ref_sprite.relative_rect.height + self.padding / 5
				modifier_icon = UIImage(
					relative_rect=Rect(
						ref_sprite.relative_rect.x + ref_sprite.relative_rect.width / 2 - self.padding / 5 + (j * self.padding / 5),
						y_offset,
						self.padding / 5, self.padding / 5
					),
					image_surface=pygame.image.load(get_icon(get_enum_by_value(ModifierType, modifier.type))),
					manager=self.ui_manager, container=self.get_container(),
					parent_element=self,
					starting_height=self.starting_height + 1
				)
				modifier_icon.set_tooltip(str(modifier))
				self.modifiers.append(modifier_icon)
		
		for i, enemy in enumerate(enemies):
			for modifier in enemy.modifiers:
				ref_sprite = self.enemies[i]
				y_offset = (self.background_image.rect.height / 2) - (
							ref_sprite.relative_rect.height / 2) / 2 - self.padding / 8
				modifier_icon = UIImage(
					relative_rect=Rect(
						ref_sprite.relative_rect.x + ref_sprite.relative_rect.width / 2 - self.padding / 8,
						y_offset,
						self.padding / 8, self.padding / 8
					),
					image_surface=pygame.image.load(get_icon(get_enum_by_value(ModifierType, modifier.type))),
					manager=self.ui_manager, container=self.get_container(),
					parent_element=self,
					starting_height=self.starting_height + 1
				)
				modifier_icon.set_tooltip(str(modifier))
				self.modifiers.append(modifier_icon)