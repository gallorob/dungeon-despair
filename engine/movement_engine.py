from typing import List, Optional, Union

from dungeon_despair.domain.corridor import Corridor
from dungeon_despair.domain.encounter import Encounter
from dungeon_despair.domain.level import Level
from dungeon_despair.domain.room import Room
from engine.message_system import msg_system
from engine.stress_system import stress_system


class Destination:
	def __init__(self, to: str, idx: int):
		self.to = to
		self.idx = idx
	
	def __eq__(self, other):
		return self.to == other.to and self.idx == other.idx
	
	def __str__(self):
		return f'{self.to}__{self.idx}'

class MovementEngine:
	def __init__(self):
		self.encounter_idx = -1
		self.current_room: Optional[Union[Corridor, Room]] = None
		self.destinations: List[Destination] = []
	
	@property
	def current_encounter(self) -> Encounter:
		'''Get the current encounter'''
		if isinstance(self.current_room, Room):
			return self.current_room.encounter
		else:
			return self.current_room.encounters[self.encounter_idx]
	
	def get_area(self,
	             level: Level) -> Union[Room, Corridor]:
		if level.current_room in level.rooms.keys():
			return level.rooms[level.current_room]
		elif level.current_room in level.corridors.keys():
			return level.corridors[level.current_room]
		else:
			raise ValueError(f'{level.current_room} not in level!')
		
	
	def compute_destinations(self,
	                         level: Level) -> List[Destination]:
		'''Compute all available destinations for the current encounter'''
		destinations = []
		if isinstance(self.current_room, Room):
			# TODO: Use level.connections instead
			for corridor in level.corridors.values():
				if corridor.room_from == self.current_room.name:
					destinations.append(Destination(corridor.name, 0))
				elif corridor.room_to == self.current_room.name:
					destinations.append(Destination(corridor.name, corridor.length - 1))
		else:
			# TODO: This could definitely be written better...
			if self.encounter_idx == 0:
				destinations.append(Destination(self.current_room.name, 1))
				destinations.append(Destination(self.current_room.room_from, -1))
			elif self.encounter_idx == self.current_room.length - 1:
				destinations.append(Destination(self.current_room.name, self.current_room.length - 2))
				destinations.append(Destination(self.current_room.room_to, -1))
			else:
				destinations.append(Destination(self.current_room.name, self.encounter_idx + 1))
				destinations.append(Destination(self.current_room.name, self.encounter_idx - 1))
		return destinations
	
	def move_to(self,
	            level: Level,
	            dest: Destination):
		'''Move to a new area in the level'''
		if self.current_room is None or (dest.to != self.current_room.name or dest.idx != self.encounter_idx):
			prev_area = self.current_room
			level.current_room = dest.to
			self.encounter_idx = dest.idx
			self.current_room = self.get_area(level)
			self.destinations = self.compute_destinations(level)
			if prev_area is None or self.current_room.name != prev_area.name:
				if isinstance(self.current_room, Room):
					msg_system.add_msg(f'You enter <b>{self.current_room.name}</b>: <i>{self.current_room.description}</i>')
				else:
					msg_system.add_msg(f'You enter the corridor that connects <b>{self.current_room.room_from}</b> to <b>{self.current_room.room_to}</b>')
			stress_system.process_movement()
			
	def reachable(self,
	              level: Level,
	              dest: Destination) -> bool:
		'''Check if a destination is reachable from the current encounter'''
		if dest in self.destinations:
			return True
		else:
			msg_system.add_msg(f'You can\'t reach <b>{dest.to}</b> from <b>{level.current_room}</b>!')
			return False
	
	
