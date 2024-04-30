import os
from client import Client
import pygame
from pygame_UI import *
import threading
import time
from batterie import Batterie
import logging

# Configuration du logger
logging.basicConfig(filename='ihm_robot.log', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S', format='%(asctime)s - %(levelname)s - %(message)s')


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
        self.EQUIPE = "jaune"
        self.energie_recue = False
        self.state_request_energy = False
        self.error = []
        self.ARU_compte = 0

        self.BACKGROUND_COLOR = (100, 100, 100)
        
        self.temp_raspberry = 0

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
        
        font = pygame.font.SysFont("Arial", 36)
        self.button_recalage = Button(self.screen, (420, 90, 360, 60), self.theme_path, "Recalage", font, self.recalage, color=(100, 0, 200))
        
        self.recalage_is_playing = False
        self.robot_move = False
        self.strategie_is_running = False    
        
        self.button_strategie = []
        
        path = "data/strategies"
        liste_strategies = os.listdir(path)
        nombre_strategies = len(liste_strategies)
        x_depart = 10
        y_depart = 90
        
        font = pygame.font.SysFont("Arial", 40)
        
        for i, strategy in enumerate(liste_strategies):
            texte = strategy.split(".")[0]
            button = Button(self.screen, (x_depart + 405 * int(nombre_strategies/6), y_depart + i * 70, 385, 60), self.theme_path, texte, font, lambda i=i: self.strategie_action(i))
            self.button_strategie.append(button)
            
        self.button_ligne_droite = Button(self.screen, (10, 90, 200, 60), self.theme_path, "Ligne droite", font, lambda : self.ligne_droite(1000))
        self.button_tourner_10 = Button(self.screen, (10, 160, 200, 60), self.theme_path, "Tourner 10", font, lambda : self.tourner(360*10))
        
        self.strategie = None
        self.config_strategie = None
        self.liste_aknowledge = []
        with open("data/config_ordre_to_can.json", "r",encoding="utf-8") as f:
            self.config_strategie = json.load(f)
        
    def button_menu_action(self, index):
        self.button_menu[self.PAGE].update_color(None) # On remet la couleur par défaut du bouton actuel
        self.PAGE = index
        self.button_menu[index].update_color((0, 0, 240)) # On met en vert le bouton cliqué
        if index == 0:
            pass            
        elif index == 4:
            self.client.add_to_send_list(self.client.create_message(1, "stop", None))
    
    def strategie_action(self, index):
        self.client.send(self.client.create_message(2, "strategie", {"strategie": index}))
        
        # Charger la stratégie
        with open(f"data/strategies/strategie_{index}.json", "r") as f:
            self.strategie = json.load(f)
            logging.info(f"Stratégie chargée : {self.strategie}")
        
        if self.ETAT == 0:
            self.zero_battery() # On bannit les batteries à 0V
            self.ETAT = 1
        
        self.play_strategie()
    
    def ligne_droite(self, distance):
        self.client.send(self.client.create_message(2, "deplacement", {"distance": distance}))
    
    def tourner(self, angle):
        self.client.send(self.client.create_message(2, "rotation", {"angle": angle*10}))
    
    def recalage(self):
        if self.recalage_is_playing:
            return
        
        if self.ETAT == 0:
            self.zero_battery()
            self.ETAT = 1
            self.client.send(self.client.create_message(10, "config", {"etat": 1, "equipe": self.EQUIPE}))
        
        def task_recalage():
            self.recalage_is_playing = True
            
            with open("data/recalage.json", "r", encoding="utf-8") as f:
                dict_recalage = json.load(f)
            
            for key, value in dict_recalage.items():
                id = value["id"]
                akn = value["aknowledge"]
                action = value[self.EQUIPE]
                logging.info(f"Recalage de la position {id}")
                if len(action["ordre"]) == 1:
                    # Ordre de rotation
                    angle = action["ordre"]["theta"]
                    logging.info(f"Rotation de {angle}°")
                    self.client.send(self.client.create_message(2, "rotation", {"angle" : angle*10}))
                else:
                    # Ordre de recalage
                    distance = action["ordre"]["distance"]
                    mode = action["ordre"]["mode"]
                    recalage = action["ordre"]["recalage"]
                    logging.info(f"Recalage de {distance}mm en mode {mode} avec recalage {recalage}")
                    self.client.send(self.client.create_message(2, "recalage", {"distance": distance, "mode": mode, "recalage": recalage}))
                
                is_arrived = False
                logging.info(f"Attente de l'aknowledge {akn}")
                while self.recalage_is_playing and self.is_running and not is_arrived:
                    time.sleep(0.1)
                    if akn in self.liste_aknowledge:
                        logging.info(f"Arrivé à la position {id}")
                        self.liste_aknowledge.remove(akn)
                        is_arrived = True
                    
                if self.is_running == False:
                    break
            
            self.recalage_is_playing = False
        
        thread_recalage = threading.Thread(target=task_recalage)
        thread_recalage.start()
    
    def play_strategie(self):
        # Jouer la stratégie
        self.strategie_is_running = True
        self.PAGE = 5
        
        def task_play(): # Fonction pour jouer la stratégie dans un thread
            for key, action in self.strategie.items():

                if not self.robot_move:
                    self.robot_move = True

                    pos = (action["Coord"]["X"], action["Coord"]["Y"], int(action["Coord"]["T"]), "0")

                    # Envoyez la position au CAN
                    self.client.add_to_send_list(self.client.create_message(
                        2, "clic", {"x": pos[0], "y": pos[1], "theta": pos[2], "sens": pos[3]}))

                    while self.robot_move and self.strategie_is_running:
                        time.sleep(0.1)
                    
                    if self.strategie_is_running == False:
                        break                  
                    logging.info("Fin de l'instruction de positionnement")
                    # Gérer les actions à effectuer
                    for key, value in action.items():
                        commande = []
                        aknowledge = []
                        if key == "Moteur":
                            for ordre, cmd in action["Moteur"]["ordre"].items():
                                commande.append(self.config_strategie["Moteur"]["ordre"][ordre][cmd])
                                aknowledge.append(self.config_strategie["Moteur"]["aknowledge"][ordre])
                        elif key == "HerkuleX":
                            for key2, value2 in action["HerkuleX"].items():
                                if key2 == "Peigne":
                                    for ordre, cmd in action["HerkuleX"]["Peigne"]["ordre"].items():
                                        commande.append(self.config_strategie["HerkuleX"]["Peigne"]["ordre"][ordre][cmd])
                                        aknowledge.append(self.config_strategie["HerkuleX"]["Peigne"]["aknowledge"][ordre])
                                elif key2 == "Pinces":
                                    for cote, value3 in action["HerkuleX"]["Pinces"].items():
                                        for ordre, cmd in action["HerkuleX"]["Pinces"][cote]["ordre"].items():
                                            commande.append(self.config_strategie["HerkuleX"]["Pinces"][cote]["ordre"][cmd])
                                            aknowledge.append(self.config_strategie["HerkuleX"]["Pinces"][cote]["aknowledge"])
                                elif key2 == "Bras":
                                    for ordre, cmd in action["HerkuleX"]["Bras"]["ordre"].items():
                                        commande.append(self.config_strategie["HerkuleX"]["Bras"]["ordre"][ordre][cmd])
                                        aknowledge.append(self.config_strategie["HerkuleX"]["Bras"]["aknowledge"][ordre])
                        
                        logging.info(f"Commande : {commande}")
                        # Envoyer les commandes au CAN
                        for i, cmd in enumerate(commande):
                            self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": cmd, "byte1": 0, "byte2": 0, "byte3": 0}))
                            
                            while not self.robot_move and self.strategie_is_running and self.is_running:
                                time.sleep(0.1)
                                if aknowledge[i] in self.liste_aknowledge:
                                    self.liste_aknowledge.remove(aknowledge[i])
                                    break

            logging.info("Fin de la stratégie")
            self.strategie_is_running = False
            self.PAGE = 1
            
        thread_play = threading.Thread(target=task_play)
        thread_play.start()
    
    def page_favori(self):
        # Cette page comprend 4 grands rectangles correspondant aux batteries du robot
        # Chaque rectangle affichera les informations de la batterie

        for batterie in self.batteries:
            batterie.draw()
        self.button_recalage.draw()
    
    def page_strategie(self):
        # Cette page affiche les différentes stratégies possibles
        for button in self.button_strategie:
            button.draw()

    def page_energie(self):
        pass
    
    def page_autres(self):
        self.button_ligne_droite.draw()
        self.button_tourner_10.draw()

    def page_erreur(self):
        # Cette page affiche un message d'erreur si une erreur est survenue lors de la réception des données des batteries
        pygame.draw.rect(self.screen, (255, 0, 0), (self.width//2 - 350, 90, 700, 370), 0, 10)
        pygame.draw.rect(self.screen, (0, 0, 0), (self.width//2 - 350, 90, 700, 370), 2, 10)
        
        font = pygame.font.SysFont("Arial", 30)
        
        for error in self.error:
            if error == 0x10:
                draw_text_center(self.screen, "Erreur de réception des données des batteries", x=self.width//2, y=self.height//2 - 65, font=font, color=(255, 255, 255))
                draw_text_center(self.screen, "La carte énergie est-elle alimenté ?", x=self.width//2, y=self.height//2 + - 35, font=font, color=(255, 255, 255))
            if error == 0x11:
                draw_text_center(self.screen, "ARU activé", x=self.width//2, y=self.height//2+15, font=font, color=(255, 255, 255))
                self.ARU_compte += 1
                if self.ARU_compte > 10:
                    self.client.send(self.client.create_message(0, "ARU", {"etat": 0}))
                    self.ARU_compte = 0
                    if 0x11 in self.error:
                        self.error.remove(0x11)
                        self.PAGE = 0
    
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
            if i == 0:
                continue
            if batterie.is_connected() == False:
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
        self.state_request_energy = True
        
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
                    time.sleep(0.05)
                    temps += 0.05
                    if temps > 2:
                        self.client.send(self.client.create_message(2, "CAN", {"id": commande_energie[index][0], "byte1": commande_energie[index][1], "byte2": commande_energie[index][2], "byte3": commande_energie[index][3]}))
                        nb_tentatives += 1
                        temps = 0
                    
                    if nb_tentatives > 1: # On a essayé 1 fois de recevoir les données, on affiche un message d'erreur
                        if 0x10 not in self.error:
                            self.error.append(0x10)
                            for batterie in self.batteries:
                                batterie.mode_error()
                
                if 0x10 in self.error:
                    self.error.remove(0x10)
                    self.PAGE = 0
                    
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
                
            elif message["cmd"] == "config":
                data = message["data"]
                if data["etat"] == 1 and self.ETAT == 0: 
                    self.zero_battery() # On bannit les batteries à 0V
                self.ETAT = data["etat"]    
                self.EQUIPE = data["equipe"]
                
                self.recalage()
                
            elif message["cmd"] == "akn_m":
                self.robot_move = False
                
            elif message["cmd"] == "akn":
                data = message["data"]
                self.liste_aknowledge.append(data["id"])
                logging.info(f"Liste des aknowledge : {self.liste_aknowledge}")
                
            elif message["cmd"] == "ARU":
                data = message["data"]
                if data["etat"] == 1:
                    if 0x11 not in self.error:
                        self.strategie_is_running = False
                        self.robot_move = False
                        self.error.append(0x11)
                elif data["etat"] == 0:
                    if 0x11 in self.error:
                        self.error.remove(0x11)
                        self.PAGE = 0
        
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

    def get_temp_raspberry(self):
        path_exists = os.path.exists("/sys/class/thermal/thermal_zone0/temp")
        while self.is_running:
            if path_exists:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    temp = f.readline()
                    temp = int(temp) / 1000
                    self.temp_raspberry = temp
            time.sleep(2)
    
    def draw_temp_raspberry(self):
        # Affichage de la température du Raspberry
        font = pygame.font.SysFont("Arial", 26)
        color = (255, 255, 255) if self.temp_raspberry < 60 else (255, 0, 0)
        draw_text_center(self.screen, f"Temp : {self.temp_raspberry}°C", x=580, y=40, font=font, color=color)            
    
    def deconnexion(self):
        self.is_running = False
        self.strategie_is_running = False

    def run(self):
        self.taille_auto_batterie()
        
        self.client.set_callback_stop(self.deconnexion)
        self.client.connect()
        self.request_energy()
        
        handle_temp_raspberry = threading.Thread(target=self.get_temp_raspberry)
        handle_temp_raspberry.start()
        
        while self.is_running:
            
            # Si une erreur est survenue lors de la réception des données des batteries
            if len(self.error) > 0:
                self.PAGE = 4
            else:
                self.PAGE = self.PAGE
            
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.client.add_to_send_list(self.client.create_message(1, "stop", None))
                    self.is_running = False
                    self.strategie_is_running = False
                    
                for button in self.button_menu:
                    button.handle_event(event)
                
                if self.PAGE == 0:
                    for batterie in self.batteries:
                        batterie.handle_event(event)
                    self.button_recalage.handle_event(event)
                elif self.PAGE == 1:
                    for button in self.button_strategie:
                        button.handle_event(event)
                elif self.PAGE == 2:
                    pass
                elif self.PAGE == 3:
                    self.button_ligne_droite.handle_event(event)
                    self.button_tourner_10.handle_event(event)

            # Affichage
            self.screen.fill(self.BACKGROUND_COLOR)

            # ------------------- Affichage des éléments graphiques du menu -------------------
            for button in self.button_menu:
                button.draw()

            self.draw_temp_raspberry()
                
            pygame.draw.line(self.screen, (50, 50, 50), (0, 70), (self.width, 70), 2)
            # --------------------------------------------------------------------------------

            if self.PAGE == 0:
                self.page_favori()
            elif self.PAGE == 1:
                self.page_strategie()
            elif self.PAGE == 2:
                pass
            elif self.PAGE == 3:
                self.page_autres()
            elif self.PAGE == 4:
                self.page_erreur()

            pygame.display.flip()
            self.clock.tick(30)
        
        pygame.quit()

if __name__ == "__main__":
    ihm = IHM_Robot()
    ihm.run()