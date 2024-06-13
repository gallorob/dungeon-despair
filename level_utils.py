import os.path
import random

from PIL.Image import Image
from datetime import datetime

from level import *
import pickle as pkl
from configs import configs


def _get_rand_atk() -> Attack:
	atk_name = datetime.now().strftime("%Y%m%d%H%M%S")
	starting_pos = ''.join(['X' if random.random() < 0.5 else 'O' for _ in range(4)])
	target_pos = ''.join(['X' if random.random() < 0.5 else 'O' for _ in range(4)])
	base_dmg = 1 + random.randint(1, 3)

	return Attack(name=atk_name,
	              description="A random attack because this has yet to be implemented 😅",
	              starting_positions=starting_pos,
	              target_positions=target_pos,
	              base_dmg=base_dmg)


def load_level(filename: str) -> Level:
	with open(filename, 'rb') as f:
		data = pkl.load(f)
	
	# load level data
	level = data['level']
	# TEMPORARY: fix sprites location
	for room in level.rooms.values():
		room.sprite = room.sprite.split('/')[-1]
	for corridor in level.corridors:
		corridor.sprite = corridor.sprite.split('/')[-1]
	# TEMPORARY: Add attacks to enemies
	for room in level.rooms.values():
		for i, enemy in enumerate(room.encounter.entities['enemy']):
			room.encounter.entities['enemy'][i] = Enemy(name=enemy.name,
			                                            description=enemy.description,
			                                            sprite=enemy.sprite.split('/')[-1],
			                                            species=enemy.species,
			                                            hp=enemy.hp,
			                                            dodge=enemy.dodge,
			                                            prot=enemy.prot,
			                                            spd=enemy.spd,
			                                            attacks=[_get_rand_atk() for _ in range(random.randint(1, 4))])
	
	images: Dict[str, Image] = data['images']
	for fname, img in images.items():
		img.save(os.path.join(configs.assets, 'dungeon_assets', fname.split('/')[-1]))
	
	return level
