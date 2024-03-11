import pygame
import pygame_gui
from pygame_UI import *

class IHM_Command:
    def __init__(self, manager, desactive_callback=None):    
        self.manager = manager
        self.size = (500, 400)

        self.desactive_callback = desactive_callback

        self.window = pygame_gui.elements.UIWindow(rect=pygame.Rect((100, 100), self.size),
                                                   manager=self.manager,
                                                   window_display_title="Command Manager")

        self.last_command_label = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 5), (500, 30)),
                                                              text="Last command send: None",
                                                              manager=self.manager,
                                                              container=self.window)

        self.labels = []
        self.text_boxes = []
        self.tab_index = 0
        self.tab_line_index = 0

        self.command = None
        self.command_XYT_ = [None, None, None, None]

        # Ajouter des zones de texte et des labels correspondants
        text_box_info = [
            ("Command", (10, 50), (380, 30)),
            ("X", (10, 100), (80, 30)),
            ("Y", (110, 100), (80, 30)),
            ("T", (210, 100), (80, 30)),
            ("S", (310, 100), (80, 30))
        ]

        for label_text, box_position, box_size in text_box_info:
            label = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((box_position[0], box_position[1] - 20), (box_size[0],box_size[1]-10) ),
                                                 text=label_text,
                                                 manager=self.manager,
                                                 container=self.window)
            self.labels.append(label)

            text_box = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((box_position, box_size)),
                                                            manager=self.manager,
                                                            container=self.window)
            self.text_boxes.append(text_box)

        self.send_button_command = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((390, 50), (70, 30)),
                                                        text='Send',
                                                        manager=self.manager,
                                                        container=self.window)
        
        self.send_button_XYT = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((390, 100), (70, 30)),
                                                    text='Send',
                                                    manager=self.manager,
                                                    container=self.window)

        self.desactive_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, 150), (150, 30)),
                                                    text='Désactiver',
                                                    manager=self.manager,
                                                    container=self.window)
        
        # Définir les zones de texte pour chaque ligne
        self.text_boxes_lines = [
            [self.text_boxes[0]],
            [self.text_boxes[1], self.text_boxes[2], self.text_boxes[3], self.text_boxes[4]]
        ]
        
    def process_events(self, event):
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.send_button_command:
                    self.send_command()
                elif event.ui_element == self.send_button_XYT:
                    self.send_command_XYT()
                elif event.ui_element == self.desactive_button:
                    if self.desactive_callback:
                        self.desactive_callback()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                # Déplacer le focus de la zone de texte suivante avec Tab
                self.tab_index = (self.tab_index + 1) % len(self.text_boxes)
                if self.tab_index == 0:
                    self.tab_line_index = 0
                else:
                    self.tab_line_index = 1
                self.manager.set_focus_set(self.text_boxes[self.tab_index])
            elif event.key == pygame.K_RETURN:
                # Envoyer la commande si toutes les zones de texte de la ligne actuelle sont remplies
                current_line_text_boxes = self.text_boxes_lines[self.tab_line_index]
                if all(box.get_text() for box in current_line_text_boxes):
                    if self.tab_index == 0:
                        self.send_command()
                    else:
                        self.send_command_XYT()

    def send_command(self):
        self.command = self.text_boxes[0].get_text()
        self.last_command_label.set_text(f"Last Command: {self.command}")

    def send_command_XYT(self):
        self.command_XYT_[0] = self.text_boxes[1].get_text()
        self.command_XYT_[1] = self.text_boxes[2].get_text()
        self.command_XYT_[2] = self.text_boxes[3].get_text()
        self.command_XYT_[3] = self.text_boxes[4].get_text()
        self.last_command_label.set_text(f"Last Command: {self.command_XYT_[0]} {self.command_XYT_[1]} {self.command_XYT_[2]} {self.command_XYT_[3]}")

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

        self.button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((50, 50), (150, 50)),
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
                            self.new_window = IHM_Command(self.manager)
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
