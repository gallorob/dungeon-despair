from typing import List
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
		for enemy in room.encounter.enemies:
			enemy.max_hp = enemy.hp
			tot_dmg = 0
			for attack in enemy.attacks:
				tot_dmg += attack.base_dmg * attack.accuracy
			enemy.cost = enemy.max_hp + tot_dmg
		for treasure in room.encounter.treasures:
			treasure.cost = treasure.dmg * treasure.trapped_chance
	
	for corridor in game_data.corridors.values():
		for encounter in corridor.encounters:
			for enemy in encounter.enemies:
				enemy.max_hp = enemy.hp
				tot_dmg = 0
				for attack in enemy.attacks:
					tot_dmg += attack.base_dmg * attack.accuracy
				enemy.cost = enemy.max_hp + tot_dmg
			for trap in encounter.traps:
				trap.cost = trap.dmg * trap.chance
			for treasure in encounter.treasures:
				treasure.cost = treasure.dmg * treasure.trapped_chance


def get_entities_differences(ref_level: Level, curr_level: Level) -> List[Entity]:
	# Get a list of all entities that are NOT present in curr_level but are in ref_level
	diff_entities = []
	for room_name in ref_level.rooms.keys():
		ref_enemies = [f'{x.name}__{x.hp}' for x in ref_level.rooms[room_name].encounter.enemies]
		curr_enemies = [f'{x.name}__{x.hp}' for x in curr_level.rooms[room_name].encounter.enemies]
		for i, ref_enemy in enumerate(ref_enemies):
			if ref_enemy not in curr_enemies:
				diff_entities.append(ref_level.rooms[room_name].encounter.enemies[i])
		ref_treasures = [f'{x.name}' for x in ref_level.rooms[room_name].encounter.treasures]
		curr_treasures = [f'{x.name}' for x in curr_level.rooms[room_name].encounter.treasures]
		for i, ref_treasure in enumerate(ref_treasures):
			if ref_treasure not in curr_treasures:
				diff_entities.append(ref_level.rooms[room_name].encounter.treasures[i])
	for corridor_name in ref_level.corridors.keys():
		for i, encounter in enumerate(ref_level.corridors[corridor_name].encounters):
			ref_enemies = [f'{x.name}__{x.hp}' for x in encounter.enemies]
			curr_enemies = [f'{x.name}__{x.hp}' for x in curr_level.corridors[corridor_name].encounters[i].enemies]
			for j, ref_enemy in enumerate(ref_enemies):
				if ref_enemy not in curr_enemies:
					diff_entities.append(ref_level.rooms[room_name].encounter.enemies[j])
			ref_traps = [f'{x.name}' for x in encounter.traps]
			curr_traps = [f'{x.name}' for x in curr_level.corridors[corridor_name].encounters[i].traps]
			for j, ref_trap in enumerate(ref_traps):
				if ref_trap not in curr_traps:
					diff_entities.append(ref_level.corridors[room_name].encounter.traps[j])
			ref_treasures = [f'{x.name}' for x in encounter.treasures]
			curr_treasures = [f'{x.name}' for x in curr_level.corridors[corridor_name].encounters[i].treasures]
			for j, ref_treasure in enumerate(ref_treasures):
				if ref_treasure not in curr_treasures:
					diff_entities.append(ref_level.corridors[room_name].encounter.treasures[j])
	return diff_entities