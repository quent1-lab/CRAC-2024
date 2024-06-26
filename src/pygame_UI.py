import pygame
import pygame_gui
import pygame.locals as pg_constants
import json
import copy

class Button:
    def __init__(self, surface, rect, theme_file, text='', font=None, on_click=None, color=None):
        self.surface = surface
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font or pygame.font.Font(None, 30)
        self.on_click = on_click
        self.enabled = True

        # Load theme from file
        with open(theme_file, 'r') as file:
            self.theme = json.load(file)
        
        self.theme_default = copy.deepcopy(self.theme)
        
        self.update_color(color)

        self.state = 'normal'
        self.font = pygame.font.SysFont(self.theme['font'], self.theme['font_size'])

    def draw(self):
        if not self.enabled:
            return
        # Draw button based on current state
        button_color = self.theme[self.state]['color']
        pygame.draw.rect(self.surface, button_color, self.rect, border_radius=self.theme['border_radius'])

        # Draw text on button
        text_surface = self.font.render(self.text, True, self.theme['text_color'])
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.centery *1))
        self.surface.blit(text_surface, text_rect)
    
    def update_color(self, color):
        if color is None:
            self.theme['normal']['color'] = self.theme_default['normal']['color']
            self.theme['hover']['color'] = self.theme_default['hover']['color']
            self.theme['clicked']['color'] = self.theme_default['clicked']['color']
        else:
            self.theme['normal']['color'] = color
            self.theme['hover']['color'] = (min(255, int(color[0] * 1.2)), min(255, int(color[1] * 1.2)), min(255, int(color[2] * 1.2)))
            self.theme['clicked']['color'] = (color[0] * 0.8, color[1] * 0.8, color[2] * 0.8)
    
    def update_text(self, text):
        self.text = text

    def disable(self):
        self.enabled = False
    
    def enable(self):
        self.enabled = True

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
                if self.on_click is not None and self.enabled:
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


class UILabel:
    def __init__(self, rect, text, manager, theme_file):
        self.rect = rect
        self.text = text
        self.manager = manager

        # Load theme from file
        with open(theme_file, 'r') as file:
            self.theme = json.load(file)['label']

        # Set font size based on rect height
        self.font_size = int(self.rect.height * 0.8)
        self.font = pygame.font.Font(None, self.font_size)

        # Create UI label element
        self.label = pygame_gui.elements.UILabel(relative_rect=self.rect,
                                                  text=self.text,
                                                  manager=self.manager)

    def set_text(self, text):
        self.text = text
        self.label.set_text(self.text)

    def update_font_size(self):
        # Update font size based on rect height
        self.font_size = int(self.rect.height * 0.8)
        self.font = pygame.font.Font(None, self.font_size)

    def draw(self, surface):
        # Draw text
        rendered_text = self.font.render(self.text, True, self.theme['text_color'])
        surface.blit(rendered_text, self.rect.topleft)

