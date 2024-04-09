import os
from client import Client
import pygame
from pygame_UI import *
import threading
import time
from batterie import Batterie

class IHM_Robot:
    def __init__(self):
        self.client = Client("127.0.0.43", 22050, 9, self.receive_to_server)

        self.Energie = {
            "Batterie 1": {"Tension": 0, "Courant": 0, "Switch": 0},
            "Batterie 2": {"Tension": 0, "Courant": 0, "Switch": 0},
            "Batterie 3": {"Tension": 0, "Courant": 0, "Switch": 0},
            "Batterie Main": {"Tension": 0, "Courant": 0, "Switch": 0}
        }
        self.ban_battery = []
        
        self.PAGE = 0
        self.ETAT = 0
        self.energie_recue = False
        self.state_request_energy = False
        self.error = []

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
        
        self.desactiver_event = False
        def desactiver_bouton(etat):
            self.desactiver_event = etat
        
        # Initialisation des batteries
        self.batteries = [
            Batterie(capteur=False, screen=self.screen, nom='Batterie Main', _callback_desactiver_event=lambda etat: desactiver_bouton(etat), _callback_switch=lambda num_switch, etat: self.set_switch(num_switch, etat)),
            Batterie(capteur=True, screen=self.screen, nom='Batterie 1', _callback_desactiver_event=lambda etat: desactiver_bouton(etat), _callback_switch=lambda  etat: self.set_switch(1, etat)),
            Batterie(capteur=True, screen=self.screen, nom='Batterie 2', _callback_desactiver_event=lambda etat: desactiver_bouton(etat), _callback_switch=lambda etat: self.set_switch(2, etat)),
            Batterie(capteur=True, screen=self.screen, nom='Batterie 3', _callback_desactiver_event=lambda etat: desactiver_bouton(etat), _callback_switch=lambda etat: self.set_switch(3, etat))
        ]
        self.batteries_names = ["Batterie Main", "Batterie 1", "Batterie 2", "Batterie 3"]

        
        # Initialisation des variables
        self.is_running = True

        # Initialisation des éléments graphiques
        #self.background = pygame.image.load("images/background.png")
        #self.background = pygame.transform.scale(self.background, (self.width, self.height))

        self.theme_path = "data/theme.json"

        self.button_menu = []
        self.button_menu_names = ["Favori", "Stratégie", "Energie", "Autres", "Quitter"]
        self.button_menu_colors = [(0,0,200), None, None, None,(200, 0, 0)] # None = Couleur par défaut

        for i, name in enumerate(self.button_menu_names):
            x = 0
            if i == 4:
                x = 190 # Permet de décaler le bouton "Quitter" vers la droite
            self.button_menu.append(Button(self.screen, (10 + 120 * i + x, 10, 100, 50), self.theme_path, name, self.font, lambda i=i: self.button_menu_action(i), color=self.button_menu_colors[i]))
        
    def button_menu_action(self, index):
        self.button_menu[self.PAGE].update_color(None) # On remet la couleur par défaut du bouton actuel
        self.PAGE = index
        self.button_menu[index].update_color((0, 0, 240)) # On met en vert le bouton cliqué
        if index == 0:
            pass            
        if index == 4:
            self.client.add_to_send_list(self.client.create_message(1, "stop", None))
    
    def page_favori(self):
        # Cette page comprend 4 grands rectangles correspondant aux batteries du robot
        # Chaque rectangle affichera les informations de la batterie

        for batterie in self.batteries:
            batterie.draw()
    
    def page_erreur(self):
        # Cette page affiche un message d'erreur si une erreur est survenue lors de la réception des données des batteries
        pygame.draw.rect(self.screen, (255, 0, 0), (self.width//2 - 350, self.height//2 - 90, 700, 300), 0, 10)
        pygame.draw.rect(self.screen, (0, 0, 0), (self.width//2 - 350, self.height//2 - 90, 700, 300), 2, 10)
        
        font = pygame.font.SysFont("Arial", 30)
        
        for error in self.error:
            if error == 0x10:
                draw_text_center(self.screen, "Erreur de réception des données des batteries", x=self.width//2, y=self.height//2 - 15, font=font, color=(255, 255, 255))
                draw_text_center(self.screen, "La carte énergie est-elle alimenté ?", x=self.width//2, y=self.height//2 + 15, font=font, color=(255, 255, 255))
    
    def taille_auto_batterie(self):
        nb_batteries_colonne = 0
        somme_taille = 90
        
        while nb_batteries_colonne < len(self.batteries):
            if somme_taille + self.batteries[nb_batteries_colonne].taille[1] + 10 > self.height:
                break
            somme_taille += self.batteries[nb_batteries_colonne].taille[1] + 10
            nb_batteries_colonne += 1
            
        somme_taille = 0
        for i, batterie in enumerate(self.batteries):
            if i % nb_batteries_colonne == 0 and i != 0:
                somme_taille = 0
            batterie.update_position((10 + (i//nb_batteries_colonne) * (batterie.taille[0]+10), 90 + somme_taille))
            
            somme_taille += batterie.taille[1] + 10

    def zero_battery(self):
        for i, batterie in enumerate(self.batteries):
            if not batterie.is_connected:
                self.ban_battery.append(i)
                self.ban_battery.append(i+3)
                self.ban_battery.append(i+6)

    def switch_on(self, num_switch):
        self.client.send(self.client.create_message(2, "CAN", {"id": 518, "byte1": num_switch, "byte2": 1, "byte3": 0}))

    def switch_off(self, num_switch):
        self.client.send(self.client.create_message(2, "CAN", {"id": 518, "byte1": num_switch, "byte2": 0, "byte3": 0}))
    
    def set_switch(self, num_switch, etat):
        if etat == 1:
            self.switch_on(num_switch)
        elif etat == 0:
            self.switch_off(num_switch)
    

    def request_energy(self):
        if self.state_request_energy:
            return
        self.request_energy = True
        
        # Variable contenant les commandes pour demander l'énergie des batteries
        commande_energie = [ # id, byte1, byte2, byte3 => commande CAN
            [512,1,0,0],[512,2,0,0], [512,3,0,0], [512,4,0,0],  # Tension
            [513,1,0,0],[513,2,0,0], [513,3,0,0],               # Courant
            [514,1,0,0],[514,2,0,0], [514,3,0,0]                # Switch
        ]
        
        def task():
            # Variable comptant le nombre de tentatives pour recevoir les données
            nb_tentatives = 0
            index = 0
            while self.is_running:
                if index >= len(commande_energie): # On a fini de demander les énergies des batteries, on attend 0.5s avant de recommencer
                    index = 0
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
                        nb_tentatives += 1
                        temps = 0
                    
                    if nb_tentatives > 2: # On a essayé 5 fois de recevoir les données, on affiche un message d'erreur
                        self.error.append(0x10)
                
                if 0x10 in self.error:
                    self.error.remove(0x10)
                    
                nb_tentatives = 0
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
        
        for batterie in self.batteries:
            if batterie.recuperer_valeurs(data):
                self.energie_recue = True
                break

    def deconnexion(self):
        self.is_running = False

    def run(self):
        self.taille_auto_batterie()
        
        self.client.set_callback_stop(self.deconnexion)
        self.client.connect()
        self.request_energy()
        while self.is_running:
            
            # Si une erreur est survenue lors de la réception des données des batteries
            if len(self.error) > 0:
                self.PAGE = 4
            else:
                self.PAGE = 0
            
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.client.add_to_send_list(self.client.create_message(1, "stop", None))
                    self.is_running = False
                    
                for batterie in self.batteries:
                    batterie.handle_event(event)    
                    
                for button in self.button_menu:
                    button.handle_event(event)
                    

            

            # Affichage
            self.screen.fill(self.BACKGROUND_COLOR)

            for button in self.button_menu:
                button.draw()
                
            pygame.draw.line(self.screen, (50, 50, 50), (0, 70), (self.width, 70), 2)

            if self.PAGE == 0:
                self.page_favori()
            elif self.PAGE == 1:
                pass
            elif self.PAGE == 2:
                pass
            elif self.PAGE == 3:
                pass
            elif self.PAGE == 4:
                self.page_erreur()

            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    ihm = IHM_Robot()
    ihm.run()