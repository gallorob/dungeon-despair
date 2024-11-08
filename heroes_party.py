from dungeon_despair.domain.attack import Attack
from dungeon_despair.domain.entities.hero import Hero
from dungeon_despair.domain.modifier import Modifier
from dungeon_despair.domain.utils import AttackType, ModifierType


class HeroParty:
	def __init__(self):
		self.party = []
	
	def get_party_description(self) -> str:
		s = 'This is the heroes party:'
		for hero in self.party:
			hero_str = f'\n{hero.name}: {hero.description} (HP={hero.hp} DODGE={hero.dodge} PROT={hero.prot} SPD={hero.spd})'
			s += hero_str
		s += '\n'
		return s
	
	def get_party_status(self) -> str:
		s = 'This is the current heroes party status:'
		for hero in self.party:
			hero_str = f'\n{hero.name}: {hero.hp} HP'
			s += hero_str
		s += '\n'
		return s


def get_temp_heroes():
	heroes = HeroParty()
	heroes.party = [
		Hero(name='Gareth Ironclad',
		     description='A tall, muscular human fighter with short dark hair, a well-trimmed beard, and piercing blue eyes. He wears polished plate armor with a large sword and a shield with a family crest.',
		     sprite='assets/gareth ironclad.png',
		     hp=15.0,
		     dodge=0.1,
		     prot=0.8,
		     spd=0.2,
		     trap_resist=0.1,
		     stress_resist=0.0,
		     modifiers=[Modifier(type=ModifierType.BLEED,
		                         chance=1.0,
		                         turns=-1,
		                         amount=1.0)],
		     attacks=[
			     Attack(name='Blade of Valor',
			            description='Gareth swings his large sword in a powerful arc.',
			            type=AttackType.DAMAGE,
			            target_positions='XXOX',
			            starting_positions='OOXX',
			            base_dmg=3.0,
			            accuracy=0.5),
			     Attack(name='Shield Bash',
			            description='Gareth slams his shield into his enemy, stunning them.',
			            type=AttackType.DAMAGE,
			            target_positions='OXXO',
			            starting_positions='OOXX',
			            base_dmg=1.0,
			            accuracy=0.5),
			     Attack(name='Heroic Charge',
			            description='Gareth charges forward with his sword, hitting multiple foes.',
			            type=AttackType.DAMAGE,
			            target_positions='XXOX',
			            starting_positions='OOXX',
			            base_dmg=4.0,
			            accuracy=0.5)
		     ]),
		Hero(name='Elira Moonwhisper',
		     description='A small gnome priest with long wavy silver hair, large emerald eyes, and luminescent skin. She wears flowing white and gold robes with intricate patterns and a glowing crystal pendant.',
		     sprite='assets/elira moonwhisper.png',
		     hp=8.0,
		     dodge=0.2,
		     prot=0.2,
		     spd=0.1,
		     trap_resist=0.1,
		     stress_resist=0.0,
		     modifiers=[Modifier(type=ModifierType.BLEED,
		                         chance=1.0,
		                         turns=-1,
		                         amount=1.0)],
		     # modifiers=[Modifier(type=ModifierType.STUN,
		     #                     chance=1.0,
		     #                     turns=3,
		     #                     amount=0.0),
		     #            Modifier(type=ModifierType.HEAL,
		     #                     chance=1.0,
		     #                     turns=2,
		     #                     amount=4.0)
		     #            ],
		     attacks=[
			     Attack(name='Divine Light',
			            description='Elira calls down a beam of holy light to smite her enemies.',
			            type=AttackType.DAMAGE,
			            target_positions='XOXO',
			            starting_positions='OOXX',
			            base_dmg=2.0,
			            accuracy=0.5),
			     Attack(name='Healing Wave',
			            description='Elira sends out a wave of healing energy, revitalizing allies and harming undead foes.',
			            type=AttackType.HEAL,
			            target_positions='XOOX',
			            starting_positions='OOXX',
			            base_dmg=-1.0,
			            accuracy=0.5),
			     Attack(name='Holy Smite',
			            description='Elira conjures a burst of divine energy that targets the wicked.',
			            type=AttackType.DAMAGE,
			            target_positions='OXOX',
			            starting_positions='OOXX',
			            base_dmg=2.0,
			            accuracy=0.5)
		     ]),
		Hero(name='Aelarion Starfire',
		     description='A tall, slender elf mage with long platinum blonde hair, violet eyes, and pale skin. He wears a deep blue robe with silver runes, carrying a carved staff and a spellbook.',
		     sprite='assets/aelarion starfire.png',
		     hp=10.0,
		     dodge=0.1,
		     prot=0.2,
		     spd=0.5,
		     trap_resist=0.1,
		     stress_resist=0.0,
		     modifiers=[Modifier(type=ModifierType.BLEED,
		                         chance=1.0,
		                         turns=-1,
		                         amount=1.0)],
		     attacks=[
			     Attack(name='Arcane Blast',
			            description='Aelarion unleashes a burst of arcane energy from his staff.',
			            type=AttackType.DAMAGE,
			            target_positions='OXOX',
			            starting_positions='OOXX',
			            base_dmg=2.0,
			            accuracy=0.5),
			     Attack(name='Fireball',
			            description='Aelarion hurls a fiery ball that explodes on impact.',
			            type=AttackType.DAMAGE,
			            target_positions='XXOO',
			            starting_positions='OOXX',
			            base_dmg=5.0,
			            accuracy=0.5),
			     Attack(name='Frost Nova',
			            description='Aelarion releases a wave of frost, freezing enemies in place.',
			            type=AttackType.DAMAGE,
			            target_positions='OXOX',
			            starting_positions='OOXX',
			            base_dmg=1.0,
			            accuracy=0.5)
		     ]),
		Hero(name='Milo Underfoot',
		     description='A small, nimble hobbit thief with short curly brown hair, bright hazel eyes, and tanned skin. He dresses in dark colors with many pockets and moves with silent grace.',
		     sprite='assets/milo underfoot.png',
		     hp=6.0,
		     dodge=0.9,
		     prot=0.2,
		     spd=0.8,
		     trap_resist=0.1,
		     stress_resist=0.0,
		     # modifiers=[Modifier(type=ModifierType.BLEED,
		     #                     chance=1.0,
		     #                     turns=-1,
		     #                     amount=1.0)],
		     # modifiers=[Modifier(type=ModifierType.SCARE,
		     #                     chance=1.0,
		     #                     turns=-1,
		     #                     amount=0.25)],
		     attacks=[
			     Attack(name='Shadow Strike',
			            description='Milo darts through the shadows, striking from an unexpected angle.',
			            type=AttackType.DAMAGE,
			            target_positions='OXOX',
			            starting_positions='OOXX',
			            base_dmg=3.0,
			            accuracy=0.5),
			     Attack(name='Sneak Attack',
			            description='Milo sneaks up on his target, delivering a precise and deadly blow.',
			            type=AttackType.DAMAGE,
			            target_positions='XOOX',
			            starting_positions='OOXX',
			            base_dmg=5.0,
			            accuracy=0.5),
			     Attack(name='Smoke Bomb',
			            description='Milo throws a smoke bomb, disorienting his enemies and allowing for a quick strike.',
			            type=AttackType.DAMAGE,
			            target_positions='XOXO',
			            starting_positions='OOXX',
			            base_dmg=1.0,
			            accuracy=0.5)
		     ]),
	]
	return heroes
