from typing import Union, List

from configs import configs
from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.entities.hero import Hero
from dungeon_despair.domain.entities.treasure import Treasure
from dungeon_despair.domain.utils import ModifierType


class StressSystem:
	def __init__(self):
		self.stress = 0
	
	def get_stress_resist(self, hero: Hero) -> float:
		resist = hero.resist
		# check for 'scare' modifier
		for modifier in hero.modifiers:
			if modifier.type == ModifierType.SCARE:
				resist -= modifier.amount
		# no negative resist
		resist = max(0.0, resist)
		return resist
	
	def process_movement(self):
		self.stress += configs.game.stress.movement
	
	def process_dead(self,
	                 dead_entities: List[Union[Hero, Enemy]]):
		for entity in dead_entities:
			if isinstance(entity, Hero):
				self.stress += configs.game.stress.hero_dies
			else:
				self.stress += configs.game.stress.enemy_dies
	
	def process_new_turn(self):
		self.stress += configs.game.stress.turn
	
	def process_miss(self,
	                 hyp_dmg: float,
	                 attacker: Union[Hero, Enemy]):
		stress_diff = hyp_dmg / 2
		if isinstance(attacker, Hero):
			stress_diff *= -1
			stress_diff *= (1 - self.get_stress_resist(attacker))
		self.stress += int(stress_diff)
	
	def process_damage(self,
	                   dmg: float,
	                   attacker: Union[Hero, Enemy]):
		stress_diff = dmg
		if isinstance(attacker, Hero):
			stress_diff *= -1
			stress_diff *= (1 - self.get_stress_resist(attacker))
		self.stress += int(stress_diff)
	
	def process_bleed(self,
	                  dmg: float,
	                  entity: Union[Hero, Enemy]):
		stress_diff = dmg
		if isinstance(entity, Enemy):
			stress_diff *= -1
		self.stress += int(stress_diff)
		
	def process_heal(self,
	                 heal: float,
	                 entity: Union[Hero, Enemy]):
		stress_diff = heal
		if isinstance(entity, Hero):
			stress_diff *= -1
		self.stress += int(stress_diff)
	
	def process_pass(self,
	                 attacker: Union[Hero, Enemy]):
		stress_diff = configs.game.stress.passing
		if isinstance(attacker, Hero):
			stress_diff *= 1 - self.get_stress_resist(attacker)
		else:
			stress_diff *= -1
		self.stress += int(stress_diff)
	
	def process_move(self,
	                 attacker: Union[Hero, Enemy]):
		stress_diff = configs.game.stress.switch_position
		if isinstance(attacker, Hero):
			stress_diff *= 1 - self.get_stress_resist(attacker)
		else:
			stress_diff *= -1
		self.stress += int(stress_diff)
	
	def process_disarmed_treasure(self,
	                              inspected: bool):
		stress_diff = configs.game.stress.loot_treasure + configs.game.stress.disarm_trap
		stress_diff += configs.game.stress.no_inspect_treasure if not inspected else 0
		self.stress += int(stress_diff)
	
	def process_triggered_treasure(self,
	                               hero: Hero,
	                               dmg_dealt: float,
	                               inspected: bool):
		stress_diff = configs.game.stress.trigger_trapped_treasure + dmg_dealt
		stress_diff -= configs.game.stress.no_inspect_treasure if not inspected else 0
		stress_diff *= (1 - self.get_stress_resist(hero))
		self.stress += int(stress_diff)
	
	def process_safe_treasure(self,
	                          inspected: bool):
		stress_diff = configs.game.stress.loot_treasure
		stress_diff += configs.game.stress.no_inspect_treasure if not inspected else 0
		self.stress += int(stress_diff)
	
	def process_ignore_looting(self,
	                           treasure: Treasure,
	                           hero: Hero):
		stress_diff = configs.game.stress.ignore_treasure
		stress_diff *= (1 - self.get_stress_resist(hero))
		self.stress += int(stress_diff)
	
	def process_trap(self,
	                 hero: Hero,
	                 dmg_dealt: float,
	                 disarmed: bool):
		if disarmed:
			stress_diff = configs.game.stress.disarm_trap
		else:
			stress_diff = configs.game.stress.trigger_trap
			stress_diff += dmg_dealt
			stress_diff *= (1 - self.get_stress_resist(hero))
		self.stress += int(stress_diff)
		
	
stress_system = StressSystem()