class Interrupteur:
    def __init__(self,screen,pos, size,state=False, switch_color=(0, 220, 0)):
        self.x = pos[0]
        self.y = pos[1]
        self.width = size[0]
        self.height = size[1]
        self.switch_color = switch_color
        self.switched_on = state
        
        self.screen = screen
        
        self.callback_ON = None
        self.callback_OFF = None

    def draw(self):
        # Dessine le fond de l'interrupteur en gris
        pygame.draw.rect(self.screen, (200, 200, 200), (self.x, self.y, self.width, self.height), 0, self.height // 2)
        pygame.draw.rect(self.screen, (100, 100, 100), (self.x, self.y, self.width, self.height), 2, self.height // 2)

        # Dessine ON ou OFF
        font = pygame.font.SysFont("Arial", int(self.height * 0.4))
        if self.switched_on:
            draw_text(self.screen, "ON", self.x + int(self.width * 0.15), self.y + int(self.height * 0.35), (0, 0, 0), font=font)
        else:
            draw_text(self.screen, "OFF", self.x + int(self.width * 0.5), self.y + int(self.height * 0.35), (0, 0, 0), font=font)

        # Dessine l'interrupteur en position ON ou OFF
        if self.switched_on:
            pygame.draw.circle(self.screen, self.switch_color, (self.x + self.width - self.height//2, self.y + self.height//2), self.height//2-4)
            pygame.draw.rect(self.screen, (150, 150, 150), (self.x + self.width//2 +2, self.y +2,self.height-4, self.height-4),2,self.height//2)
        else:
            pygame.draw.circle(self.screen, (220, 0, 0), (self.x + self.height//2, self.y + self.height//2), self.height//2-2)
            pygame.draw.rect(self.screen, (150, 150, 150), (self.x + 2, self.y + 2, self.height-4, self.height-4),2,self.height//2)


    def toggle(self):
        self.switched_on = not self.switched_on
        
        if self.switched_on and self.callback_ON is not None:
            self.callback_ON()
        elif not self.switched_on and self.callback_OFF is not None:
            self.callback_OFF()
        
    def get_switched_on(self):
        return self.switched_on
    
    def set_on_ON(self):
        self.switched_on = True
        
    def set_on_OFF(self):
        self.switched_on = False
        
    def set_callback_ON(self, callback):
        self.callback_ON = callback
        
    def set_callback_OFF(self, callback):
        self.callback_OFF = callback

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.x < mouse_pos[0] < self.x + self.width and self.y < mouse_pos[1] < self.y + self.height:
                self.toggle()


from pygame_gui.elements import UIButton

class CheckBox:
    def __init__(self, manager,screen, xy: tuple, wh: tuple, _id: str, _state=False):
        self.checked = _state
        self.id = _id
        self.button = UIButton(relative_rect=pygame.Rect(xy, wh),
                               text='✓' if self.checked else 'X',
                               manager=manager,
                               container=screen,
                               object_id=_id)

    def toggle(self):
        self.checked = not self.checked
        self.button.set_text('✓' if self.checked else 'X')

    def get_checked(self):
        return self.checked

    def set_checked(self, state):
        self.checked = state
        self.button.set_text('✓' if self.checked else 'X')
        
    def get_id(self):
        return self.id

    def handle_event(self, event):
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.button:
                    self.toggle()
    
    def disable(self):
        self.button.disable()
    
    def enable(self):
        self.button.enable()

def draw_text(screen, text, x, y, color=(0, 0, 0), font=None, bg = None):
    """Draws text to the pygame screen, on up left corner"""
    if font is None:
        font = pygame.font.Font(None, 36)

    if bg is None:
        _text = font.render(text, True, color)
    else:
        _text = font.render(text, True, color, pygame.Color(bg))
    screen.blit(_text, (x, y))

def draw_text_center(screen, text, x, y, color=(0, 0, 0), font=None, bg = None):
    if font is None:
        font = pygame.font.Font(None, 36)
    if bg is None:
        text_surface = font.render(text, True, color)
    else:
        text_surface = font.render(text, True, color, pygame.Color(bg))
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

# Exemple d'utilisation :
if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    theme_file = "data/theme.json"

    button = Button(screen, (50, 50, 100, 50), theme_file, text='Click Me', on_click=lambda: print('Button clicked'))
    slider = Slider(screen, (50, 125, 200, 20), theme_file, value_range=(0, 100),start_value = 50)

    text_box = TextBox(screen, (100, 300, 300, 40), theme_file, send_button=True)
    
        # Initialiser l'interrupteur
    interrupteur = Interrupteur(screen,( 50, 420), (200, 100)) # x, y, width, height = width//2

    running = True
    while running:
        screen.fill((255, 255, 255))

        button.draw()
        slider.draw()
        text_box.draw()
        interrupteur.draw()

        draw_text(screen, "Hello World", 400, 100, (0, 0, 0))

        draw_text_center(screen, "Centered Text", 400, 200, (0, 0, 0))

        for event in pygame.event.get():
            if event.type == pg_constants.QUIT:
                running = False
            button.handle_event(event)
            slider.handle_event(event)
            text_box.handle_event(event)
            interrupteur.handle_event(event)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
