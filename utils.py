import pygame
from PIL import Image
from dungeon_despair.domain.attack import Attack
from dungeon_despair.domain.corridor import Corridor
from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.entities.entity import Entity
from dungeon_despair.domain.entities.trap import Trap
from dungeon_despair.domain.entities.treasure import Treasure
from dungeon_despair.domain.level import Level
from dungeon_despair.domain.room import Room
from pygame import Surface

from heroes_party import Hero


def img_to_pygame_sprite(img: Image) -> Surface:
	return pygame.image.frombuffer(img.tobytes(), img.size, img.mode)


def get_current_room(level: Level):
	if level.current_room in level.rooms.keys():
		return level.rooms[level.current_room]
	else:
		return level.corridors[level.current_room]


def get_current_encounter(level: Level,
                          encounter_idx: int = -1):
	curr_room = get_current_room(level)
	if isinstance(curr_room, Room):
		return curr_room.encounter
	else:
		return curr_room.encounters[encounter_idx]


def basic_room_description(room: Room) -> str:
	return f'<b>{room.name}</b><br><p><i>{room.description}</i></p>'


def basic_corridor_description(corridor: Corridor) -> str:
	return f'<h3>Corridor between <i>{corridor.room_from.name}</i> and <i>{corridor.room_to.name}</i></h3>'


def rich_entity_description(entity: Entity) -> str:
	rich_description = f'<b>{entity.name}</b>'
	rich_description += f'<br><i>{entity.description}</i>'
	
	if isinstance(entity, Enemy) or isinstance(entity, Hero):
		rich_description += f'Species: {entity.species}  HP:{entity.hp}  DODGE:{entity.dodge:.2f}  PROT:{entity.prot:.2f}  SPD:{entity.spd:.2f}'
	elif isinstance(entity, Treasure):
		rich_description += f'<p>Loot: {entity.loot}</p>'
	elif isinstance(entity, Trap):
		rich_description += f'<p>Effect: {entity.effect}</p>'
	
	return rich_description


def rich_attack_description(attack: Attack) -> str:
	return f'<b>{attack.name}</b>:  <i>{attack.description}</i> (DMG: {attack.base_dmg} FROM: {attack.starting_positions} TO: {attack.target_positions})'
