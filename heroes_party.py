import json
import random
from typing import List, Tuple
from dungeon_despair.domain.attack import Attack
from dungeon_despair.domain.entities.hero import Hero
from dungeon_despair.domain.modifier import Modifier
from dungeon_despair.domain.utils import ActionType, ModifierType, get_enum_by_value

from configs import configs, resource_path
from dungeon_despair.domain.configs import config as ddd_config

from server_utils import convert_and_save, send_to_server


def generate_sprite(name: str, description: str) -> str:
    data = {
        "hero_name": name,
        "hero_description": description,
    }
    res = send_to_server(data=data, endpoint="dd_generate_hero")
    return convert_and_save(
        b64_img=res["image_base64"],
        fname=res["fname"],
        dirname=configs.assets.dungeon_dir,
    )


def get_heromakingtools():
    from gptfunctionutil import (
        AILibFunction,
        GPTFunctionLibrary,
        LibParam,
        LibParamSpec,
    )

    class HeroMakingTools(GPTFunctionLibrary):
        def try_call_func(self, func_name: str, func_args: str) -> str:
            if isinstance(func_args, str):
                func_args = json.loads(func_args)
            try:
                operation_result = self.call_by_dict(
                    {"name": func_name, "arguments": {**func_args}}
                )
                return operation_result
            except AssertionError as e:
                return f"Domain validation error: {e}"
            except AttributeError as e:
                return f"Function {func_name} not found."
            except TypeError as e:
                return f"Missing arguments: {e}"

        @AILibFunction(
            name="make_hero",
            description="Create a hero.",
            required=[
                "name",
                "description",
                "hp",
                "dodge",
                "prot",
                "spd",
                "trap_resist",
                "stress_resist",
                "attacks",
            ],
        )
        @LibParamSpec(name="name", description="The unique name of the hero")
        @LibParamSpec(
            name="description", description="The physical description of the hero"
        )
        @LibParamSpec(
            name="hp",
            description=f"The health points of the hero, must be a value must be between {ddd_config.min_hp} and {ddd_config.max_hp}.",
        )
        @LibParamSpec(
            name="dodge",
            description=f"The dodge points of the hero, must be a value must be between {ddd_config.min_dodge} and {ddd_config.max_dodge}.",
        )
        @LibParamSpec(
            name="prot",
            description=f"The protection points of the hero, must be a value must be between {ddd_config.min_prot} and {ddd_config.max_prot}.",
        )
        @LibParamSpec(
            name="spd",
            description=f"The speed points of the hero, must be a value must be between {ddd_config.min_spd} and {ddd_config.max_spd}.",
        )
        @LibParamSpec(
            name="trap_resist",
            description=f"The chance this hero will not trigger traps, must be a value must be between 0.0 and 1.0.",
        )
        @LibParamSpec(
            name="stress_resist",
            description=f"The percentage resistance of the hero to stress, must be a value must be between 0.0 and 1.0.",
        )
        def make_hero(
            self,
            name: str,
            description: str,
            hp: float,
            dodge: float,
            prot: float,
            spd: float,
            trap_resist: float,
            stress_resist: float,
        ) -> Hero:
            assert name != "", "Hero name should be provided."
            assert description != "", "Hero description should be provided."
            assert (
                ddd_config.min_hp <= hp <= ddd_config.max_hp
            ), f"Invalid hp value: {hp}; should be between {ddd_config.min_hp} and {ddd_config.max_hp}."
            assert (
                ddd_config.min_dodge <= dodge <= ddd_config.max_dodge
            ), f"Invalid dodge value: {dodge}; should be between {ddd_config.min_dodge} and {ddd_config.max_dodge}."
            assert (
                ddd_config.min_prot <= prot <= ddd_config.max_prot
            ), f"Invalid prot value: {prot}; should be between {ddd_config.min_prot} and {ddd_config.max_prot}."
            assert (
                ddd_config.min_spd <= spd <= ddd_config.max_spd
            ), f"Invalid spd value: {spd}; should be between {ddd_config.min_spd} and {ddd_config.max_spd}."
            assert (
                0.0 <= trap_resist <= 1.0
            ), f"Invalid trap_resist value: {trap_resist}; should be between 0.0 and 1.0."
            assert (
                0.0 <= stress_resist <= 1.0
            ), f"Invalid trastress_resistp_resist value: {stress_resist}; should be between 0.0 and 1.0."
            hero = Hero(
                name=name,
                description=description,
                hp=hp,
                dodge=dodge,
                prot=prot,
                spd=spd,
                trap_resist=trap_resist,
                stress_resist=stress_resist,
                max_hp=hp,
                type="hero",
            )
            return hero

        @AILibFunction(
            name="add_attack",
            description="Add an attack to a hero.",
            required=[
                "name",
                "description",
                "starting_positions",
                "target_positions",
                "base_dmg",
                "modifier_type",
                "modifier_chance",
                "modifier_turns",
                "modifier_amount",
            ],
        )
        @LibParam(name="The unique name of the attack.")
        @LibParam(description="The description of the attack.")
        @LibParam(attack_type='The attack type: must be one of "damage" or "heal".')
        @LibParam(
            starting_positions='A string of 4 characters describing the positions from which the attack can be executed. Use "X" where the attack can be executed from, and "O" otherwise.'
        )
        @LibParam(
            target_positions='A string of 4 characters describing the positions that the attack strikes to. Use "X" where the attack strikes to, and "O" otherwise.'
        )
        @LibParam(
            base_dmg=f"The base damage of the attack. Must be between {ddd_config.min_base_dmg} and {ddd_config.max_base_dmg}."
        )
        @LibParam(accuracy="The attack accuracy (a percentage between 0.0 and 1.0).")
        @LibParam(
            modifier_type=f'The type of modifier this attack applies when triggered. Set to "no-modifier" if no modifier should be applied, else set it to one of {", ".join([x.value for x in ModifierType])}.'
        )
        @LibParam(
            modifier_chance="The chance that the modifier is applied to a target (between 0.0 and 1.0)"
        )
        @LibParam(modifier_turns="The number of turns the modifier is active for")
        @LibParam(
            modifier_amount=f'The amount the modifier applies. If the modifier is "bleed" or "heal", the value must be between {ddd_config.min_base_dmg} and {ddd_config.max_base_dmg}, otherwise it must be between 0.0 and 1.0.'
        )
        def add_attack(
            self,
            name: str,
            description: str,
            attack_type: str,
            starting_positions: str,
            target_positions: str,
            base_dmg: float,
            accuracy: float,
            modifier_type: str,
            modifier_chance: float,
            modifier_turns: float,
            modifier_amount: float,
        ) -> Attack:
            assert name != "", f"Attack name should be specified."
            assert description != "", f"Attack description should be specified."
            assert modifier_type != "", "Attack modifier type should be provided."
            assert (
                modifier_chance is not None
            ), "Attack modifier chance should be provided."
            assert (
                modifier_turns is not None
            ), "Attack modifier turns should be provided."
            assert (
                modifier_amount is not None
            ), "Attack modifier amount should be provided."
            type_enum = get_enum_by_value(ActionType, attack_type)
            assert (
                type_enum is not None
            ), f'Attack type "{attack_type}" is not a valid type: it must be one of {", ".join([t.value for t in ActionType])}.'
            if type_enum == ActionType.DAMAGE:
                assert (
                    ddd_config.min_base_dmg <= base_dmg <= ddd_config.max_base_dmg
                ), f"Invalid base_dmg value: {base_dmg}; should be between {ddd_config.min_base_dmg} and {ddd_config.max_base_dmg}."
            else:  # type is HEAL
                assert (
                    -ddd_config.max_base_dmg <= base_dmg <= -ddd_config.min_base_dmg
                ), f"Invalid base_dmg value: {base_dmg}; should be between {-ddd_config.max_base_dmg} and {-ddd_config.min_base_dmg}."
            assert (
                0.0 <= accuracy <= 1.0
            ), f"Invalid accuracy: must be between 0.0 and 1.0"
            assert (
                len(starting_positions) == 4
            ), f"Invalid starting_positions value: {starting_positions}. Must be 4 characters long."
            assert (
                len(target_positions) == 4
            ), f"Invalid target_positions value: {target_positions}. Must be 4 characters long."
            assert set(starting_positions).issubset(
                {"X", "O"}
            ), f'Invalid starting_positions value: {starting_positions}. Must contain only "X" and "O" characters.'
            assert set(target_positions).issubset(
                {"X", "O"}
            ), f'Invalid target_positions value: {target_positions}. Must contain only "X" and "O" characters.'
            attack = Attack(
                name=name,
                description=description,
                type=type_enum,
                starting_positions=starting_positions,
                target_positions=target_positions,
                base_dmg=base_dmg,
                accuracy=accuracy,
            )
            if modifier_type != "no-modifier":
                assert modifier_type in [
                    x.value for x in ModifierType
                ], f"Could not add attack: {modifier_type} is not a valid modifier type."
                assert (
                    0.0 <= modifier_chance <= 1.0
                ), f"modifier_chance must be a value between 0.0 and 1.0; you passed {modifier_chance}."
                assert (
                    modifier_turns >= 0
                ), f"modifier_turns must be a positive value; you passed {modifier_turns}."
                if modifier_type in [ModifierType.BLEED.value, ModifierType.HEAL.value]:
                    assert (
                        ddd_config.min_base_dmg
                        <= modifier_amount
                        <= ddd_config.max_base_dmg
                    ), f"Invalid modifier_amount value: {modifier_amount}; should be between {ddd_config.min_base_dmg} and {ddd_config.max_base_dmg}."
                elif modifier_type == ModifierType.SCARE.value:
                    assert (
                        0.0 <= modifier_amount <= 1.0
                    ), f"Invalid modifier_amount value: {modifier_amount}; should be between 0.0 and 1.0."
                attack.modifier = Modifier(
                    type=modifier_type,
                    chance=modifier_chance,
                    turns=modifier_turns,
                    amount=modifier_amount,
                )
            return attack

    return HeroMakingTools()


