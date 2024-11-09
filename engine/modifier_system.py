import copy
import random
from typing import List, Union

from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.entities.hero import Hero
from dungeon_despair.domain.modifier import Modifier
from dungeon_despair.domain.utils import get_enum_by_value, ModifierType

from engine.message_system import msg_system
from engine.stress_system import stress_system

class ModifierSystem:
	@staticmethod
	def apply_and_tick_modifiers(entities: List[Union[Hero, Enemy]]) -> None:
		for entity in entities:
			for modifier in entity.modifiers:
				m_type = get_enum_by_value(ModifierType, modifier.type)
				if m_type == ModifierType.BLEED:
					dmg = min(entity.hp, modifier.amount)
					entity.hp -= dmg
					stress_system.process_bleed(dmg=dmg, entity=entity)
					msg_system.add_msg(f'<b>{entity.name}</b> takes {modifier.amount} damage from {modifier.type}!')
				elif m_type == ModifierType.HEAL:
					heal = min(entity.max_hp - entity.hp, modifier.amount)
					entity.hp += heal
					stress_system.process_heal(heal=heal, entity=entity)
					msg_system.add_msg(f'<b>{entity.name}</b> heals {heal} points via {modifier.type}!')
				modifier.turns -= 1
			entity.modifiers = [m for m in entity.modifiers if m.turns != 0]
	
	@staticmethod
	def try_add_modifier(target: Union[Hero, Enemy],
	                     modifier: Modifier) -> None:
		if modifier is not None:
			if random.random() <= modifier.chance:
				# TODO: Refresh modifiers of the same type as the one being added
				target.modifiers.append(copy.deepcopy(modifier))
				msg_system.add_msg(f'<b>{target.name}</b> receives a {modifier.type} modifier!')

		