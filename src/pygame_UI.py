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
    def __init__(self, surface, rect, theme_file, value_range=(0, 100), start_value=50, font=None):
        self.surface = surface
        self.rect = pygame.Rect(rect)
        self.value_range = value_range
        self.current_value = start_value
        self.font = font or pygame.font.Font(None, 24)
        self.dragging = False

        # Load theme from file
        with open(theme_file, 'r') as file:
            self.theme = json.load(file)

        self.thumb_rect = pygame.Rect(self.rect.x, self.rect.y, self.theme['thumb_size'], self.rect.height)
        self.thumb_rect.centerx = self._get_thumb_pos_from_value()

    def _get_thumb_pos_from_value(self):
        value_range = self.value_range[1] - self.value_range[0]
        percentage = (self.current_value - self.value_range[0]) / value_range
        return self.rect.x + percentage * self.rect.width

    def _get_value_from_thumb_pos(self):
        percentage = (self.thumb_rect.centerx - self.rect.x) / self.rect.width
        return round(self.value_range[0] + percentage * (self.value_range[1] - self.value_range[0]))

    def draw(self):
        # Get the current dimensions of the track
        x, y, width, height = self.rect

        # Increase the width and height by a certain factor
        width += self.theme['thumb_size']
        x -= (width - self.rect.width) / 2  # Move x to the left by half of the increased width

        # Draw track with the new dimensions
        pygame.draw.rect(self.surface, self.theme['track_color'], (x, y, width, height), border_radius=int(self.theme['border_radius']/2))

        # Draw thumb
        pygame.draw.rect(self.surface, self.theme['thumb_color'], self.thumb_rect, border_radius=self.theme['border_radius'])

        # Draw current value
        current_value_text = self.font.render(str(self.current_value), True, self.theme['text_color'])
        current_value_text_rect = current_value_text.get_rect(midtop=(self.rect.centerx, self.rect.bottom + 5))
        self.surface.blit(current_value_text, current_value_text_rect)

        if self.dragging:
            min_text = self.font.render(str(self.value_range[0]), True, self.theme['text_color'])
            min_text_rect = min_text.get_rect(midtop=(self.rect.left, self.rect.bottom + 5))
            self.surface.blit(min_text, min_text_rect)

            max_text = self.font.render(str(self.value_range[1]), True, self.theme['text_color'])
            max_text_rect = max_text.get_rect(midtop=(self.rect.right, self.rect.bottom + 5))
            self.surface.blit(max_text, max_text_rect)

    def handle_event(self, event):
        if self.dragging:
            if event.type == pygame.MOUSEMOTION:
                self.thumb_rect.centerx = min(max(event.pos[0], self.rect.left), self.rect.right)
                self.current_value = self._get_value_from_thumb_pos()
            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.thumb_rect.collidepoint(event.pos):
                self.dragging = True

    def disable(self):
        self.dragging = False


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
    slider = Slider(screen, (50, 125, 200, 20), 'src/theme.json', value_range=(0, 100),start_value = 50)
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
