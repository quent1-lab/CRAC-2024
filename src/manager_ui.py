import pygame
import pygame_gui as gui


class GUIManager:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        self.manager = gui.UIManager((screen_width, screen_height))

    def create_button(self, text, position, size, callback):
        button = gui.elements.UIButton(relative_rect=pygame.Rect(position, size),
                                              text=text,
                                              manager=self.manager,
                                              container=None)
        button.callback = callback
        return button

    def create_slider(self, position, size, start_value, value_range, callback):
        slider = gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(position, size),
                                                        start_value=start_value,
                                                        value_range=value_range,
                                                        manager=self.manager,
                                                        container=None)
        slider.callback = callback
        return slider

    def create_label(self, text, position, size):
        label = gui.elements.UILabel(relative_rect=pygame.Rect(position, size),
                                             text=text,
                                             manager=self.manager,
                                             container=None)
        return label

    def create_drop_down(self, options, position, size, callback):
        drop_down = gui.elements.UIDropDownMenu(options_list=options,
                                                        starting_option=options[0],
                                                        relative_rect=pygame.Rect(position, size),
                                                        manager=self.manager,
                                                        container=None)
        drop_down.callback = callback
        return drop_down

    def open_window(self, title, size):
        window = gui.elements.UIWindow(rect=pygame.Rect((100, 100), size),
                                              manager=self.manager,
                                              window_display_title=title)
        return window

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        self.manager.process_events(event)

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
            time_delta = clock.tick(60) / 1000.0
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
