from typing import Optional

import pygame
from pygame import Rect
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UIWindow, UIImage, UILabel

from configs import configs
from engine.stress_system import stress_system


class GameOver(UIWindow):
    def __init__(self, rect: Rect, ui_manager: IUIManagerInterface):
        super().__init__(
            rect,
            ui_manager,
            window_display_title="Game Over",
            resizable=False,
            draggable=False,
            always_on_top=True,
        )
        self.img = pygame.image.load(configs.assets.screens.gameover).convert_alpha()
        self.img.set_alpha(0)

        self.background_image: Optional[UIImage] = None
        self.score_str: Optional[UILabel] = None

    def toggle(self):
        self.background_image = UIImage(
            relative_rect=pygame.rect.Rect(
                0, 0, self.relative_rect.width, self.relative_rect.height
            ),
            image_surface=self.img,
            manager=self.ui_manager,
            container=self.get_container(),
            starting_height=self.starting_height,
        )

        self.score_str = UILabel(
            relative_rect=Rect(
                self.get_container().rect.width / 2
                - self.get_container().rect.width / 8,
                0,
                self.get_container().rect.width / 4,
                self.get_container().rect.height / 8,
            ),
            text=f"Your Score: {stress_system.score}",
            container=self.get_container(),
            manager=self.ui_manager,
        )
        self.show()

    def update(self, time_delta: float) -> None:
        if self.background_image is not None:
            self.img.set_alpha(min(self.img.get_alpha() + 1, 256))
            self.background_image.set_image(self.img)
