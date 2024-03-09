import pygame
import pygame.locals as pg_constants
import json

class Button:
    def __init__(self, surface, rect, theme_file, text='', font=None, on_click=None, color=None):
        self.surface = surface
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font or pygame.font.Font(None, 30)
        self.on_click = on_click

        # Load theme from file
        with open(theme_file, 'r') as file:
            self.theme = json.load(file)
        
        if color is not None:
            self.theme['normal']['color'] = color
            # Hover color is 20% lighter than normal color
            self.theme['hover']['color'] = (color[0] * 1.2, color[1] * 1.2, color[2] * 1.2)
            # Clicked color is 20% darker than normal color
            self.theme['clicked']['color'] = (color[0] * 0.8, color[1] * 0.8, color[2] * 0.8)

        self.state = 'normal'
        self.font = pygame.font.SysFont(self.theme['font'], self.theme['font_size'])

    def draw(self):
        # Draw button based on current state
        button_color = self.theme[self.state]['color']
        pygame.draw.rect(self.surface, button_color, self.rect, border_radius=self.theme['border_radius'])

        # Draw text on button
        text_surface = self.font.render(self.text, True, self.theme['text_color'])
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.centery *1))
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
                if self.on_click is not None:
                    self.on_click()
                    print("Button clicked")
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
    def __init__(self, surface, rect, theme_file, font=None, max_length=50, send_button = False):
        self.surface = surface
        self.rect = pygame.Rect(rect)
        self.font = font or pygame.font.Font(None, 24)
        self.theme_file = theme_file
        self.max_length = max_length
        self.text = ""
        self.text_to_display = ""
        self.cursor_pos = 0
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_interval = 500  # Interval for cursor blinking (milliseconds)
        self.selected = False

        # Get the average width of a character
        average_char_width = self.font.size('a')[0]

        # Calculate the max length of text to display based on the width of the text box
        self.max_text_display_length = self.rect.width // average_char_width

        # Load theme from file
        with open(theme_file, 'r') as file:
            self.theme = json.load(file)
        
        # Send button
        self.send_button = send_button
        if self.send_button:
            self.button = Button(surface, (self.rect.right + 5, self.rect.y, 50, self.rect.height), theme_file, text='Send', on_click=self.send_message)
            self.send_button_rect = self.button.rect


    def draw(self):
        # Draw text box
        pygame.draw.rect(self.surface, self.theme['bg_color'], self.rect, border_radius=self.theme['border_radius'])

        # Draw text
        text_render = self.font.render(self.text_to_display, True, self.theme['text_color'])
        text_rect = text_render.get_rect(midleft=(self.rect.left + 5, self.rect.centery))
        self.surface.blit(text_render, text_rect)

        if self.send_button:
            self.button.draw()

    def update_text_to_display(self):
        # Update text to display based on current text and cursor position
        self.text_to_display = ""
        if len(self.text) > self.max_text_display_length:
            if self.cursor_pos < self.max_text_display_length - 1:
                self.text_to_display = self.text[:self.max_text_display_length]
            else:
                self.text_to_display = self.text[self.cursor_pos - self.max_text_display_length + 1:self.cursor_pos + 1]
        else:
            self.text_to_display = self.text

        # Add cursor to text to display
        #self.update_cursor(1000/60)
        if self.cursor_visible and self.selected:
            self.text_to_display = self.text_to_display[:self.cursor_pos] + "|" + self.text_to_display[self.cursor_pos:]

    def update_cursor(self, dt):
        # Update cursor visibility
        self.cursor_timer += dt
        if self.cursor_timer >= self.cursor_interval:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def handle_event(self, event):
        self.button.handle_event(event)        
        if event.type == pygame.KEYDOWN and self.selected:
            if event.key == pygame.K_LEFT:
                self.cursor_pos = max(0, self.cursor_pos - 1)
            elif event.key == pygame.K_RIGHT:
                self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
            elif event.key == pygame.K_BACKSPACE:
                if self.cursor_pos > 0:
                    self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
                    self.cursor_pos -= 1
            elif event.key == pygame.K_DELETE:
                if self.cursor_pos < len(self.text):
                    self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]
            elif event.key == pygame.K_RETURN:
                self.send_message()
            else:
                # Handle text input
                if len(self.text) < self.max_length:
                    self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                    self.cursor_pos += 1
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.selected = True
            else:
                self.selected = False
        # Update text to display
        self.update_text_to_display()

    def send_message(self):
        print("Sending message:", self.text)



# Exemple d'utilisation :
if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    theme_file = "src/theme.json"

    button = Button(screen, (50, 50, 100, 50), theme_file, text='Click Me', on_click=lambda: print('Button clicked'))
    slider = Slider(screen, (50, 125, 200, 20), theme_file, value_range=(0, 100),start_value = 50)

    text_box = TextBox(screen, (100, 300, 300, 40), theme_file, send_button=True)

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
