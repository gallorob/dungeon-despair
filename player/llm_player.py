from typing import Dict, List, Optional, Union

from context_manager import CombatContext, TreasureContext, MovementContext, TrapContext
from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.entities.entity import Entity
from dungeon_despair.domain.entities.hero import Hero
from player.base_player import Player, PlayerType


class LLMPlayer(Player):
    def __init__(self, model_name: str):
        super().__init__(PlayerType.LLM)
        self.model_name = model_name
        with open("./assets/llm_prompts/attack_prompt", "r") as f:
            self.attack_prompt = f.read()
        with open("./assets/llm_prompts/trap_prompt", "r") as f:
            self.trap_prompt = f.read()
        with open("./assets/llm_prompts/treasure_prompt", "r") as f:
            self.treasure_prompt = f.read()
        with open("./assets/llm_prompts/movement_prompt", "r") as f:
            self.movement_prompt = f.read()
        self.context: Optional[
            Union[CombatContext, TrapContext, TreasureContext, MovementContext]
        ] = None

    def __chat(self, msgs: List[Dict[str, str]]) -> str:
        # TODO: Should go through the server instead
        output = {}  # ollama.chat(model=self.model_name,
        #         messages=msgs)
        response = output["message"]["content"]
        return response

    def pick_actions(self, attacks) -> int:
        attacks_names = [attack.name for attack in attacks]
        attacks_formatted = ""
        for attack, targets, dmgs in zip(
            self.context.attacks, self.context.targeted, self.context.expected_dmg
        ):
            if attack == "Pass":
                attacks_formatted += f' - "{attack}": Skip the current turn'
            else:
                attacks_formatted += f' - "{attack}": Would deal '
                dmgs_formatted = []
                for target, dmg in zip(targets, dmgs):
                    dmgs_formatted.append(f"{dmg} damage to {target}")
                attacks_formatted += ", ".join(dmgs_formatted) + "\n"
        prompt_copy = self.attack_prompt.format(
            heroes_status=self.context.heroes_status,
            enemies_status=self.context.enemies_status,
            stress=self.context.stress,
            n=len(self.context.combat_history),
            combat_history="\n".join(self.context.combat_history),
            attacker=self.context.attacking,
            attacks_formatted=attacks_formatted,
        )
        messages = [{"role": "user", "content": prompt_copy}]
        response = self.__chat(messages)
        # print(f'LLMPlayer.pick_attack - {response=}')
        for idx, attack in enumerate(attacks_names):
            if attack in response:
                self.context = None
                return idx
        raise ValueError(f"LLMPlayer.pick_attack - invalid response: {response}")

    def pick_moving(
        self, attacker: Entity, heroes: List[Hero], enemies: List[Enemy]
    ) -> int:
        raise NotImplementedError(f"LLMPlayer can't pick movement!")

    def pick_destination(self, destinations):
        destinations_str = ""
        for destination, description, enc_descs in zip(
            self.context.destinations,
            self.context.descriptions,
            self.context.encounters_desc,
        ):
            destinations_str += f' - "{destination}": {description} ('
            destinations_str += ", ".join(enc_descs) + ")\n"

        prompt_copy = self.movement_prompt.format(
            heroes_status=self.context.heroes_status,
            stress=self.context.stress,
            destinations_str=destinations_str,
        )
        messages = [{"role": "user", "content": prompt_copy}]
        response = self.__chat(messages)
        print(f"LLMPlayer.pick_destination - {destinations=} {response=}")
        for destination in destinations:
            if destination in response:
                self.context = None
                return destination.split("_")
        raise ValueError(f"LLMPlayer.pick_destination - invalid response: {response}")

    def choose_disarm_trap(self) -> bool:
        prompt_copy = self.trap_prompt.format(
            heroes_status=self.context.heroes_status,
            stress=self.context.stress,
            trap_description=self.context.desc,
            disarming_outcome=self.context.outcome,
        )
        messages = [{"role": "user", "content": prompt_copy}]
        response = self.__chat(messages)
        # print(f'LLMPlayer.choose_disarm_trap - {response=}')
        if "Disarm" in response or "Leave Alone" in response:
            self.context = None
            return "Disarm" in response
        raise ValueError(f"LLMPlayer.choose_disarm_trap - invalid response: {response}")

    def choose_loot_treasure(self) -> bool:
        prompt_copy = self.treasure_prompt.format(
            heroes_status=self.context.heroes_status,
            stress=self.context.stress,
            treasure_description=self.context.desc,
            looting_outcome=self.context.outcome,
        )
        messages = [{"role": "user", "content": prompt_copy}]
        response = self.__chat(messages)
        # print(f'LLMPlayer.choose_loot_treasure - {response=}')
        if "Loot" in response or "Leave Alone" in response:
            self.context = None
            return "Loot" in response
        raise ValueError(
            f"LLMPlayer.choose_loot_treasure - invalid response: {response}"
        )
