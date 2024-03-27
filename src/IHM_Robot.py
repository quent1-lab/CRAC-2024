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
        self.screen = pygame.display.set_mode((800, 480))
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
        pygame.mouse.set_visible(False)
        
        # Initialisation des variables
        self.is_running = True

        # Initialisation des éléments graphiques
        #self.background = pygame.image.load("images/background.png")
        #self.background = pygame.transform.scale(self.background, (self.width, self.height))

        self.theme_path = "data/theme.json"

        self.button_menu = []
        self.button_menu_names = ["Favori", "Stratégie", "Energie", "Autres", "Quitter"]


        for i, name in enumerate(self.button_menu_names):
            self.button_menu.append(Button(self.screen, (10 + 120 * i, 10, 100, 50), self.theme_path, name, self.font, lambda i=i: self.button_menu_action(i)))
        
    def button_menu_action(self, index):
        self.PAGE = index
        if index == 4:
            self.is_running = False
    
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
        print("Update energie")
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
        self.client.connect()
        while self.is_running:
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.is_running = False
                for button in self.button_menu:
                    button.handle_event(event)

            # Affichage
            self.screen.fill(self.BACKGROUND_COLOR)

            for button in self.button_menu:
                button.draw()

            self.page_favori()

            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    # Vérifie si la variable d'environnement DISPLAY est définie
    if "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = "0"
        print("Variable DISPLAY non définie, définition de DISPLAY à :0")

    ihm = IHM_Robot()
    ihm.run()
