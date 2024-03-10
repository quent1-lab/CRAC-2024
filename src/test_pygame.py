import pygame
import pygame_gui
from pygame_UI import *

class NewWindow:
    def __init__(self, manager):
        self.manager = manager
        self.size = (500, 400)
        self.window = pygame_gui.elements.UIWindow(rect=pygame.Rect((100, 100), self.size),
                                                   manager=self.manager,
                                                   window_display_title="Command Manager")

        self.last_command_label = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((10, 10), (380, 30)),
                                                              text="Last Command: None",
                                                              manager=self.manager,
                                                              container=self.window)

        self.command_input = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((10, 50), (300, 30)),
                                                                 manager=self.manager,
                                                                 container=self.window)

        self.send_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((320, 50), (70, 30)),
                                                        text='Send',
                                                        manager=self.manager,
                                                        container=self.window)

        self.action_button1 = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, 100), (150, 30)),
                                                           text='Action 1',
                                                           manager=self.manager,
                                                           container=self.window)

        self.action_button2 = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((170, 100), (150, 30)),
                                                           text='Action 2',
                                                           manager=self.manager,
                                                           container=self.window)

        self.action_button3 = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, 150), (150, 30)),
                                                           text='Action 3',
                                                           manager=self.manager,
                                                           container=self.window)

        self.action_button4 = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((170, 150), (150, 30)),
                                                           text='Action 4',
                                                           manager=self.manager,
                                                           container=self.window)

        self.action_button5 = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, 200), (150, 30)),
                                                           text='Action 5',
                                                           manager=self.manager,
                                                           container=self.window)

        self.action_button6 = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((170, 200), (150, 30)),
                                                           text='Action 6',
                                                           manager=self.manager,
                                                           container=self.window)

        self.command = None

    
    def process_events(self, event):
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.send_button:
                    self.send_command()
                elif event.ui_element == self.action_button1:
                    self.action_1()
                elif event.ui_element == self.action_button2:
                    self.action_2()
                elif event.ui_element == self.action_button3:
                    self.action_3()
                elif event.ui_element == self.action_button4:
                    self.action_4()
                elif event.ui_element == self.action_button5:
                    self.action_5()
                elif event.ui_element == self.action_button6:
                    self.action_6()
        self.manager.process_events(event)

    def send_command(self):
        self.command = self.command_input.get_text()
        self.last_command_label.set_text(f"Last Command: {self.command}")

    def action_1(self):
        print("Action 1 triggered")

    def action_2(self):
        print("Action 2 triggered")

    def action_3(self):
        print("Action 3 triggered")

    def action_4(self):
        print("Action 4 triggered")

    def action_5(self):
        print("Action 5 triggered")

    def action_6(self):
        print("Action 6 triggered")

class MainWindow:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.manager = pygame_gui.UIManager((800, 600))

        self.button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((50, 50), (100, 50)),
                                                    text='Open Window',
                                                    manager=self.manager)

        self.new_window = None

    def run(self):
        clock = pygame.time.Clock()
        is_running = True
        while is_running:
            time_delta = clock.tick(60)/1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_running = False
                if event.type == pygame.USEREVENT:
                    if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                        if event.ui_element == self.button:
                            self.new_window = NewWindow(self.manager)
                self.manager.process_events(event)
                if self.new_window:
                    self.new_window.process_events(event)

            self.manager.update(time_delta)
            self.screen.fill((255, 255, 255))
            self.manager.draw_ui(self.screen)
            pygame.display.update()

if __name__ == "__main__":
    main_window = MainWindow()
    main_window.run()
