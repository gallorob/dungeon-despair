import json
import random
from typing import List, Optional, Tuple
from dungeon_despair.domain.attack import Attack
from dungeon_despair.domain.entities.hero import Hero
from dungeon_despair.domain.modifier import Modifier
from dungeon_despair.domain.utils import ActionType, ModifierType, get_enum_by_value
from pydantic import ValidationError

from configs import configs
from dungeon_despair.domain.configs import config as ddd_config

from server_utils import convert_and_save, send_to_server


def generate_sprite(name: str,
					description: str) -> str:
	data = {
		'hero_name': name,
		'hero_description': description,
	}
	res = send_to_server(data=data, endpoint='dd_generate_hero')
	return convert_and_save(b64_img=res['image_base64'], fname=res['fname'], dirname=configs.assets.dungeon_dir)


def get_heromakingtools():
	from gptfunctionutil import AILibFunction, GPTFunctionLibrary, LibParam, LibParamSpec

	class HeroMakingTools(GPTFunctionLibrary):
		def try_call_func(self,
						func_name: str,
						func_args: str) -> str:
			if isinstance(func_args, str):
				func_args = json.loads(func_args)
			try:
				operation_result = self.call_by_dict({
					'name': func_name,
					'arguments': {
						**func_args
					}
				})
				return operation_result
			except AssertionError as e:
				return f'Domain validation error: {e}'
			except AttributeError as e:
				return f'Function {func_name} not found.'
			except TypeError as e:
				return f'Missing arguments: {e}'
		
		@AILibFunction(name='make_hero', description='Create a hero.',
					required=['name', 'description', 'hp', 'dodge', 'prot', 'spd', 'trap_resist', 'stress_resist', 'attacks'])
		@LibParamSpec(name='name', description='The unique name of the hero')
		@LibParamSpec(name='description', description='The physical description of the hero')
		@LibParamSpec(name='hp', description=f'The health points of the hero, must be a value must be between {ddd_config.min_hp} and {ddd_config.max_hp}.')
		@LibParamSpec(name='dodge', description=f'The dodge points of the hero, must be a value must be between {ddd_config.min_dodge} and {ddd_config.max_dodge}.')
		@LibParamSpec(name='prot', description=f'The protection points of the hero, must be a value must be between {ddd_config.min_prot} and {ddd_config.max_prot}.')
		@LibParamSpec(name='spd', description=f'The speed points of the hero, must be a value must be between {ddd_config.min_spd} and {ddd_config.max_spd}.')
		@LibParamSpec(name='trap_resist', description=f'The chance this hero will not trigger traps, must be a value must be between 0.0 and 1.0.')
		@LibParamSpec(name='stress_resist', description=f'The percentage resistance of the hero to stress, must be a value must be between 0.0 and 1.0.')
		def make_hero(self, 
					name: str,
					description: str,
					hp: float,
					dodge: float,
					prot: float,
					spd: float,
					trap_resist: float,
					stress_resist: float) -> Hero:
			assert name != '', 'Hero name should be provided.'
			assert description != '', 'Hero description should be provided.'
			assert ddd_config.min_hp <= hp <= ddd_config.max_hp, f'Invalid hp value: {hp}; should be between {ddd_config.min_hp} and {ddd_config.max_hp}.'
			assert ddd_config.min_dodge <= dodge <= ddd_config.max_dodge, f'Invalid dodge value: {dodge}; should be between {ddd_config.min_dodge} and {ddd_config.max_dodge}.'
			assert ddd_config.min_prot <= prot <= ddd_config.max_prot, f'Invalid prot value: {prot}; should be between {ddd_config.min_prot} and {ddd_config.max_prot}.'
			assert ddd_config.min_spd <= spd <= ddd_config.max_spd, f'Invalid spd value: {spd}; should be between {ddd_config.min_spd} and {ddd_config.max_spd}.'
			assert 0.0 <= trap_resist <= 1.0, f'Invalid trap_resist value: {trap_resist}; should be between 0.0 and 1.0.'
			assert 0.0 <= stress_resist <= 1.0, f'Invalid trastress_resistp_resist value: {stress_resist}; should be between 0.0 and 1.0.'
			hero = Hero(name=name, description=description, hp=hp, dodge=dodge, prot=prot, spd=spd, trap_resist=trap_resist, stress_resist=stress_resist, max_hp=hp, type="hero")
			return hero

		@AILibFunction(name='add_attack', description='Add an attack to a hero.',
					required=['name', 'description', 'starting_positions', 'target_positions', 'base_dmg', 'modifier_type', 'modifier_chance', 'modifier_turns', 'modifier_amount'])
		@LibParam(name='The unique name of the attack.')
		@LibParam(description='The description of the attack.')
		@LibParam(attack_type='The attack type: must be one of "damage" or "heal".')
		@LibParam(starting_positions='A string of 4 characters describing the positions from which the attack can be executed. Use "X" where the attack can be executed from, and "O" otherwise.')
		@LibParam(target_positions='A string of 4 characters describing the positions that the attack strikes to. Use "X" where the attack strikes to, and "O" otherwise.')
		@LibParam(base_dmg=f'The base damage of the attack. Must be between {ddd_config.min_base_dmg} and {ddd_config.max_base_dmg}.')
		@LibParam(accuracy='The attack accuracy (a percentage between 0.0 and 1.0).')
		@LibParam(modifier_type=f'The type of modifier this attack applies when triggered. Set to "no-modifier" if no modifier should be applied, else set it to one of {", ".join([x.value for x in ModifierType])}.')
		@LibParam(modifier_chance='The chance that the modifier is applied to a target (between 0.0 and 1.0)')
		@LibParam(modifier_turns='The number of turns the modifier is active for')
		@LibParam(modifier_amount=f'The amount the modifier applies. If the modifier is "bleed" or "heal", the value must be between {ddd_config.min_base_dmg} and {ddd_config.max_base_dmg}, otherwise it must be between 0.0 and 1.0.')
		def add_attack(self, 
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
					modifier_amount: float) -> Attack:
			assert name != '', f'Attack name should be specified.'
			assert description != '', f'Attack description should be specified.'
			assert modifier_type != '', 'Attack modifier type should be provided.'
			assert modifier_chance is not None, 'Attack modifier chance should be provided.'
			assert modifier_turns is not None, 'Attack modifier turns should be provided.'
			assert modifier_amount is not None, 'Attack modifier amount should be provided.'
			type_enum = get_enum_by_value(ActionType, attack_type)
			assert type_enum is not None, f'Attack type "{attack_type}" is not a valid type: it must be one of {", ".join([t.value for t in ActionType])}.'
			if type_enum == ActionType.DAMAGE:
				assert ddd_config.min_base_dmg <= base_dmg <= ddd_config.max_base_dmg, f'Invalid base_dmg value: {base_dmg}; should be between {ddd_config.min_base_dmg} and {ddd_config.max_base_dmg}.'
			else:  # type is HEAL
				assert -ddd_config.max_base_dmg <= base_dmg <= -ddd_config.min_base_dmg, f'Invalid base_dmg value: {base_dmg}; should be between {-ddd_config.max_base_dmg} and {-ddd_config.min_base_dmg}.'
			assert 0.0 <= accuracy <= 1.0, f'Invalid accuracy: must be between 0.0 and 1.0'
			assert len(starting_positions) == 4, f'Invalid starting_positions value: {starting_positions}. Must be 4 characters long.'
			assert len(target_positions) == 4, f'Invalid target_positions value: {target_positions}. Must be 4 characters long.'
			assert set(starting_positions).issubset({'X', 'O'}), f'Invalid starting_positions value: {starting_positions}. Must contain only "X" and "O" characters.'
			assert set(target_positions).issubset({'X', 'O'}), f'Invalid target_positions value: {target_positions}. Must contain only "X" and "O" characters.'
			attack = Attack(name=name, description=description,
							type=type_enum,
							starting_positions=starting_positions, target_positions=target_positions,
							base_dmg=base_dmg, accuracy=accuracy)
			if modifier_type != 'no-modifier':
				assert modifier_type in [x.value for x in ModifierType], f'Could not add attack: {modifier_type} is not a valid modifier type.'
				assert 0.0 <= modifier_chance <= 1.0, f'modifier_chance must be a value between 0.0 and 1.0; you passed {modifier_chance}.'
				assert modifier_turns >= 0, f'modifier_turns must be a positive value; you passed {modifier_turns}.'
				if modifier_type in [ModifierType.BLEED.value, ModifierType.HEAL.value]:
					assert ddd_config.min_base_dmg <= modifier_amount <= ddd_config.max_base_dmg, f'Invalid modifier_amount value: {modifier_amount}; should be between {ddd_config.min_base_dmg} and {ddd_config.max_base_dmg}.'
				elif modifier_type == ModifierType.SCARE.value:
					assert 0.0 <= modifier_amount <= 1.0, f'Invalid modifier_amount value: {modifier_amount}; should be between 0.0 and 1.0.'
				attack.modifier = Modifier(type=modifier_type, chance=modifier_chance, turns=modifier_turns, amount=modifier_amount)
			return attack

	return HeroMakingTools()


