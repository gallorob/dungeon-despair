from typing import List, Optional, Tuple

from level import Level, Room
from utils import get_current_room


class MovementEngine:
	def __init__(self):
		self.encounter_idx = -1
	
	def move_to_room(self,
	                 level: Level,
	                 dest_room_name: str,
	                 encounter_idx: int = -1) -> List[Optional[str]]:
		level.current_room = dest_room_name
		self.encounter_idx = encounter_idx
		
		if dest_room_name != level.current_room:
			area = get_current_room(level=level)
			if isinstance(area, Room):
				msg = f'You enter <b>{area.name}</b>: <i>{area.description}</i>'
			else:
				msg = f'You enter the corridor that connects <b>{area.room_from}</b> to <b>{area.room_to}</b>'
			return [msg]
		return []
	
	def reachable(self,
	              level: Level,
	              room_name: str,
	              idx: int) -> bool:
		curr_room = get_current_room(level=level)
		# check if current room is a corridor or a room
		if isinstance(curr_room, Room):
			# check if we are clicking on a connected corridor
			names = room_name.split('-')
			if len(names) == 2:
				corridor = level.get_corridor(*names, ordered=False)
				if corridor is not None:
					# make sure the corridor connects this room
					if corridor.room_to == curr_room.name or corridor.room_from == curr_room.name:
						# we can go to a corridor only if idx = 0 or corridor.length - 2
						return idx == 0 or idx == corridor.length - 1
		else:
			# check if we are clicking on the same corridor
			if room_name == curr_room.name:
				# we can move only by 1 encounter
				return idx in [x + self.encounter_idx for x in [-1, 1]]
			else:
				# check we are moving to a connected room
				if room_name == curr_room.room_from or room_name == curr_room.room_to:
					# make sure we are on the edge of the corridor
					return self.encounter_idx == 0 or self.encounter_idx == curr_room.length - 1
		return False
	
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
			for corridor in level.corridors:
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
