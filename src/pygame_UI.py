import pygame
import pygame.locals as pg_constants


class Button:
    def __init__(self, surface, rect, color, text='', font=None, text_color=(0, 0, 0), border_width=0,
                 border_color=(0, 0, 0), on_click=None):
        self.surface = surface
        self.rect = pygame.Rect(rect)
        self.color = color
        self.text = text
        self.font = font or pygame.font.Font(None, 30)
        self.text_color = text_color
        self.border_width = border_width
        self.border_color = border_color
        self.on_click = on_click

    def draw(self):
        pygame.draw.rect(self.surface, self.color, self.rect, 0)
        if self.border_width:
            pygame.draw.rect(self.surface, self.border_color, self.rect, self.border_width)
        if self.text:
            text_surface = self.font.render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(center=self.rect.center)
            self.surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pg_constants.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()


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

    button = Button(screen, (50, 50, 100, 50), (255, 0, 0), text='Click Me', on_click=lambda: print('Button clicked'))
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
