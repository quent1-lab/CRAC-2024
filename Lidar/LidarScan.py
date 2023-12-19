from collections.abc import Iterable
import logging
from rplidar import RPLidar
import pygame
import math
import random
import time
import serial.tools.list_ports
import json
import os
import can
import time

class ComESP32:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.esp32 = None

    def connect(self):
        try:
            self.esp32 = serial.Serial(self.port, self.baudrate)
        except Exception as e:
            logging.error(f"Failed to connect to ESP32: {e}")
            raise

    def disconnect(self):
        try:
            self.esp32.close()
        except Exception as e:
            logging.error(f"Failed to disconnect from ESP32: {e}")
            raise

    def send(self, data):
        try:
            self.esp32.write(data)
        except Exception as e:
            logging.error(f"Failed to send data to ESP32: {e}")
            raise

    def receive(self):
        try:
            return self.esp32.readline()
        except Exception as e:
            logging.error(f"Failed to receive data from ESP32: {e}")
            raise

    def load_json(self, data):
        try:
            return json.loads(data)
        except Exception as e:
            logging.error(f"Failed to unload JSON: {e}")
            raise

    def run(self):
        try:
            self.connect()
            while True:
                data = self.receive()
                data = self.load_json(data)
                print(data)
                if data["type"] == "x":
                    print(data["x"])
                elif data["type"] == "y":
                    print(data["x"])
                elif data["type"] == "theta":
                    print(data["theta"])
                else:
                    print("error")
        except KeyboardInterrupt:
            self.disconnect()
            pass

class ComCAN:
    def __init__(self, channel, bustype):
        self.channel = channel
        self.bustype = bustype
        self.can = None

    def connect(self):
        #Vérifie si le système d'exploitation est Linux
        #Si oui, on lance les commandes pour configurer le CAN
        try:
            if os.name == "posix":
                os.system('sudo ip link set can0 type can bitrate 1000000')
                os.system('sudo ifconfig can0 up')
                self.can = can.interface.Bus(channel = self.channel, bustype = self.bustype)
            else:
                logging.error("OS not supported")
                raise OSError("OS not supported")       
        except Exception as e:
            logging.error(f"Failed to connect to CAN: {e}")
            raise

    def disconnect(self):
        try:
            self.can.shutdown()
        except Exception as e:
            logging.error(f"Failed to disconnect from CAN: {e}")
            raise

    def send(self, data):
        try:
            self.can.send(data)
        except Exception as e:
            logging.error(f"Failed to send data to CAN: {e}")
            raise

    def receive(self):
        try:
            return self.can.recv(10.0)
        except Exception as e:
            logging.error(f"Failed to receive data from CAN: {e}")
            raise

    def run(self):
        try:
            self.connect()
            while True:
                data = self.receive()
                print(data)
                
        except KeyboardInterrupt:
            self.disconnect()
            pass