def generate_hero(n_attacks: int,
				  difficulty: str,
				  curr_heroes: List[Hero]) -> Hero:
	tool_lib = get_heromakingtools()

	options = {
		'temperature': configs.gen.temperature,
		'top_p': configs.gen.top_p,
		'top_k': configs.gen.top_k,
		# 'seed': configs.rng_seed,
		'num_ctx': 32768 * 3
	}

	curr_heroes_str = '\n'.join([hero.model_dump_json() for hero in curr_heroes])
	curr_heroes_str = curr_heroes_str.replace('"modifier":null', ',"modifier_type":"no-modifier","modifier_chance":0.0,"modifier_turns":0,"modifier_amount":0.0')
	curr_heroes_str = curr_heroes_str.replace('"sprite":null', '"sprite":""')

	formatted_usrmsg = configs.gen.llm_usrmsg.format(n_attacks=n_attacks,
												  	 difficult=difficulty)
	hero = None
	while hero is None or len(hero.attacks) != n_attacks:
		# print('New session...')
		with open(configs.gen.llm_sysprompt, 'r') as f:
			sysprompt = f.read()
		sysprompt = sysprompt.replace('$curr_heroes$', curr_heroes_str)
		if hero:
			sysprompt = sysprompt.replace('$current_hero$', hero.model_dump_json())
		else:
			sysprompt = sysprompt.replace('$current_hero$', 'There is no current hero.')
		messages = [
			{'role': 'system', 'content': sysprompt},
			{'role': 'user', 'content': formatted_usrmsg},
		]
		# print(f'{messages=}')
		res = send_to_server(data={
									 'model_name': configs.gen.llm_model,
									 'messages': messages,
									 'stream': False,
									 'options': options,
									 'tools': tool_lib.get_tool_schema()
								 },
							 endpoint='ollama_generate')
		# print(f'{res=}')
		if res['message'].get('tool_calls'):
			for tool in res['message']['tool_calls']:
				func_name = tool['function']['name']
				func_args = tool['function']['arguments']
				output = tool_lib.try_call_func(func_name=func_name,
												func_args=func_args)
				# print(f'{output=}')
				if isinstance(output, Hero):
					hero = output
				elif isinstance(output, Attack):
					if hero is not None:
						hero.attacks.append(output)
				else:
					messages.append({'role': 'tool', 'content': output})

	return hero



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