def generate_hero(n_attacks: int, difficulty: str, curr_heroes: List[Hero]) -> Hero:
    tool_lib = get_heromakingtools()

    options = {
        "temperature": configs.gen.temperature,
        "top_p": configs.gen.top_p,
        "top_k": configs.gen.top_k,
        # 'seed': configs.rng_seed,
        "num_ctx": 32768 * 3,
    }

    curr_heroes_str = "\n".join([hero.model_dump_json() for hero in curr_heroes])
    curr_heroes_str = curr_heroes_str.replace(
        '"modifier":null',
        ',"modifier_type":"no-modifier","modifier_chance":0.0,"modifier_turns":0,"modifier_amount":0.0',
    )
    curr_heroes_str = curr_heroes_str.replace('"sprite":null', '"sprite":""')

    formatted_usrmsg = configs.gen.llm_usrmsg.format(
        n_attacks=n_attacks, difficult=difficulty
    )
    hero = None
    while hero is None or len(hero.attacks) != n_attacks:
        # print('New session...')
        with open(resource_path(configs.gen.llm_sysprompt), "r") as f:
            sysprompt = f.read()
        sysprompt = sysprompt.replace("$curr_heroes$", curr_heroes_str)
        if hero:
            sysprompt = sysprompt.replace("$current_hero$", hero.model_dump_json())
        else:
            sysprompt = sysprompt.replace("$current_hero$", "There is no current hero.")
        messages = [
            {"role": "system", "content": sysprompt},
            {"role": "user", "content": formatted_usrmsg},
        ]
        # print(f'{messages=}')
        res = send_to_server(
            data={
                "model_name": configs.gen.llm_model,
                "messages": messages,
                "stream": False,
                "options": options,
                "tools": tool_lib.get_tool_schema(),
            },
            endpoint="ollama_generate",
        )
        # print(f'{res=}')
        if res["message"].get("tool_calls"):
            for tool in res["message"]["tool_calls"]:
                func_name = tool["function"]["name"]
                func_args = tool["function"]["arguments"]
                output = tool_lib.try_call_func(
                    func_name=func_name, func_args=func_args
                )
                # print(f'{output=}')
                if isinstance(output, Hero):
                    hero = output
                elif isinstance(output, Attack):
                    if hero is not None:
                        hero.attacks.append(output)
                else:
                    messages.append({"role": "tool", "content": output})

    return hero


