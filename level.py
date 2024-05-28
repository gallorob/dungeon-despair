import pickle
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field

from configs import configs

DIRECTIONS = ['LEFT', 'UP', 'RIGHT', 'DOWN']
OPPOSITE_DIRECTIONS = {
	'UP':    'DOWN',
	'DOWN':  'UP',
	'LEFT':  'RIGHT',
	'RIGHT': 'LEFT'
}


class Entity(BaseModel):
	class Config:
		arbitrary_types_allowed = True
	
	name: str = Field(..., description="The name of the entity.", required=True)
	description: str = Field(..., description="The description of the entity.", required=True)
	sprite: str = Field(default=None, description='The sprite for the entity.', required=False)
	
	def __str__(self):
		return f'{self.name}: {self.description}'


class Attack(BaseModel):
	class Config:
		arbitrary_types_allowed = True
	
	name: str = Field(..., description="The name of the attack.", required=True)
	description: str = Field(..., description='The description of the attack', required=True)
	starting_positions: str = Field(..., description='The starting positions of the attack', required=True)
	target_positions: str = Field(..., description='The positions targeted by the attack', required=True)
	base_dmg: int = Field(..., description='The base attack damage', required=True)
	active: bool = Field(default=True, description='Whether the attack can be executed', required=False)


class Enemy(Entity):
	species: str = Field(..., description="The enemy species.", required=True)
	hp: int = Field(..., description="The enemy HP.", required=True)
	dodge: float = Field(..., description="The enemy dodge stat.", required=True)
	prot: float = Field(..., description="The enemy prot stat.", required=True)
	spd: int = Field(..., description="The enemy spd stat.", required=True)
	attacks: List[Attack] = Field([], description='The enemy attacks', required=True)
	
	def __str__(self):
		return f'Enemy {super().__str__()} Species={self.species} HP={self.hp} DODGE={self.dodge} PROT={self.prot} SPD={self.spd}'


class Trap(Entity):
	effect: str = Field(..., description="The effect of the trap.", required=True)
	
	def __str__(self):
		return f'Trap {super().__str__()} Effect={self.effect}'


class Treasure(Entity):
	loot: str = Field(..., description="The loot in the treasure.", required=True)
	
	def __str__(self):
		return f'Treasure {super().__str__()} Loot={self.loot}'


class EntityClass(Enum):
	ENEMY = Enemy
	TRAP = Trap
	TREASURE = Treasure


entityclass_to_str = {
	Enemy:    'enemy',
	Trap:     'trap',
	Treasure: 'treasure'
}

entityclass_thresolds = {
	Enemy:    configs.max_enemies_per_encounter,
	Trap:     configs.max_traps_per_encounter,
	Treasure: configs.max_treasures_per_encounter
}


class Encounter(BaseModel):
	class Config:
		arbitrary_types_allowed = True
	
	entities: Dict[str, List[Union[Enemy, Trap, Treasure]]] = Field(
		default={k: [] for k in entityclass_to_str.values()},
		description="The entities for this encounter.", required=True)
	
	def __str__(self):
		s = ''
		for k in self.entities.keys():
			all_type_str = [str(x) for x in self.entities[k]]
			unique_with_count = [f'{all_type_str.count(x)}x {x}' for x in all_type_str]
			s += f'\n\t{str(k).lower()}: {", ".join(unique_with_count)}'
		return s
	
	def try_add_entity(self, entity: Entity) -> bool:
		klass = entityclass_to_str[entity.__class__]
		if klass not in self.entities.keys(): self.entities[klass] = []
		if len(self.entities[klass]) < entityclass_thresolds[entity.__class__]:
			# add the entity
			self.entities[klass].append(entity)
			return True
		return False
	
	def try_remove_entity(self, entity_name: str, entity_type: str) -> bool:
		n = None
		for i, entity in enumerate(self.entities[entity_type]):
			if entity.name == entity_name:
				n = i
			if n is not None:
				self.entities[entity_type].pop(n)
				return True
		return False
	
	def try_update_entity(self, entity_reference_name: str, entity_reference_type: str, updated_entity: Entity) -> bool:
		for i, entity in enumerate(self.entities[entity_reference_type]):
			if entity.name == entity_reference_name:
				if updated_entity.description == self.entities[entity_reference_type][i].description:
					updated_entity.sprite = self.entities[entity_reference_type][i].sprite
				self.entities[entity_reference_type][i] = updated_entity
				return True
		return False


class Room(BaseModel):
	class Config:
		arbitrary_types_allowed = True
	
	name: str = Field(..., description="The name of the room.", required=True)
	description: str = Field(..., description="The description of the room", required=True)
	encounter: Encounter = Field(default=Encounter(), description='The encounter in the room.', required=True)
	sprite: str = Field(default=None, description='The sprite for the room.', required=False)
	
	def __str__(self):
		return f'{self.name}: {self.description};{self.encounter}'


