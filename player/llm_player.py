from typing import Dict, List

from player.base_player import Player, PlayerType
import ollama

class LLMPlayer(Player):
	def __init__(self,
	             model_name: str):
		super().__init__(PlayerType.LLM)
		self.model_name = model_name
		with open('./assets/llm_player_system_prompt', 'r') as f:
			self.prompt = f.read()
		self.context = ''
		self.heroes_party_str = ''
	
	def __chat(self,
	           msgs: List[Dict[str, str]]) -> str:
		output = ollama.chat(model=self.model_name,
		                     messages=msgs)
		response = output['message']['content']
		return response
		
	def pick_attack(self,
	                attacks) -> int:
		attacks_names = [attack.name for attack in attacks]
		task_description = 'Choose one of the following:'
		task_context = f'{attacks_names}'
		prompt_copy = self.prompt.format(heroes_party_str = self.heroes_party_str,
		                                 n=len(self.context),
		                                 events_history_trimmed='\n'.join(self.context),
		                                 task_description=task_description,
		                                 task_context=task_context)
		messages = [{'role': 'user', 'content': prompt_copy}]
		response = self.__chat(messages)
		print(f'LLMPlayer.pick_attack - options={attacks_names} {response=}')
		for idx, attack in enumerate(attacks_names):
			if attack in response:
				self.context = ''
				return idx
		raise ValueError(f'LLMPlayer.pick_attack - invalid response: {response}')
	
	def pick_destination(self,
	                     destinations):
		task_description = 'Here is a list of possible destinations and their descriptions. Choose one of the following destinations:'
		prompt_copy = self.prompt.format(heroes_party_str=self.heroes_party_str,
		                                 n=len(self.context),
		                                 events_history_trimmed='\n'.join(self.context),
		                                 task_description=task_description,
		                                 task_context=destinations)
		messages = [{'role': 'user', 'content': prompt_copy}]
		response = self.__chat(messages)
		print(f'LLMPlayer.pick_destination - {destinations=} {response=}')
		for destination in destinations.split('\n')[1:]:
			destination = destination.split(':')[0].replace(':', '')
			if destination in response:
				self.context = ''
				dest_name, dest_idx = destination.split('_')[:2]
				dest_idx = int(dest_idx)
				return dest_name, dest_idx
		raise ValueError(f'LLMPlayer.pick_destination - invalid response: {response}')
	
	def choose_disarm_trap(self) -> bool:
		task_description = 'Choose one of the following:'
		task_context = "Disarm, Leave Alone"
		prompt_copy = self.prompt.format(heroes_party_str=self.heroes_party_str,
		                                 n=len(self.context),
		                                 events_history_trimmed='\n'.join(self.context),
		                                 task_description=task_description,
		                                 task_context=task_context)
		messages = [{'role': 'user', 'content': prompt_copy}]
		response = self.__chat(messages)
		self.context = ''
		print(f'LLMPlayer.choose_disarm_trap - {response=}')
		if 'Disarm' in response or 'Leave Alone' in response:
			return 'Disarm' in response
		raise ValueError(f'LLMPlayer.choose_disarm_trap - invalid response: {response}')
	
	def choose_loot_treasure(self) -> bool:
		task_description = 'Choose one of the following:'
		task_context = "Loot, Leave Alone"
		prompt_copy = self.prompt.format(heroes_party_str=self.heroes_party_str,
		                                 n=len(self.context),
		                                 events_history_trimmed='\n'.join(self.context),
		                                 task_description=task_description,
		                                 task_context=task_context)
		messages = [{'role': 'user', 'content': prompt_copy}]
		response = self.__chat(messages)
		self.context = ''
		print(f'LLMPlayer.choose_loot_treasure - {response=}')
		if 'Loot' in response or 'Leave Alone' in response:
			return 'Loot' in response
		raise ValueError(f'LLMPlayer.choose_loot_treasure - invalid response: {response}')
