import os

import pygame
from pygame import Rect
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UIWindow, UIImage

from configs import configs


class GameOver(UIWindow):
	def __init__(self,
	             rect: Rect,
	             ui_manager: IUIManagerInterface):
		super().__init__(rect, ui_manager, window_display_title='Game Over', resizable=False, draggable=False,
		                 always_on_top=True)
		
		self.imgs = [
			pygame.image.load(os.path.join(configs.assets, 'heroes_gameover_screen.jpeg')).convert_alpha(),
			pygame.image.load(os.path.join(configs.assets, 'enemies_gameover_screen.jpeg')).convert_alpha()
		]
		for img in self.imgs:
			img.set_alpha(0)
		
		self.img_idx = -1
		
		self.background_image = UIImage(
			relative_rect=pygame.rect.Rect(0, 0, self.relative_rect.width, self.relative_rect.height),
			image_surface=self.imgs[self.img_idx],
			manager=self.ui_manager,
			container=self.get_container(),
			starting_height=self.starting_height)
	
	def update(self, time_delta: float) -> None:
		self.imgs[self.img_idx].set_alpha(min(self.imgs[self.img_idx].get_alpha() + 1, 256))
		self.background_image.set_image(self.imgs[self.img_idx])
