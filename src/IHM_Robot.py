import os
from client import Client
import pygame
from pygame_UI import *

class IHM_Robot:
    def __init__(self):
        self.client = Client("127.0.0.43", 22050, 9, self.receive_to_server)

        self.Energie = {
            "Tension" : {"Main": 0, "Bat1" : 13, "Bat2" : 12, "Bat3" : 1},
            "Courant" : {"Bat1" : 0, "Bat2" : 0, "Bat3" : 0},
            "Switch" : {"Bat1" : False, "Bat2" : False, "Bat3" : False}
        }

        self.PAGE = 0

        self.BACKGROUND_COLOR = (100, 100, 100)

        # Initialisation de la fenêtre
        pygame.init()

        # Vérifie si la taille de l'écran est 800x480
        if pygame.display.Info().current_w == 800 and pygame.display.Info().current_h == 480:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            pygame.mouse.set_visible(False)
        else:
            self.screen = pygame.display.set_mode((800, 480))
            pygame.mouse.set_visible(True)

        # Fullscreen
        #self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width, self.height = pygame.display.get_surface().get_size()
        pygame.display.set_caption("IHM Robot")
        # Icone
        #icon = pygame.image.load("images/icon.png")
        #pygame.display.set_icon(icon)
        # Horloge
        self.clock = pygame.time.Clock()
        # Police
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 20)
        
        # Initialisation des variables
        self.is_running = True

        # Initialisation des éléments graphiques
        #self.background = pygame.image.load("images/background.png")
        #self.background = pygame.transform.scale(self.background, (self.width, self.height))

        self.theme_path = "data/theme.json"

        self.button_menu = []
        self.button_menu_names = ["Favori", "Stratégie", "Energie", "Autres", "Quitter"]
        self.button_menu_colors = [None, None, None, None,(200, 0, 0)] # None = Couleur par défaut


        for i, name in enumerate(self.button_menu_names):
            x = 0
            if i == 4:
                x = 190
            self.button_menu.append(Button(self.screen, (10 + 120 * i + x, 10, 100, 50), self.theme_path, name, self.font, lambda i=i: self.button_menu_action(i), color=self.button_menu_colors[i]))
        
    def button_menu_action(self, index):
        self.PAGE = index
        if index == 4:
            self.client.add_to_send_list(self.client.create_message(1, "stop", None))
    
    def page_favori(self):
        # Cette page comprend 4 grands rectangles correspondant aux batteries du robot
        # Chaque rectangle affichera les informations de la batterie

        # Création des rectangles
        for i in range(2):
            for j in range(2):
                pygame.draw.rect(self.screen, (255, 255, 255), (10 + 390 * i, 80 + 200 * j, 380, 190), 2, 10)
        
        # Affichage des informations
        # Affichage de la tension
        i = 0
        j = 0
        for key, value in self.Energie["Tension"].items():
            if i == 2:
                i = 0
                j = 1
            font_Titre = pygame.font.SysFont("Arial", 36)
            font_Valeur = pygame.font.SysFont("Arial", 24)
            draw_text_center(self.screen, key,(200 + 390 * i), (100 + 200 * j), (0,0,0), font_Titre)
            draw_text(self.screen, f"Tension : {value} V",20 + 390 * i, 140 + 200 * j, (0,0,0), font_Valeur)
            i += 1

        # Affichage du courant
        i = 1
        j = 0
        for key, value in self.Energie["Courant"].items():
            if i == 2:
                i = 0
                j = 1
            font_Valeur = pygame.font.SysFont("Arial", 24)
            draw_text(self.screen, f"Courant : {value} A",20 + 390 * i, 170 + 200 * j, (0,0,0), font_Valeur)
            i += 1
        
        # Affichage de l'état des switchs
        i = 1
        j = 0
        for key, value in self.Energie["Switch"].items():
            if i == 2:
                i = 0
                j = 1
            font_Valeur = pygame.font.SysFont("Arial", 24)
            draw_text(self.screen, f"Switch : {value}",20 + 390 * i, 200 + 200 * j, (0,0,0), font_Valeur)
            i += 1

    def receive_to_server(self, message):
        try:
            if message["cmd"] == "stop":
                self.client.stop()
            elif message["cmd"] == "energie":
                energie = message["data"]
                self.update_energie(energie)
        
        except Exception as e:
            print(f"Erreur lors de la réception du message : {str(e)}")
        
    def update_energie(self, _json):
        if _json is None:
            return
        else:
            data = _json
        for key in data:
            if key in self.Energie:
                for subkey in data[key]:
                    if subkey in self.Energie[key]:
                        self.Energie[key][subkey] = data[key][subkey]

    def deconnexion(self):
        self.is_running = False

    def run(self):
        self.client.set_callback_stop(self.deconnexion)
        #self.client.connect()
        while self.is_running:
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.client.add_to_send_list(self.client.create_message(1, "stop", None))
                for button in self.button_menu:
                    button.handle_event(event)

            # Affichage
            self.screen.fill(self.BACKGROUND_COLOR)

            for button in self.button_menu:
                button.draw()

            if self.PAGE == 0:
                self.page_favori()
            elif self.PAGE == 1:
                pass
            elif self.PAGE == 2:
                pass
            elif self.PAGE == 3:
                pass

            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    ihm = IHM_Robot()
    ihm.run()