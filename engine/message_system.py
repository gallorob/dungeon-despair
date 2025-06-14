from typing import List, Union

from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.entities.hero import Hero
from dungeon_despair.domain.entities.treasure import Treasure


class MessageSystem:
    def __init__(self):
        self.queue = []

    def add_msg(self, msg: str) -> None:
        self.queue.append(msg)

    def get_queue(self) -> List[str]:
        q = self.queue.copy()
        self.queue = []
        return q

    def process_dead(self, dead_entities: List[Union[Hero, Enemy]]):
        for entity in dead_entities:
            self.add_msg(msg=f"{entity.name} is dead!")

    def ignore_looting(self, hero: Hero, treasure: Treasure):
        self.add_msg(msg=f"{hero.name} ignores {treasure.name}... For now.")


msg_system = MessageSystem()