class Objet:
    def __init__(self, id, x, y, taille):
        self.id = id
        self.x = x
        self.y = y
        self.taille = taille
        self.positions_precedentes = [(x, y, time.time())]  # Ajout du temps actuel
        self.direction = 0
        self.vitesse = 0
        self.vitesse_ms = 0

    def update_position(self, x, y):
        # Mettre à jour la position de l'objet et ajouter la position précédente à la liste
        self.positions_precedentes.append((self.x, self.y, time.monotonic_ns()))  # Ajout du temps actuel
        self.x = x
        self.y = y

    def get_direction_speed(self):
        # Calculer le vecteur de déplacement entre la position actuelle et la position précédente
        dx = self.x - self.positions_precedentes[-1][0]
        dy = self.y - self.positions_precedentes[-1][1]

        # Calculer le temps écoulé entre la position actuelle et la position précédente
        dt = (time.monotonic_ns() - self.positions_precedentes[-1][2])

        # La direction est l'angle du vecteur de déplacement
        self.direction = math.atan2(dy, dx)

        # La vitesse est la magnitude du vecteur de déplacement divisée par le temps écoulé
        self.vitesse = math.sqrt(dx**2 + dy**2) / dt * 1000000000 # Conversion en mm/s

        # Convertir la vitesse en m/s
        self.vitesse_ms = self.vitesse /1000

        return self.direction, self.vitesse

    def simulate_movement(self, direction, vitesse, temps):
        # Convertir la direction en radians

        # Calculer le déplacement en x et y
        dx = vitesse * 10 * math.cos(direction) * temps
        dy = vitesse * 10 * math.sin(direction) * temps

        # Mettre à jour la position de l'objet
        self.x += dx
        self.y += dy

    def calculate_dx_dy(self, direction, vitesse, temps):
        # Assurez-vous que la direction est entre 0 et 2π
        direction = direction % (2 * math.pi)

        # Calculer le déplacement en x et y
        dx = vitesse  * math.cos(direction) * temps
        dy = vitesse  * math.sin(direction) * temps

        return dx, dy

    def __str__(self):
        return f"Objet {self.id} : x = {self.x} y = {self.y} taille = {self.taille}"
    
