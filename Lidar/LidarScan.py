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
        self.positions_precedentes = [(x, y)]  # Liste pour stocker les positions précédentes
        self.direction = 0
        self.vitesse = 0

    def update_position(self, x, y):
        # Mettre à jour la position de l'objet et ajouter la position précédente à la liste
        self.positions_precedentes.append((self.x, self.y))
        self.x = x
        self.y = y

    def get_direction_vitesse(self):
        # Calculer le vecteur de déplacement entre la position actuelle et la position précédente
        dx = self.x - self.positions_precedentes[-1][0]
        dy = self.y - self.positions_precedentes[-1][1]

        # La direction est l'angle du vecteur de déplacement
        self.direction = math.atan2(dy, dx)

        # La vitesse est la magnitude du vecteur de déplacement
        self.vitesse = math.sqrt(dx**2 + dy**2)

        return self.direction, self.vitesse

    def calculer_position(self, direction, vitesse, temps):
        # Convertir la direction en radians
        direction_rad = math.radians(direction)

        # Calculer le déplacement en x et y
        dx = vitesse * math.cos(direction_rad) * temps
        dy = vitesse * math.sin(direction_rad) * temps

        # Mettre à jour la position de l'objet
        self.x += dx
        self.y += dy

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
        self.WINDOW_SIZE = (1100, 800)
        self.BORDER_DISTANCE = 200
        self.X_RATIO = self.WINDOW_SIZE[0] / self.FIELD_SIZE[0]
        self.Y_RATIO = self.WINDOW_SIZE[1] / self.FIELD_SIZE[1]
        self.X_ROBOT = self.FIELD_SIZE[0] / 2
        self.Y_ROBOT = self.FIELD_SIZE[1] / 2
        self.POINT_COLOR = (255, 0, 0)
        self.BACKGROUND_COLOR = self.LIGHT_GREY
        self.FONT_COLOR = self.BLACK

        self.path_picture = "Lidar/Terrain_Jeu.png"

        self.nb_scan = 0
        self.tab_scan = []

        self.id_compteur = 0  # Compteur pour les identifiants d'objet
        self.objets = []  # Liste pour stocker les objets détectés

        pygame.init()
        self.lcd = pygame.display.set_mode(self.WINDOW_SIZE)
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 20)
        pygame.mouse.set_visible(True)
        pygame.display.set_caption('LiDAR Scan')
        self.lcd.fill(self.BACKGROUND_COLOR)
        pygame.display.update()

        self.port = self.choix_du_port()

        logging.basicConfig(filename='lidar_scan.log', level=logging.INFO,datefmt='%d/%m/%Y %H:%M:%S',format='%(asctime)s - %(levelname)s - %(message)s')

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
        self.draw_text("x: " + str(self.X_ROBOT), 10, 5)
        self.draw_text("y: " + str(self.Y_ROBOT), 10, 25)
        self.draw_text("theta: " + str(self.ROBOT_ANGLE), 100, 15)                

    def draw_field(self):
        pygame.draw.rect(self.lcd, pygame.Color(100, 100, 100),
                         (self.BORDER_DISTANCE * self.X_RATIO - 5, self.BORDER_DISTANCE * self.Y_RATIO - 5,
                          (self.FIELD_SIZE[0] - 2 * self.BORDER_DISTANCE) * self.X_RATIO + 10,
                          (self.FIELD_SIZE[1] - 2 * self.BORDER_DISTANCE) * self.Y_RATIO + 10), 10)

    def draw_point(self, x, y, angle, distance):
        new_angle = angle - self.ROBOT_ANGLE
        if new_angle < 0:
            new_angle += 360
        x = self.X_ROBOT + int(distance * math.cos(new_angle * math.pi / 180))
        y = self.Y_ROBOT + int(distance * math.sin(new_angle * math.pi / 180))

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
        direction, vitesse = objet.get_direction_vitesse()
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

        x = self.X_ROBOT + int(x / len(points_autour_objet))
        y = self.Y_ROBOT + int(y / len(points_autour_objet))

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

        # Incrémenter le compteur d'identifiants
        self.id_compteur += 1

        # Si l'objet n'est pas déjà suivi, créer un nouvel objet
        nouvel_objet = Objet(self.id_compteur, x, y, taille)
        self.objets.append(nouvel_objet)

        return nouvel_objet

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
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit(0)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                        exit(0)

            scan = self.valeur_de_test()
            zone_objet = self.detect_object(scan)
            self.draw_background()
            self.draw_robot(self.X_ROBOT, self.Y_ROBOT, self.ROBOT_ANGLE)
            self.draw_object(zone_objet)
            for point in scan:
                self.draw_point(self.X_ROBOT, self.Y_ROBOT, point[1], point[2])

            pygame.display.update()
            self.lcd.fill(self.WHITE)
            self.ROBOT_ANGLE += 5
            
            #Déplacement du robot virtuel avec des touches du clavier
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.X_ROBOT -= 10
            if keys[pygame.K_RIGHT]:
                self.X_ROBOT += 10
            if keys[pygame.K_UP]:
                self.Y_ROBOT -= 10
            if keys[pygame.K_DOWN]:
                self.Y_ROBOT += 10

            time.sleep(0.01)
    
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
            logging.info("Starting LiDAR motor")
            print("Démarrage du moteur LiDAR")

            #ComESP32(port="COM3", baudrate=115200).run()

            running = True  # Ajoutez une variable de contrôle pour gérer la fermeture de la fenêtre

            while running:

                for scan in self.lidar.iter_scans(8000):
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.stop()
                            pass
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                                self.stop()
                                pass
                    
                    self.draw_background()
                    self.draw_robot(self.X_ROBOT, self.Y_ROBOT, self.ROBOT_ANGLE)
                    zone_objet = self.detect_object(scan)
                    self.draw_object(self.objets[0])

                    for (_, angle, distance) in scan:
                        self.draw_point(self.X_ROBOT, self.Y_ROBOT, angle, distance)
                    pygame.display.update()
                    self.lcd.fill(self.WHITE)

        except KeyboardInterrupt:
            self.stop()
            pass

if __name__ == '__main__':
    scanner = LidarScanner()
    scanner.run()