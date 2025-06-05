from typing import List, Optional, Union

from pygame import Rect
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UIButton, UIWindow

from dungeon_despair.domain.attack import Attack
from dungeon_despair.domain.utils import ActionType, get_enum_by_value
from engine.actions_engine import LootingChoice
from utils import rich_attack_description


class Choice:
    def __init__(
        self,
        name: str,
        description: str,
        looting_choice: Optional[LootingChoice] = None,
    ):
        self.name = name
        self.description = description
        self.looting_choice = looting_choice


trap_choices = [
    Choice(name="Attempt to disarm", description="Try your luck disarming the trap")
]
treasure_choices = [
    Choice(
        name="Inspect and Loot",
        description="Inspect the treasure for traps and then loot",
        looting_choice=LootingChoice.INSPECT_AND_LOOT,
    ),
    Choice(
        name="Loot",
        description="Try your luck looting the treasure",
        looting_choice=LootingChoice.LOOT,
    ),
    Choice(
        name="Ignore",
        description="Move on and leave the treasure behind",
        looting_choice=LootingChoice.IGNORE,
    ),
]


class ActionWindow(UIWindow):
    def __init__(self, rect: Rect, ui_manager: IUIManagerInterface):
        super().__init__(
            rect,
            ui_manager,
            window_display_title="Actions",
            resizable=False,
            draggable=False,
        )
        self.actions: List[UIButton] = []

    def clear_actions(self):
        for action in self.actions:
            action.kill()
        self.actions = []

    def display_actions(
        self, actions: List[Union[Attack, Choice]], disable_not_moving: bool = False
    ):
        self.clear_actions()

        btn_height = self.get_container().rect.height / 8
        starting_height = (
            self.get_container().rect.height / 2 - (btn_height * len(actions)) / 2
        )

        for i, action in enumerate(actions):
            action_btn = UIButton(
                text=action.name,
                relative_rect=Rect(
                    0,
                    starting_height + (i * btn_height),
                    self.get_container().rect.width,
                    btn_height,
                ),
                manager=self.ui_manager,
                starting_height=self.starting_height,
                container=self.get_container(),
            )
            if isinstance(action, Attack):
                action_btn.set_tooltip(rich_attack_description(action))
                action_btn.enable() if action.active else action_btn.disable()
                if (
                    disable_not_moving
                    and get_enum_by_value(ActionType, action.type) != ActionType.MOVE
                ):
                    action_btn.disable()
            else:
                action_btn.set_tooltip(action.description)
            self.actions.append(action_btn)

    def check_colliding_action(self, pos) -> Optional[int]:
        for i, choice in enumerate(self.actions):
            if choice.rect.collidepoint(pos):
                return i if choice.is_enabled else None
        return None
