from typing import List

from pydantic import Field

from dungeon_despair.domain.attack import Attack
from dungeon_despair.domain.entities.hero import Hero


# from level import Attack, Entity

#
# class Hero(Entity):
# 	hp: int = Field(..., description="The enemy HP.", required=True)
# 	species: str = 'Human'
# 	dodge: float = Field(..., description="The hero dodge stat.", required=True)
# 	prot: float = Field(..., description="The hero prot stat.", required=True)
# 	spd: int = Field(..., description="The hero spd stat.", required=True)
# 	attacks: List[Attack] = Field([], description='The enemy attacks', required=True)


class HeroParty:
	def __init__(self):
		self.party = []


def get_temp_heroes():
	heroes = HeroParty()
	heroes.party = [
		Hero(name='Gareth Ironclad',
		     description='A tall, muscular human fighter with short dark hair, a well-trimmed beard, and piercing blue eyes. He wears polished plate armor with a large sword and a shield with a family crest.',
		     sprite='assets/gareth ironclad.png',
		     hp=50,
		     dodge=0.8,
		     prot=0.8,
		     spd=0.2,
		     attacks=[
			     Attack(name='Blade of Valor',
			            description='Gareth swings his large sword in a powerful arc.',
			            target_positions='XXOX',
			            starting_positions='OOXX',
			            base_dmg=3),
			     Attack(name='Shield Bash',
			            description='Gareth slams his shield into his enemy, stunning them.',
			            target_positions='OXXO',
			            starting_positions='OOXX',
			            base_dmg=1),
			     Attack(name='Heroic Charge',
			            description='Gareth charges forward with his sword, hitting multiple foes.',
			            target_positions='XXOX',
			            starting_positions='OOXX',
			            base_dmg=4)
		     ]),
		Hero(name='Elira Moonwhisper',
		     description='A small gnome priest with long wavy silver hair, large emerald eyes, and luminescent skin. She wears flowing white and gold robes with intricate patterns and a glowing crystal pendant.',
		     sprite='assets/elira moonwhisper.png',
		     hp=18,
		     dodge=0.2,
		     prot=0.2,
		     spd=0.1,
		     attacks=[
			     Attack(name='Divine Light',
			            description='Elira calls down a beam of holy light to smite her enemies.',
			            target_positions='XOXO',
			            starting_positions='OOXX',
			            base_dmg=2),
			     Attack(name='Healing Wave',
			            description='Elira sends out a wave of healing energy, revitalizing allies and harming undead foes.',
			            target_positions='XOOX',
			            starting_positions='OOXX',
			            base_dmg=1),
			     Attack(name='Holy Smite',
			            description='Elira conjures a burst of divine energy that targets the wicked.',
			            target_positions='OXOX',
			            starting_positions='OOXX',
			            base_dmg=2)
		     ]),
		Hero(name='Aelarion Starfire',
		     description='A tall, slender elf mage with long platinum blonde hair, violet eyes, and pale skin. He wears a deep blue robe with silver runes, carrying a carved staff and a spellbook.',
		     sprite='assets/aelarion starfire.png',
		     hp=25,
		     dodge=0.3,
		     prot=0.3,
		     spd=0.5,
		     attacks=[
			     Attack(name='Arcane Blast',
			            description='Aelarion unleashes a burst of arcane energy from his staff.',
			            target_positions='OXOX',
			            starting_positions='OOXX',
			            base_dmg=2),
			     Attack(name='Fireball',
			            description='Aelarion hurls a fiery ball that explodes on impact.',
			            target_positions='XXOO',
			            starting_positions='OOXX',
			            base_dmg=5),
			     Attack(name='Frost Nova',
			            description='Aelarion releases a wave of frost, freezing enemies in place.',
			            target_positions='OXOX',
			            starting_positions='OOXX',
			            base_dmg=1)
		     ]),
		Hero(name='Milo Underfoot',
		     description='A small, nimble hobbit thief with short curly brown hair, bright hazel eyes, and tanned skin. He dresses in dark colors with many pockets and moves with silent grace.',
		     sprite='assets/milo underfoot.png',
		     hp=10,
		     dodge=0.9,
		     prot=0.2,
		     spd=0.8,
		     attacks=[
			     Attack(name='Shadow Strike',
			            description='Milo darts through the shadows, striking from an unexpected angle.',
			            target_positions='OXOX',
			            starting_positions='OOXX',
			            base_dmg=3),
			     Attack(name='Sneak Attack',
			            description='Milo sneaks up on his target, delivering a precise and deadly blow.',
			            target_positions='XOOX',
			            starting_positions='OOXX',
			            base_dmg=5),
			     Attack(name='Smoke Bomb',
			            description='Milo throws a smoke bomb, disorienting his enemies and allowing for a quick strike.',
			            target_positions='XOXO',
			            starting_positions='OOXX',
			            base_dmg=1)
		     ]),
	]
	return heroes
