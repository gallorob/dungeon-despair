import copy
import os
from typing import List
from dungeon_despair.domain.entities.hero import Hero
import pygame
from pygame_gui.elements import UITextBox, UIWindow, UIImage
from pygame.rect import Rect
from configs import configs
from heroes_party import HeroParty, generate_hero, generate_sprite, scale_difficulty
from pygame_gui.core.interfaces import IUIManagerInterface

from utils import rich_entity_description


class HeroRosterWindow(UIWindow):
    def __init__(self, rect: pygame.Rect, ui_manager: IUIManagerInterface):
        super().__init__(
            rect,
            ui_manager,
            window_display_title="Heroes Roster",
            resizable=False,
            draggable=False,
        )

        self.final_party = None
        self.__ops = []
        self.__args = []
        self.__last_res = None
        self.__step = 0

        self.__party = HeroParty()

        self.heroes: List[UIImage] = []

        self.num_heroes = -1
        self.n_attacks = -1
        self.difficulty = ""

        self.log_panel_height = self.relative_rect.height / 4
        self.log_panel_voff = 0.75 * self.relative_rect.height

        self.heroes_portraits_hoff = self.relative_rect.width / 8
        self.heroes_portraits_voff = self.log_panel_voff / 4
        self.heroes_portraits_block = (
            self.relative_rect.width - (2 * self.heroes_portraits_hoff)
        ) / 4
        self.heroes_portraits_innerpad = (self.heroes_portraits_block / 4) / 4
        self.hero_portrait_w = (
            self.heroes_portraits_block - 2 * self.heroes_portraits_innerpad
        )
        self.hero_portrait_h = self.log_panel_voff - 2 * self.heroes_portraits_voff

        self.log_panel = UITextBox(
            html_text="<b>Events log: </b>",
            relative_rect=pygame.Rect(
                0, self.log_panel_voff, self.relative_rect.width, self.log_panel_height
            ),
            manager=ui_manager,
            container=self.get_container(),
            starting_height=self.starting_height,
        )

    def generate_party_steps(self, wave_n: int) -> bool:
        self.__party = HeroParty()

        self.num_heroes, self.n_attacks, self.difficulty = scale_difficulty(
            wave_n=wave_n
        )

        # prepare portraits
        self.heroes = []
        for i in range(self.num_heroes):
            hero_portrait = UIImage(
                relative_rect=Rect(
                    self.heroes_portraits_hoff
                    + i * (self.hero_portrait_w + 2 * self.heroes_portraits_innerpad)
                    + self.heroes_portraits_innerpad,
                    self.heroes_portraits_voff,
                    self.hero_portrait_w,
                    self.hero_portrait_h,
                ),
                image_surface=pygame.image.load(configs.assets.icons.unk_hero),
                manager=self.ui_manager,
                container=self.get_container(),
                parent_element=self,
                starting_height=self.starting_height + 2,
            )
            self.heroes.append(hero_portrait)

        for i in range(self.num_heroes):
            self.__ops.append(self.update_log_text)
            self.__args.append(
                {"msg": f"Generating hero {i + 1} / {self.num_heroes}..."}
            )

            self.__ops.append(generate_hero)
            self.__args.append(
                {
                    "n_attacks": self.n_attacks,
                    "difficulty": self.difficulty,
                    "curr_heroes": [],
                }
            )

            self.__ops.append(self.update_log_text)
            self.__args.append(
                {"msg": "New hero created ({hero_name})! Generating sprite..."}
            )

            self.__ops.append(generate_sprite)
            self.__args.append({"name": "", "description": ""})

            self.__ops.append(self.update_log_text)
            self.__args.append({"msg": f"New hero sprite generated!"})

            self.__ops.append(self.update_portrait)
            self.__args.append({"idx": i})

        return True

    def update_log_text(self, msg: str) -> None:
        self.log_panel.set_text(f"<b>Events log: </b> {msg}")

    def step(self) -> None:
        if self.__step < len(self.__ops):
            op, args = self.__ops[self.__step], self.__args[self.__step]
            if op == generate_hero:
                args["curr_heroes"] = self.__party.party
            elif (
                self.__last_res is not None
                and isinstance(self.__last_res, Hero)
                and op == generate_sprite
            ):
                self.__last_res.hp = 0.1
                args["name"] = self.__last_res.name
                args["description"] = self.__last_res.description
            elif self.__last_res is not None and "hero_name" in args.get("msg", ""):
                args["msg"] = args["msg"].format(hero_name=self.__last_res.name)
            res = op(**args)
            if isinstance(res, Hero):
                self.__last_res = res
            elif isinstance(res, str) and res.endswith(".png"):
                self.__last_res.sprite = res
                self.__party.party.append(copy.deepcopy(self.__last_res))
            self.__step += 1
        else:
            self.final_party = self.__party

    def update_portrait(self, idx: int) -> None:
        self.heroes[idx].set_image(
            pygame.image.load(
                os.path.join(configs.assets.dungeon_dir, self.__last_res.sprite)
            )
        )
        self.heroes[idx].set_tooltip(rich_entity_description(entity=self.__last_res))
        self.__last_res = None

    def update(self, time_delta: float):
        super().update(time_delta)
