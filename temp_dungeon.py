from level import *

dungeon = Level()

dungeon.try_add_room(room_name='Clocktower Observatory',
                     room_description='A towering structure equipped with telescopes and gears, offering a panoramic view of the surrounding sky.')
dungeon.try_add_room(room_name='Forgotten Throne Room',
                     room_description='A grand hall adorned with coral and pearls, where the ghostly echoes of an ancient ruler still linger.',
                     room_from='Clocktower Observatory')
dungeon.try_add_room(room_name='Goblin Market',
                     room_description='A bustling marketplace where mischievous goblins barter and trade stolen treasures under the watchful eyes of their queen.',
                     room_from='Clocktower Observatory')
dungeon.try_add_room(room_name='Shadowy Thicket',
                     room_description='A dense forest shrouded in darkness, where twisted trees and thorns conceal hidden dangers.',
                     room_from='Clocktower Observatory')
dungeon.try_add_room(room_name='Sunken Library',
                     room_description='An underwater chamber containing ancient scrolls and artifacts, guarded by spectral guardians.',
                     room_from='Clocktower Observatory')
dungeon.try_add_room(room_name='Corporate Skyscraper',
                     room_description='A towering edifice controlled by powerful corporations, filled with security checkpoints and automated defenses.',
                     room_from='Shadowy Thicket')

dungeon.get_corridor(room_from_name='Clocktower Observatory', room_to_name='Forgotten Throne Room').length = 3
dungeon.get_corridor(room_from_name='Clocktower Observatory', room_to_name='Sunken Library').length = 3
dungeon.get_corridor(room_from_name='Shadowy Thicket', room_to_name='Corporate Skyscraper').length = 4

for corridor in dungeon.corridors:
	corridor.sprite = 'N/A'

dungeon.rooms['Clocktower Observatory'].sprite = 'assets/temp_dungeon/clocktower observatory.png'
dungeon.rooms['Forgotten Throne Room'].sprite = 'assets/temp_dungeon/forgotten throne room.png'
dungeon.rooms['Goblin Market'].sprite = 'assets/temp_dungeon/goblin market.png'
dungeon.rooms['Shadowy Thicket'].sprite = 'assets/temp_dungeon/shadowy thicket.png'
dungeon.rooms['Sunken Library'].sprite = 'assets/temp_dungeon/sunken library.png'
dungeon.rooms['Corporate Skyscraper'].sprite = 'assets/temp_dungeon/corporate skyscraper.png'

dungeon.rooms['Clocktower Observatory'].encounter.try_add_entity(entity=Enemy(name='Banshee',
                                                                              description='Ghostly apparitions wailing mournful cries, capable of inflicting fear and despair with their haunting presence.',
                                                                              sprite='assets/temp_dungeon/banshee banshee_Clocktower Observatory_semantic_and_image_context.png',
                                                                              species='Ghost',
                                                                              hp=10,
                                                                              dodge=2,
                                                                              prot=0.1,
                                                                              spd=2,
                                                                              attacks=[
	                                                                              Attack(name='Wail of Despair',
	                                                                                     description="A banshee's wail that pierces the souls of those in its path, causing deep fear and reducing the morale of the targets.",
	                                                                                     starting_positions='XXOO',
	                                                                                     target_positions='XOOX',
	                                                                                     base_dmg=3),
	                                                                              Attack(name='Ethereal Slash',
	                                                                                     description='Ghostly claws swipe through the air, inflicting both physical and psychological wounds to those they hit.',
	                                                                                     starting_positions='XXOO',
	                                                                                     target_positions='OOXX',
	                                                                                     base_dmg=5),
                                                                              ]))
dungeon.rooms['Clocktower Observatory'].encounter.try_add_entity(entity=Enemy(name='Hacktivist Hacker',
                                                                              description='Skilled hackers fighting against corporate oppression, capable of infiltrating systems and disabling security measures.',
                                                                              sprite='assets/temp_dungeon/hacktivist hacker_Clocktower Observatory_semantic_and_image_context.png',
                                                                              species='Humanoid',
                                                                              hp=10,
                                                                              dodge=1,
                                                                              prot=0.05,
                                                                              spd=3,
                                                                              attacks=[
	                                                                              Attack(name='Data Spike',
	                                                                                     description="Injects malicious code into the target’s system, causing immediate and severe damage to the infrastructure.",
	                                                                                     target_positions='OOXX',
	                                                                                     starting_positions='XXOO',
	                                                                                     base_dmg=6),
                                                                              ]))
