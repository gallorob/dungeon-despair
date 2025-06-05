from enum import auto, Enum

from engine.actions_engine import LootingChoice
from engine.movement_engine import Destination


class PlayerType(Enum):
    HUMAN: int = auto()
    RANDOM: int = auto()
    LLM: int = auto()
    AI: int = auto()


class Player:
    def __init__(self, player_type: PlayerType):
        self.type = player_type

    def pick_actions(self, **kwargs) -> int:
        pass

    def pick_moving(self, **kwargs) -> int:
        pass

    def pick_destination(self, **kwargs) -> Destination:
        pass

    def choose_disarm_trap(self, **kwargs) -> bool:
        pass

    def choose_loot_treasure(self, **kwargs) -> LootingChoice:
        pass
