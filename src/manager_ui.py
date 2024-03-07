import pygame
from pygame_gui import *
from pygame_gui.elements import *



class GUIManager:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        self.manager = UIManager((screen_width, screen_height))
        self.callbacks = {}

    def create_button(self, text, position, size, callback):
        object_id = f'{text}_button'.replace(' ', '_').replace('.', '_')
        button = elements.UIButton(relative_rect=pygame.Rect(position, size),
                                              text=text,
                                              manager=self.manager,
                                              container=None,
                                              object_id=object_id)  # Assigning object_id
        self.callbacks[object_id] = callback  # Store the callback function
        return button

    def create_slider(self, position, size, start_value, value_range, callback):
        object_id = f'slider_{position}_{size}'.replace(' ', '_').replace('.', '_')
        slider = elements.UIHorizontalSlider(relative_rect=pygame.Rect(position, size),
                                                        start_value=start_value,
                                                        value_range=value_range,
                                                        manager=self.manager,
                                                        container=None,
                                                        object_id=object_id)  # Assigning object_id
        self.callbacks[object_id] = callback  # Store the callback function
        return slider

    def create_label(self, text, position, size):
        object_id = f'label_{text}'.replace(' ', '_').replace('.', '_')
        label = elements.UILabel(relative_rect=pygame.Rect(position, size),
                                             text=text,
                                             manager=self.manager,
                                             container=None,
                                             object_id=object_id)  # Assigning object_id
        return label

    def create_drop_down(self, options, position, size, callback):
        object_id = f'drop_down_{position}_{size}'.replace(' ', '_').replace('.', '_')
        drop_down = elements.UIDropDownMenu(options_list=options,
                                                        starting_option=options[0],
                                                        relative_rect=pygame.Rect(position, size),
                                                        manager=self.manager,
                                                        container=None,
                                                        object_id=object_id)  # Assigning object_id
        self.callbacks[object_id] = callback  # Store the callback function
        return drop_down

    def open_window(self, title, size):
        object_id = f'{title}_window'.replace(' ', '_').replace('.', '_')
        window = elements.UIWindow(rect=pygame.Rect((100, 100), size),
                                              manager=self.manager,
                                              window_display_title=title,
                                              object_id=object_id)  # Assigning object_id
        return window

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        self.manager.process_events(event)

        if event.type == UI_BUTTON_PRESSED:
            button = event.ui_element
            object_id = button.object_ids  # Get the object_id
            if object_id is not None:
                callback = self.callbacks.get(object_id[0])  # Get the callback function
                if callback is not None:
                    if isinstance(button, UIDropDownMenu):
                        selected_option = button.selected_option
                        callback(selected_option)  # Call the callback function with the selected option
                    else:
                        callback()  # Call the callback function

    def update(self, delta_time):
        self.manager.update(delta_time)

    def draw(self):
        self.screen.fill((255, 255, 255))
        self.manager.draw_ui(self.screen)
        pygame.display.update()

    def run(self):
        clock = pygame.time.Clock()
        is_running = True
        while is_running:
            time_delta = clock.tick(60)/1000.0
            for event in pygame.event.get():
                self.handle_events(event)
            self.update(time_delta)
            self.draw()


if __name__ == "__main__":
    gui_manager = GUIManager(800, 600)
    gui_manager.create_button("Click Me", (50, 50), (100, 50), lambda: print("Button Clicked"))
    gui_manager.create_slider((50, 150), (200, 20), 50, (0, 100), lambda value: print("Slider Value:", value))
    gui_manager.create_label("Hello World", (50, 200), (200, 20))
    gui_manager.create_drop_down(["Option 1", "Option 2", "Option 3"], (50, 250), (200, 50),
                                 lambda selected_option: print("Selected Option:", selected_option))
    window = gui_manager.open_window("Test Window", (300, 300))
    gui_manager.create_button("Close Window", (400, 50), (100, 50), window.kill)
    gui_manager.run()
