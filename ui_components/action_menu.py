from typing import List, Optional

from pygame import Rect
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UIButton, UIWindow

from dungeon_despair.domain.attack import Attack
from dungeon_despair.domain.utils import AttackType
from utils import rich_attack_description


class ActionWindow(UIWindow):
	def __init__(self,
	             rect: Rect,
	             ui_manager: IUIManagerInterface):
		super().__init__(rect, ui_manager, window_display_title='Actions', resizable=False, draggable=False)
		self.attacks: List[UIButton] = []
		self.choices: List[UIButton] = []
	
	def clear_attacks(self):
		for attack in self.attacks:
			attack.kill()
		self.attacks = []
	
	def clear_choices(self):
		for choice in self.choices:
			choice.kill()
		self.choices = []
	
	def display_attacks(self, attacks: List[Attack], moving: bool):
		self.clear_attacks()
		
		btn_height = self.get_container().rect.height / 8
		starting_height = self.get_container().rect.height / 2 - (btn_height * len(attacks)) / 2
		
		for i, attack in enumerate(attacks):
			attack_btn = UIButton(text=attack.name,
			                      relative_rect=Rect(0,
			                                         starting_height + (i * btn_height),
			                                         self.get_container().rect.width,
			                                         btn_height),
			                      manager=self.ui_manager,
			                      starting_height=self.starting_height,
			                      container=self.get_container())
			attack_btn.set_tooltip(rich_attack_description(attack))
			if attack.active:
				attack_btn.enable()
			else:
				attack_btn.disable()
			if attack.type != AttackType.MOVE and moving: attack_btn.disable()
			self.attacks.append(attack_btn)
	
	def display_trap_choices(self):
		self.clear_choices()
		btn_height = self.get_container().rect.height / 8
		starting_height = self.get_container().rect.height / 2 - btn_height
		
		for i, (choice, tooltip) in enumerate(zip(['Attempt to disarm', 'Ignore'],
		                                          ['Try your luck disarming the trap',
		                                           'Move on and leave the trap as-is'])):
			choice_btn = UIButton(text=choice,
			                      relative_rect=Rect(0,
			                                         starting_height + (i * btn_height),
			                                         self.get_container().rect.width,
			                                         btn_height),
			                      manager=self.ui_manager,
			                      starting_height=self.starting_height,
			                      container=self.get_container())
			choice_btn.set_tooltip(tooltip)
			self.choices.append(choice_btn)
	
	def display_treasure_choices(self):
		self.clear_choices()
		btn_height = self.get_container().rect.height / 8
		starting_height = self.get_container().rect.height / 2 - btn_height
		
		for i, (choice, tooltip) in enumerate(zip(['Try looting', 'Ignore'],
		                                          ['Try your luck looting the treasure',
		                                           'Move on and treasure behind'])):
			choice_btn = UIButton(text=choice,
			                      relative_rect=Rect(0,
			                                         starting_height + (i * btn_height),
			                                         self.get_container().rect.width,
			                                         btn_height),
			                      manager=self.ui_manager,
			                      starting_height=self.starting_height,
			                      container=self.get_container())
			choice_btn.set_tooltip(tooltip)
			self.choices.append(choice_btn)
	
	def check_clicked_choice(self, pos) -> Optional[int]:
		for i, choice in enumerate(self.choices):
			if choice.rect.collidepoint(pos):
				return i
		return None
	
	def check_clicked_attack(self, pos) -> Optional[int]:
		for i, attack in enumerate(self.attacks):
			if attack.rect.collidepoint(pos):
				return i if attack.is_enabled else None
		return None
	
	def check_hovered_attack(self, pos) -> Optional[int]:
		for i, attack in enumerate(self.attacks):
			if attack.rect.collidepoint(pos) and attack.is_enabled:
				return i
		return None
	
	def toggle_nonmove_actions(self):
		for attack in self.attacks:
			if attack.text != 'Move':
				if attack.is_enabled: attack.disable()
				else: attack.enable()
