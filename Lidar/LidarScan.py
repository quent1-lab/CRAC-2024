import logging
from objet import Objet
import pygame
from pygame.locals import *
import math
import os
import random
import numpy as np
from sklearn.cluster import DBSCAN
from rplidar import RPLidar, RPLidarException
import serial.tools.list_ports
from client import *
import json

"""# Initialiser le serveur
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('', 5000))  # Utilisez une adresse IP appropriée et un port disponible
server_socket.listen(1)

print("Attente de la connexion du client...")

# Accepter la connexion du client
client_socket, client_address = server_socket.accept()
print(f"Connexion établie avec {client_address}")"""


class LidarScanner:
    def __init__(self, port=None):
        self.port = port
        self.lidar = None
        self.lcd = None
        self.ROBOT_ANGLE = 0
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.LIGHT_GREY = (200, 200, 200)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.RED = (255, 0, 0)
        self.DARK_GREEN = (0, 100, 0)
        self.FIELD_SIZE = (3000, 2000)
        self.BORDER_DISTANCE = 200
        self.POINT_COLOR = (255, 0, 0)
        self.BACKGROUND_COLOR = self.LIGHT_GREY
        self.FONT_COLOR = self.BLACK

        # Initialisation du robot virtuel
        self.ROBOT = Objet(0, 1500, 1000, 20)

        if os.name == 'nt':  # Windows
            self.path_picture = "Lidar/Terrain_Jeu.png"
        else:  # Linux et autres
            self.path_picture = "Documents/CRAC-2024/Lidar/Terrain_Jeu.png"

        self.path_picture = "Lidar/Terrain_Jeu.png"
        self.id_compteur = 0  # Compteur pour les identifiants d'objet
        self.objets = []  # Liste pour stocker les objets détectés
        self.new_scan = []

        # Initialisation de Pygame et ajustement de la taille de la fenêtre
        pygame.init()
        info_object = pygame.display.Info()
        screen_width, screen_height = info_object.current_w, info_object.current_h - 100
        target_ratio = 3/2
        target_width = min(screen_width, int(screen_height * target_ratio))
        target_height = min(screen_height, int(screen_width / target_ratio))
        self.WINDOW_SIZE = (target_width, target_height)
        self.X_RATIO = self.WINDOW_SIZE[0] / self.FIELD_SIZE[0]
        self.Y_RATIO = self.WINDOW_SIZE[1] / self.FIELD_SIZE[1]
        self.lcd = pygame.display.set_mode(self.WINDOW_SIZE)

        self.client_socket = Client("192.168.22.101", 22050, 10)

        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 20)
        pygame.mouse.set_visible(True)
        pygame.display.set_caption('LiDAR Scan')
        self.lcd.fill(self.BACKGROUND_COLOR)
        pygame.display.update()

        logging.basicConfig(filename='lidar_scan.log', level=logging.INFO,
                            datefmt='%d/%m/%Y %H:%M:%S', format='%(asctime)s - %(levelname)s - %(message)s')

    def draw_robot(self, x, y, angle):
        pygame.draw.circle(self.lcd, pygame.Color(self.WHITE),
                           (x * self.X_RATIO, y * self.Y_RATIO), 20)
        pygame.draw.line(
            self.lcd, pygame.Color(self.WHITE),
            (x * self.X_RATIO, y * self.Y_RATIO),
            ((x + 100 * math.cos(math.radians(-angle))) * self.X_RATIO, (y + 100 * math.sin(math.radians(-angle))) * self.Y_RATIO), 5)

    def draw_image(self, image_path):
        # Charge l'image à partir du chemin du fichier
        image = pygame.image.load(image_path)

        # Redimensionne l'image
        image = pygame.transform.scale(image, ((self.FIELD_SIZE[0] - 2 * self.BORDER_DISTANCE) * self.X_RATIO,
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

    def draw_text(self, text, x, y, color=(0, 0, 0)):
        """Draws text to the pygame screen, on up left corner"""
        text = self.font.render(
            text, True, color, pygame.Color(self.BACKGROUND_COLOR))
        self.lcd.blit(text, (x, y))

    def draw_text_center(self, text, x, y, color=(0, 0, 0)):
        text_surface = self.font.render(
            text, True, color, pygame.Color(self.BACKGROUND_COLOR))
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
        pygame.draw.circle(self.lcd, pygame.Color(
            255, 255, 0), (objet.x * self.X_RATIO, objet.y * self.Y_RATIO), 10)
        pygame.draw.circle(self.lcd, pygame.Color(50, 50, 200), (objet.x * self.X_RATIO,
                           objet.y * self.Y_RATIO), int(objet.taille / 2 * self.X_RATIO), 3)

        # Affichage des coordonnées de l'objet et de son ID
        self.draw_text("ID: " + str(objet.id), objet.x *
                       self.X_RATIO + 20, objet.y * self.Y_RATIO - 30)

        # Affichage de la direction et de la vitesse de l'objet avec un vecteur
        direction, vitesse = objet.get_direction_speed()
        pygame.draw.line(
            self.lcd, pygame.Color(255, 255, 0),
            (objet.x * self.X_RATIO, objet.y * self.Y_RATIO),
            ((objet.x + vitesse * math.cos(direction)) * self.X_RATIO, (objet.y + vitesse * math.sin(direction)) * self.Y_RATIO), 3)

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

    def display_lidar_status(self):
        # Obtenir l'état du lidar
        try:
            health = self.lidar.get_health()
            status = health[0]
            if status == 'Good':
                status_color = self.DARK_GREEN
            else:
                status_color = self.RED
        except:
            status = 'Error'
            status_color = self.RED

        # Créer le texte de l'état
        status_text = self.font.render(
            'Lidar status: ' + status, True, status_color)

        # Dessiner le texte de l'état
        status_rect = status_text.get_rect(
            center=(self.WINDOW_SIZE[0] / 2, self.WINDOW_SIZE[1] / 2 + 50))
        self.lcd.blit(status_text, status_rect)

        # Mettre à jour l'écran
        pygame.display.update()
        time.sleep(1.5)

    def transform_scan(self, scan):
        """
        Transforme les données du scan en coordonnées cartésiennes.
        Retire les points en dehors du terrain de jeu.

        :param scan: Liste de tuples (quality, angle, distance)
        :return: Liste de tuples (x, y, distance)
        """
        points = []
        for point in scan:
            distance = point[2]
            new_angle = point[1] - self.ROBOT_ANGLE

            new_angle %= 360
            if new_angle < 0:
                new_angle += 360

            if distance != 0:
                x = distance * math.cos(math.radians(new_angle)) + self.ROBOT.x
                y = distance * math.sin(math.radians(new_angle)) + self.ROBOT.y

                # Vérifier si le point est en dehors du terrain de jeu
                if self.BORDER_DISTANCE < x < self.FIELD_SIZE[0] - self.BORDER_DISTANCE and self.BORDER_DISTANCE < y < self.FIELD_SIZE[1] - self.BORDER_DISTANCE:
                    points.append((x, y, distance, new_angle))
        return points

    def get_points_in_zone(self, points, origin_distance, origin_angle):
        """
        Renvoie les points compris dans une zone spécifiée par un seuil de distance par rapport à un point d'origine et une position angulaire.

        :param points: Liste de points à vérifier. Chaque point est un tuple (x, y, distance, angle).
        :param origin_distance: Distance du point d'origine.
        :param origin_angle: Angle du point d'origine.
        :return: Liste des points dans la zone.
        """
        points_in_zone = []

        for point in points:
            distance = point[2]
            angle = point[3]

            # Vérifier si le point est dans une zone de 50 mm autour du point d'origine et d'un angle de 60 degrés
            if origin_distance - 50 < distance < origin_distance + 50 and origin_angle - 30 < angle < origin_angle + 30:
                points_in_zone.append(point)

        return points_in_zone

    def detect_object(self, scan, max_iteration=2):
        iteration = 0
        while True:
            # Liste des points associés aux objets déjà trouvés
            points_objets_trouves = []
            for k in range(iteration):
                if k < len(self.objets):
                    points_objets_trouves += self.objets[k].points

            # Sélectionne le point le plus proche du robot en excluant les points des objets déjà trouvés
            points_non_objets = [
                point for point in scan if point not in points_objets_trouves]
            if not points_non_objets:
                # Aucun point trouvé en dehors des objets, retourner None
                return None

            # Sélectionne le point le plus proche du robot
            point_proche = min(points_non_objets, key=lambda x: x[2])
            distance_objet = point_proche[2]
            angle_objet = point_proche[3]
            points_autour_objet = []

            # Sélectionne les points autour de l'objet en fonction des coordonnées (x, y) des points
            points_autour_objet = self.get_points_in_zone(
                points_non_objets, distance_objet, angle_objet)

            if not points_autour_objet or len(points_autour_objet) < 3:
                # Aucun point autour de l'objet ou pas assez de points, retourner None
                return None

            # Calcul des coordonnées moyennes pondérées des points autour de l'objet
            x = sum([point[0] for point in points_autour_objet]) / \
                len(points_autour_objet)
            y = sum([point[1] for point in points_autour_objet]) / \
                len(points_autour_objet)

            iteration += 1
            if iteration > max_iteration:
                return None

            # Calcul de la taille de l'objet
            x_min = min(points_autour_objet, key=lambda x: x[0])
            x_max = max(points_autour_objet, key=lambda x: x[0])
            y_min = min(points_autour_objet, key=lambda x: x[1])
            y_max = max(points_autour_objet, key=lambda x: x[1])
            taille = math.sqrt((x_max[0] - x_min[0])
                               ** 2 + (y_max[1] - y_min[1])**2)

            # Seuil de détection d'un objet en mm
            # en mm (distance que peut parcourir le robot entre deux scans)
            SEUIL = 100

            id_objet_existant = self.trouver_id_objet_existants(x, y, SEUIL)

            if id_objet_existant != None:
                # Si l'objet est déjà suivi, mettre à jour ses coordonnées
                self.objets[id_objet_existant - 1].update_position(x, y)
                self.objets[id_objet_existant - 1].taille = taille
                self.objets[id_objet_existant - 1].points = points_autour_objet
            else:
                # Si l'objet n'est pas déjà suivi, créer un nouvel objet
                self.id_compteur += 1
                nouvel_objet = Objet(self.id_compteur, x, y, taille)
                nouvel_objet.points = points_autour_objet
                self.objets.append(nouvel_objet)

    def detect_objects(self, scan):

        # Regroupement des points avec DBSCAN
        X = np.array([(point[0], point[1]) for point in scan])

        eps = 150  # À ajuster en fonction de la densité des points
        min_samples = 14  # À ajuster en fonction de la densité des points
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
            distance_min = np.min(
                cluster_points[:, 0]**2 + cluster_points[:, 1]**2)**0.5
            distance_max = np.max(
                cluster_points[:, 0]**2 + cluster_points[:, 1]**2)**0.5
            taille = distance_max - distance_min

            nouvel_objet = Objet(id=len(objets) + 1,
                                 x=x_moyen, y=y_moyen, taille=taille)
            objets.append(nouvel_objet)

        return objets

    def trouver_id_objet_existants(self, x, y, seuil_distance=100):
        # Vérifier si l'objet est déjà suivi
        for objet in self.objets:
            distance = math.sqrt((x - objet.x)**2 + (y - objet.y)**2)
            if distance < seuil_distance:
                return objet.id  # Retourne l'ID de l'objet existant
        return None

    def suivre_objet(self, objets, seuil_distance=100):

        if len(self.objets) != len(objets):
            # Ajoute les objets manquants
            for objet in objets[len(self.objets):]:
                self.objets.append(objet)

        # Pré-calculer le carré du seuil de distance
        seuil_distance_carre = seuil_distance ** 2
        # Vérifier si l'objet est déjà suivi
        for objet in self.objets:
            for objet_param in objets:
                distance_carre = (objet_param.x - objet.x)**2 + \
                    (objet_param.y - objet.y)**2

                if distance_carre < seuil_distance_carre:
                    self.objets[objet_param.id -
                                1].update_position(objet_param.x, objet_param.y)
                    objets.remove(objet_param)  # Retirer l'objet de la liste

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
        x_actuel, y_actuel = robot_actuel.x, robot_actuel.y
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

    def connexion_lidar(self):
        # Connexion au lidar
        try:
            if self.port == None:
                self.port = [port.name for port in serial.tools.list_ports.comports(
                ) if port.serial_number and "0001" in port.serial_number][0]

            print(f"Connexion au port {self.port}")

            self.lidar = RPLidar(self.port)
            self.lidar.connect()
            logging.info("Lidar connected")
            print("LiDAR connecté")
        except RPLidarException as e:
            # Code pour gérer RPLidarException
            print(
                f"Une erreur RPLidarException s'est produite dans le connexion : {e}")
            self.lidar.stop()
            self.connexion_lidar()
        except Exception as e:
            logging.error(f"Failed to create an instance of RPLidar: {e}")
            print("Erreur lors de la création de l'instance du LiDAR")

            time.sleep(1.5)
            exit(0)
            raise

    def stop(self):
        print("Arret du Programme")
        self.client_socket.add_to_send_list(self.client_socket.create_message(1, "stop", None))
        self.objets = []

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

    def calculer_angle(self, objet, deg):
        # Les coordonnées du robot et de l'objet doivent être fournies en entrée
        x_robot, y_robot = self.ROBOT.x, self.ROBOT.y
        x_objet, y_objet = objet.x,objet.y

        # Calculer la différence de x et de y
        dx = x_objet - x_robot
        dy = y_objet - y_robot

        # Calculer l'angle en radians
        angle = math.atan2(dy, dx)

        if deg:
            # Convertir l'angle en degrés
            angle = math.degrees(angle)
    
        return angle

    def calculer_distance(self, objet):
        # Les coordonnées du robot et de l'objet doivent être fournies en entrée
        x_robot, y_robot = self.ROBOT.x, self.ROBOT.y
        x_objet, y_objet = objet.x, objet.y

        # Calculer la différence de x et de y
        dx = x_objet - x_robot
        dy = y_objet - y_robot

        # Calculer la distance entre le robot et l'objet
        distance = math.sqrt(dx**2 + dy**2)

        return distance

    def triangulation(self, objet1, objet2, objet3):
        """
        Détermine la position (x, y, theta) du robot en fonction des distances mesurées par le capteur Lidar
        et des coordonnées des trois points fixes sur les bords de l'aire de jeu.

        Args:
        points_fixes: Une liste de trois tuples représentant les coordonnées des points fixes.
        distances: Une liste de trois distances mesurées par le capteur Lidar jusqu'aux points fixes.

        Returns:
        Un tuple contenant les coordonnées (x, y) et l'orientation theta du robot.
        """
        # Convertit les coordonnées en tableau numpy
        points_fixes = np.array([[objet1.x, objet1.y], [objet2.x, objet2.y], [objet3.x, objet3.y]])
        distances = np.array([self.calculer_distance(objet1), self.calculer_distance(objet2), self.calculer_distance(objet3)])

        # Calcule les vecteurs du robot par rapport aux points fixes
        vecteurs = points_fixes - np.array([[0, 0]])

        # Calcule les distances horizontales et verticales entre le point du Lidar et les points fixes
        distances_horizontales = distances * np.cos(np.arctan2(vecteurs[:, 1], vecteurs[:, 0]))
        distances_verticales = distances * np.sin(np.arctan2(vecteurs[:, 1], vecteurs[:, 0]))

        # Calcule la position du robot
        x = np.mean(points_fixes[:, 0] + distances_horizontales)
        y = np.mean(points_fixes[:, 1] + distances_verticales)

        # Calcule l'orientation du robot (theta)
        theta = np.arctan2(np.mean(vecteurs[:, 1]), np.mean(vecteurs[:, 0]))

        return x, y, theta

    def triangulation2(self, objet1, objet2, objet3):
        """
        Calcule la position d'un point par triangulation en se basant sur trois points fixes
        et les distances entre ces points et le point inconnu.

        Args:
        x1, y1: Coordonnées du premier point fixe.
        x2, y2: Coordonnées du deuxième point fixe.
        x3, y3: Coordonnées du troisième point fixe.
        d1: Distance entre le premier point fixe et le point inconnu.
        d2: Distance entre le deuxième point fixe et le point inconnu.
        d3: Distance entre le troisième point fixe et le point inconnu.

        Returns:
        Un tuple contenant les coordonnées du point inconnu (x, y).
        """
        # Calcule les longueurs des côtés des triangles formés par les points fixes et le point inconnu.
        a = self.calculer_distance(objet1)
        b = self.calculer_distance(objet2)
        c = self.calculer_distance(objet3)

        # Calcule les coordonnées des points fixes.
        x1, y1 = objet1.x, objet1.y
        x2, y2 = objet2.x, objet2.y
        x3, y3 = objet3.x, objet3.y

        # Calcule les coordonnées du point inconnu.
        x = (a**2 - b**2 + x2**2 - x1**2 + y2**2 - y1**2) / (2 * (x2 - x1))
        y = ((a**2 - c**2 + x3**2 - x1**2 + y3**2 - y1**2) / (2 * (y3 - y1))
            - ((x3 - x1) / (y3 - y1)) * x)
        theta = 0

        return x, y, theta

    def calculer_coordonnees(self, objet1, objet2, objet3):
        balises = np.array([[objet1.x, objet1.y], [objet2.x, objet2.y], [objet3.x, objet3.y]])
        distances = np.array([self.calculer_distance(objet1), self.calculer_distance(objet2), self.calculer_distance(objet3)])
        # Vérifier que le nombre de balises et de distances correspondent
        if len(balises) != len(distances):
            raise ValueError("Le nombre de balises et de distances doit être le même")

        # Créer une matrice pour stocker les différences entre les coordonnées des balises
        A = np.zeros((len(balises) - 1, 2))

        # Remplir la matrice avec les différences entre les coordonnées des balises
        for i in range(len(balises) - 1):
            A[i] = np.array(balises[i + 1]) - np.array(balises[0])

        # Calculer les distances entre les balises
        d = np.array(distances[1:]) ** 2 - np.array(distances[0]) ** 2 + np.sum(np.array(balises[0])**2) - np.sum(np.array(balises[1:])**2)

        # Résoudre le système d'équations linéaires pour obtenir les coordonnées du robot
        coord_robot = np.linalg.solve(2*A, d)

        return coord_robot

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

    def programme_simulation(self):
        print("Programme de simulation")
        logging.info("Starting simulation program")
        last_time = time.time()
        while True:
            keys = pygame.key.get_pressed()
            quit = pygame.event.get(pygame.QUIT)
            if quit or keys[pygame.K_ESCAPE] or keys[pygame.K_SPACE]:
                exit(0)

            scan = self.valeur_de_test()
            new_scan = self.transform_scan(scan)

            # self.detect_object(new_scan)
            new_objets = self.detect_objects(new_scan)
            self.suivre_objet(new_objets, 100)

            self.draw_background()
            self.draw_text_center("PROGRAMME DE SIMULATION",
                                  self.WINDOW_SIZE[0] / 2, 35, self.RED)
            self.draw_robot(self.ROBOT.x, self.ROBOT.y, self.ROBOT_ANGLE)

            if len(self.objets) >= 3:
                x_r,y_r = self.calculer_coordonnees(self.objets[0],self.objets[1],self.objets[2])
                print(f"x: {x_r}, y: {y_r}")
                self.draw_robot(x_r, y_r,0)

            for objet in self.objets:
                self.draw_object(objet)
                trajectoire_actuel, trajectoire_adverse, trajectoire_evitement = self.trajectoires_anticipation(
                    self.ROBOT, objet, 1.5, 0.1, 50)
                self.draw_all_trajectoires(trajectoire_actuel, trajectoire_adverse, trajectoire_evitement)

            for point in new_scan:
                self.draw_point(point[0], point[1])

            # Affiche les fps sur l'écran (en bas a gauche)
            self.draw_text("FPS: " + str(int(1 / (time.time() - last_time))), 10, self.WINDOW_SIZE[1] - 30)
            last_time = time.time()

            pygame.display.update()
            self.lcd.fill(self.WHITE)
            self.ROBOT_ANGLE += 1

            # Déplacement du robot virtuel avec des touches du clavier
            x = self.ROBOT.x
            y = self.ROBOT.y

            if keys[pygame.K_LEFT]:
                x -= 10
            if keys[pygame.K_RIGHT]:
                x += 10
            if keys[pygame.K_UP]:
                y -= 10
            if keys[pygame.K_DOWN]:
                y += 10
            self.ROBOT.update_position(x, y)

            time.sleep(0.01)

    def receive_to_server(self, message):
        if message["cmd"] == "objects":
                self.objets = []
                json_string = json.loads(message["data"])
                for obj in json_string:
                    self.objets.append(Objet(obj["id"], obj["x"], obj["y"], obj["taille"]))
        elif message["cmd"] == "coord":
            coord = message["data"]
            self.ROBOT.update_position(coord["x"], coord["y"])
            self.ROBOT_ANGLE = coord["theta"]
        elif message["cmd"] == "points":
            scan = message["data"]
            scan = json.loads(scan)
            self.new_scan = []
            for point in scan:
                print(point)
                self.new_scan.append((point["x"],point["y"], point["dist"], point["angle"]))
            print("Scan reçu")
        elif message["cmd"] == "stop":
            self.client_socket.stop()
            
        
    def run(self):
        #self.programme_simulation()
        start_time = time.time()
        start = False
        #self.connexion_lidar()
        self.client_socket.set_callback(self.receive_to_server)
        self.client_socket.set_callback_stop(self.stop)
        self.client_socket.connect()
        print("Connecté au serveur")
        while True:
            try:
                pygame.event.get()
                keys = pygame.key.get_pressed()
                quit = pygame.event.get(pygame.QUIT)
                if quit or keys[pygame.K_ESCAPE]:
                    self.stop()
                    break

                self.draw_background()
                self.draw_robot(self.ROBOT.x, self.ROBOT.y, self.ROBOT_ANGLE)

                for point in self.new_scan:
                    self.draw_point(point[0], point[1])

                if len(self.new_scan) >= 3:
                    self.detect_objects(self.new_scan)
                    self.suivre_objet(self.objets, 100)

                for objet in self.objets:
                    self.draw_object(objet)
                
                pygame.display.update()

            except RPLidarException as e:
                # Code pour gérer RPLidarException
                print(
                    f"Une erreur RPLidarException s'est produite dans le run : {e}")
                self.lidar.stop()
                time.sleep(1)

            except KeyboardInterrupt:
                self.stop()
                break


if __name__ == '__main__':
    scanner = LidarScanner("/dev/ttyUSB0")
    scanner.run()
