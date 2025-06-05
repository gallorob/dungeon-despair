import random

from dungeon_despair.domain.entities.hero import Hero
from engine.actions_engine import LootingChoice
from engine.movement_engine import Destination
from player.base_player import Player, PlayerType
from ui_components.action_menu import treasure_choices


class RandomPlayer(Player):
    def __init__(self):
        super().__init__(PlayerType.RANDOM)

    def pick_actions(self, **kwargs) -> int:
        actions = kwargs["actions"]
        active_actions = [action for action in actions if action.active]
        random_action = random.choice(active_actions)
        return actions.index(random_action)

    def pick_moving(self, **kwargs) -> int:
        attacker_type = kwargs["attacker_type"]
        n_heroes = kwargs["n_heroes"]
        n_enemies = kwargs["n_enemies"]
        if attacker_type == Hero:
            idx = random.choice(range(n_heroes))
            return idx
        else:
            idx = random.choice(range(n_enemies))
            return idx + n_heroes

    def pick_destination(self, **kwargs) -> Destination:
        destinations = kwargs["destinations"]
        return random.choice(destinations)

    def choose_disarm_trap(self, **kwargs) -> bool:
        return True

    def choose_loot_treasure(self, **kwargs) -> LootingChoice:
        return random.choice(treasure_choices).looting_choice