def scale_difficulty(wave_n: int) -> Tuple[int, int, str]:
	# Difficulty increaseas every cycle, number of heroes increases within cycle with small variations, number of attacks is random 1-4
	difficulty = min(wave_n // configs.game.diff_cycle, len(configs.game.difficulties))
	local_wave = wave_n % configs.game.diff_cycle
	base_hero_count = 1 + (local_wave * ddd_config.max_enemies_per_encounter) // configs.game.diff_cycle
	num_heroes = min(base_hero_count + random.choice([0, 1]), ddd_config.max_enemies_per_encounter)
	n_attacks = random.choice(range(4)) + 1
	return num_heroes, n_attacks, configs.game.difficulties[difficulty]


def generate_new_party(wave_n: int) -> HeroParty:
	party = HeroParty()
	num_heroes, n_attacks, difficulty = scale_difficulty(wave_n=wave_n) 
	for i in range(num_heroes):
		print(f"Generating hero {i + 1} / {wave_n + 1} ({n_attacks=}, {difficulty=})...")
		hero = generate_hero(n_attacks=n_attacks, difficulty=difficulty)
		hero.sprite = generate_sprite(name=hero.name, description=hero.description)
		party.party.append(hero)
	return party



def get_temp_heroes():
	heroes = HeroParty()
	heroes.party = [
		Hero(name='Gareth Ironclad',
		     description='A tall, muscular human fighter with short dark hair, a well-trimmed beard, and piercing blue eyes. He wears polished plate armor with a large sword and a shield with a family crest.',
		     sprite='assets/base_heroes/gareth ironclad.png',
		     hp=15.0,
		     dodge=0.1,
		     prot=0.8,
		     spd=0.2,
		     trap_resist=0.1,
		     stress_resist=0.0,
		     # modifiers=[Modifier(type=ModifierType.BLEED,
		     #                     chance=1.0,
		     #                     turns=-1,
		     #                     amount=1.0)],
		     attacks=[
			     Attack(name='Blade of Valor',
			            description='Gareth swings his large sword in a powerful arc.',
			            type=ActionType.DAMAGE,
			            target_positions='XXOX',
			            starting_positions='OOXX',
			            base_dmg=13.0,
			            accuracy=2.0),
			     Attack(name='Shield Bash',
			            description='Gareth slams his shield into his enemy, stunning them.',
			            type=ActionType.DAMAGE,
			            target_positions='OXXO',
			            starting_positions='OOXX',
			            base_dmg=11.0,
			            accuracy=2.0),
			     Attack(name='Heroic Charge',
			            description='Gareth charges forward with his sword, hitting multiple foes.',
			            type=ActionType.DAMAGE,
			            target_positions='XXOX',
			            starting_positions='OOXX',
			            base_dmg=14.0,
			            accuracy=2.0)
		     ]),
		Hero(name='Elira Moonwhisper',
		     description='A small gnome priest with long wavy silver hair, large emerald eyes, and luminescent skin. She wears flowing white and gold robes with intricate patterns and a glowing crystal pendant.',
		     sprite='assets/base_heroes/elira moonwhisper.png',
		     hp=8.0,
		     dodge=0.2,
		     prot=0.2,
		     spd=0.1,
		     trap_resist=0.1,
		     stress_resist=0.0,
		     # modifiers=[Modifier(type=ModifierType.BLEED,
		     #                     chance=1.0,
		     #                     turns=-1,
		     #                     amount=1.0)],
		     modifiers=[Modifier(type=ModifierType.STUN,
		                         chance=1.0,
		                         turns=3,
		                         amount=0.0),
		                Modifier(type=ModifierType.HEAL,
		                         chance=1.0,
		                         turns=2,
		                         amount=4.0)
		                ],
		     attacks=[
			     Attack(name='Divine Light',
			            description='Elira calls down a beam of holy light to smite her enemies.',
			            type=ActionType.DAMAGE,
			            target_positions='XOXO',
			            starting_positions='OOXX',
			            base_dmg=12.0,
			            accuracy=2.0),
			     Attack(name='Healing Wave',
			            description='Elira sends out a wave of healing energy, revitalizing allies and harming undead foes.',
			            type=ActionType.HEAL,
			            target_positions='XOOX',
			            starting_positions='OOXX',
			            base_dmg=-11.0,
			            accuracy=2.0),
			     Attack(name='Holy Smite',
			            description='Elira conjures a burst of divine energy that targets the wicked.',
			            type=ActionType.DAMAGE,
			            target_positions='OXOX',
			            starting_positions='OOXX',
			            base_dmg=12.0,
			            accuracy=2.0)
		     ]),
		Hero(name='Aelarion Starfire',
		     description='A tall, slender elf mage with long platinum blonde hair, violet eyes, and pale skin. He wears a deep blue robe with silver runes, carrying a carved staff and a spellbook.',
		     sprite='assets/base_heroes/aelarion starfire.png',
		     hp=10.0,
		     dodge=0.1,
		     prot=0.2,
		     spd=2.0,
		     trap_resist=0.1,
		     stress_resist=0.0,
		     # modifiers=[Modifier(type=ModifierType.BLEED,
		     #                     chance=1.0,
		     #                     turns=-1,
		     #                     amount=1.0)],
		     attacks=[
			     Attack(name='Arcane Blast',
			            description='Aelarion unleashes a burst of arcane energy from his staff.',
			            type=ActionType.DAMAGE,
			            target_positions='OXOX',
			            starting_positions='OOXX',
			            base_dmg=12.0,
			            accuracy=2.0),
			     Attack(name='Fireball',
			            description='Aelarion hurls a fiery ball that explodes on impact.',
			            type=ActionType.DAMAGE,
			            target_positions='XXOO',
			            starting_positions='OOXX',
			            base_dmg=15.0,
			            accuracy=2.0),
			     Attack(name='Frost Nova',
			            description='Aelarion releases a wave of frost, freezing enemies in place.',
			            type=ActionType.DAMAGE,
			            target_positions='OXOX',
			            starting_positions='OOXX',
			            base_dmg=11.0,
			            accuracy=2.0)
		     ]),
		Hero(name='Milo Underfoot',
		     description='A small, nimble hobbit thief with short curly brown hair, bright hazel eyes, and tanned skin. He dresses in dark colors with many pockets and moves with silent grace.',
		     sprite='assets/base_heroes/milo underfoot.png',
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
			            type=ActionType.DAMAGE,
			            target_positions='OXOX',
			            starting_positions='OOXX',
			            base_dmg=13.0,
			            accuracy=2.0),
			     Attack(name='Sneak Attack',
			            description='Milo sneaks up on his target, delivering a precise and deadly blow.',
			            type=ActionType.DAMAGE,
			            target_positions='XOOX',
			            starting_positions='OOXX',
			            base_dmg=15.0,
			            accuracy=2.0),
			     Attack(name='Smoke Bomb',
			            description='Milo throws a smoke bomb, disorienting his enemies and allowing for a quick strike.',
			            type=ActionType.DAMAGE,
			            target_positions='XOXO',
			            starting_positions='OOXX',
			            base_dmg=11.0,
			            accuracy=2.0)
		     ]),
	]
	return heroes


if __name__ == '__main__':
	p = get_temp_heroes()
	print(p.party[0].model_dump_json())