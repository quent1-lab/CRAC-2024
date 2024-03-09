import pygame
import pygame.locals as pg_constants
import json

class Button:
    def __init__(self, surface, rect, theme_file, text='', font=None, on_click=None):
        self.surface = surface
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font or pygame.font.Font(None, 30)
        self.on_click = on_click

        # Load theme from file
        with open(theme_file, 'r') as file:
            self.theme = json.load(file)

        self.state = 'normal'
        self.font = pygame.font.SysFont(self.theme['font'], self.theme['font_size'])

    def draw(self):
        # Draw button based on current state
        button_color = self.theme[self.state]['color']
        pygame.draw.rect(self.surface, button_color, self.rect, border_radius=self.theme['border_radius'])

        # Draw text on button
        text_surface = self.font.render(self.text, True, self.theme['text_color'])
        text_rect = text_surface.get_rect(center=self.rect.center)
        self.surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pg_constants.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.state = 'hover'
            else:
                self.state = 'normal'
        elif event.type == pg_constants.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.state = 'clicked'
        elif event.type == pg_constants.MOUSEBUTTONUP:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
                self.state = 'hover'


class Slider:
    def __init__(self, surface, rect, color, min_value=0, max_value=100, initial_value=0, slider_color=(0, 0, 255),
                 on_value_change=None):
        self.surface = surface
        self.rect = pygame.Rect(rect)
        self.color = color
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.slider_color = slider_color
        self.on_value_change = on_value_change
        self.dragging = False

    def draw(self):
        pygame.draw.rect(self.surface, self.color, self.rect)
        slider_pos = self.calculate_slider_pos()
        pygame.draw.circle(self.surface, self.slider_color, slider_pos, 10)

    def calculate_slider_pos(self):
        percent = (self.value - self.min_value) / (self.max_value - self.min_value)
        x = int(self.rect.left + percent * self.rect.width)
        y = self.rect.centery
        return x, y

    def handle_event(self, event):
        if event.type == pg_constants.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pg_constants.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        elif event.type == pg_constants.MOUSEMOTION:
            if self.dragging:
                x = event.pos[0]
                x = max(self.rect.left, min(self.rect.right, x))
                percent = (x - self.rect.left) / self.rect.width
                self.value = round(percent * (self.max_value - self.min_value) + self.min_value)
                if self.on_value_change:
                    self.on_value_change(self.value)


class TextBox:
    def __init__(self, surface, rect, color, font=None, text_color=(0, 0, 0), on_text_change=None):
        self.surface = surface
        self.rect = pygame.Rect(rect)
        self.color = color
        self.text = ''
        self.font = font or pygame.font.Font(None, 30)
        self.text_color = text_color
        self.on_text_change = on_text_change

    def draw(self):
        pygame.draw.rect(self.surface, self.color, self.rect)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        self.surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pg_constants.KEYDOWN:
            if event.key == pg_constants.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            if self.on_text_change:
                self.on_text_change(self.text)


# Exemple d'utilisation :
if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    button = Button(screen, (50, 50, 100, 50), "src/theme.json", text='Click Me', on_click=lambda: print('Button clicked'))
    slider = Slider(screen, (50, 150, 300, 20), (0, 255, 0), min_value=0, max_value=100, initial_value=50)
    text_box = TextBox(screen, (50, 200, 200, 50), (0, 0, 255))

    running = True
    while running:
        screen.fill((255, 255, 255))

        button.draw()
        slider.draw()
        text_box.draw()

        for event in pygame.event.get():
            if event.type == pg_constants.QUIT:
                running = False
            button.handle_event(event)
            slider.handle_event(event)
            text_box.handle_event(event)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