class LidarScanner:
    def __init__(self, port=None):
        self.port = port
        self.lidar = None
        self.lcd = None
        self.ROBOT_ANGLE = 0
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.LIGHT_GREY = (200, 200, 200)
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

        self.id_compteur = 0  # Compteur pour les identifiants d'objet
        self.objets = []  # Liste pour stocker les objets détectés

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
        
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 20)
        pygame.mouse.set_visible(True)
        pygame.display.set_caption('LiDAR Scan')
        self.lcd.fill(self.BACKGROUND_COLOR)
        pygame.display.update()

        logging.basicConfig(filename='lidar_scan.log', level=logging.INFO,datefmt='%d/%m/%Y %H:%M:%S',format='%(asctime)s - %(levelname)s - %(message)s')
        
        #Choix du port si aucun port n'est spécifié
        if self.port == None:
            self.port = self.choix_du_port()

    def draw_robot(self, x, y, angle):
        pygame.draw.circle(self.lcd, pygame.Color(self.WHITE), (x * self.X_RATIO, y * self.Y_RATIO), 20)
        pygame.draw.line(
            self.lcd, pygame.Color(self.WHITE),
            (x * self.X_RATIO, y * self.Y_RATIO),
            ((x + 100 * math.cos(math.radians(angle))) * self.X_RATIO, (y + 100 * math.sin(math.radians(angle))) * self.Y_RATIO), 5)
    
    def draw_image(self,image_path):
        # Charge l'image à partir du chemin du fichier
        image = pygame.image.load(image_path)

        # Redimensionne l'image
        image = pygame.transform.scale(image, ( (self.FIELD_SIZE[0] - 2 * self.BORDER_DISTANCE) * self.X_RATIO,
                                                (self.FIELD_SIZE[1] - 2 * self.BORDER_DISTANCE) * self.Y_RATIO))

        # Dessine l'image à la position (x, y)
        self.lcd.blit(image, (self.BORDER_DISTANCE * self.X_RATIO, self.BORDER_DISTANCE * self.Y_RATIO))

    def draw_background(self):
        self.lcd.fill(self.BACKGROUND_COLOR)
        self.draw_image(self.path_picture)
        self.draw_field()
        self.draw_data()
        #Afficher l'image en fond d'écran, dans l'emplacement du terrain de jeu
    
    def draw_text(self, text, x, y):
        """Draws text to the pygame screen, on up left corner"""
        text = self.font.render(text, True, pygame.Color(self.FONT_COLOR), pygame.Color(self.BACKGROUND_COLOR))
        self.lcd.blit(text, (x, y))

    def draw_data(self):
        """Draws data to the pygame screen, on up left corner.For x, y and theta"""
        """Data is x, y and theta"""
        self.draw_text("x: " + "{:.2f}".format(self.ROBOT.x), 10, 5)
        self.draw_text("y: " + "{:.2f}".format(self.ROBOT.y), 10, 25)
        self.draw_text("theta: " + "{:.2f}".format(self.ROBOT_ANGLE), 100, 15)
        self.draw_text("speed: " + "{:.2f}".format(self.ROBOT.vitesse/10) + " cm/s", 200, 5)
        self.draw_text("direction: " + "{:.2f}".format(self.ROBOT.direction), 200, 25)

        if(len(self.objets) > 0):
            '''Draws data, on up right corner.For x, y, speed and direction'''
            self.draw_text("ID: " + "{:.2f}".format(self.objets[0].id), 800, 5)
            self.draw_text("x: " + "{:.2f}".format(self.objets[0].x), 800, 25)
            self.draw_text("y: " + "{:.2f}".format(self.objets[0].y), 800, 45)
            self.draw_text("speed: " + "{:.2f}".format(self.objets[0].vitesse/10) + " cm/s", 900, 20)
            self.draw_text("direction: " + "{:.2f}".format(self.objets[0].direction), 900, 40)          

    def draw_field(self):
        pygame.draw.rect(self.lcd, pygame.Color(100, 100, 100),
                         (self.BORDER_DISTANCE * self.X_RATIO - 5, self.BORDER_DISTANCE * self.Y_RATIO - 5,
                          (self.FIELD_SIZE[0] - 2 * self.BORDER_DISTANCE) * self.X_RATIO + 10,
                          (self.FIELD_SIZE[1] - 2 * self.BORDER_DISTANCE) * self.Y_RATIO + 10), 10)

    def draw_point(self, x, y, angle, distance):
        new_angle = angle - self.ROBOT_ANGLE
        if new_angle < 0:
            new_angle += 360
        x +=int(distance * math.cos(new_angle * math.pi / 180))
        y += int(distance * math.sin(new_angle * math.pi / 180))

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

        try:
            pygame.draw.circle(self.lcd, pygame.Color(self.POINT_COLOR), (x * self.X_RATIO, y * self.Y_RATIO), 3)
        except pygame.error as e:
            print("Failed to draw circle")
            logging.error(f"Failed to draw circle: {e}")

    def draw_object(self, objet):
        pygame.draw.circle(self.lcd, pygame.Color(255, 255, 0), (objet.x * self.X_RATIO, objet.y * self.Y_RATIO), 10)
        pygame.draw.circle(self.lcd, pygame.Color(50, 50, 200), (objet.x * self.X_RATIO, objet.y * self.Y_RATIO), int(objet.taille / 2 * self.X_RATIO), 3)

        # Affichage des coordonnées de l'objet et de son ID
        self.draw_text("ID: " + str(objet.id), objet.x * self.X_RATIO + 20, objet.y * self.Y_RATIO - 30)

        # Affichage de la direction et de la vitesse de l'objet avec un vecteur
        direction, vitesse = objet.get_direction_speed()
        pygame.draw.line(
            self.lcd, pygame.Color(255, 255, 0),
            (objet.x * self.X_RATIO, objet.y * self.Y_RATIO),
            ((objet.x + vitesse * math.cos(direction)) * self.X_RATIO, (objet.y + vitesse * math.sin(direction)) * self.Y_RATIO), 3)

    def detect_object(self, scan):
        objet = min(scan, key=lambda x: x[2])
        angle_objet = objet[1]
        distance_objet = objet[2]
        points_autour_objet = []

        #sélectionne les points autour de l'objet en fonction de la distance des points
        for point in scan:
            if point[2] < distance_objet + 50 and point[2] > distance_objet - 50:
                points_autour_objet.append(point)

        x = 0
        y = 0
        taille = 0

        for point in points_autour_objet:
            new_angle = point[1] - self.ROBOT_ANGLE
            if new_angle < 0:
                new_angle += 360
            x += point[2] * math.cos(new_angle * math.pi / 180)
            y += point[2] * math.sin(new_angle * math.pi / 180)

        angle_min = min(points_autour_objet, key=lambda x: x[1])
        angle_max = max(points_autour_objet, key=lambda x: x[1])
        distance_min = min(points_autour_objet, key=lambda x: x[2])
        distance_max = max(points_autour_objet, key=lambda x: x[2])
        taille = math.sqrt((distance_max[2] * math.cos(angle_max[1] * math.pi / 180) - distance_min[2] * math.cos(
            angle_min[1] * math.pi / 180)) ** 2 + (distance_max[2] * math.sin(angle_max[1] * math.pi / 180) - distance_min[2] * math.sin(
            angle_min[1] * math.pi / 180)) ** 2)

        x = self.ROBOT.x + int(x / len(points_autour_objet))
        y = self.ROBOT.y + int(y / len(points_autour_objet))

        # Seuil de détection d'un objet en mm
        SEUIL = 100 # en mm (distance que peut parcourir le robot entre deux scans)
        #Valeur à affiner

        # Vérifier si l'objet est déjà suivi
        for objet in self.objets:
            distance = math.sqrt((x - objet.x)**2 + (y - objet.y)**2)
            if distance < SEUIL:
                # Si l'objet est déjà suivi, mettre à jour ses coordonnées
                objet.update_position(x, y)
                objet.taille = taille
                return objet
            else:
                # Si l'objet n'est pas déjà suivi, créer un nouvel objet
                #nouvel_objet = Objet(self.id_compteur, x, y, taille)
                #self.objets.append(nouvel_objet)
                return objet
            
        if(len(self.objets) < 1):
            # Incrémenter le compteur d'identifiants
            self.id_compteur += 1

            # Si l'objet n'est pas déjà suivi, créer un nouvel objet
            nouvel_objet = Objet(self.id_compteur, x, y, taille)
            self.objets.append(nouvel_objet)

    def choix_du_port(self):
        ports = serial.tools.list_ports.comports()

        #Affichage des ports détectés
        for port in ports:
            #Si le port contient AMA, on le supprime de la liste
            if "AMA" in port.device:
                ports.remove(port)
                continue
            print(port.device)
        
        #Si un seul port est détecté, on le retourne
        if len(ports) == 1:
            logging.info(f"Port detected: {ports[0].device}")
            return ports[0].device

        #Si aucun port n'est détecté, on lance le programme de test
        if len(ports) == 0:
            print("Aucun port détecté")
            logging.error("No port detected")
            self.programme_test()
            exit(0)
        
        #Distinction entre les ports windows et linux
        if ports[0].device[:3] == "COM":
            port = "COM"
        else:
            port = "/dev/ttyUSB"

        #Choix du port
        while True:
            try:
                numero = int(input("Entrez le port du LiDAR : " + port))

                if(numero >= 9):
                    print("Port invalide (COM9 ou plus)")
                    logging.error("Invalid port (COM9 or more)")
                    self.programme_test()
                    exit(0)

                #Vérification de l'existence du port
                for port_ in ports:
                    if port_.device == port + str(numero):
                        logging.info(f"Port detected: {port_.device}")
                        return port_.device
                raise ValueError
            except ValueError:
                logging.error("Invalid port")
                print("Port invalide")
                continue
            except KeyboardInterrupt:
                exit(0)

    def valeur_de_test(self):
        scan = []
        for i in range(0,350,):
            angle = i + self.ROBOT_ANGLE
            if angle > 360:
                angle -= 360
            distance = 3000
            scan.append((0, angle, distance))
        for i in range(350, 360):
            angle = i + self.ROBOT_ANGLE
            if angle > 360:
                angle -= 360
            distance = random.randint(800, 850)
            scan.append((0, angle, distance))

        return scan

    def programme_test(self):
        print("Programme de test")
        logging.info("Test program")
        while True:
            keys = pygame.key.get_pressed()
            quit = pygame.event.get(pygame.QUIT)
            if quit:
                exit(0)                            
            if keys[pygame.K_ESCAPE] or keys[pygame.K_SPACE]:
                exit(0)

            scan = self.valeur_de_test()
            zone_objet = self.detect_object(scan)
            self.draw_background()
            self.draw_robot(self.ROBOT.x, self.ROBOT.y, self.ROBOT_ANGLE)
            self.draw_object(self.objets[0])
            self.dessiner_trajectoires_anticipation(self.ROBOT, self.objets[0],4)

            for point in scan:
                self.draw_point(self.ROBOT.x, self.ROBOT.y, point[1], point[2])

            pygame.display.update()
            self.lcd.fill(self.WHITE)
            self.ROBOT_ANGLE += 1
            
            #Déplacement du robot virtuel avec des touches du clavier
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
    
    def anticiper_collision(robot_actuel, robot_adverse, duree_anticipation=1.0, pas_temps=0.1, distance_securite=50):
        """
        Anticipe les collisions entre le robot actuel et le robot adverse.

        :param robot_actuel: Objet représentant le robot actuel
        :param robot_adverse: Objet représentant le robot adverse
        :param duree_anticipation: Durée d'anticipation en secondes
        :param pas_temps: Pas de temps pour la simulation en secondes
        :param distance_securite: Distance de sécurité minimale entre les robots
        :return: True si une collision est anticipée, False sinon, et le chemin d'évitement proposé
        """
        # Copie des positions actuelles des robots
        x_actuel, y_actuel = robot_actuel.x, robot_actuel.y
        x_adverse, y_adverse = robot_adverse.x, robot_adverse.y

        # Copie des vitesses actuelles des robots
        vitesse_actuel, _ = robot_actuel.get_direction_speed()
        vitesse_adverse, _ = robot_adverse.get_direction_speed()

        # Simulation de mouvement pour anticiper la trajectoire future des robots
        temps_total = duree_anticipation
        for temps in range(int(duree_anticipation / pas_temps)):
            # Calcul des nouvelles positions des robots
            robot_actuel.calculate_dx_dy(robot_actuel.direction, vitesse_actuel, pas_temps)
            robot_adverse.calculate_dx_dy(robot_adverse.direction, vitesse_adverse, pas_temps)

            # Calcul de la distance entre les robots
            distance_entre_robots = math.sqrt((robot_actuel.x - robot_adverse.x)**2 + (robot_actuel.y - robot_adverse.y)**2)

            # Vérification de la collision anticipée
            if distance_entre_robots < distance_securite:
                # Collision anticipée, proposer un chemin d'évitement
                chemin_evitement = [(x_actuel, y_actuel)]
                for temps_evitement in range(int(duree_anticipation / pas_temps)):
                    # Simulation de mouvement pour l'évitement
                    robot_actuel.calculate_dx_dy(robot_actuel.direction, vitesse_actuel, pas_temps)

                    chemin_evitement.append((robot_actuel.x, robot_actuel.y))

                return True, chemin_evitement

        # Pas de collision anticipée
        return False, []

    def dessiner_trajectoires_anticipation(self, robot_actuel, robot_adverse, duree_anticipation=1.0, pas_temps=0.1, distance_securite=50):
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
        temps_total = duree_anticipation
        for temps in range(int(duree_anticipation / pas_temps)):
            # Calcul des nouvelles positions des robots
            new_x_R, new_y_R = robot_actuel.calculate_dx_dy(robot_actuel.direction, vitesse_actuel, pas_temps)
            new_x_A, new_y_A = robot_adverse.calculate_dx_dy(robot_adverse.direction, vitesse_adverse, pas_temps)

            new_x_R += trajectoire_actuel[-1][0]
            new_y_R += trajectoire_actuel[-1][1]
            new_x_A += trajectoire_adverse[-1][0]
            new_y_A += trajectoire_adverse[-1][1]

            # Ajout des points aux trajectoires
            trajectoire_actuel.append((new_x_R, new_y_R))
            trajectoire_adverse.append((new_x_A, new_y_A))
            
            # Calcul de la distance entre les robots
            distance_entre_robots = math.sqrt((new_x_R - new_x_A)**2 + (new_y_R - new_y_A)**2)
            
            # Vérification de la collision anticipée
            if distance_entre_robots < distance_securite:
                # Proposer un chemin d'évitement
                trajectoire_evitement = [(x_actuel, y_actuel)]
                for temps_evitement in range(int(duree_anticipation / pas_temps)):
                    # Choisir une direction d'évitement
                    direction_evitement = (robot_actuel.direction + math.pi) % (2 * math.pi)

                    # Simulation de mouvement pour l'évitement
                    new_x_E, new_y_E = robot_actuel.calculate_dx_dy(direction_evitement, vitesse_actuel, pas_temps)

                    new_x_E += trajectoire_evitement[-1][0]
                    new_y_E += trajectoire_evitement[-1][1]

                    # Ajout des points à la trajectoire d'évitement
                    trajectoire_evitement.append((new_x_E, new_y_E))

                break

        # Dessin des trajectoires
        self.draw_trajectoire(trajectoire_actuel, color=(255, 0, 0))  # Rouge pour le robot actuel
        self.draw_trajectoire(trajectoire_adverse, color=(0, 0, 255))  # Bleu pour le robot adverse
        self.draw_trajectoire(trajectoire_evitement, color=(0, 255, 0))  # Vert pour la trajectoire d'évitement

    def draw_trajectoire(self, trajectoire, color=(255, 255, 255)):
        """
        Dessine une trajectoire sur l'écran.

        :param trajectoire: Liste de points (x, y) représentant la trajectoire
        :param color: Couleur de la trajectoire (RGB)
        """
        for point in trajectoire:
            pygame.draw.circle(self.lcd, pygame.Color(color), (int(point[0] * self.X_RATIO), int(point[1] * self.Y_RATIO)), 2)

    def stop(self):
        logging.info("Stopping LiDAR motor")
        print("Arrêt du moteur LiDAR")
        self.lidar.stop()
        time.sleep(1)
        self.lidar.disconnect()
        exit(0)

    def run(self):
        try:
            self.lidar = RPLidar(self.port)
        except Exception as e:
            logging.error(f"Failed to create an instance of RPLidar: {e}")
            self.programme_test()
            raise

        try:
            self.lidar.connect()
            logging.info("Lidar connected")
            print("LiDAR connecté")

            #ComESP32(port="COM3", baudrate=115200).run()

            self.draw_background()
            self.draw_robot(self.ROBOT.x, self.ROBOT.y, self.ROBOT_ANGLE)
            pygame.display.update()

            running = False
            while(running == False):
                keys = pygame.key.get_pressed()            
                if keys[pygame.K_SPACE]:
                    running = True
                    print("Début du scan")
                    logging.info("Starting scan")
                    break

            while running:

                for scan in self.lidar.iter_scans(4000):
                    keys = pygame.key.get_pressed()
                    quit = pygame.event.get(pygame.QUIT)
                    if quit:
                        self.stop()                    
                    if keys[pygame.K_ESCAPE] or keys[pygame.K_SPACE]:
                        self.stop()
                    
                    self.draw_background()
                    self.draw_robot(self.ROBOT.x, self.ROBOT.y, self.ROBOT_ANGLE)
                    zone_objet = self.detect_object(scan)
                    self.draw_object(self.objets[0])
                    self.dessiner_trajectoires_anticipation(self.ROBOT, self.objets[0])

                    for (_, angle, distance) in scan:
                        self.draw_point(self.ROBOT.x, self.ROBOT.y, angle, distance)
                    pygame.display.update()
                    self.lcd.fill(self.WHITE)

        except KeyboardInterrupt:
            self.stop()
            pass

if __name__ == '__main__':
    scanner = LidarScanner()
    scanner.run()