dungeon.rooms['Clocktower Observatory'].encounter.try_add_entity(entity=Enemy(name='Mummy Priest',
                                                                              description='Undead priests skilled in dark rituals and ancient curses, capable of draining the life force of their foes.',
                                                                              sprite='assets/temp_dungeon/mummy priest_Clocktower Observatory_semantic_and_image_context.png',
                                                                              species='Zombie',
                                                                              hp=20,
                                                                              dodge=3,
                                                                              prot=0.2,
                                                                              spd=1,
                                                                              attacks=[
	                                                                              Attack(name='Curse of the Pharaoh',
	                                                                                     description="An ancient curse that drains the life force of those afflicted, weakening their physical and magical abilities.",
	                                                                                     target_positions='XOXO',
	                                                                                     starting_positions='XXOO',
	                                                                                     base_dmg=3),
	                                                                              Attack(name='Sandstorm Shroud',
	                                                                                     description="Summons a swirling sandstorm that obscures vision and chokes enemies, making it difficult for them to act.",
	                                                                                     target_positions='OXOX',
	                                                                                     starting_positions='XXOO',
	                                                                                     base_dmg=2),
	                                                                              Attack(name='Ankh\'s Drain',
	                                                                                     description="Channels dark energy through an ankh, siphoning health from the targets to heal the mummy priest.",
	                                                                                     target_positions='XXOO',
	                                                                                     starting_positions='XXOO',
	                                                                                     base_dmg=2),
                                                                              ]))

dungeon.rooms['Forgotten Throne Room'].encounter.try_add_entity(entity=Enemy(name='Spectral Guardian',
                                                                             description='Ethereal beings tasked with protecting the secrets of atlantis, wielding energy beams and teleportation.',
                                                                             sprite='assets/temp_dungeon/spectral guardian_Forgotten Throne Room_semantic_and_image_context.png',
                                                                             species='Ghost',
                                                                             hp=15,
                                                                             dodge=4,
                                                                             prot=0.3,
                                                                             spd=5,
                                                                             attacks=[
	                                                                             Attack(name='Phantom Step',
	                                                                                    description="Teleports behind enemies and strikes from the shadows, catching them off guard and dealing heavy damage.",
	                                                                                    target_positions='OXOX',
	                                                                                    starting_positions='XXOO',
	                                                                                    base_dmg=7),
	                                                                             Attack(name='Atlantian Shield',
	                                                                                    description="Projects a shield of ethereal energy that absorbs incoming attacks, protecting allies in the adjacent slots.",
	                                                                                    target_positions='OXXO',
	                                                                                    starting_positions='XXOO',
	                                                                                    base_dmg=2),
                                                                             ]))
dungeon.rooms['Forgotten Throne Room'].encounter.try_add_entity(entity=Enemy(name='Luminescent Jellyfin Swarm',
                                                                             description='Bioluminescent creatures that stun their prey with electric shocks, attacking in large groups.',
                                                                             sprite='assets/temp_dungeon/luminescent jellyfish swarm_Forgotten Throne Room_semantic_and_image_context.png',
                                                                             species='Fish',
                                                                             hp=10,
                                                                             dodge=2,
                                                                             prot=0.4,
                                                                             spd=2,
                                                                             attacks=[
	                                                                             Attack(name='Electric Shock',
	                                                                                    description="A coordinated shock from multiple jellyfins, stunning and paralyzing the targets for a short duration.",
	                                                                                    target_positions='XXOO',
	                                                                                    starting_positions='XXOO',
	                                                                                    base_dmg=4),
	                                                                             Attack(name='Blinding Flash',
	                                                                                    description="Emits a burst of bright bioluminescence that blinds enemies, reducing their accuracy and reaction time.",
	                                                                                    target_positions='OXOX',
	                                                                                    starting_positions='XXOO',
	                                                                                    base_dmg=1),
	                                                                             Attack(name='Swarm Surge',
	                                                                                    description="A collective surge forward that overwhelms the targets with sheer numbers, inflicting cumulative damage.",
	                                                                                    target_positions='XOXO',
	                                                                                    starting_positions='XXOO',
	                                                                                    base_dmg=4),
                                                                             ]))

dungeon.current_room = ('Clocktower Observatory')

with open('./assets/temp_dungeon/dungeon_data.json', 'w') as f:
	f.write(dungeon.model_dump_json())

# for room_name in dungeon.rooms.keys():
#     for enemy in dungeon.rooms[room_name].encounter.entities['enemy']:
#         print(f'{enemy.name}: {enemy.description}')
