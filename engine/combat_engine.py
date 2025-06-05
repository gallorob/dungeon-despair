import random
from enum import auto, Enum
from typing import List, Union, Optional

from dungeon_despair.domain.attack import Attack
from dungeon_despair.domain.encounter import Encounter
from dungeon_despair.domain.entities.enemy import Enemy
from dungeon_despair.domain.utils import ActionType, get_enum_by_value, ModifierType
from engine.modifier_system import ModifierSystem
from heroes_party import Hero, HeroParty

from engine.message_system import msg_system
from engine.stress_system import stress_system


class CombatPhase(Enum):
    PICK_ATTACK = auto()
    CHOOSE_POSITION = auto()
    END_OF_TURN = auto()
    END_OF_COMBAT = auto()


class CombatEngine:
    def __init__(self):
        self.turn_number = 0
        self.currently_active = 0
        self.sorted_entities = []
        self.current_encounter: Optional[Encounter] = None

        self.actions: List[Attack] = []
        self.targets_by_action: List[List[int]] = []

        self.extra_actions = [
            Attack(
                name="Pass",
                description="Pass the current turn.",
                type=ActionType.PASS,
                starting_positions="XXXX",
                target_positions="OOOO",
                base_dmg=0,
                accuracy=0.0,
            ),
            Attack(
                name="Move",
                description="Move to another hero's position.",
                type=ActionType.MOVE,
                starting_positions="XXXX",
                target_positions="OOOO",
                base_dmg=0,
                accuracy=0.0,
            ),
        ]

        self.state = CombatPhase.PICK_ATTACK

    def start_encounter(self, encounter: Encounter, heroes: HeroParty) -> None:
        """Start the encounter"""
        msg_system.add_msg("<b><i>### NEW ENCOUNTER</i></b>")
        self.turn_number = 0
        self.current_encounter = encounter

    def start_turn(self, heroes: HeroParty, enemies: List[Enemy]):
        """Start a new turn in combat"""
        self.turn_number += 1
        self.currently_active = -1
        msg_system.add_msg(f"<b>Turn {self.turn_number}</b>")
        # Everyone takes a move during the turn, then the turn advances and everyone rerolls turn order and goes again.
        self.sorted_entities = self.sort_entities([*heroes.party, *enemies])
        self.state = CombatPhase.PICK_ATTACK
        stress_system.process_new_turn()

    def get_next_attacker(self):
        for i in range(self.currently_active + 1, len(self.sorted_entities)):
            entity = self.sorted_entities[i]
            is_stunned = False
            for modifier in entity.modifiers:
                if get_enum_by_value(ModifierType, modifier.type) == ModifierType.STUN:
                    is_stunned = True
                    break
            if not is_stunned:
                self.currently_active = i
                msg_system.add_msg(
                    f"Attacking: <b>{self.sorted_entities[self.currently_active].name}</b>"
                )
                break

    def sort_entities(
        self, entities: List[Union[Hero, Enemy]]
    ) -> List[Union[Hero, Enemy]]:
        """Sort the entities for combat order"""
        # Turn order is determined semi-randomly: 1d10+Speed.
        modified_speed = [
            (entity.spd * 10) + random.randint(1, 10) for entity in entities
        ]
        sorted_entities = [
            i for i, _ in sorted(enumerate(modified_speed), key=lambda x: x[1])
        ]
        # return sorted_entities
        sorted_entities = [entities[i] for i in sorted_entities]
        return sorted_entities

    @property
    def attacker(self) -> Union[Hero, Enemy]:
        return self.sorted_entities[self.currently_active]

    def tick(self, heroes: HeroParty):
        """Update the state of combat"""
        # Try update the current attacker
        curr_n = self.currently_active
        self.get_next_attacker()
        if curr_n == self.currently_active:  # No available next attacker
            self.state = CombatPhase.END_OF_TURN
        else:
            self.set_actions_and_targets(heroes=heroes)
        # Check for end of combat in this encounter
        if len(heroes.party) == 0 or len(self.current_encounter.enemies) == 0:
            self.state = CombatPhase.END_OF_COMBAT
            self.actions = []

    def convert_mask(self, mask: str) -> List[int]:
        """Convert the mask from string to list of ints"""
        return [1 if x == "X" else 0 for x in mask]

    def set_actions_and_targets(self, heroes: HeroParty) -> None:
        self.targets_by_action = []
        self.actions = self.attacker.attacks.copy()
        self.actions.extend(self.extra_actions)
        positioned_entities = [
            *heroes.party,
            *self.current_encounter.enemies,
        ]  # TODO: Set in self?
        attacker_idx = positioned_entities.index(self.attacker)

        # disable attacks that cannot be executed
        for action in self.actions:
            action_type = get_enum_by_value(ActionType, action.type)
            if action_type == ActionType.MOVE:
                # Move should be disabled if there are no other entities to change place with
                if isinstance(self.attacker, Hero):
                    action.active = len(heroes.party) > 1
                else:
                    action.active = len(self.current_encounter.enemies) > 1
                self.targets_by_action.append([])
            elif action_type != ActionType.PASS:
                # Disable actions that cannot be executed from the current position
                from_mask = self.convert_mask(action.starting_positions)
                if isinstance(self.attacker, Hero):  # FROM is reversed for heroes
                    from_mask = list(reversed(from_mask))
                idx = (
                    attacker_idx
                    if isinstance(self.attacker, Hero)
                    else attacker_idx - len(heroes.party)
                )
                action.active = from_mask[idx] == 1
                if action.active:
                    # Disable actions that don't have a target entity
                    to_mask = self.convert_mask(action.target_positions)
                    if action_type == ActionType.DAMAGE:
                        if isinstance(
                            self.attacker, Enemy
                        ):  # TO is reversed for enemies
                            to_mask = list(reversed(to_mask))
                            targets = heroes.party
                            offset = 0
                        else:
                            targets = self.current_encounter.enemies
                            offset = len(heroes.party)
                    else:
                        if isinstance(
                            self.attacker, Hero
                        ):  # HEAL is applied to the same group
                            to_mask = list(reversed(to_mask))
                            targets = heroes.party
                            offset = 0
                        else:
                            targets = self.current_encounter.enemies
                            offset = len(heroes.party)
                    # targeted are entities that exist and are in the mask
                    targeted = [
                        to_mask[i] if i < len(targets) else 0
                        for i in range(len(targets))
                    ]
                    # save the indices of targeted entities for each attack
                    self.targets_by_action.append(
                        [offset + i for i, v in enumerate(targeted) if v == 1]
                    )
                    action.active = sum(targeted) > 0
                else:
                    self.targets_by_action.append([])
            else:
                self.targets_by_action.append([])

    def process_attack(self, heroes: HeroParty, idx: int) -> None:
        action = self.actions[idx]
        action_type = get_enum_by_value(ActionType, action.type)
        positioned_entities = [*heroes.party, *self.current_encounter.enemies]

        if action_type == ActionType.MOVE:
            self.state = CombatPhase.CHOOSE_POSITION
        elif action_type == ActionType.PASS:
            msg_system.add_msg(f"<b>{self.attacker.name}</b> passes!")
            stress_system.process_pass(attacker=self.attacker)
        elif action_type == ActionType.DAMAGE:
            for target_idx in self.targets_by_action[idx]:
                target = positioned_entities[target_idx]
                do_hit = (
                    1
                    if random.random() < max(0.0, action.accuracy - target.dodge)
                    else 0
                )
                hyp_dmg = int(action.base_dmg * (1 - target.prot))
                if do_hit:
                    dmg_taken = hyp_dmg
                    target.hp -= dmg_taken
                    msg_system.add_msg(
                        f"<b>{self.attacker.name}</b>: {action.name} <i>{dmg_taken}</i> damage dealt to <b>{target.name}</b>!"
                    )
                    stress_system.process_damage(dmg=dmg_taken, attacker=self.attacker)
                    if action.modifier is not None:
                        ModifierSystem.try_add_modifier(target, action.modifier)
                else:
                    msg_system.add_msg(
                        f"<b>{self.attacker.name}</b>: {action.name} at {target.name} but misses!"
                    )
                    stress_system.process_miss(hyp_dmg=hyp_dmg, attacker=self.attacker)
        elif action_type == ActionType.HEAL:
            for target_idx in self.targets_by_action[idx]:
                target = positioned_entities[target_idx]
                heal = min(target.max_hp - target.hp, -action.base_dmg)
                target.hp += heal
                msg_system.add_msg(
                    f"<b>{self.attacker.name}</b>: {action.name} heals <b>{target.name}</b> by <i>{heal}</i>!"
                )
                stress_system.process_heal(heal=heal, entity=target)
                if action.modifier is not None:
                    ModifierSystem.try_add_modifier(target, action.modifier)

    def process_move(self, heroes: HeroParty, target_idx: int) -> None:
        positioned_entities = [*heroes.party, *self.current_encounter.enemies]
        target = positioned_entities[target_idx]

        if target.name != self.attacker.name:
            if self.attacker.__class__ == target.__class__:
                msg_system.add_msg(
                    f"<b>{self.attacker.name}</b> moves in <b>{target.name}</b> position!"
                )
                l = (
                    heroes.party
                    if isinstance(self.attacker, Hero)
                    else self.current_encounter.enemies
                )
                l.insert(l.index(target), l.pop(l.index(self.attacker)))
                stress_system.process_move(self.attacker)
                self.state = CombatPhase.PICK_ATTACK
            else:
                msg_system.add_msg(
                    f"<b>{self.attacker.name}</b> can only move within its party!"
                )

    def try_cancel_move(self, action_idx: int) -> None:
        action = self.actions[action_idx]
        action_type = get_enum_by_value(ActionType, action.type)
        if action_type == ActionType.MOVE:
            self.state = CombatPhase.PICK_ATTACK

    def process_dead(self, dead_entities: List[Union[Hero, Enemy]]):
        for entity in dead_entities:
            self.sorted_entities.remove(entity)
