from typing import List, Optional

from pygame import Rect
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UIButton, UIWindow

from level import Attack
from utils import rich_attack_description


class ActionWindow(UIWindow):
	def __init__(self,
	             rect: Rect,
	             ui_manager: IUIManagerInterface):
		super().__init__(rect, ui_manager, window_display_title='Actions', resizable=False, draggable=False)
		self.attacks: List[UIButton] = []
	
	def clear_attacks(self):
		for attack in self.attacks:
			attack.kill()
		self.attacks = []
	
	def display_attacks(self, attacks: List[Attack]):
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
			self.attacks.append(attack_btn)
	
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
