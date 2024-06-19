import logging
from objet import Objet
import pygame
from pygame_gui import *
from pygame_gui.elements import *
from pygame.locals import *
from pygame_UI import *
import math
import os
import random
import numpy as np
#from sklearn.cluster import DBSCAN
from client import *
import json
import re

from windows import IHM_Command, IHM_Action_Aux, IHM_Save_Strat, IHM_Load_Strat

class IHM:
    def __init__(self, port=None):
        self.port = port
        self.lidar = None
        self.lcd = None
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.BLUE  = (0, 0, 255)
        self.RED   = (255, 0, 0)
        self.LIGHT_GREY = (200, 200, 200)
        self.DARK_GREEN = (0, 100, 0)
        self.FIELD_SIZE = (3000, 2000)
        self.POINT_COLOR = (255, 0, 0)
        self.BORDER_DISTANCE = 200
        self.BACKGROUND_COLOR = self.LIGHT_GREY
        self.FONT_COLOR = self.BLACK

        # Initialisation du robot virtuel
        self.ROBOT_Dimension = (264, 269)
        self.ROBOT = Objet(0, self.ROBOT_Dimension[0], self.ROBOT_Dimension[1], 20)
        self.ROBOT_ANGLE = 0

        self.path_picture = "data/Terrain_Jeu.png"
        self.id_compteur = 0    # Compteur pour les identifiants d'objet
        self.objets = []        # Liste pour stocker les objets détectés
        self.new_scan = []
        self.scanning = True
        self.ETAT = 0
        self.EQUIPE = "jaune"
        self.zone_depart = 1
        self.desactive_m = False

        self.Energie = {
            "Batterie 1": {"Tension": 10, "Courant": 0, "Switch": 0},
            "Batterie 2": {"Tension": 20, "Courant": 0, "Switch": 0},
            "Batterie 3": {"Tension": 10, "Courant": 0, "Switch": 0},
            "Batterie Main": {"Tension": 30, "Courant": 0, "Switch": 0}
        }

        self.pos_waiting_list = {}      # Liste pour stocker les futurs positions positions du robot à atteindre 
        self.robot_move = True          # Variable pour savoir si le robot est en mouvement
        self.numero_strategie = 0       # Numéro de la stratégie en cours
        self.angle_mouse = 0            # Angle de la souris
        self.perimetre_securite = 400   # Périmètre de sécurité autour des objets
        
        # Vider le fichier de sauvegarde des stratégies
        with open("data/strategie.json", "w") as f:
            f.write("{}")

        # Initialisation de Pygame et ajustement de la taille de la fenêtre
        pygame.init()
        info_object = pygame.display.Info()
        screen_width, screen_height = info_object.current_w, info_object.current_h - 100
        target_ratio = 3/2
        target_width  = min(screen_width, int(screen_height * target_ratio))
        target_height = min(screen_height, int(screen_width / target_ratio))
        self.WINDOW_SIZE = (target_width, target_height)
        self.X_RATIO = self.WINDOW_SIZE[0] / self.FIELD_SIZE[0]
        self.Y_RATIO = self.WINDOW_SIZE[1] / self.FIELD_SIZE[1]
        self.lcd = pygame.display.set_mode(self.WINDOW_SIZE)

        self.callbacks = {}

        self.BROADCAST = 0
        self.SERVEUR = 1
        self.CAN = 2
        self.LIDAR = 3
        self.STRATEGIE = 4
        self.IHM_Robot = 9
        self.IHM = 10
        self.client_socket = Client("192.168.22.101", 22050, self.IHM)
        self.image = pygame.image.load("data/Terrain_Jeu.png")
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 20)
        pygame.mouse.set_visible(True)
        pygame.display.set_caption('IHM')
        self.lcd.fill(self.BACKGROUND_COLOR)
        pygame.event.set_allowed([MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION])
        self.clicked_position = None  # Variable pour stocker les coordonnées du clic
        pygame.display.update()

        self.manager = pygame_gui.UIManager(self.WINDOW_SIZE)
        self.command_window = None
        self.action_window = None
        self.save_window = None
        self.load_window = None

        self.start_button = Button(self.lcd, pygame.Rect(self.WINDOW_SIZE[0]/2-50, self.WINDOW_SIZE[1]-55, 100, 40),"data/theme.json", "Démarrer", color=(20,200,20),on_click= self.start_match)
        self.command_button = Button(self.lcd, pygame.Rect(70, self.WINDOW_SIZE[1]-65, 120, 40),"data/theme.json", "Commandes",
                                    on_click= lambda : setattr(self, "command_window", IHM_Command(self.manager, 
                                                                                                   self.desactive_motor, 
                                                                                                   self.restart_motor,
                                                                                                   self.command_CAN
                                                                                                   )) if self.command_window is None else None)
        
        # Bouton pour enregistrer la stratégie en cours
        self.save_strategie_button = Button(self.lcd, pygame.Rect(210, self.WINDOW_SIZE[1]-65, 180, 40),"data/theme.json", "Enregistrer Stratégie",
                                    on_click= self.page_sauvegarde)
        
        # Bouton pour charger une stratégie
        self.load_strategie_button = Button(self.lcd, pygame.Rect(410, self.WINDOW_SIZE[1]-65, 160, 40),"data/theme.json", "Charger Stratégie",
                                    on_click= self.page_chargement)
        
        # Bouton pour ajouter la position actuelle du robot à la stratégie
        self.add_position_button = Button(self.lcd, pygame.Rect(590, self.WINDOW_SIZE[1]-65, 200, 40),"data/theme.json", "Ajouter Position",
                                    on_click= self.add_position)
        
        # Bouton pour play pour lancer la stratégie
        self.play_strategie_button = Button(self.lcd, pygame.Rect(810, self.WINDOW_SIZE[1]-65, 40, 40),"data/theme.json", "Play", #▶︎
                                    on_click= self.play_strategie)
        
        logging.basicConfig(filename='ihm.log', level=logging.INFO,
                            datefmt='%d/%m/%Y %H:%M:%S', format='%(asctime)s - %(levelname)s - %(message)s')

    # ======================== Fin de constructeur ==========================
    
    def draw_robot(self):
        x = self.ROBOT.x
        y = self.ROBOT.y
        angle = self.ROBOT_ANGLE
        x_r = self.map_value(x, 0, self.FIELD_SIZE[0], self.WINDOW_SIZE[0]-5-self.BORDER_DISTANCE*self.X_RATIO, self.BORDER_DISTANCE*self.X_RATIO+5)
        y_r = self.map_value(y, 0, self.FIELD_SIZE[1], self.BORDER_DISTANCE*self.Y_RATIO+5 ,self.WINDOW_SIZE[1]-5-self.BORDER_DISTANCE*self.Y_RATIO)
        x_r = int(x_r)
        y_r = int(y_r)
        # Dessiner le robot en fonction de ses coordonnées et de son angle et de ses dimensions en rectangle
        # Créer une nouvelle surface pour le robot
        robot_surface = pygame.Surface((self.ROBOT_Dimension[0] * self.X_RATIO, self.ROBOT_Dimension[1]* self.Y_RATIO), pygame.SRCALPHA)

        # Dessiner le rectangle du robot sur la nouvelle surface
        pygame.draw.rect(robot_surface, pygame.Color(101, 67, 33), (0, 0, self.ROBOT_Dimension[0] * self.X_RATIO, self.ROBOT_Dimension[1]* self.Y_RATIO), 0,10)

        dim_x = self.ROBOT_Dimension[0] * self.X_RATIO
        dim_y = self.ROBOT_Dimension[1] * self.Y_RATIO

        # Dessiner la flèche sur la nouvelle surface
        pygame.draw.polygon(robot_surface, pygame.Color(255, 0, 0), [(dim_x - 5, dim_y / 2), (dim_x /2, 10), (dim_x / 2, dim_y / 2 - 10),(10,dim_y / 2 - 10), (10,dim_y / 2 + 10), (dim_x / 2, dim_y / 2 + 10), (dim_x / 2, dim_y - 10), (dim_x-5, dim_y / 2)], 0)

        # Dessine un périmètre de sécurité autour du robot
        pygame.draw.circle(self.lcd, pygame.Color(255, 0, 0), (x_r, y_r), self.perimetre_securite * self.X_RATIO, 2)
        
        # Faire pivoter la surface du robot par rapport au centre
        # Obtenir la position actuelle du centre de la surface
        old_center = robot_surface.get_rect().center

        # Faire pivoter la surface du robot
        robot_surface = pygame.transform.rotate(robot_surface, angle+180)
        robot_surface_rect = robot_surface.get_rect(center=(x_r, y_r))

        # Obtenir la position du nouveau centre de la surface

        # Dessiner la surface du robot sur l'écran en ajustant les coordonnées pour que le centre reste à la même position
        self.lcd.blit(robot_surface, robot_surface_rect)
        
    def draw_image(self, image_path):

        # Redimensionne l'image
        image = pygame.transform.scale(self.image, ((self.FIELD_SIZE[0] - 2 * self.BORDER_DISTANCE) * self.X_RATIO,
                                               (self.FIELD_SIZE[1] - 2 * self.BORDER_DISTANCE) * self.Y_RATIO))

        # Dessine l'image à la position (x, y)
        self.lcd.blit(image, (self.BORDER_DISTANCE * self.X_RATIO,
                      self.BORDER_DISTANCE * self.Y_RATIO))

    def draw_background(self):
        self.lcd.fill(self.BACKGROUND_COLOR)
        self.draw_image(self.path_picture)
        self.draw_field()
        self.draw_data()
        # Afficher l'image en fond d'écran, dans l'emplacement du terrain de jeu

    def draw_mouse_coordinates(self):
        # Créer une police
        font = pygame.font.Font(None, 26)

        # Obtenir les coordonnées de la souris
        pos = pygame.mouse.get_pos()
        key = pygame.key.get_pressed()

        if self.is_within_game_area(pos):
            # Convertissez les coordonnées de la souris en coordonnées du terrain de jeu
            # On recalibre les coordonnées pour que le 0,0 soit en bas à droite
            x = self.map_value(pos[0], self.WINDOW_SIZE[0]-5-self.BORDER_DISTANCE*self.X_RATIO, self.BORDER_DISTANCE*self.X_RATIO+5, 0, self.FIELD_SIZE[0])
            y = self.map_value(pos[1], self.BORDER_DISTANCE*self.Y_RATIO+5 ,self.WINDOW_SIZE[1]-5-self.BORDER_DISTANCE*self.Y_RATIO, 0, self.FIELD_SIZE[1])

            # Créer un texte avec les coordonnées transformées
            self.draw_text_center(f"( {x:.0f}, {y:.0f} )", pos[0], pos[1]-20, font=font, bg=None)
            
            # Dessiner un petit cercle rouge sur la pointe de la souris
            pygame.draw.circle(self.lcd, pygame.Color(255, 0, 0), pos, 5)
            
            # Dessine le robot si la touche shift est enfoncée
            if key[pygame.K_LSHIFT]:
                robot_image = pygame.image.load('data/robot.png').convert_alpha()
                
                # Ajuster la taille de l'image du robot à la taille du terrain de jeu
                robot_image = pygame.transform.scale(robot_image, (int(self.ROBOT_Dimension[0] * self.X_RATIO), int(self.ROBOT_Dimension[1] * self.Y_RATIO)))
                
                # Rendre l'image du robot transparente pour que le fond soit visible
                robot_image.set_alpha(128)
                
                if key[pygame.K_LEFT]:
                    self.angle_mouse += 2
                elif key[pygame.K_RIGHT]:
                    self.angle_mouse -= 2
                
                # Tourner l'image du robot en fonction de l'angle de la souris
                robot_image = pygame.transform.rotate(robot_image, self.angle_mouse)
                
                # Ajuster la position pour que le robot soit centré sur la souris
                robot_pos = (pos[0] - robot_image.get_width() // 2, pos[1] - robot_image.get_height() // 2)
                self.lcd.blit(robot_image, robot_pos)
            else:
                self.angle_mouse = 0
                # Dessine le robot si la souris est a proximité d'un point de la liste d'attente
                for idx, pos_r in self.pos_waiting_list.items():
                    if math.sqrt((pos_r[0] - x)**2 + (pos_r[1] - y)**2) < 25:
                        robot_image = pygame.image.load('data/robot.png').convert_alpha()
                        
                        # Ajuster la taille de l'image du robot à la taille du terrain de jeu
                        robot_image = pygame.transform.scale(robot_image, (int(self.ROBOT_Dimension[0] * self.X_RATIO), int(self.ROBOT_Dimension[1] * self.Y_RATIO)))
                        
                        # Rendre l'image du robot transparente pour que le fond soit visible
                        robot_image.set_alpha(128)

                        # Tourner l'image du robot en fonction de l'angle du robot
                        robot_image = pygame.transform.rotate(robot_image, pos_r[2])
                        
                        # Ajuster la position pour que le robot soit centré le point de la liste d'attente
                        x_r = self.map_value(pos_r[0], 0, self.FIELD_SIZE[0], self.WINDOW_SIZE[0]-5-self.BORDER_DISTANCE*self.X_RATIO, self.BORDER_DISTANCE*self.X_RATIO+5)
                        y_r = self.map_value(pos_r[1], 0, self.FIELD_SIZE[1], self.BORDER_DISTANCE*self.Y_RATIO+5 ,self.WINDOW_SIZE[1]-5-self.BORDER_DISTANCE*self.Y_RATIO)
                        x_r = int(x_r)
                        y_r = int(y_r)
                        robot_pos = (x_r - robot_image.get_width() // 2, y_r - robot_image.get_height() // 2)
                        self.lcd.blit(robot_image, robot_pos)

    def draw_text(self, text, x, y, color=(0, 0, 0)):
        """Draws text to the pygame screen, on up left corner"""
        text = self.font.render(
            text, True, color, pygame.Color(self.BACKGROUND_COLOR))
        self.lcd.blit(text, (x, y))

    def draw_text_center(self, text, x, y, color=(0, 0, 0),font=None, bg =(200, 200, 200)):
        if font is None:
            font = pygame.font.Font(None, 36)
        if bg is None:
            text_surface = font.render(text, True, color)
        else:
            text_surface = font.render(text, True, color, pygame.Color(bg))
            
        text_rect = text_surface.get_rect(center=(x, y))
        self.lcd.blit(text_surface, text_rect)

    def draw_data(self):
        """Draws data to the pygame screen, on up left corner.For x, y and theta"""
        """Data is x, y and theta"""
        window_width, window_height = pygame.display.get_surface().get_size()
        self.draw_text("x: " + "{:.2f}".format(self.ROBOT.x),
                       window_width * 0.01, window_height * 0.01)
        self.draw_text("y: " + "{:.2f}".format(self.ROBOT.y),
                       window_width * 0.01, window_height * 0.05)
        self.draw_text("theta: " + "{:.2f}".format(self.ROBOT_ANGLE),
                       window_width * 0.1, window_height * 0.03)
        self.draw_text("speed: " + "{:.2f}".format(self.ROBOT.vitesse/10) +
                       " cm/s", window_width * 0.2, window_height * 0.01)
        self.draw_text("direction: " + "{:.2f}".format(
            self.ROBOT.direction), window_width * 0.2, window_height * 0.05)

        if (len(self.objets) > 0):
            '''Draws data, on up right corner.For x, y, speed and direction'''
            self.draw_text(
                "x: " + "{:.2f}".format(self.objets[0].x), window_width * 0.76, window_height * 0.01)
            self.draw_text(
                "y: " + "{:.2f}".format(self.objets[0].y), window_width * 0.76, window_height * 0.05)
            self.draw_text("speed: " + "{:.2f}".format(
                self.objets[0].vitesse/10) + " cm/s", window_width * 0.86, window_height * 0.01)
            self.draw_text("direction: " + "{:.2f}".format(
                self.objets[0].direction), window_width * 0.86, window_height * 0.05)
        
        # Dessine les données liées à l'énergie
        # Tension si la batterie est connectée
        k = 0
        for i, key in enumerate(self.Energie):
            if self.Energie[key]["Tension"] != 0:
                if k < 2:
                    self.draw_text(key + ": " + "{:.2f}".format(self.Energie[key]["Tension"]) + " V", window_width * 0.88, window_height * (0.92 + k*0.04))
                else :
                    self.draw_text(key + ": " + "{:.2f}".format(self.Energie[key]["Tension"]) + " V", window_width * 0.73, window_height * (0.92 + (k-2)*0.04))
                k += 1

    def draw_field(self):
        pygame.draw.rect(self.lcd, pygame.Color(100, 100, 100),
                         (self.BORDER_DISTANCE * self.X_RATIO - 5, self.BORDER_DISTANCE * self.Y_RATIO - 5,
                          (self.FIELD_SIZE[0] - 2 *
                           self.BORDER_DISTANCE) * self.X_RATIO + 10,
                          (self.FIELD_SIZE[1] - 2 * self.BORDER_DISTANCE) * self.Y_RATIO + 10), 10)

    def draw_point(self, x, y):
        self.POINT_COLOR = (200, 200, 200)

        if x > self.FIELD_SIZE[0] - self.BORDER_DISTANCE:
            x = self.FIELD_SIZE[0] - self.BORDER_DISTANCE
            self.POINT_COLOR = (0, 255, 0)
        elif x < self.BORDER_DISTANCE:
            x = self.BORDER_DISTANCE
            self.POINT_COLOR = (0, 255, 0)

        if y > self.FIELD_SIZE[1] - self.BORDER_DISTANCE:
            y = self.FIELD_SIZE[1] - self.BORDER_DISTANCE
            self.POINT_COLOR = (0, 255, 0)
        elif y < self.BORDER_DISTANCE:
            y = self.BORDER_DISTANCE
            self.POINT_COLOR = (0, 255, 0)

        pygame.draw.circle(self.lcd, pygame.Color(
            self.POINT_COLOR), (x * self.X_RATIO, y * self.Y_RATIO), 3)

    def draw_object(self, objet):
        x = self.map_value(objet.x, self.FIELD_SIZE[0], 0, self.WINDOW_SIZE[0]-5-self.BORDER_DISTANCE*self.X_RATIO, self.BORDER_DISTANCE*self.X_RATIO+5)
        y = self.map_value(objet.y, 0, self.FIELD_SIZE[1], self.BORDER_DISTANCE*self.Y_RATIO+5 ,self.WINDOW_SIZE[1]-5-self.BORDER_DISTANCE*self.Y_RATIO)
        pygame.draw.circle(self.lcd, pygame.Color(
            255, 255, 0), (x, y), 10)
        pygame.draw.circle(self.lcd, pygame.Color(50, 50, 200), (x, y), int(objet.taille / 2 * self.X_RATIO), 3)
        
        # Dessine le périmètre de sécurité autour de l'objet
        pygame.draw.circle(self.lcd, pygame.Color(255, 0, 0), (x, y), self.perimetre_securite * self.X_RATIO, 2)

        # Affichage des coordonnées de l'objet et de son ID
        self.draw_text("ID: " + str(objet.id), x + 20, y - 30)

        # Affichage de la direction et de la vitesse de l'objet avec un vecteur
        # direction, vitesse = objet.get_direction_speed()
        # pygame.draw.line(
        #     self.lcd, pygame.Color(255, 255, 0),
        #     (x, y),
        #     ((objet.x + vitesse * math.cos(direction)) * self.X_RATIO, (objet.y + vitesse * math.sin(direction)) * self.Y_RATIO), 3)

    def draw_list_position(self):
        # Dessine les positions de la liste d'attente par un point rouge
        # Et dessine le chemin entre le robot et le prochain point et entre les points
        new_waiting_list = []
        if self.pos_waiting_list:
            # Remettre dans la bonne origine les valeurs de position
            for idx, pos in self.pos_waiting_list.items():
                x = self.map_value(pos[0], 0, self.FIELD_SIZE[0], self.WINDOW_SIZE[0]-5-self.BORDER_DISTANCE*self.X_RATIO, self.BORDER_DISTANCE*self.X_RATIO+5)
                y = self.map_value(pos[1], 0, self.FIELD_SIZE[1], self.BORDER_DISTANCE*self.Y_RATIO+5 ,self.WINDOW_SIZE[1]-5-self.BORDER_DISTANCE*self.Y_RATIO)
                new_waiting_list.append((int(x), int(y)))

            # Dessine le chemin entre le robot et le prochain point
            x = 225
            y = 225
            x = int(self.map_value(x, 0, self.FIELD_SIZE[0], self.WINDOW_SIZE[0]-5-self.BORDER_DISTANCE*self.X_RATIO, self.BORDER_DISTANCE*self.X_RATIO+5))
            y = int(self.map_value(y, 0, self.FIELD_SIZE[1], self.BORDER_DISTANCE*self.Y_RATIO+5 ,self.WINDOW_SIZE[1]-5-self.BORDER_DISTANCE*self.Y_RATIO))
            # Dessine un point bleu sur le point de départ
            pygame.draw.circle(self.lcd, pygame.Color(0, 0, 255), (x, y), 5)
            pygame.draw.line(
                self.lcd, pygame.Color(0, 255, 0),
                (x, y),
                (new_waiting_list[0][0], new_waiting_list[0][1]), 3)
            
            # Dessine le points de départ
            pygame.draw.circle(self.lcd, pygame.Color(0, 0, 255), (x, y), 5)

            # Dessine le chemin entre les points
            for i in range(len(new_waiting_list) - 1):
                pygame.draw.line(
                    self.lcd, pygame.Color(0, 255, 0),
                    (new_waiting_list[i][0], new_waiting_list[i][1]),
                    (new_waiting_list[i + 1][0], new_waiting_list[i + 1][1]), 3)
                
            # Dessine les points de la liste d'attente
            for pos in new_waiting_list:
                pygame.draw.circle(self.lcd, pygame.Color(255, 0, 0), (pos[0], pos[1]), 5)

    def draw_all_trajectoires(self, trajectoire_actuel, trajectoire_adverse, trajectoire_evitement):
        # Dessin des trajectoires
        self.draw_trajectoire(trajectoire_actuel, color=(
            255, 0, 0))  # Rouge pour le robot actuel
        self.draw_trajectoire(trajectoire_adverse, color=(
            0, 0, 255))  # Bleu pour le robot adverse
        self.draw_trajectoire(trajectoire_evitement, color=(
            0, 255, 0))  # Vert pour la trajectoire d'évitement

    def draw_trajectoire(self, trajectoire, color=(255, 255, 255)):
        """
        Dessine une trajectoire sur l'écran.

        :param trajectoire: Liste de points (x, y) représentant la trajectoire
        :param color: Couleur de la trajectoire (RGB)
        """
        for point in trajectoire:
            x = int(point[0] * self.X_RATIO)
            y = int(point[1] * self.Y_RATIO)

            # Vérifier si le point n'est pas un nombre infini
            if x > 10000 or x < -10000 or y > 10000 or y < -10000:
                continue

            pygame.draw.circle(self.lcd, color, (x, y), 2)

    def transform_scan(self, scan, x_r, y_r, angle):
        """
        Transforme les données du scan en coordonnées cartésiennes.
        Retire les points en dehors du terrain de jeu.

        :param scan: Liste de tuples (quality, angle, distance)
        :param x_r: Coordonnée x du robot
        :param y_r: Coordonnée y du robot
        :param angle: Angle du robot
        :return: Liste de tuples (x, y, distance)
        """
        points = []
        for point in scan:
            distance = point[2]
            new_angle = point[1] - angle

            new_angle %= 360
            if new_angle < 0:
                new_angle += 360

            if distance != 0:
                x = distance * math.cos(math.radians(new_angle)) + x_r
                y = distance * math.sin(math.radians(new_angle)) + y_r

                # Vérifier si le point est en dehors du terrain de jeu
                if self.BORDER_DISTANCE < x < self.FIELD_SIZE[0] - self.BORDER_DISTANCE and self.BORDER_DISTANCE < y < self.FIELD_SIZE[1] - self.BORDER_DISTANCE:
                    points.append((x, y, distance, new_angle))
        return points

    def detect_objects(self, scan, eps=300, min_samples=3):
        pass
        """# Regroupement des points avec DBSCAN
        X = np.array([(point[0], point[1]) for point in scan])

        #eps = 200  # À ajuster en fonction de la densité des points
        #min_samples = 20  # À ajuster en fonction de la densité des points
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        labels = dbscan.fit_predict(X)

        # Création des objets à partir des clusters
        objets = []
        for label in set(labels):
            if label == -1:
                # Ignore les points considérés comme du bruit (pas de cluster)
                continue

            cluster_points = X[labels == label]
            x_moyen = np.mean(cluster_points[:, 0])
            y_moyen = np.mean(cluster_points[:, 1])

            # Calcul de la taille de l'objet (peut être ajusté en fonction de votre application)
            x_min = np.min(cluster_points[:, 0])
            x_max = np.max(cluster_points[:, 0])
            y_min = np.min(cluster_points[:, 1])
            y_max = np.max(cluster_points[:, 1])
            taille = math.sqrt((x_max - x_min)**2 + (y_max - y_min)**2)

            nouvel_objet = Objet(id=len(objets) + 1,
                                 x=x_moyen, y=y_moyen, taille=taille)
            objets.append(nouvel_objet)

        return objets"""

    def suivre_objet(self, objets, rayon_cercle=100):

        if len(self.objets) != len(objets):
            # Ajoute les objets manquants
            for objet in objets[len(self.objets):]:
                self.objets.append(objet)

        # Pré-calculer le carré du rayon du cercle
        rayon_cercle_carre = rayon_cercle ** 2
        # Vérifier si l'objet est déjà suivi
        objets_copy = objets.copy()
        for objet in self.objets:
            objets_dans_cercle = [objet_param for objet_param in objets_copy if (objet_param.x - objet.x)**2 + (objet_param.y - objet.y)**2 < rayon_cercle_carre]
            
            if objets_dans_cercle:
                # Trouver l'objet le plus proche
                objet_le_plus_proche = min(objets_dans_cercle, key=lambda objet_param: (objet_param.x - objet.x)**2 + (objet_param.y - objet.y)**2)
                self.objets[objet_le_plus_proche.id - 1].update_position(objet_le_plus_proche.x, objet_le_plus_proche.y)
                objets_copy.remove(objet_le_plus_proche)  # Retirer l'objet de la liste

        return None

    def trajectoires_anticipation(self, robot_actuel, robot_adverse, duree_anticipation=1.0, pas_temps=0.1, distance_securite=50):
        """
        Dessine les futures trajectoires des robots et la trajectoire d'évitement anticipée.

        :param robot_actuel: Objet représentant le robot actuel
        :param robot_adverse: Objet représentant le robot adverse
        :param duree_anticipation: Durée d'anticipation en secondes
        :param pas_temps: Pas de temps pour la simulation en secondes
        :param distance_securite: Distance de sécurité minimale entre les robots
        """
        # Copie des positions actuelles des robots
        x = robot_actuel.x
        y = robot_actuel.y
        x = int(self.map_value(x, 0, self.FIELD_SIZE[0], self.FIELD_SIZE[0], 0))

        x_actuel, y_actuel = x, y
        x_adverse, y_adverse = robot_adverse.x, robot_adverse.y

        # Copie des vitesses actuelles des robots
        _, vitesse_actuel = robot_actuel.get_direction_speed()
        _, vitesse_adverse = robot_adverse.get_direction_speed()

        # Liste pour stocker les points des trajectoires
        trajectoire_actuel = [(x_actuel, y_actuel)]
        trajectoire_adverse = [(x_adverse, y_adverse)]
        trajectoire_evitement = []

        # Simulation de mouvement pour anticiper la trajectoire future des robots
        for temps in range(int(duree_anticipation / pas_temps)):
            # Calcul des nouvelles positions des robots
            new_x_R, new_y_R = robot_actuel.calculate_dx_dy(
                robot_actuel.direction, vitesse_actuel, pas_temps)
            new_x_A, new_y_A = robot_adverse.calculate_dx_dy(
                robot_adverse.direction, vitesse_adverse, pas_temps)

            new_x_R += trajectoire_actuel[-1][0]
            new_y_R += trajectoire_actuel[-1][1]
            new_x_A += trajectoire_adverse[-1][0]
            new_y_A += trajectoire_adverse[-1][1]

            # Ajout des points aux trajectoires
            trajectoire_actuel.append((new_x_R, new_y_R))
            trajectoire_adverse.append((new_x_A, new_y_A))

            # Calcul de la distance entre les robots
            distance_entre_robots = math.sqrt(
                (new_x_R - new_x_A)**2 + (new_y_R - new_y_A)**2)

            # Vérification de la collision anticipée
            if distance_entre_robots < distance_securite:
                # Proposer un chemin d'évitement
                trajectoire_evitement = [(x_actuel, y_actuel)]
                for temps_evitement in range(int(duree_anticipation / pas_temps)):
                    # Choisir une direction d'évitement
                    direction_evitement = (
                        robot_actuel.direction + math.pi) % (2 * math.pi)

                    # Simulation de mouvement pour l'évitement
                    new_x_E, new_y_E = robot_actuel.calculate_dx_dy(
                        direction_evitement, vitesse_actuel, pas_temps)

                    new_x_E += trajectoire_evitement[-1][0]
                    new_y_E += trajectoire_evitement[-1][1]

                    # Ajout des points à la trajectoire d'évitement
                    trajectoire_evitement.append((new_x_E, new_y_E))

                break

        return trajectoire_actuel, trajectoire_adverse, trajectoire_evitement

    def stop(self):
        print("Arret du Programme en cours...")
        self.objets = []
        self.scanning = False

    def load_json(self, json_string):
        try:
            data = json.loads(json_string)
        except Exception as e:
            logging.error(f"Failed to unload JSON: {e}")
            print(f"Failed to unload JSON : {json_string}")
            return None
        for item in data:
            if item["id"] == 1:
                self.objets[0].update_position(item["x"], item["y"])
                self.objets[0].taille = item["taille"]
            elif item["id"] == 2:
                pass

    def desactive_motor(self):
        self.desactive_m = not self.desactive_m
        self.client_socket.add_to_send_list(self.client_socket.create_message(2, "desa", self.desactive_m))
        print("Moteur est", "désactivé" if self.desactive_m else "activé")

    def restart_motor(self):
        self.client_socket.add_to_send_list(self.client_socket.create_message(2, "resta", True))
        print("Moteur est activé")

    def command_CAN(self, message):
        commande = message[0]
        if type(commande) == str:
            if commande[:2] != "0x":
                commande = "0x" + commande
            commande = int(commande, 16)
        byte1 = int(message[1])
        byte2 = int(message[2])
        byte3 = int(message[3])
        print(f"Commande CAN: {commande}, {byte1}, {byte2}, {byte3}")
        self.client_socket.add_to_send_list(self.client_socket.create_message(2, "CAN", {"id": commande, "byte1": byte1, "byte2": byte2, "byte3": byte3}))

    def valeur_de_test(self):
        scan = []
        for i in range(0, 360):
            angle = i + self.ROBOT_ANGLE
            angle %= 360
            if 200 <= i <= 215:
                distance = random.randint(1000, 1050)
            elif 345 <= i < 360:
                distance = random.randint(800, 850)
            elif 80 <= i <= 95:
                distance = random.randint(700, 720)
            else:
                distance = random.randint(700, 900)
                distance = 2000
            scan.append((0, angle, distance))
        return scan

    def receive_to_server(self, message):
        if message["cmd"] == "objects":
            try:
                self.objets = []
                if len(message["data"]) <= 2:
                    return
                json_string = json.loads(message["data"])
                for obj in json_string:
                    x_o = self.map_value(obj["x"], 0, self.FIELD_SIZE[0], self.FIELD_SIZE[0], 0)
                    self.objets.append(
                        Objet(obj["id"], x_o, obj["y"], obj["taille"]))
            except Exception as e:
                print("Erreur dans la réception des objets", e)
                
        elif message["cmd"] == "coord":
            coord = message["data"]
            self.ROBOT.update_position(coord["x"], coord["y"])
            self.ROBOT_ANGLE = coord["theta"]/10 # Angle en degrés * 10
            
        elif message["cmd"] == "points":
            try:
                scan = message["data"]
                scan = json.loads(scan)
                self.new_scan = []
                for point in scan:
                    #x_r = self.map_value(point["x"], 0, self.FIELD_SIZE[0], self.WINDOW_SIZE[0]-5-self.BORDER_DISTANCE*self.X_RATIO, self.BORDER_DISTANCE*self.X_RATIO+5)
                    x_r = self.map_value(point["x"], 0, self.FIELD_SIZE[0], self.FIELD_SIZE[0], 0)
                    self.new_scan.append(
                        (x_r, point["y"], point["dist"], point["angle"]))
            except Exception as e:
                print("Erreur dans la réception des points", e)
                
        elif message["cmd"] == "energie":
            energie = message["data"]
            self.update_energie(energie)
            
        elif message["cmd"] == "akn_m":
            self.robot_move = False
            #self.pos_waiting_list.pop(0)
        
        elif message["cmd"] == "config":
            config = message["data"]
            self.ETAT = config["etat"]
            self.EQUIPE = config["equipe"]

        elif message["cmd"] == "stop":
            self.client_socket.stop()

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

    def map_value(self,x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def handle_mouse_click(self, event):
        key = pygame.key.get_pressed()
        # Si la touche MAJ gauche est enfoncée et que l'on clique
        if (event.type == MOUSEBUTTONDOWN and event.button == 1) and key[pygame.K_LSHIFT]:
            # Vérifiez si le clic a eu lieu dans la zone de jeu
            if self.is_within_game_area(event.pos):
                # Convertissez les coordonnées de la souris en coordonnées du terrain de jeu
                #On recalibre les coordonnées pour que le 0,0 soit en bas à droite
                x = self.map_value(event.pos[0], self.WINDOW_SIZE[0]-5-self.BORDER_DISTANCE*self.X_RATIO, self.BORDER_DISTANCE*self.X_RATIO+5, 0, self.FIELD_SIZE[0])
                y = self.map_value(event.pos[1], self.BORDER_DISTANCE*self.Y_RATIO+5 ,self.WINDOW_SIZE[1]-5-self.BORDER_DISTANCE*self.Y_RATIO, 0, self.FIELD_SIZE[1])
                x = int(x)
                y = int(y)
                
                # Stockez les coordonnées du clic
                self.clicked_position = (x, y)

                if self.action_window is None:
                    self.action_window = IHM_Action_Aux(self.manager, self.numero_strategie+1, (x, y, self.ROBOT_ANGLE), _callback_save=self.save_action, _angle = self.angle_mouse)
        
        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            # Si le clic droit est dans les alentours d'un point de la liste d'attente, ouvrir le gestionnaire de stratégie
            try:
                for idx, pos in self.pos_waiting_list.items():
                    i = int(idx)
                    x = self.map_value(pos[0], 0, self.FIELD_SIZE[0], self.WINDOW_SIZE[0]-5-self.BORDER_DISTANCE*self.X_RATIO, self.BORDER_DISTANCE*self.X_RATIO+5)
                    y = self.map_value(pos[1], 0, self.FIELD_SIZE[1], self.BORDER_DISTANCE*self.Y_RATIO+5 ,self.WINDOW_SIZE[1]-5-self.BORDER_DISTANCE*self.Y_RATIO)
                    x = int(x)
                    y = int(y)
                    # Vérifiez si le clic est à proximité d'un point de la liste d'attente à moins de 10 pixels
                    if math.sqrt((event.pos[0] - x)**2 + (event.pos[1] - y)**2) < 10:
                        if self.action_window is None:
                            with open("data/strategie.json", "r") as file: # BUG: Suite jamais exécutée
                                strategie = json.load(file)
                            strat = strategie[str(i)]
                            if "Coord" in strat["Déplacement"]:
                                strat["Déplacement"]["Coord"]["T"] = strat["Déplacement"]["Coord"]["T"]//10
                            elif "Rotation" in strat["Déplacement"]:
                                strat["Déplacement"]["Rotation"] = strat["Déplacement"]["Rotation"]//10
                            try:
                                self.action_window = IHM_Action_Aux(self.manager, i, (pos[0], pos[1], 0), _callback_save=self.save_action, _config = strat, _callback_delete=self.delete_action, _id = "save")
                            except Exception as e:
                                print(f"Erreur dans l'ouverture de la fenêtre de configuration de l'action {i+1} :", e)                               
                        break
            except Exception as e:
                print("Erreur dans la gestion des clics :", e)

    def is_within_game_area(self, pos):
        # Vérifie si les coordonnées du clic sont dans la zone de jeu
        return self.BORDER_DISTANCE * self.X_RATIO + 5 <= pos[0] <= (self.FIELD_SIZE[0] - self.BORDER_DISTANCE) * self.X_RATIO -5\
            and self.BORDER_DISTANCE * self.Y_RATIO + 5 <= pos[1] <= (self.FIELD_SIZE[1] - self.BORDER_DISTANCE) * self.Y_RATIO -5

    def go_to_position(self):
        # Cette fonction gère les déplacements du robot
        # Elle vérifie s'il y a des positions à atteindre, si le robot attent ou est en mouvement
        # Elle envoie les commandes de déplacement au CAN

        # Si la liste des positions à atteindre n'est pas vide
        if self.pos_waiting_list:
            # Si le robot n'est pas en mouvement
            if not self.robot_move:
                self.robot_move = True
                # Prenez la première position de la liste
                pos = self.pos_waiting_list[str(0)]
                # Envoyez la position au CAN
                self.client_socket.add_to_send_list(self.client_socket.create_message(
                    self.CAN, "clic", {"x": pos[0], "y": pos[1], "theta": pos[2], "sens": pos[3]}))
                print("Going to position:", pos)
        elif len(self.pos_waiting_list) == 0 and not self.robot_move:
            self.robot_move = True
            self.numero_strategie = 0
            
            print("Fin du trajet")

    def page_sauvegarde(self):
        # Page de sauvegarde de la stratégie / permet de choisir le nombre de points de la stratégie
        
        if self.numero_strategie > 0 and self.save_window is None:
            # Extraire les numéros des fichiers existants
            files = os.listdir("data/strategies")
            numbers = [int(re.search(r'\d+', file).group()) for file in files if re.search(r'\d+', file)]

            # Trouver le numéro le plus élevé et l'incrémenter pour le nouveau fichier
            if numbers:
                numero = max(numbers) + 1
            else:
                numero = 1
                
            name_strat = "strategie_" + str(numero)
            
            self.save_window = IHM_Save_Strat(self.manager, name_strat)
            self.save_window.set_callback_save(self.save_strategie)
        else:
            print("Aucune stratégie à sauvegarder")
    
    def page_chargement(self):
        # Page de chargement de la stratégie / permet de choisir le fichier à charger
        
        files = os.listdir("data/strategies")
        files = [file for file in files if file.endswith(".json")]
        
        # Mettre les stratégies dans l'ordre alphabétique
        def key_func(strategie):
            match = re.match(r"strategie_(\d+)", strategie)
            if match:
                # Pour les stratégies numérotées, renvoyer le numéro pour le tri
                return int(match.group(1))
            else:
                # Pour les stratégies nommées, renvoyer une valeur élevée pour les placer à la fin
                return float('inf')
        
        files = sorted(files, key=key_func)
        
        if files and self.load_window is None:
            self.load_window = IHM_Load_Strat(self.manager, files)
            self.load_window.set_callback_load(self.load_strategie)
        else:
            print("Aucune stratégie à charger")
    
    def delete_action(self, numero):
        # Permet de supprimer une action de la stratégie
        print("Suppression de l'action", numero)
        
        with open("data/strategie.json", "r") as file:
            strategie = json.load(file)
        try:
            strategie.pop(str(numero))
        except KeyError:
            pass
        
        # Supprimer les coordonnées de la liste d'attente
        self.pos_waiting_list.pop(numero)
        self.numero_strategie -= 1
        # Modifier les numéros des actions suivantes
        for i in range(numero+1, len(strategie)+2):
            strat = strategie.pop(str(i))
            strat["id_action"] = i-1
            strategie[str(i-1)] = strat
            
            # Modifier les numéros des coordonnées de la liste d'attente
            pos = self.pos_waiting_list.pop(i)
            self.pos_waiting_list[i-1] = pos
        
        with open("data/strategie.json", "w") as file:
            json.dump(strategie, file, indent=4)
            
        self.action_window.close()
        self.action_window = None
    
    def save_action(self, strat, _action = ""):
        try:
            action = strat["Action"]
            numero = strat["id_action"]
            vitesse = strat.get("Vitesse", "Normal")
            id_action = numero
            strat.pop("id_action")
            
            strategie = {str(numero): strat}
            print(f"\n[ Enregistrement ...\n| ID : {numero} | Déplacement", strat["Déplacement"], "\n| Action", action, "| Special", strat["Special"])
            
            if numero > 1: # Récupérer les coordonnées précédentes
                coord_prec = self.pos_waiting_list[numero-1]
            else:
                coord_prec = (225, 225, 0, "0")
            
            if "Coord" in strat["Déplacement"]:
                coord = strat["Déplacement"]["Coord"]
                
                
                """if coord["T"] == "":
                    # Si l'angle d'arrivée n'est pas renseigné, on calcule l'angle entre le robot et la position d'arrivée
                    angle = math.degrees(math.atan2(coord["Y"] - coord_prec[1], coord["X"] - coord_prec[0]))
                    coord["T"] = int(angle*10)
                else:
                    coord["T"] = int(coord["T"]*10) if -360 <= int(coord["T"]) <= 360 else int(coord["T"])
                    
                new_pos = (int(coord["X"]), int(coord["Y"]), coord["T"], "0")"""
                
                coord = strat["Déplacement"]["Coord"]
        
        
                """if coord["T"] == "":
                    # Si l'angle d'arrivée n'est pas renseigné, on calcule l'angle entre le robot et la position d'arrivée
                    angle = math.degrees(math.atan2(coord["Y"] - coord_prec[1], coord["X"] - coord_prec[0]))
                    coord["T"] = int(angle*10)
                else:
                    coord["T"] = int(coord["T"]*10) if -360 <= int(coord["T"]) <= 360 else int(coord["T"])
                    
                new_pos = (int(coord["X"]), int(coord["Y"]), coord["T"], "0")"""
                
                coord = strat["Déplacement"]["Coord"]
        
                # Calcul de l'angle de rotation nécessaire
                angle_destination = math.degrees(math.atan2(coord["Y"] - coord_prec[1], coord["X"] - coord_prec[0]))
                # Normalisation de l'angle entre -180 et 180
                angle_deplacement = angle_destination if angle_destination < 180 else angle_destination - 360
                angle_deplacement = angle_deplacement
                
                # Conversion de l'angle actuel en une valeur entre 0 et 360
                angle_arrivee = coord["T"] if coord["T"] != "" else None
                
                # Conversion angle actuel en une valeur entre -180 et 180
                angle_prec = coord_prec[2] if coord_prec[2] < 180 else coord_prec[2] - 360
                
                if angle_arrivee is None:
                    # Si l'angle d'arrivée n'est pas renseigné, utilisez l'angle calculé
                    coord["T"] = int(angle_deplacement)
                    
                # Calcul de la différence d'angle la plus courte
                delta_angle = angle_deplacement - angle_prec
                delta_angle = (delta_angle + 180) % 360 - 180  # Ajustement pour le chemin le plus court
                
                # Si la rotation nécessaire est inf"rieur à 90 degrés, il peut être plus efficace de reculer
                if abs(delta_angle) > 90:
                    # Ajustement de l'angle pour la marche arrière
                    if delta_angle < 0:
                        delta_angle = delta_angle + 180
                    else:
                        delta_angle = delta_angle - 180             
                    
                    # Calcul de la distance à parcourir pour atteindre la position en marche arrière
                    distance = int(math.sqrt((coord["X"] - coord_prec[0])**2 + (coord["Y"] - coord_prec[1])**2))
                    #print("Distance", distance, "Delta angle", delta_angle, "Angle destination", angle_destination, "Angle actuel", angle_prec)
                    # Si la distance n'est pas nulle, on les actions tourner et avancer
                    if distance != 0:
                        # On ajoute l'action de rotation
                        angle_deplacement = angle_deplacement + 180
                        new_pos = (coord_prec[0], coord_prec[1], angle_deplacement, "0")
                        print(180 - angle_destination)
                        self.pos_waiting_list[numero] = new_pos
                        
                        new_x = int(coord_prec[0] - distance * math.cos(math.radians(angle_deplacement)))
                        new_y = int(coord_prec[1] - distance * math.sin(math.radians(angle_deplacement)))
                        
                        new_pos = (new_x, new_y, angle_deplacement, "0") # Ajout coord après distance
                        self.pos_waiting_list[numero+1] = new_pos
                        
                        # Création de la nouvelle action
                        strategie = {}
                        strategie[str(numero)] = {"Déplacement": {"Rotation": int(delta_angle * 10), 'aknowledge' : 278}, "Action": action, "Special": {}, "Vitesse": vitesse}
                        strategie[str(numero+1)] = {"Déplacement": {"Ligne_Droite": -distance, 'aknowledge' : 277}, "Action": {}, "Special": {}, "Vitesse": vitesse}
                        
                        numero += 1
                        if angle_arrivee is not None:
                            # Calcul le delta angle pour l'angle d'arrivée en fonction de l'angle de destination
                            angle_a = int(angle_arrivee - angle_deplacement)
                            
                            coord["T"] = angle_a
                            strategie[str(numero+1)] = {"Déplacement": {"Rotation": int(coord["T"]*10), 'aknowledge' : 278}, "Action": {}, "Special": {}, "Vitesse": vitesse}
                            print(f"|  Rotation : {delta_angle} | Distance : {distance} | Reculer | Rotation : {coord['T']}")
                            new_pos = (new_x, new_y, angle_arrivee, "0")
                            self.pos_waiting_list[numero+1] = new_pos
                            numero += 1
                        else:
                            print(f"| Rotation : {delta_angle} | Distance : {distance} ")
                    else:
                        pass
                else:
                    new_pos = (int(coord["X"]), int(coord["Y"]), coord["T"], "0")
                    print(f"| Coord : {coord['X']}, {coord['Y']} | Angle arrivée : {coord["T"]}")
                    strategie[str(numero)]["Déplacement"]["Coord"]["T"] = int(coord["T"] * 10)
                    self.pos_waiting_list[numero] = new_pos
                    
            elif "Ligne_Droite" in strat["Déplacement"]:
                distance = strat["Déplacement"]["Ligne_Droite"]
                print(f"| Distance : {distance}")
                # Calcul de la position d'arrivée en fonction de la coordonnée précédente       
                x = coord_prec[0] + distance * math.cos(math.radians(coord_prec[2]))
                y = coord_prec[1] + distance * math.sin(math.radians(coord_prec[2]))
                new_pos = (int(x), int(y), coord_prec[2], "0")
                self.pos_waiting_list[numero] = new_pos
                
            elif "Rotation" in strat["Déplacement"]:
                angle = strat["Déplacement"]["Rotation"]
                print(f"| Rotation : {angle}")
                # Calcul de l'angle d'arrivée en fonction de l'angle précédent
                if _action == "" or True :
                    x = coord_prec[0]
                    y = coord_prec[1]
                else:
                    x = self.pos_waiting_list[numero][0]
                    y = self.pos_waiting_list[numero][1]
                
                strategie[str(numero)]["Déplacement"]["Rotation"] = int(angle * 10)
                angle = (coord_prec[2] + angle)
                new_pos = (x, y, angle, "0")
                self.pos_waiting_list[numero] = new_pos
            
            new_window = None
            
            with open("data/strategie.json", "r") as file:
                try:
                    data = json.load(file)
                except:
                    data = {}
                try:
                    data.update(strategie)
                except KeyError:
                    pass
                    
            with open("data/strategie.json", "w") as file:
                json.dump(data, file, indent=4)
            
            if self.action_window is not None:
                self.action_window.close()
                self.action_window = None
            
            if numero >= self.numero_strategie and _action == "":
                self.numero_strategie += 1 + (numero - id_action)
            
            # Si l'action est next ou back, on ouvre une nouvelle fenêtre de configuration avec les valeurs de l'action suivante ou précédente
            if _action == "next" and numero < self.numero_strategie:
                strategie = data[str(numero+1)]
                if "Coord" in strategie["Déplacement"]:
                    strategie["Déplacement"]["Coord"]["T"] = strategie["Déplacement"]["Coord"]["T"]//10
                elif "Rotation" in strategie["Déplacement"]:
                    strategie["Déplacement"]["Rotation"] = strategie["Déplacement"]["Rotation"]//10
                
                try:
                    new_window = IHM_Action_Aux(self.manager, numero+1, self.pos_waiting_list[numero+1], _callback_save=self.save_action, _config = strategie, _callback_delete=self.delete_action, _id="New_wind")
                except KeyError:
                    print("Erreur dans la récupération de la configuration de l'action")
            
            elif _action == "back" and numero > 1:
                strategie = data[str(numero-1)]
                if "Coord" in strategie["Déplacement"]:
                    strategie["Déplacement"]["Coord"]["T"] = strategie["Déplacement"]["Coord"]["T"]//10
                elif "Rotation" in strategie["Déplacement"]:
                    strategie["Déplacement"]["Rotation"] = strategie["Déplacement"]["Rotation"]//10
                
                try:
                    new_window = IHM_Action_Aux(self.manager, numero-1, self.pos_waiting_list[numero-1], _callback_save=self.save_action, _config = strategie, _callback_delete=self.delete_action, _id="New_wind")
                except KeyError:
                    print("Erreur dans la récupération de la configuration de l'action")
            else:
                new_window = None
            
            self.action_window = new_window
        except Exception as e:
            print("Erreur dans la sauvegarde de l'action :", e)
        
        
    
    def save_strategie(self, data):
        # Permet de sauvegarder la stratégie en cours
        name_strat = data["Nom"].split('_')[-1]        
        nb_points = data["Nb_points"]
        
        # Chargement de la stratégie actuelle
        with open("data/strategie.json", "r") as file:
            strategie = json.load(file)
        
        # Ajout des méta-données de la stratégie
        strategie["meta"] = {"Nom": data["Nom"], "Nb_points": nb_points}

        # Sauvegarde de la stratégie
        with open(f"data/strategies/strategie_{name_strat}.json", "w") as file:
            json.dump(strategie, file, indent=4)
            
        self.client_socket.add_to_send_list(self.client_socket.create_message(self.IHM_Robot,"strategie", {"id": name_strat,"strategie": strategie}))           
    
    def load_strategie(self, name_strat):
        # Permet de charger une stratégie sauvegardée

        # Charger la stratégie
        with open(f"data/strategies/{name_strat}", "r") as file:
            strategie = json.load(file)
        # Charger la stratégie dans le programme
        with open("data/strategie.json", "w") as file:
            json.dump(strategie, file, indent=4)
            
        if "meta" in strategie:
            meta = strategie["meta"]
            points = meta["Nb_points"]
            strategie.pop("meta")
            
        self.pos_waiting_list = {}
        self.numero_strategie = 1
        
        for key, strat in strategie.items():
            # Ajout du numéro de l'action
            strat["id_action"] = self.numero_strategie
            # Division par 10 pour la valeur de l'angle
            if "Coord" in strat["Déplacement"]:
                strat["Déplacement"]["Coord"]["T"] = strat["Déplacement"]["Coord"]["T"]//10
            elif "Rotation" in strat["Déplacement"]:
                strat["Déplacement"]["Rotation"] = strat["Déplacement"]["Rotation"]//10
            try:
                self.save_action(strat)
            except Exception as e:
                raise Exception(f"Erreur dans le chargement de l'action {key} :", e)
    
        # for key in strategie:
        #     action = strategie[key]
        #     self.numero_strategie = key
            
        #     if len(self.pos_waiting_list) > 1: # Récupérer les coordonnées précédentes
        #         coord_prec = self.pos_waiting_list[str(self.numero_strategie-1)]
        #     else:
        #         coord_prec = (225, 225, 0, "0")
            
        #     if "Coord" in action["Déplacement"]:
        #         coord = action["Déplacement"]["Coord"]
                    
        #         new_pos = (int(coord["X"]), int(coord["Y"]), (coord["T"]//10), "0")
                    
        #     elif "Ligne_Droite" in action["Déplacement"]:
        #         distance = action["Déplacement"]["Ligne_Droite"]
                    
        #         x = coord_prec[0] + distance * math.cos(math.radians((coord_prec[2])))
        #         y = coord_prec[1] + distance * math.sin(math.radians((coord_prec[2])))
        #         new_pos = (int(x), int(y), coord_prec[2], "0")
                
        #     elif "Rotation" in action["Déplacement"]:
        #         angle = action["Déplacement"]["Rotation"]
                
        #         # Calculer le nouvel angle en fonction de l'angle précédent
        #         new_angle = coord_prec[2] + angle//10
        #         new_angle %= 360
        #         new_pos = (coord_prec[0], coord_prec[1], new_angle, "0")
        
        #     self.pos_waiting_list[str(self.numero_strategie)] = new_pos
            
    def add_position(self):
        pass

    def play_strategie(self):
        self.robot_move = False
    
    def init_match(self):
        # Définir les rectangles de départ
        shape_x = 400
        shape_y = 350
        start_positions = [pygame.Rect((self.FIELD_SIZE[0] - self.BORDER_DISTANCE - shape_x) * self.X_RATIO - 5, self.BORDER_DISTANCE * self.Y_RATIO + 5, shape_x * self.X_RATIO, shape_y * self.Y_RATIO),
                           pygame.Rect(self.BORDER_DISTANCE * self.X_RATIO + 5, self.BORDER_DISTANCE * self.Y_RATIO + 5, shape_x * self.X_RATIO, shape_y * self.Y_RATIO),
                           pygame.Rect((self.FIELD_SIZE[0] - self.BORDER_DISTANCE - shape_x) * self.X_RATIO - 5, (self.FIELD_SIZE[1] - self.BORDER_DISTANCE - shape_y) * self.Y_RATIO - 5, shape_x * self.X_RATIO, shape_y * self.Y_RATIO),
                           pygame.Rect(self.BORDER_DISTANCE * self.X_RATIO + 5, (self.FIELD_SIZE[1] - self.BORDER_DISTANCE - shape_y) * self.Y_RATIO - 5, shape_x * self.X_RATIO, shape_y * self.Y_RATIO)]
        angle_depart = [180, 0, 0, 180]
        pos_r_depart = [((0 + self.ROBOT_Dimension[0]/2), (0 + self.ROBOT_Dimension[1]/2)), 
                        ((self.FIELD_SIZE[0] - self.ROBOT_Dimension[0]/2), (0 + self.ROBOT_Dimension[1]/2)), 
                        ((0 + self.ROBOT_Dimension[0]/2), (self.FIELD_SIZE[1] - self.ROBOT_Dimension[1]/2)), 
                        ((self.FIELD_SIZE[0] - self.ROBOT_Dimension[0] / 2), (self.FIELD_SIZE[1] - self.ROBOT_Dimension[1]/2))]
        
        self.start_button.draw()

        for event in pygame.event.get():
            self.start_button.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                for i, rect in enumerate(start_positions):
                    if rect.collidepoint(mouse_pos):
                        print(f"Robot commencera à la position de départ {i+1}, x: {pos_r_depart[i][0]}, y: {pos_r_depart[i][1]}, angle: {angle_depart[i]}")
                        self.zone_depart = i
                        if self.zone_depart%2 == 0:
                            self.EQUIPE = "jaune"
                        else:
                            self.EQUIPE = "bleu"
                        print("Equipe:", self.EQUIPE)

        # Dessiner les rectangles de départ
        for i, rect in enumerate(start_positions):
            color = (0, 255, 0) if i == self.zone_depart else (255, 255, 255)
            pygame.draw.rect(self.lcd, color, rect, 10)
 
    def start_match(self):# Démarre le match
        self.ETAT = 1
        self.client_socket.add_to_send_list(self.client_socket.create_message(self.IHM_Robot, "config", {"equipe": self.EQUIPE, "etat": self.ETAT}))

    def programme_simulation(self):
        print("Programme de simulation")
        logging.info("Starting simulation program")
        last_time = time.time()
        self.ROBOT.x = 225
        self.ROBOT.y = 225

        while True:
            keys = pygame.key.get_pressed()
            quit = pygame.event.get(pygame.QUIT)
            if quit or keys[pygame.K_ESCAPE] or keys[pygame.K_SPACE]:
                exit(0)

            scan = self.valeur_de_test()
            new_scan = self.transform_scan(scan, self.ROBOT.x, self.ROBOT.y, self.ROBOT_ANGLE)

            # self.detect_object(new_scan)
            #new_objets = self.detect_objects(new_scan)
            #self.suivre_objet(new_objets, 100)

            self.draw_background()
            self.draw_list_position()

            if self.ETAT == 0:
                self.draw_text_center("INITIALISATION DU MATCH", self.WINDOW_SIZE[0] / 2, 35, self.RED)
                self.init_match()
            elif self.ETAT == 1:
                self.draw_text_center("MATCH EN COURS", self.WINDOW_SIZE[0] / 2, 35, self.RED)

                self.command_button.draw()
                self.save_strategie_button.draw()
                self.load_strategie_button.draw()
                self.add_position_button.draw()
                self.play_strategie_button.draw()

            for event in pygame.event.get():
                self.manager.process_events(event)
                if event.type == UI_WINDOW_CLOSE: # BUG: Fermeture de la fenêtre non personnalisée
                    if self.command_window:
                        self.command_window = None
                    elif self.save_window:
                        self.save_window = None
                    elif self.load_window:
                        self.load_window = None
                    elif self.action_window:
                        if self.action_window.get_id() != "New_wind":
                            self.action_window = None          
                if self.command_window:
                    self.command_window.process_events(event)
                elif self.action_window:
                    self.action_window.process_events(event)
                elif self.save_window:
                    self.save_window.process_events(event)
                elif self.load_window:
                    self.load_window.process_events(event)
                elif self.ETAT == 1:
                    self.handle_mouse_click(event)

                if self.ETAT == 1:
                    self.go_to_position()
                    self.command_button.handle_event(event)
                    self.save_strategie_button.handle_event(event)
                    self.load_strategie_button.handle_event(event)
                    self.add_position_button.handle_event(event)
                    self.play_strategie_button.handle_event(event)
            
            self.draw_robot()

            for objet in self.objets:
                self.draw_object(objet)

            for point in new_scan:
                self.draw_point(point[0], point[1])
            
            self.draw_mouse_coordinates()

            # Affiche les fps sur l'écran (en bas a gauche)
            self.draw_text(
                "FPS: " + str(int(1 / (time.time() - last_time))), 10, self.WINDOW_SIZE[1] - 30)
            last_time = time.time()

            self.manager.update(1/60.0)
            self.manager.draw_ui(self.lcd)
            pygame.display.update()
            self.lcd.fill(self.WHITE)
            #self.ROBOT_ANGLE += 1

            # Déplacement du robot virtuel avec des touches du clavier
            x = self.ROBOT.x
            y = self.ROBOT.y

            if keys[pygame.K_LEFT]:
                x += 10
            if keys[pygame.K_RIGHT]:
                x -= 10
            if keys[pygame.K_UP]:
                y -= 10
            if keys[pygame.K_DOWN]:
                y += 10
            self.ROBOT.update_position(x, y)

            time.sleep(0.01)
    
    def run(self):
        #self.programme_simulation()
        
        self.client_socket.set_callback(self.receive_to_server)
        self.client_socket.set_callback_stop(self.stop)
        self.client_socket.connect()
        print("Connecté au serveur")
        while self.scanning:
            try:
                key = pygame.key.get_pressed()
                quit = pygame.event.get(pygame.QUIT)
                if key[pygame.K_ESCAPE] or key[pygame.K_SPACE] or quit:
                    self.client_socket.add_to_send_list(self.client_socket.create_message(self.SERVEUR, "stop", None))
                    break

                self.draw_background()
                self.draw_list_position()

                if self.ETAT == 0:
                    self.draw_text_center("INITIALISATION DU MATCH", self.WINDOW_SIZE[0] / 2, 35, self.RED)
                    self.init_match()
                elif self.ETAT == 1:
                    self.draw_text_center("MATCH EN COURS", self.WINDOW_SIZE[0] / 2, 35, self.RED)

                    self.command_button.draw()
                    self.command_button.draw()
                    self.save_strategie_button.draw()
                    self.load_strategie_button.draw()
                    self.add_position_button.draw()
                    self.play_strategie_button.draw()
                    
                    self.go_to_position()

                for event in pygame.event.get(): # ATTENTION : s'active uniquement lors d'un évènement utilisateur
                    self.manager.process_events(event)
                    
                    if event.type == UI_WINDOW_CLOSE: # BUG: Fermeture de la fenêtre non personnalisée
                        if self.command_window:
                            self.command_window = None
                        elif self.save_window:
                            self.save_window = None
                        elif self.load_window:
                            self.load_window = None
                        elif self.action_window:
                            if self.action_window.get_id() != "New_wind":
                                self.action_window = None          
                    if self.command_window:
                        self.command_window.process_events(event)
                    elif self.action_window:
                        self.action_window.process_events(event)
                    elif self.save_window:
                        self.save_window.process_events(event)
                    elif self.load_window:
                        self.load_window.process_events(event)
                    elif self.ETAT == 1:
                        self.handle_mouse_click(event)

                    if self.ETAT == 1:
                        self.command_button.handle_event(event)
                        self.save_strategie_button.handle_event(event)
                        self.load_strategie_button.handle_event(event)
                        self.add_position_button.handle_event(event)
                        self.play_strategie_button.handle_event(event)

                self.draw_robot()

                for point in self.new_scan:
                    self.draw_point(point[0], point[1])
                    
                self.draw_mouse_coordinates()
                new_objets = []
                """if len(self.new_scan) > 0:
                    new_objets = self.detect_objects(self.new_scan)
                    #self.suivre_objet(new_objets, 100)
                     #self.suivre_objet(new_objets, 100)"""
                    
                for objet in self.objets:
                    self.draw_object(objet)

                self.manager.update(1/60.0)
                self.manager.draw_ui(self.lcd)
                pygame.display.update()

            except KeyboardInterrupt:
                self.client_socket.add_to_send_list(
                    self.client_socket.create_message(self.SERVEUR, "stop", None))
                break
        
        print("Fin du programme")
        exit(0)


if __name__ == '__main__':
    try :
        Ihm = IHM()
        Ihm.run()
    except Exception as e:
        print("Erreur dans le programme", e)
        exit(0)
