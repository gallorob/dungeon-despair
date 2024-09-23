from time import sleep

from pygame import Rect
from pygame_gui.core.interfaces import IUIManagerInterface
from pygame_gui.elements import UITextBox, UIWindow


class EventsHistory(UIWindow):
	def __init__(self,
	             rect: Rect,
	             ui_manager: IUIManagerInterface):
		super().__init__(rect, ui_manager, window_display_title='Events', resizable=False, draggable=False)
		
		self.combat_history = UITextBox(html_text='Events History<br>',
		                                relative_rect=Rect(0, 0, self.get_container().rect.width,
		                                                   self.get_container().rect.height),
		                                manager=self.ui_manager,
		                                starting_height=self.starting_height + 1,
		                                container=self.get_container())
	
	def add_text_and_scroll(self, text: str):
		self.combat_history.append_html_text(f'{text}<br>')
		if self.combat_history.scroll_bar:
			self.combat_history.scroll_bar.start_percentage = 1.0
			self.combat_history.scroll_bar.rebuild()