class Corridor(BaseModel):
	class Config:
		arbitrary_types_allowed = True
	
	room_from: Room = Field(..., description="The room the corridor is connected to.", required=True)
	room_to: Room = Field(..., description="The room the corridor is connects to.", required=True)
	name: str = Field('', description='The name of the corridor.', required=True)
	length: int = Field(default=2, description="The length of the corridor", required=True)
	encounters: List[Encounter] = Field(default=[Encounter() for _ in range(configs.corridor_min_length)],
	                                    description="The encounters in the corridor.", required=True)
	sprite: str = Field(default=None, description='The sprite for the corridor.', required=False)
	
	def __str__(self):
		return f'Corridor long {self.length} cells from {self.room_from.name} to {self.room_to.name};{"".join(str(e) for e in self.encounters)}'


class Level(BaseModel):
	class Config:
		arbitrary_types_allowed = True
	
	rooms: Dict[str, Room] = Field(default={}, description="The rooms in the level.", required=True)
	corridors: List[Corridor] = Field(default=[], description="The corridors in the level.", required=True)
	
	current_room: str = Field(default='', description="The currently selected room.", required=True)
	
	level_geometry: Dict[str, Dict[str, str]] = Field(default={}, description="The geometry of the level.",
	                                                  required=True)
	
	def save_to_file(self, filename: str) -> None:
		with open(f'{filename}.bin', 'wb') as f:
			pickle.dump(self, f)
	
	@staticmethod
	def load_from_file(filename: str) -> "Level":
		with open(filename, 'rb') as f:
			return pickle.load(f)
	
	def __str__(self) -> str:
		# This is the GLOBAL level description
		# TODO: Implement the LOCAL level description that only gives specific information for the current room
		level_description = '\n'.join([str(self.rooms[k]) for k in self.rooms.keys()]) + '\n'
		level_description += '\n'.join([str(c) for c in self.corridors])
		return level_description
	
	def get_corridor(self, room_from_name, room_to_name, ordered=False) -> Optional[Corridor]:
		for c in self.corridors:
			if (c.room_from.name == room_from_name and c.room_to.name == room_to_name) or (
				not ordered and (c.room_from.name == room_to_name and c.room_to.name == room_from_name)):
				return c
		return None
	
	def try_add_room(self, room_name: str, room_description: str, room_from: Optional[str] = None) -> str:
		if room_name not in self.rooms.keys():
			# try add corridor to connecting room
			if room_from is not None and room_from in self.rooms.keys():
				n = 0
				for corridor in self.corridors:
					if corridor.room_from.name == room_from or corridor.room_to.name == room_from:
						n += 1
				# can only add corridor if the connecting room has at most 3 corridors already
				if n < 4:
					# add the new room to the level
					self.rooms[room_name] = Room(name=room_name, description=room_description)
					self.current_room = room_name
					self.corridors.append(Corridor(room_from=self.rooms[room_from], room_to=self.rooms[room_name],
					                               name=f'{self.rooms[room_from].name}-{room_name}'))
					
					self.level_geometry[room_name] = {direction: '' for direction in DIRECTIONS}
					for direction in DIRECTIONS:
						if self.level_geometry[room_from][direction] == '':
							self.level_geometry[room_from][direction] = room_name
							self.level_geometry[room_name][OPPOSITE_DIRECTIONS[direction]] = room_from
							break
					
					return f'Added {room_name} to the level.'
				else:
					return f'Could not add {room_name} to the level: {room_from} has too many connections.'
			# add the new room to the level
			self.rooms[room_name] = Room(name=room_name, description=room_description)
			self.current_room = room_name
			
			self.level_geometry[room_name] = {direction: '' for direction in DIRECTIONS}
			
			return f'Added {room_name} to the level.'
		return f'Could not add {room_name} to the level: {room_name} already exists.'
	
	def try_remove_room(self, room_name: str) -> str:
		if room_name in self.rooms.keys():
			# remove room
			del self.rooms[room_name]
			# remove connections from-to deleted room
			to_remove = []
			for i, corridor in enumerate(self.corridors):
				if corridor.room_from.name == room_name or corridor.room_to.name == room_name:
					to_remove.append(i)
			for i in reversed(to_remove):
				self.corridors.pop(i)
			
			del self.level_geometry[room_name]
			for other_room_name in self.level_geometry.keys():
				for direction in DIRECTIONS:
					if self.level_geometry[other_room_name][direction] == room_name:
						self.level_geometry[other_room_name][direction] = ''
			
			self.current_room = list(self.rooms.keys())[0] if len(self.rooms) > 0 else ''
			return f'{room_name} has been removed from the dungeon.'
		return f'{room_name} is not in the level.'
	
	def try_update_room(self, room_reference_name: str, name: str, description: str) -> str:
		if room_reference_name in self.rooms.keys():
			# get the current room
			room = self.rooms[room_reference_name]
			# remove it from the list of rooms (since room name can change)
			del self.rooms[room_reference_name]
			# update the room
			room.name = name
			# different description -> sprite must be regenerated
			if room.description != description:
				room.sprite = None
				# entities in the room may be updated, so reset their sprites as well
				for k in room.encounter.entities.keys():
					for entity in room.encounter.entities[k]:
						entity.sprite = None
				# reset the corridor(s) as well
				for corridor in self.corridors:
					if corridor.room_from.name == room_reference_name:
						corridor.room_from = room
						corridor.sprite = None
					if corridor.room_to.name == room_reference_name:
						corridor.room_to = room
						corridor.sprite = None
			room.description = description
			# add room back
			self.rooms[name] = room
			
			del self.level_geometry[room_reference_name]
			for other_room_name in self.level_geometry.keys():
				for direction in DIRECTIONS:
					if self.level_geometry[other_room_name][direction] == room_reference_name:
						self.level_geometry[other_room_name][direction] = name
			
			if self.current_room == room_reference_name:
				self.current_room = name
			return f'Updated {room_reference_name}.'
		return f'{room_reference_name} is not in the level.'
	
	def try_add_corridor(self, room_from_name: str, room_to_name: str, corridor_length: int) -> str:
		n = (0, 0)  # number of corridors for each room
		for corridor in self.corridors:
			# check if the corridor already exists
			if (corridor.room_from.name == room_from_name and corridor.room_to.name == room_to_name) or (
				corridor.room_to.name == room_from_name and corridor.room_from.name == room_to_name):
				return f'Could not add corridor: a corridor between {room_from_name} and {room_to_name} already exists.'
			# count corridors from each room
			if corridor.room_from.name == room_from_name or corridor.room_to.name == room_from_name:
				n[0] += 1
			if corridor.room_from.name == room_to_name or corridor.room_to.name == room_to_name:
				n[1] += 1
		# only add corridor if each room has at most 3 corridors
		if n[0] < 4 and n[1] < 4:
			self.corridors.append(Corridor(room_from=self.rooms[room_from_name], room_to=self.rooms[room_to_name],
			                               name=f'{room_from_name}-{room_to_name}',
			                               length=corridor_length,
			                               encounters=[Encounter() for _ in range(corridor_length)]))
			
			for direction in DIRECTIONS:
				if self.level_geometry[room_from_name][direction] == '':
					self.level_geometry[room_from_name][direction] = room_to_name
					self.level_geometry[room_to_name][OPPOSITE_DIRECTIONS[direction]] = room_from_name
					break
			
			self.current_room = self.corridors[-1].name
			return f'Added corridor from {room_from_name} to {room_to_name}.'
		return f'Could not add corridor: one (or both) of the rooms hase too many connections already'
	
	def try_remove_corridor(self, room_from_name: str, room_to_name: str) -> str:
		to_remove = None
		# get the index of the corridor to remove
		for i, corridor in enumerate(self.corridors):
			if (corridor.room_from.name == room_from_name and corridor.room_to.name == room_to_name) or (
				corridor.room_to.name == room_from_name and corridor.room_from.name == room_to_name):
				to_remove = i
				break
		# remove the corridor if it exists
		if to_remove is not None:
			
			if len(self.current_room.split('-')) > 0 and self.current_room.split('-')[0] == self.corridors[
				to_remove].room_from.name and self.current_room.split('-')[1] == self.corridors[to_remove].room_to.name:
				self.current_room = self.corridors[to_remove].room_from.name
			
			for direction in DIRECTIONS:
				for room_a, room_b in [(room_from_name, room_to_name), (room_to_name, room_from_name)]:
					if self.level_geometry[room_a][direction] == room_b:
						self.level_geometry[room_a][direction] = ''
			
			self.corridors.pop(to_remove)
			return f'Removed corridor between {room_from_name} and {room_to_name}.'
		return f'Could not remove corridor: there is no corridor between {room_from_name} and {room_to_name}.'
	
	def try_update_corridor(self, room_from_name: str, room_to_name: str, corridor_length: int) -> str:
		# make sure the length of the corridor is valid
		if corridor_length < configs.corridor_min_length or corridor_length > configs.corridor_max_length: return False
		# update the corridor
		corridor = self.get_corridor(room_from_name, room_to_name, ordered=False)
		if corridor is not None:
			corridor.length = corridor_length
			# drop encounters if the corridor has shrunk
			if len(corridor.encounters) > corridor.length:
				corridor.encounters = corridor.encounters[:corridor.length]
			# changing the size of the corridor means we need to recreate the background
			corridor.sprite = None
			
			if len(self.current_room.split('-')) > 0 and self.current_room.split('-')[0] == corridor.room_from.name and \
				self.current_room.split('-')[1] == corridor.room_to.name:
				self.current_room = corridor.name
			
			return f'Updated corridor between {room_from_name} and {room_to_name}.'
		return f'Could not updated corridor between {room_from_name} and {room_to_name}: desired length exceeds limits.'
