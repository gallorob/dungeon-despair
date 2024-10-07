from typing import Dict, List, Union

import pygame
import pygame_gui
from pygame import Rect
from pygame_gui.core import ObjectID
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UIButton, UIWindow

from configs import configs
from dungeon_despair.domain.corridor import Corridor
from dungeon_despair.domain.encounter import Encounter
from dungeon_despair.domain.level import Level
from dungeon_despair.domain.room import Room
from dungeon_despair.domain.utils import Direction
from utils import basic_room_description


class LevelPreview(UIWindow):
	def __init__(self,
	             rect: Rect,
	             ui_manager: IUIManagerInterface):
		super().__init__(rect, ui_manager, window_display_title='Level', resizable=False, draggable=False)
		
		self.allow_movement = True
		
		self.map: List[UIButton] = []
		self._map_areas: Dict[UIButton, Union[Corridor, Room]] = {}
		self._map_idxs: Dict[UIButton, int] = {}
	
	def get_encounter_text(self, encounter: Encounter):
		enemies_text = f'x{len(encounter.entities["enemy"])}' if len(encounter.entities["enemy"]) > 0 else '0'
		treasure_text = ', $' if len(encounter.entities["treasure"]) > 1 else ''
		return f'{enemies_text}{treasure_text}'
	
	def update_button_text(self, encounter: Encounter, roomcorridor_name: str):
		for button, room in self._map_areas.items():
			if room.name == roomcorridor_name:
				button.text = self.get_encounter_text(encounter)
				button.rebuild()
				break
	
	def create_minimap(self, game_data: Level):
		if len(self.map) == 0:
			room_button_size = (self.get_container().get_relative_rect().height * configs.minimap_room_scale,
			                    self.get_container().get_relative_rect().height * configs.minimap_room_scale)
			corridor_button_size = (self.get_container().get_relative_rect().height * configs.minimap_corridor_scale,
			                        self.get_container().get_relative_rect().height * configs.minimap_corridor_scale)
			corridor_room_difference = ((room_button_size[0] - corridor_button_size[0]) / 2,
			                            (room_button_size[1] - corridor_button_size[1]) / 2)
			room_positions = {}
			
			# Initial position
			start_x, start_y = (self.get_container().get_relative_rect().width // 2 - room_button_size[0] // 2,
			                    self.get_container().get_relative_rect().height // 2 - room_button_size[1] // 2)
			room_positions[game_data.current_room] = (start_x, start_y)
			
			offsets_directions = {
				Direction.WEST:  (-1, 0),
				Direction.EAST: (1, 0),
				Direction.NORTH:    (0, -1),
				Direction.SOUTH:  (0, 1)
			}
			correcting_directions = {
				Direction.WEST:  (0, 1),
				Direction.EAST: (0, 1),
				Direction.NORTH:    (1, 0),
				Direction.SOUTH:  (1, 0)
			}
			
			# Queue to process rooms and their adjacent rooms
			queue = [game_data.current_room]
			processed_rooms = set()
			
			while queue:
				current_room = queue.pop(0)
				current_pos = room_positions[current_room]
				
				actual_room = game_data.rooms[current_room]
				
				room_button = UIButton(
					relative_rect=pygame.Rect(current_pos, room_button_size),
					text=self.get_encounter_text(actual_room.encounter),
					tool_tip_text=basic_room_description(actual_room),
					container=self.get_container(),
					manager=self.ui_manager,
				)
				
				# Set the first room as current room
				if current_room == game_data.current_room:
					room_button.change_object_id(ObjectID(class_id='button', object_id='#current_room_button'))
				
				self.map.append(room_button)
				self._map_areas[room_button] = game_data.rooms[current_room]
				
				for direction, adjacent_room in game_data.connections[current_room].items():
					dx, dy = (room_button_size[0] - (room_button_size[0] // 2) if direction == Direction.EAST else 0,
					          room_button_size[1] - (room_button_size[1] // 2) if direction == Direction.SOUTH else 0)
					if adjacent_room and adjacent_room not in room_positions:
						# Draw corridor
						for corridor in game_data.corridors.values():
							room_from, room_to = corridor.room_from, corridor.room_to
							if (room_from == current_room or room_from == adjacent_room) and (
								room_to == current_room or room_to == adjacent_room):
								length = corridor.length
								for i in range(length):
									dx += offsets_directions[direction][0] * corridor_button_size[0]
									dy += offsets_directions[direction][1] * corridor_button_size[1]
									corridor_button = pygame_gui.elements.UIButton(
										relative_rect=pygame.Rect((current_pos[0] + dx + correcting_directions[direction][0] * corridor_room_difference[0],
										                           current_pos[1] + dy + correcting_directions[direction][1] * corridor_room_difference[1]),
										                          corridor_button_size),
										text='?',
										tool_tip_text=f"{room_from} - {room_to} ({i})",
										container=self.get_container(),
										manager=self.ui_manager,
									)
									self.map.append(corridor_button)
									self._map_areas[corridor_button] = corridor
									self._map_idxs[corridor_button] = i
								continue
						# Calculate position of the adjacent room
						ddx, ddy = (-room_button_size[0] / 2 if direction == Direction.EAST else 0,
						            -room_button_size[1] / 2 if direction == Direction.SOUTH else 0)
						adjacent_pos = (current_pos[0] + dx + offsets_directions[direction][0] * room_button_size[0] + ddx,
						                current_pos[1] + dy + offsets_directions[direction][1] * room_button_size[1] + ddy)
						room_positions[adjacent_room] = adjacent_pos
						queue.append(adjacent_room)
				
				processed_rooms.add(current_room)
	
	def update(self, time_delta: float):
		super().update(time_delta)
	
	def check_clicked_encounter(self, pos):
		if self.allow_movement:
			for encounter in self.map:
				if encounter.rect.collidepoint(pos):
					return self._map_areas[encounter].name, self._map_idxs.get(encounter, -1)
		return None, -1
	
	def update_minimap(self, clicked_room_name, encounter_idx):
		# Remove custom theming
		for encounter in self.map:
			encounter.change_object_id(None)
		# Shift the minimap
		dx, dy = 0, 0
		for encounter in self.map:
			target_encounter = self._map_areas[encounter]
			if target_encounter.name == clicked_room_name and encounter_idx == self._map_idxs.get(encounter, -1):
				encounter.change_object_id(ObjectID(class_id='button', object_id='#current_room_button'))
				dx, dy = encounter.get_relative_rect().x, encounter.get_relative_rect().y
				break
		offset_x, offset_y = self.get_container().get_relative_rect().width // 2 - dx, self.get_container().get_relative_rect().height // 2 - dy
		for encounter in self.map:
			encounter.rect.move_ip(offset_x, offset_y)
			encounter.set_position(encounter.rect)
	
	def set_movement(self,
	                 allowed: bool) -> None:
		self.allow_movement = allowed
		for encounter in self.map:
			if self.allow_movement:
				encounter.enable()
			else:
				encounter.disable()
