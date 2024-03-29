import os
from client import Client
import pygame
from pygame_UI import *
import threading
import time

class IHM_Robot:
    def __init__(self):
        self.client = Client("127.0.0.43", 22050, 9, self.receive_to_server)

        self.Energie = {
            "Tension" : {"Main": 0, "Bat1" : 0, "Bat2" : 0, "Bat3" : 0},
            "Courant" : {"Bat1" : 0, "Bat2" : 0, "Bat3" : 0},
            "Switch" : {"Bat1" : False, "Bat2" : False, "Bat3" : False}
        }
        self.ban_battery = []

        self.PAGE = 0
        self.ETAT = 0
        self.energie_recue = False
        self.state_request_energy = False

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
                x = 190 # Permet de décaler le bouton "Quitter" vers la droite
            self.button_menu.append(Button(self.screen, (10 + 120 * i + x, 10, 100, 50), self.theme_path, name, self.font, lambda i=i: self.button_menu_action(i), color=self.button_menu_colors[i]))
        
    def button_menu_action(self, index):
        self.PAGE = index
        if index == 0:
            pass
            #self.request_energy()
        if index == 4:
            self.client.add_to_send_list(self.client.create_message(1, "stop", None))
    
    def page_favori(self):
        # Cette page comprend 4 grands rectangles correspondant aux batteries du robot
        # Chaque rectangle affichera les informations de la batterie

        nb_batteries = 0
        for key, value in self.Energie["Tension"].items():
            if self.ETAT == 1 and value == 0:
                continue
            nb_batteries += 1

        # Création des rectangles
        for i in range(nb_batteries):
            pygame.draw.rect(self.screen, (200, 200, 200), (10 + 390 * (i % 2), 80 + 200 * (i // 2), 380, 190), 0, 10)
            pygame.draw.rect(self.screen, (0, 0, 0), (10 + 390 * (i % 2), 80 + 200 * (i // 2), 380, 190), 2, 10)
        
        # Affichage des informations
        # Affichage de la tension
        i = 0
        j = 0
        for key, value in self.Energie["Tension"].items():
            if self.ETAT == 1 and value == 0:
                continue
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
            if self.ETAT == 1 and self.Energie["Tension"][key] == 0:
                continue
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
            if self.ETAT == 1 and self.Energie["Tension"][key] == 0:
                continue
            if i == 2:
                i = 0
                j = 1
            font_Valeur = pygame.font.SysFont("Arial", 24)
            text = "Ouvert" if value == 0 else "Fermé"
            draw_text(self.screen, f"Switch : {text}",20 + 390 * i, 200 + 200 * j, (0,0,0), font_Valeur)
            i += 1

    def zero_battery(self):
        if self.Energie["Tension"]["Bat1"] == 0:
            self.ban_battery.append(1)
            self.ban_battery.append(4)
            self.ban_battery.append(7)
        if self.Energie["Tension"]["Bat2"] == 0:
            self.ban_battery.append(2)
            self.ban_battery.append(5)
            self.ban_battery.append(8)
        if self.Energie["Tension"]["Bat3"] == 0:
            self.ban_battery.append(3)
            self.ban_battery.append(6)
            self.ban_battery.append(9)

    def switch_on(self, num_switch):
        self.client.send(self.client.create_message(2, "CAN", {"id": 518, "byte1": num_switch, "byte2": 1, "byte3": 0}))

    def switch_off(self, num_switch):
        self.client.send(self.client.create_message(2, "CAN", {"id": 518, "byte1": num_switch, "byte2": 0, "byte3": 0}))
    
    def switch(self, num_switch):
        if self.Energie["Tenstion"][f"Bat{num_switch}"] != 0 and self.Energie["Switch"][f"Bat{num_switch}"] == 0:
            self.switch_on(num_switch)
        elif self.Energie["Tenstion"][f"Bat{num_switch}"] == 0 and self.Energie["Switch"][f"Bat{num_switch}"] == 1:
            self.switch_off(num_switch)

    def request_energy(self):
        if self.state_request_energy:
            return
        self.request_energy = True

        commande_energie = [ # id, byte1, byte2, byte3 => commande CAN
            [512,1,0,0],[512,2,0,0], [512,3,0,0], [512,4,0,0],  # Tension
            [513,1,0,0],[513,2,0,0], [513,3,0,0],               # Courant
            [514,1,0,0],[514,2,0,0], [514,3,0,0]                # Switch
        ]

        def task():
            index = 0
            while self.is_running:
                if index >= len(commande_energie): # On a fini de demander les énergies des batteries, on attend 0.5s avant de recommencer
                    index = 0
                    if self.ETAT == 0:
                        for i in range(1, 4):
                            self.switch(i)
                    time.sleep(0.5)
                
                if index in self.ban_battery: # On ne demande pas l'énergie des batteries à 0V
                    index += 1
                    continue
                
                self.client.send(self.client.create_message(2, "CAN", {"id": commande_energie[index][0], "byte1": commande_energie[index][1], "byte2": commande_energie[index][2], "byte3": commande_energie[index][3]}))

                temps = 0
                while not self.energie_recue: # On attend de recevoir les données
                    if not self.is_running:
                        break
                    time.sleep(0.01)
                    temps += 0.01
                    if temps > 2:
                        self.client.send(self.client.create_message(2, "CAN", {"id": commande_energie[index][0], "byte1": commande_energie[index][1], "byte2": commande_energie[index][2], "byte3": commande_energie[index][3]}))
                        temps = 0

                self.energie_recue = False
                index += 1

        thread = threading.Thread(target=task) # On crée un thread pour ne pas bloquer le programme
        thread.start()

    def receive_to_server(self, message):
        try:
            if message["cmd"] == "stop":
                self.client.stop()
            elif message["cmd"] == "energie":
                energie = message["data"]
                self.update_energie(energie)
            elif message["cmd"] == "etat":
                data = message["data"]
                self.ETAT = data["etat"]
                self.zero_battery() # On bannit les batteries à 0V
        
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
                        self.energie_recue = True

    def deconnexion(self):
        self.is_running = False

    def run(self):
        self.client.set_callback_stop(self.deconnexion)
        #self.client.connect()
        self.request_energy()
        while self.is_running:
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.client.add_to_send_list(self.client.create_message(1, "stop", None))
                    self.is_running = False
                for button in self.button_menu:
                    button.handle_event(event)

            # Affichage
            self.screen.fill(self.BACKGROUND_COLOR)

            for button in self.button_menu:
                button.draw()

            if self.PAGE == 0:
                self.page_favori()
                self.Energie["Tension"]["Bat2"] += 1
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