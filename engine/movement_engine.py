from typing import List, Optional, Tuple

from dungeon_despair.domain.level import Level
from dungeon_despair.domain.room import Room
from utils import get_current_room
from configs import configs


class MovementEngine:
	def __init__(self):
		self.encounter_idx = -1
	
	def move_to_room(self,
	                 level: Level,
	                 dest_room_name: str,
	                 encounter_idx: int = -1) -> Tuple[List[str], int]:
		if dest_room_name != level.current_room or self.encounter_idx != encounter_idx:
			prev_room = level.current_room
			level.current_room = dest_room_name
			self.encounter_idx = encounter_idx
			area = get_current_room(level=level)
			if prev_room != area.name:
				if isinstance(area, Room):
					msg = [f'You enter <b>{area.name}</b>: <i>{area.description}</i>']
				else:
					msg = [f'You enter the corridor that connects <b>{area.room_from}</b> to <b>{area.room_to}</b>']
			else: msg = []
			return msg, configs.game.stress.movement
		return [], 0
	
	def reachable(self,
	              level: Level,
	              room_name: str,
	              idx: int) -> Tuple[bool, str]:
		curr_room = get_current_room(level=level)
		is_reachable = False
		if isinstance(curr_room, Room):
			if room_name in level.corridors.keys():
				corridor = level.corridors[room_name]
				if corridor.room_from == curr_room.name:
					is_reachable = idx == 0
				elif corridor.room_to == curr_room.name:
					is_reachable = idx == corridor.length - 1
		else:
			if room_name == curr_room.name:
				is_reachable = idx in [x + self.encounter_idx for x in [-1, 1]]
			else:
				if room_name == curr_room.room_from:
					is_reachable = self.encounter_idx == 0
				elif room_name == curr_room.room_to:
					is_reachable = self.encounter_idx == curr_room.length - 1
		return is_reachable, f'You can\'t reach <b>{room_name}</b> from <b>{level.current_room}</b>!'
	
	def same_area(self,
	              level: Level,
	              room_name: str,
	              encounter_idx: int = -1) -> bool:
		return room_name == level.current_room and encounter_idx == self.encounter_idx
	
	def available_destinations(self,
	                           level: Level) -> List[Tuple[str, int]]:
		destinations = []
		curr_room = get_current_room(level=level)
		if isinstance(curr_room, Room):
			for corridor in level.corridors.values():
				if corridor.room_from == curr_room.name:
					destinations.append((corridor.name, 0))
				elif corridor.room_to == curr_room.name:
					destinations.append((corridor.name, corridor.length - 1))
		else:
			if self.encounter_idx == 0:
				destinations.append((curr_room.name, 1))
				destinations.append((curr_room.room_from, -1))
			elif self.encounter_idx == curr_room.length - 1:
				destinations.append((curr_room.name, curr_room.length - 2))
				destinations.append((curr_room.room_to, -1))
			else:
				destinations.append((curr_room.name, self.encounter_idx + 1))
				destinations.append((curr_room.name, self.encounter_idx - 1))
		return destinations
