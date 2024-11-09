import pygame
from PIL import Image
from pygame import Surface

from dungeon_despair.domain.attack import Attack
from dungeon_despair.domain.corridor import Corridor
from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.entities.entity import Entity
from dungeon_despair.domain.entities.trap import Trap
from dungeon_despair.domain.entities.treasure import Treasure
from dungeon_despair.domain.level import Level
from dungeon_despair.domain.room import Room
from dungeon_despair.domain.utils import get_enum_by_value, ActionType
from heroes_party import Hero, HeroParty


def img_to_pygame_sprite(img: Image) -> Surface:
	return pygame.image.frombuffer(img.tobytes(), img.size, img.mode)


def basic_room_description(room: Room) -> str:
	return f'<b>{room.name}</b><br><p><i>{room.description}</i></p>'


def basic_corridor_description(corridor: Corridor) -> str:
	return f'<h3>Corridor between <i>{corridor.room_from}</i> and <i>{corridor.room_to}</i></h3>'


def rich_entity_description(entity: Entity) -> str:
	rich_description = f'<b>{entity.name}</b>'
	rich_description += f'<br><i>{entity.description}</i>'
	
	if isinstance(entity, Enemy) or isinstance(entity, Hero):
		rich_description += f'Species: {entity.species}  HP:{entity.hp}  DODGE:{entity.dodge:.2%}  PROT:{entity.prot:.2f}  SPD:{entity.spd:.2f}'
	elif isinstance(entity, Treasure):
		rich_description += f'<p>Loot: {entity.loot}</p>'
	elif isinstance(entity, Trap):
		rich_description += f'<p>Effect: {entity.effect}</p>'
	
	return rich_description


def rich_attack_description(attack: Attack) -> str:
	attack_type = get_enum_by_value(ActionType, attack.type)
	if attack_type == ActionType.MOVE:
		s = f'<b>Move</b>: <i>Move to another position within the group.</i>'
	elif attack_type == ActionType.PASS:
		s = f'<b>Pass</b>: <i>Skip the current turn.</i>'
	elif attack_type == ActionType.DAMAGE:
		s = f'<b>{attack.name}</b>:  <i>{attack.description}</i> (DMG: {attack.base_dmg}HP {attack.accuracy:.0%} FROM: {attack.starting_positions} TO: {attack.target_positions})'
	elif attack_type == ActionType.HEAL:
		s = f'<b>{attack.name}</b>:  <i>{attack.description}</i> (HEAL: {-attack.base_dmg}HP FROM: {attack.starting_positions} TO: {attack.target_positions})'
	else:
		raise NotImplementedError(f'Unknown attack type: {attack.type}')
	if attack.modifier:
		s += f'\n{str(attack.modifier)}'
	return s

def set_ingame_properties(game_data: Level, heroes: HeroParty) -> None:
	for hero in heroes.party:
		hero.max_hp = hero.hp
	
	for room in game_data.rooms.values():
		for enemy in room.encounter.entities['enemy']:
			enemy.max_hp = enemy.hp
	
	for corridor in game_data.corridors.values():
		for encounter in corridor.encounters:
			for enemy in encounter.entities['enemy']:
				enemy.max_hp = enemy.hp