from    batterie    import Batterie
from    client      import Client
from    pygame_UI   import *
import  threading
import  logging
import  pygame
import  time
import  os

# Configuration du logger
logging.basicConfig(filename='ihm_robot.log', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S', format='%(asctime)s - %(levelname)s - %(message)s')

class IHM_Robot:
    version = "1.060"
    points = 50
    def __init__(self):
        
        self.client = Client("127.0.0.9", 22050, 9, self.receive_to_server)

        self.Energie = {
            "Batterie 1": {"Tension": 0, "Courant": 0, "Switch": 0},
            "Batterie 2": {"Tension": 0, "Courant": 0, "Switch": 0},
            "Batterie 3": {"Tension": 0, "Courant": 0, "Switch": 0},
            "Batterie Main": {"Tension": 0, "Courant": 0, "Switch": 0}
        }
        self.ban_battery = []
        
        self.ROBOT_Dimension = (264, 269)
        self.ROBOT_pos = (0, 0, 0)
        self.RATIO_x = 720/3000
        self.RATIO_y = 480/2000
        self.perimetre_securite = 600
        
        self.objets = []
        
        self.PAGE = 0
        self.ETAT = 0
        self.EQUIPE = "jaune"
        self.energie_recue = False
        self.state_request_energy = False
        self.error = []
        self.id_card_action = 416

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
        self.width, self.height = pygame.display.get_surface().get_size()
        pygame.display.set_caption("IHM Robot")
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
        
        self.button_favori = [
                Button(self.screen, (420, 90, 360, 60), self.theme_path, "Recalage", font, lambda : self.button_menu_action(9), color=(100, 0, 200)),
                Button(self.screen, (420, 160, 360, 100), self.theme_path, "Homologation", font, lambda : self.strategie_action("Homologation",True), color=(100, 200, 100))
        ]
        
        self.recalage_is_playing = False
        self.robot_move = False
        self.strategie_is_running = False
        self.can_connect = False
        
        self.button_recalages = [
            Button(self.screen, (40, 0, 120, 120), self.theme_path, "1", self.font,  lambda : self.recalage(1), color=(0, 0, 200)),
            Button(self.screen, (40, 180, 120, 120), self.theme_path, "2", self.font,  lambda : self.recalage(2), color=(200, 200, 0)),
            Button(self.screen, (40, 360, 120, 120), self.theme_path, "3", self.font,  lambda : self.recalage(3), color=(0, 0, 200)),
            Button(self.screen, (640, 0, 120, 120), self.theme_path, "4", self.font,  lambda : self.recalage(4), color=(200, 200, 0)),
            Button(self.screen, (640, 180, 120, 120), self.theme_path, "5", self.font,  lambda : self.recalage(5), color=(0, 0, 200)),
            Button(self.screen, (640, 360, 120, 120), self.theme_path, "6", self.font,  lambda : self.recalage(6), color=(200, 200, 0))
        ]
        
        self.button_strategie = []
        self.supprimer_start = False
        
        self.path_strat = "data/strategies_cache"
        
        self.create_button_strategie()
        
        self.button_autres = [
            Button(self.screen, (40, 220, 200, 80), self.theme_path, "TEST Mouvement", font, lambda : self.button_autres_action(0)),
            Button(self.screen, (280, 220, 200, 80), self.theme_path, "TEST Action", font, lambda : self.button_autres_action(1)),
            Button(self.screen, (520, 220, 240, 80), self.theme_path, "TEST Spécial", font, lambda : self.button_autres_action(2)),
            Button(self.screen, (280, 320, 200, 80), self.theme_path, "GET pos", font, lambda : self.button_autres_action(3)),
            Button(self.screen, (280, 120, 200, 80), self.theme_path, "Terrain", font, lambda : self.button_autres_action(4))
        ]
        
        self.button_tests_mouvement = [
            Button(self.screen, (10, 90, 150, 80), self.theme_path, "Ligne droite 2m",  font, lambda : self.ligne_droite(2000)),
            Button(self.screen, (10, 180, 150, 80), self.theme_path, "Ligne droite 1m", font, lambda : self.ligne_droite(1000)),
            Button(self.screen, (10, 270, 150, 80), self.theme_path, "Tourner 8",       font, lambda : self.tourner(360*8)),
        ]
        
        self.button_tests_action = [
            Button(self.screen, (100, 90, 200, 60), self.theme_path, "Carte Avant",     font, lambda : self.set_id_card_action(416)),
            Button(self.screen, (500, 90, 200, 60), self.theme_path, "Carte Arrière",   font, lambda : self.set_id_card_action(417)),
            
            Button(self.screen, (20, 160, 150, 60), self.theme_path, "HOMING",          font, lambda : self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": self.id_card_action, "byte1": 6}))),
            Button(self.screen, (20, 230, 150, 60), self.theme_path, "UP",              font, lambda : self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": self.id_card_action, "byte1": 7}))),
            Button(self.screen, (20, 300, 150, 60), self.theme_path, "MID",             font, lambda : self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": self.id_card_action, "byte1": 8}))),
            Button(self.screen, (20, 370, 150, 60), self.theme_path, "DOWN",            font, lambda : self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": self.id_card_action, "byte1": 9}))),
            
            Button(self.screen, (200, 160, 150, 60), self.theme_path, "CLOSE",          font, lambda : self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": self.id_card_action, "byte1": 1}))),
            Button(self.screen, (200, 230, 150, 60), self.theme_path, "OPEN",           font, lambda : self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": self.id_card_action, "byte1": 2}))),
            Button(self.screen, (200, 300, 150, 60), self.theme_path, "PLANT",          font, lambda : self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": self.id_card_action, "byte1": 3}))),
            Button(self.screen, (200, 370, 150, 60), self.theme_path, "RESET",          font, lambda : self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": self.id_card_action, "byte1": 11}))),
            
            Button(self.screen, (380, 160, 150, 60), self.theme_path, "COMB UP", font, lambda : self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": self.id_card_action, "byte1": 4}))),
            Button(self.screen, (380, 230, 150, 60), self.theme_path, "COMB SHAKE", font, lambda : self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": self.id_card_action, "byte1": 10}))),
            Button(self.screen, (380, 300, 150, 60), self.theme_path, "COMB TAKE", font, lambda : self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": self.id_card_action, "byte1": 12}))),
            
            Button(self.screen, (560, 160, 150, 60), self.theme_path, "COMB DROPOFF", font, lambda : self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": self.id_card_action, "byte1": 13}))),
        ]
        
        self.button_tests_special = [
            Button(self.screen, (10, 90, 150, 80), self.theme_path, "Recalage", font, self.recalage),
        ]
        
        self.button_get_pos = [
            Button(self.screen, (100, 90, 200, 60), self.theme_path, "Carte Avant", font, lambda : self.set_id_card_action(416)),
            Button(self.screen, (500, 90, 200, 60), self.theme_path, "Carte Arrière", font, lambda : self.set_id_card_action(417))
        ]
        
        self.value_get_pos = [0, 0, 0]
        
        self.set_id_card_action(416)
        self.zone_recalage = [1,2,3,4,5,6]
        
        self.strategie = None
        self.config_strategie = None
        self.liste_aknowledge = []
        self.text_page_play = ""
        self.is_started = False
        
        with open("data/config_ordre_to_can.json", "r",encoding="utf-8") as f:
            self.config_strategie = json.load(f)
    
    # ============================ Fin du constructeur ============================
    
    def draw_robot(self):
        x,y,angle = self.ROBOT_pos
        x_r = int(self.map_value(x, 0, 3000, 760, 40))
        y_r = int(self.map_value(y, 0, 2000, 0, 480))
        
        dim_x = self.ROBOT_Dimension[0] * self.RATIO_x
        dim_y = self.ROBOT_Dimension[1] * self.RATIO_y
        
        # Dessiner le robot en fonction de ses coordonnées et de son angle et de ses dimensions en rectangle
        # Créer une nouvelle surface pour le robot
        robot_surface = pygame.Surface((dim_x, dim_y), pygame.SRCALPHA)

        # Dessiner le rectangle du robot sur la nouvelle surface
        pygame.draw.rect(robot_surface, pygame.Color(101, 67, 33), (0, 0, dim_x, dim_y), 0,10)

        # Dessiner la flèche sur la nouvelle surface
        pygame.draw.polygon(robot_surface, pygame.Color(255, 0, 0), [(dim_x - 5, dim_y / 2), (dim_x /2, 10), (dim_x / 2, dim_y / 2 - 10),(10,dim_y / 2 - 10), (10,dim_y / 2 + 10), (dim_x / 2, dim_y / 2 + 10), (dim_x / 2, dim_y - 10), (dim_x-5, dim_y / 2)], 0)

        # Dessine un périmètre de sécurité autour du robot
        pygame.draw.circle(self.screen, pygame.Color(255, 0, 0), (x_r, y_r), self.perimetre_securite * self.RATIO_x, 2)

        # Faire pivoter la surface du robot
        robot_surface = pygame.transform.rotate(robot_surface, angle+180)
        robot_surface_rect = robot_surface.get_rect(center=(x_r, y_r))

        # Obtenir la position du nouveau centre de la surface

        # Dessiner la surface du robot sur l'écran en ajustant les coordonnées pour que le centre reste à la même position
        self.screen.blit(robot_surface, robot_surface_rect)
    
    def draw_object(self, objet):
        x = int(self.map_value(objet[0], 0, 3000, 40, 760))
        y = int(self.map_value(objet[1], 0, 2000, 0, 480))
        
        logging.info(f"Objet : {objet} - x={x}, y={y}")
                
        pygame.draw.circle(self.lcd, pygame.Color(255, 255, 0), (x , y), 10)
        pygame.draw.circle(self.lcd, pygame.Color(50, 50, 200), (x, y), int(objet[2] / 2 * self.RATIO_x), 3)
        
        # Dessine le périmètre de sécurité autour de l'objet
        pygame.draw.circle(self.lcd, pygame.Color(255, 0, 0), (x, y), self.perimetre_securite * self.RATIO_x, 2)
    
    def button_menu_action(self, index):
        if self.PAGE < 4:
            self.button_menu[self.PAGE].update_color(None) # On remet la couleur par défaut du bouton actuel
        self.PAGE = index
        self.button_menu[index].update_color((0, 0, 240)) # On met en vert le bouton cliqué
        if index == 0:
            pass            
        elif index == 4:
            self.client.add_to_send_list(self.client.create_message(1, "stop", None))
        elif index == 9:
            self.zone_recalage = [1,2,3,4,5,6]

    def set_id_card_action(self, id):
        self.id_card_action = id
        if id == 416:
            self.button_tests_action[0].update_color((10, 200, 10))
            self.button_tests_action[1].update_color(None)
            self.button_get_pos[0].update_color((10, 200, 10))
            self.button_get_pos[1].update_color(None)
        elif id == 417:
            self.button_tests_action[0].update_color(None)
            self.button_tests_action[1].update_color((10, 200, 10))
            self.button_get_pos[0].update_color(None)
            self.button_get_pos[1].update_color((10, 200, 10))
    
    def button_autres_action(self, index):
        self.PAGE = 10 + index
        if index == 4:
            self.PAGE = 20
        time.sleep(0.2)
    
    def supprimer_acton(self):
        self.supprimer_start = not self.supprimer_start
        if self.supprimer_start:
            self.button_strategie[-1].update_color((200, 0, 0))
            self.button_strategie[-1].update_text("Annuler")
        else:
            self.button_strategie[-1].update_color((200, 200, 200))
            self.button_strategie[-1].update_text("Supprimer")
        time.sleep(0.1)
    
    def strategie_action(self, name, recaler=False):
        
        # Charger la stratégie
        if self.ETAT == 0:
            self.zero_battery() # On bannit les batteries à 0V
            self.ETAT = 1
            #self.client.add_to_send_list(self.client.create_message(10, "config", {"etat": 1, "equipe": self.EQUIPE}))  
          
        if recaler:
            try:
                with open(self.path_strat + f"/strategie_{name}.json", "r") as f:
                    self.strategie = json.load(f)
                    logging.info(f"Chargement de la stratégie {name}")
            except Exception as e:
                logging.error(f"Erreur lors du chargement de la stratégie : {e}")
            for equipe, zone in self.strategie["zone"].items():
                self.zone_recalage.append(zone)
            if "points" in self.strategie:
                self.points = self.strategie["points"]
            self.PAGE = 9
            logging.info(f"Recalage de la zone {self.zone_recalage}")
            return
        elif self.supprimer_start:
            # Supprimer la stratégie
            if os.path.exists(self.path_strat + f"/strategie_{name}.json"):
                os.remove(self.path_strat + f"/strategie_{name}.json")
                logging.info(f"Suppression de la stratégie {name}")
            self.supprimer_start = False
            
            self.create_button_strategie()
            
            return
        else:
            # Envoie un reset aux cartes action
            self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 416, "byte1": 11}))
            self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 417, "byte1": 11}))
            time.sleep(0.5)
            
            # Fermé les pinces
            self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 416, "byte1": 1}))
            self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 417, "byte1": 1}))
            time.sleep(0.5)
            
            # Lever les peignes
            self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 416, "byte1": 4}))
            self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 417, "byte1": 4}))
            time.sleep(0.5)

            # Lever le bras
            self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 416, "byte1" : 16}))
        
        self.play_strategie(name)
    
    def create_button_strategie(self):
        self.button_strategie = []
        self.supprimer_start = False
        
        # Vériication de l'existence du dossier
        if not os.path.exists(self.path_strat):
            os.makedirs(self.path_strat)
        
        liste_strategies = os.listdir(self.path_strat)
        
        # Vérifie si le nombre de fichier est inférieur à 8, si plus de 8 fichiers, on affiche les 8 derniers
        if len(liste_strategies) > 8:
            liste_strategies = liste_strategies[-8:]
            
        # Mettre les stratégies dans l'ordre alphabétique
        liste_strategies.sort()
        
        x_depart = 10
        y_depart = 140
        
        font = pygame.font.SysFont("Arial", 40)
        
        for i, strategy in enumerate(liste_strategies):
            texte = strategy.split(".")[0]
            name = texte.split("_")[1]
            button = Button(self.screen, (x_depart + 400 * int(i/4), y_depart + (i % 4) * 90, 385, 75), self.theme_path, texte, font, lambda i=name: self.strategie_action(i))
            self.button_strategie.append(button)
        
        button_supp = Button(self.screen, (300, 80, 200, 50), self.theme_path, "Supprimer", self.font, lambda : self.supprimer_acton(), color=(200, 200, 200))
        self.button_strategie.append(button_supp)
    
    def ligne_droite(self, distance):
        self.client.add_to_send_list(self.client.create_message(2, "deplacement", {"distance": distance}))
    
    def tourner(self, angle):
        self.client.add_to_send_list(self.client.create_message(2, "rotation", {"angle": angle*10}))
    
    def recalage(self, zone = 0):
        if self.recalage_is_playing:
            return
        
        if zone == 0:
            self.PAGE = 9
            return
        
        if self.PAGE == 9 and zone != 0:
            self.PAGE = 20
        
        # Si zone paire, equipe jaune, sinon equipe bleue
        if zone % 2 == 0:
            self.EQUIPE = "jaune"
        else:
            self.EQUIPE = "bleu"
        
        self.client.add_to_send_list(self.client.create_message(0, "config", {"equipe": self.EQUIPE, "etat": 0}))
        
        self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 0x032, "byte1": 1}))
        
        def task_recalage():
            self.recalage_is_playing = True
            
            # Vérifier si le fichier de recalage existe
            if not os.path.exists(f"data/recalages/recalage_{zone}.json"):
                logging.error(f"Le fichier de recalage_{zone}.json n'existe pas")
                self.recalage_is_playing = False
                return
            
            with open(f"data/recalages/recalage_{zone}.json", "r", encoding="utf-8") as f:
                dict_recalage = json.load(f)
            
            for key, value in dict_recalage.items():
                logging.info(f"Recalage : {value}")
                id = value["id"]
                akn = value["aknowledge"]
                action = value
                try:
                    if "ordre" in action:
                        if len(action["ordre"]) == 1:
                            # Ordre de rotation
                            angle = action["ordre"]["theta"]
                            self.client.add_to_send_list(self.client.create_message(2, "rotation", {"angle" : angle*10}))
                        else:
                            # Ordre de recalage
                            distance = action["ordre"]["distance"]
                            mode = action["ordre"]["mode"]
                            recalage = action["ordre"]["recalage"]
                            self.client.add_to_send_list(self.client.create_message(2, "recalage", {"distance": distance, "mode": mode, "recalage": recalage}))
                        
                        is_arrived = False
                        while self.recalage_is_playing and self.is_running and not is_arrived:
                            time.sleep(0.1)
                            if akn in self.liste_aknowledge:
                                self.liste_aknowledge.remove(akn)
                                is_arrived = True
                            
                        if self.is_running == False:
                            break
                    elif "can" in action:
                        # Ordre CAN pour set odometrie
                        x = action["can"]["x"]
                        y = action["can"]["y"]
                        theta = action["can"]["theta"]
                        
                        logging.info(f"Recalage : x={x}, y={y}, theta={theta}")
                        self.client.add_to_send_list(self.client.create_message(2, "set_odo", {"x": x, "y": y, "theta": theta}))
                except Exception as e:
                    logging.error(f"Erreur lors du recalage {action} : {e}")
                    self.recalage_is_playing = False
                    break
            
            if 6 > len(self.zone_recalage) > 0:
                self.zone_recalage = []
                self.play_strategie("Homologation")
            else:
                self.PAGE = 0
            self.recalage_is_playing = False
        
        thread_recalage = threading.Thread(target=task_recalage)
        thread_recalage.start()
    
    def play_strategie(self,name):
        # Jouer la stratégie
        self.strategie_is_running = True
        self.PAGE = 5
        
        # Envoyer un message pour dire que la stratégie est choisie
        self.client.add_to_send_list(self.client.create_message(4, "strategie", {"strategie_path": self.path_strat + f"/strategie_{name}.json"}))
    
    def page_favori(self):
        # Cette page comprend 4 grands rectangles correspondant aux batteries du robot
        # Chaque rectangle affichera les informations de la batterie

        for batterie in self.batteries:
            batterie.draw()
        
        for button in self.button_favori:
            button.draw()
        
        # Affiche la version du code en bas à droite en petit
        draw_text(self.screen, f"Version {self.version}", x=self.width-125, y=self.height-20, font=self.font, color=(255, 255, 255))
    
    def page_strategie(self):
        # Cette page affiche les différentes stratégies possibles
        for button in self.button_strategie:
            button.draw()

    def page_energie(self):
        pass
    
    def page_autres(self):
        for button in self.button_autres:
            button.draw()
    
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
    
    def page_play(self):
        # Cette page affiche la stratégie en cours
        font = pygame.font.SysFont("Arial", 40)
        draw_text_center(self.screen, self.text_page_play, x=self.width//2, y=self.height//2 + 15, font=font, color=(255, 255, 255))
    
    def page_mouvement(self):
        for button in self.button_tests_mouvement:
            button.draw()
    
    def page_action(self):
        for button in self.button_tests_action:
            button.draw()
    
    def page_special(self):
        for button in self.button_tests_special:
            button.draw()
    
    def page_get_pos(self):
        
        # Dessiner les valeurs
        font = pygame.font.SysFont("Arial", 30)
        for i, value in enumerate(self.value_get_pos):
            # Faire une demande de position HerkulEX par HerkulEX
            #self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": self.id_card_action, "byte1": 5, "byte2": i}))
            time.sleep(0.1)
            draw_text_center(self.screen, f"Position {i} : {value}", x=self.width//2, y=90 + i * 50, font=font, color=(255, 255, 255))
    
    def page_match(self):
        # Dessine l'image du terrain de jeu en 720x480
        self.screen.fill((0, 0, 0))
        
        # Dessine l'image
        image_terrain = pygame.image.load("data/Terrain_Jeu.png")
        # Redimensionne l'image
        image_terrain = pygame.transform.scale(image_terrain, (720, 480))
        # Dessine l'image
        self.screen.blit(image_terrain, (40, 0))
        
        self.draw_robot()
        
        for objet in self.objets:
            self.draw_object(objet)

    def page_points(self):
        # Dessine les points estimés par le robot
        font = pygame.font.SysFont("Arial", 50)
        draw_text_center(self.screen, f"{self.points} points :|", x=self.width//2, y=250, font=font, color=(255, 255, 255))
    
    def page_recalage(self):
        # Dessine le terrain de jeu en 720x480
        self.screen.fill((0, 0, 0))
        
        # Dessine l'image
        image = pygame.image.load("data/Terrain_Jeu.png")
        # Redimensionne l'image
        image = pygame.transform.scale(image, (720, 480))
        # Dessine l'image
        self.screen.blit(image, (40, 0))
        
        try:
            for zone in self.zone_recalage:
                self.button_recalages[zone-1].draw()
        except Exception as e:
            logging.error(f"Erreur lors de l'affichage des boutons de recalage : {e}")
    
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
        self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 518, "byte1": num_switch, "byte2": 1, "byte3": 0}))

    def switch_off(self, num_switch):
        self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 518, "byte1": num_switch, "byte2": 0, "byte3": 0}))
    
    def set_switch(self, num_switch, etat):
        if etat == 1:
            self.switch_on(num_switch)
            if num_switch == 3:
                # Activer l'asservissement
                logging.info("IHM : Asservissement activé")
                self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 503, "byte1": 1}))
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
            while self.is_running and not self.is_started:
                if index >= len(commande_energie): # On a fini de demander les énergies des batteries, on attend 0.5s avant de recommencer
                    index = 0
                    time.sleep(0.5)
                
                if index in self.ban_battery: # On ne demande pas l'énergie des batteries à 0V
                    index += 1
                    continue
                
                self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": commande_energie[index][0], "byte1": commande_energie[index][1], "byte2": commande_energie[index][2], "byte3": commande_energie[index][3]}))

                temps = 0
                while not self.energie_recue: # On attend de recevoir les données
                    if not self.is_running:
                        break
                    time.sleep(0.05)
                    temps += 0.05
                    if temps > 1:
                        self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": commande_energie[index][0], "byte1": commande_energie[index][1], "byte2": commande_energie[index][2], "byte3": commande_energie[index][3]}))
                        nb_tentatives += 1
                        temps = 0
                    
                    if nb_tentatives > 1: # On a essayé 1 fois de recevoir les données, on affiche un message d'erreur
                        if 0x10 not in self.error:
                            self.error.append(0x10)
                            for batterie in self.batteries:
                                batterie.mode_error()
                
                if not self.can_connect:
                    self.can_connect = True
                    self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 503, "byte1": 0}))
                
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
            
            if message["cmd"] == "end":
                self.PAGE = 21
                logging.info("Fin de la partie")
                self.state_request_energy = False
                self.is_started = False
                if not self.state_request_energy:
                    self.request_energy()
                
                # Eteindre les switchs
                self.set_switch(1, 0)
                self.set_switch(2, 0)
                self.set_switch(3, 0)
                
            if message["cmd"] == "objects":
                self.objets = []
                try:
                    json_string = message["data"]
                    for obj in json_string:
                        logging.info(f"Objet : {obj}")
                        #obj = json.loads(obj)
                        self.objets.append(obj["x"], obj["y"], obj["taille"])
                except Exception as e:
                    logging.error(f"Erreur lors de la réception des objets : {e}")

            elif message["cmd"] == "energie":
                energie = message["data"]
                self.update_energie(energie)
                
            elif message["cmd"] == "config":
                data = message["data"]
                if data["etat"] == 1 and self.ETAT == 0: 
                    self.zero_battery() # On bannit les batteries à 0V
                self.ETAT = data["etat"]    
                self.EQUIPE = data["equipe"]
                
                #self.recalage()
                
            elif message["cmd"] == "akn_m":
                self.robot_move = False
                
            elif message["cmd"] == "akn":
                data = message["data"]
                if self.strategie_is_running or self.recalage_is_playing:
                    if data["id"] != 0x114:
                        self.liste_aknowledge.append(data["id"])
                        logging.info(f"Liste des aknowledge : {self.liste_aknowledge}")
                    else:
                        self.robot_move = False
                
            elif message["cmd"] == "ARU":
                data = message["data"]
                if data["etat"] == 1:
                    if 0x11 not in self.error:
                        self.strategie_is_running = False
                        self.recalage_is_playing = False
                        self.robot_move = False
                        if not self.is_started:
                            self.error.append(0x11)
                        else:
                            self.PAGE = 21
                        self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 503, "byte1": 0}))
                elif data["etat"] == 0:
                    if 0x11 in self.error:
                        self.error.remove(0x11)
                        self.PAGE = 0
                        self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 503, "byte1": 1}))
            
            elif message["cmd"] == "jack":
                data = message["data"]
                logging.info(f"Jack : {data}")
                if data["data"] == "input_jack":
                    self.text_page_play = "Veillez insérer le Jack"
                elif data["data"] == "wait_start":
                    self.text_page_play = "Prêt à démarrer le match"
                elif data["data"] == "start":
                    self.text_page_play = "Stratégie en cours..."
                    self.PAGE = 20
            
            elif message["cmd"] == "start":
                self.text_page_play = "Stratégie en cours..."
                self.PAGE = 20
                self.is_started = True
                logging.info("Début de la partie")
            
            elif message["cmd"] == "strategie":
                data = message["data"]
                id = data["id"]
                strategie = data["strategie"]
                
                # Récupère la liste des fichiers de stratégies
                liste_strategies = os.listdir(self.path_strat)
                
                # Vérifie si le nombre de fichier est inférieur à 8, si plus de 8 fichiers, on affiche les 8 derniers
                if len(liste_strategies) > 8:
                    liste_strategies = liste_strategies[-8:]
            
                    
                # Récupère le dernier numéro de stratégie pour enregistrer la nouvelle stratégie
                num_strategie = 0
                if len(liste_strategies) == 0:
                    path = self.path_strat + f"/strategie_1.json"
                    
                    with open(path, "w") as f:
                        f.write(json.dumps(strategie))
                else:
                    for strategy in liste_strategies:
                        try :
                            num = int(strategy.split("_")[1].split(".")[0])
                        except:
                            pass
                        if num > num_strategie:
                            num_strategie = num
                    
                    num_strategie += 1
                    path = self.path_strat + f"/strategie_{num_strategie}.json"
                    
                    with open(path, "w") as f:
                        f.write(json.dumps(strategie))
                
                """else:
                    # Si la stratégie existe, on met à jour la stratégie existante
                    with open(self.path_strat + f"/strategie_{id}.json", "w") as f:
                        f.write(json.dumps(strategie))"""
                
                self.create_button_strategie()
            
            elif message["cmd"] == "get_pos":
                data = message["data"]
                self.value_get_pos["id_herk"] = data["pos"]
            
            elif message["cmd"] == "lidar":
                data = message["data"]
                """if "etat" in data:
                    if data["etat"] == "start":
                        self.PAGE = 20 # PAGE de match
                        self.ETAT = 2
                    elif data["etat"] == "stop":
                        self.PAGE = 0
                        self.ETAT = 0
                    elif data["etat"] == "end":
                        self.PAGE = 21 # PAGE de fin de match 'points'
                        self.ETAT = 0"""
                logging.info(f"Lidar : {data}")

            elif message["cmd"] == "coord":
                coord = message["data"]
                self.ROBOT_pos = (int(coord["x"]), int(coord["y"]), int(coord["theta"]/10))
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
    
    def map_value(self,x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    
    def run(self):
        self.taille_auto_batterie()
        
        self.client.set_callback_stop(self.deconnexion)
        self.client.connect()
        self.request_energy()
        
        handle_temp_raspberry = threading.Thread(target=self.get_temp_raspberry)
        handle_temp_raspberry.start()
        
        while self.is_running:
            try:
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
                    
                    if self.PAGE == 0:
                        for batterie in self.batteries:
                            batterie.handle_event(event)
                        for button in self.button_favori:
                            button.handle_event(event)
                    elif self.PAGE == 1:
                        for button in self.button_strategie:
                            button.handle_event(event)
                    elif self.PAGE == 2:
                        pass
                    elif self.PAGE == 3:
                        for button in self.button_autres:
                            button.handle_event(event)
                    elif self.PAGE == 5:
                        pass
                    elif self.PAGE == 10:
                        for button in self.button_tests_mouvement:
                            button.handle_event(event)
                    elif self.PAGE == 11:
                        for button in self.button_tests_action:
                            button.handle_event(event)
                    elif self.PAGE == 12:
                        for button in self.button_tests_special:
                            button.handle_event(event)
                            
                    if self.PAGE != 20 and self.PAGE != 9: # Si on est pas sur la page de match on peut changer de page
                        for button in self.button_menu:
                            button.handle_event(event)
                    if self.PAGE == 9:
                        # Si on appuie en dehors des boutons de recalage, on revient à la page d'accueil
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            if event.pos[0] < 40 or event.pos[0] > 760:
                                self.PAGE = 0
                        
                        for zone in self.zone_recalage:
                            self.button_recalages[zone-1].handle_event(event)

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
                elif self.PAGE == 5:
                    self.page_play()
                elif self.PAGE == 9:
                    self.page_recalage()
                elif self.PAGE == 10:
                    self.page_mouvement()
                elif self.PAGE == 11:
                    self.page_action()
                elif self.PAGE == 12:
                    self.page_special()
                elif self.PAGE == 13:
                    self.page_get_pos()
                
                elif self.PAGE == 20:
                    self.page_match()
                elif self.PAGE == 21:
                    self.page_points()

                pygame.display.flip()
                self.clock.tick(30)
            except Exception as e:
                logging.error(f"Erreur : {str(e)}")
        pygame.quit()

if __name__ == "__main__":
    try:
        ihm = IHM_Robot()
        ihm.run()
    except Exception as e:
        logging.error(f"Erreur : {str(e)}")