class HeroParty:
    def __init__(self):
        self.party = []

    def get_party_description(self) -> str:
        s = "This is the heroes party:"
        for hero in self.party:
            hero_str = f"\n{hero.name}: {hero.description} (HP={hero.hp} DODGE={hero.dodge} PROT={hero.prot} SPD={hero.spd})"
            s += hero_str
        s += "\n"
        return s

    def get_party_status(self) -> str:
        s = "This is the current heroes party status:"
        for hero in self.party:
            hero_str = f"\n{hero.name}: {hero.hp} HP"
            s += hero_str
        s += "\n"
        return s


def scale_difficulty(wave_n: int) -> Tuple[int, int, str]:
    # Difficulty increaseas every cycle, number of heroes increases within cycle with small variations, number of attacks is random 1-4
    difficulty = min(wave_n // configs.game.diff_cycle, len(configs.game.difficulties))
    local_wave = wave_n % configs.game.diff_cycle
    base_hero_count = (
        1
        + (local_wave * ddd_config.max_enemies_per_encounter) // configs.game.diff_cycle
    )
    num_heroes = min(
        base_hero_count + random.choice([0, 1]), ddd_config.max_enemies_per_encounter
    )
    n_attacks = random.choice(range(4)) + 1
    return num_heroes, n_attacks, configs.game.difficulties[difficulty]


def generate_new_party(wave_n: int) -> HeroParty:
    party = HeroParty()
    num_heroes, n_attacks, difficulty = scale_difficulty(wave_n=wave_n)
    for i in range(num_heroes):
        print(
            f"Generating hero {i + 1} / {wave_n + 1} ({n_attacks=}, {difficulty=})..."
        )
        hero = generate_hero(n_attacks=n_attacks, difficulty=difficulty)
        hero.sprite = generate_sprite(name=hero.name, description=hero.description)
        party.party.append(hero)
    return party
