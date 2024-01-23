import logging
from rplidar import RPLidar,RPLidarException
import math
import time
import serial.tools.list_ports
import os
#import can
import time
import json

import socket
import threading
import pickle


class Client:
    def __init__(self):
        self.objet_lidar = None
        self.objet_lidar_lock = threading.Lock()  # Verrou pour assurer une lecture/écriture sécurisée
        self.ROBOT = Objet(0, 1500, 1000, 20)
        self.Robot_lock = threading.Lock()  # Verrou pour assurer une lecture/écriture sécurisée

    def receive_data(self, client_socket):
        while True:
            data_received = client_socket.recv(4096)
            if not data_received:
                break
            else:
                message = pickle.loads(data_received)
                data = json.loads(message)
                with self.Robot_lock:
                    self.ROBOT.update_position(data["x"], data["y"])
                    self.ROBOT.taille = data["taille"]
                print(message)

    def send_data(self, client_socket):
        while True:
            # Faire quelque chose avec objet_lidar_local et l'envoyer au serveur
            with self.objet_lidar_lock:
                message_to_send = pickle.dumps(self.objet_lidar)
            if message_to_send != None:
                client_socket.sendall(message_to_send)
            time.sleep(0.1)
    
    def update_lidar_object(self, objet):
        with self.objet_lidar_lock:
            self.objet_lidar = objet
    
    def get_objet_robot(self):
        with self.Robot_lock:
            return self.ROBOT
            
"""class ComCAN:
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
            pass"""

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
        self.points = []
        self.last_moved = time.time()

    def update_position(self, x, y):
        # Mettre à jour la position de l'objet et ajouter la position précédente à la liste
        if self.x != x or self.y != y:
            self.positions_precedentes.append((self.x, self.y, time.monotonic_ns()))
            self.x = x
            self.y = y
            self.last_moved = time.time()

    def reset_if_not_moved(self, delay):
        if time.time() > self.last_moved + delay:
            return True
        else:
            return False

    def get_direction_speed(self):
        # Calculer le vecteur de déplacement entre la position actuelle et la position précédente
        dx = self.x - self.positions_precedentes[-1][0]
        dy = self.y - self.positions_precedentes[-1][1]

        # Calculer le temps écoulé entre la position actuelle et la position précédente
        dt = (time.monotonic_ns() - self.positions_precedentes[-1][2]) + 0.0000001 # Ajout de 0.00001 pour éviter la division par 0

        # La direction est l'angle du vecteur de déplacement
        self.direction = math.atan2(dy, dx)

        # La vitesse est la magnitude du vecteur de déplacement divisée par le temps écoulé
        self.vitesse = math.sqrt(dx**2 + dy**2) / dt * 1000000000  # Conversion en mm/s

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
        # Retourne une chaîne de caractères représentant l'objet sous format JSON
        return f"{{\"id\": {self.id}, \"x\": {int(self.x)}, \"y\": {int(self.y)}, \"taille\": {int(self.taille)}}}"
    
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

        self.objets = []  # Liste pour stocker les objets détectés

        self.client_socket = None

        logging.basicConfig(filename='lidar_scan.log', level=logging.INFO,datefmt='%d/%m/%Y %H:%M:%S',format='%(asctime)s - %(levelname)s - %(message)s')

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

    def detect_object(self, scan, max_iteration=5, nb_objets_max=1):
        iteration = 0
        while iteration < max_iteration:
            iteration += 1

            # Liste des points associés aux objets déjà trouvés
            points_objets_trouves = []
            for k in range(iteration):
                if k < len(self.objets):
                    points_objets_trouves += self.objets[k].points

            # Sélectionne le point le plus proche du robot en excluant les points des objets déjà trouvés
            points_non_objets = [point for point in scan if point not in points_objets_trouves]
            if not points_non_objets:
                # Aucun point trouvé en dehors des objets, retourner None
                return None

            # Sélectionne le point le plus proche du robot
            point_proche = min(points_non_objets, key=lambda x: x[2])
            distance_objet = point_proche[2]
            angle_objet = point_proche[3]
            points_autour_objet = []

            # Sélectionne les points autour de l'objet en fonction des coordonnées (x, y) des points
            points_autour_objet = self.get_points_in_zone(points_non_objets, distance_objet, angle_objet)

            if not points_autour_objet or len(points_autour_objet) < 3:
                # Aucun point autour de l'objet ou pas assez de points, retourner None
                return None

            # Calcul des coordonnées moyennes pondérées des points autour de l'objet
            x = sum([point[0] for point in points_autour_objet]) / len(points_autour_objet)
            y = sum([point[1] for point in points_autour_objet]) / len(points_autour_objet)

            # Calcul de la taille de l'objet
            x_min = min(points_autour_objet, key=lambda x: x[0])
            x_max = max(points_autour_objet, key=lambda x: x[0])
            y_min = min(points_autour_objet, key=lambda x: x[1])
            y_max = max(points_autour_objet, key=lambda x: x[1])
            taille = math.sqrt((x_max[0] - x_min[0])**2 + (y_max[1] - y_min[1])**2)

            # Seuil de détection d'un objet en mm
            SEUIL = 120  # en mm (distance que peut parcourir le robot entre deux scans)
            
            id_objet_existant = self.trouver_id_objet_existants(x, y, SEUIL)

            if id_objet_existant != None:
                # Si l'objet est déjà suivi, mettre à jour ses coordonnées
                self.objets[id_objet_existant - 1].update_position(x, y)
                self.objets[id_objet_existant - 1].taille = taille
                self.objets[id_objet_existant - 1].points = points_autour_objet
            else:
                if len(self.objets) < nb_objets_max:
                    # Si l'objet n'est pas déjà suivi, créer un nouvel objet
                    nouvel_objet = Objet(len(self.objets)+1, x, y, taille)
                    nouvel_objet.points = points_autour_objet
                    self.objets.append(nouvel_objet)
                else:
                    # Si le nombre d'objets max est atteint, retourner None
                    return None           

    def detect_object_v1(self, scan):
        objet = min(scan, key=lambda x: x[2]) #Sélectionne le point le plus proche du robot
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
            new_angle %= 360
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
            
        if(len(self.objets) < 1):
            # Incrémenter le compteur d'identifiants
            self.id_compteur += 1

            # Si l'objet n'est pas déjà suivi, créer un nouvel objet
            nouvel_objet = Objet(self.id_compteur, x, y, taille)
            self.objets.append(nouvel_objet)

    def trouver_id_objet_existants(self, x, y, seuil_distance=100):
        # Vérifier si l'objet est déjà suivi
        for objet in self.objets:
            distance = math.sqrt((x - objet.x)**2 + (y - objet.y)**2)
            if distance < seuil_distance:
                return objet.id # Retourne l'ID de l'objet existant
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
        
        return trajectoire_actuel, trajectoire_adverse, trajectoire_evitement

    def connexion_lidar(self):
        # Connexion au lidar
        try:
            if self.port == None:
                self.port = [port.name for port in serial.tools.list_ports.comports() if port.serial_number and "0001" in port.serial_number][0]

            self.lidar = RPLidar(self.port)
            self.lidar.connect()
            logging.info("Lidar connected")
            print("LiDAR connecté")
        except RPLidarException as e:
            # Code pour gérer RPLidarException
            print(f"Une erreur RPLidarException s'est produite dans le connexion : {e}")
            self.lidar.stop()
            self.connexion_lidar()
        except Exception as e:
            logging.error(f"Failed to create an instance of RPLidar: {e}")
            print("Erreur lors de la création de l'instance du LiDAR")

            time.sleep(1.5)
            exit(0)
            raise

    def stop(self):
        logging.info("Stopping LiDAR motor")
        print("Arrêt du moteur LiDAR")
        self.lidar.stop()
        time.sleep(1)
        self.lidar.disconnect()
        self.client_socket.close()
        exit(0)

    def generate_JSON(self):
        # Générer une chaîne de caractères au format JSON des objets détectés en fonction des id
        json = "["
        for objet in self.objets:
            json += str(objet) + ","
        json = json[:-1] + "]"
        return json

    def run(self):
        
        self.connexion_lidar()

        while True:
            self.objets = []
            try:
                
                for scan in self.lidar.iter_scans(4000):
                    ROBOT = client.get_objet_robot()
                    new_scan = self.transform_scan(scan)
                    
                    for objet in self.objets:
                        if objet.reset_if_not_moved(2):
                            self.objets.remove(objet)

                    self.detect_object(new_scan)
                    client.update_lidar_object(self.generate_JSON())
                    
            except RPLidarException as e:
                # Code pour gérer RPLidarException
                print(f"Une erreur RPLidarException s'est produite dans le run : {e}")
                self.lidar.stop()
                time.sleep(1)
                
            except KeyboardInterrupt:
                self.stop()
                break

if __name__ == '__main__':
    # Initialiser le client
    client = Client()
    scanner = LidarScanner("/dev/ttyUSB0")

    server_address = ('192.168.36.141', 5000)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(server_address)

    # Démarrer les threads de communication
    receive_thread = threading.Thread(target=client.receive_data, args=(client_socket,))
    send_thread = threading.Thread(target=client.send_data, args=(client_socket,))
    lidar_handler_thread = threading.Thread(target=client.update_lidar_object, args=(scanner.objets,))

    lidar_scan = threading.Thread(target=scanner.run)
    
    receive_thread.start()
    send_thread.start()
    lidar_handler_thread.start()
    lidar_scan.start()

    send_thread.join()
    receive_thread.join()
    lidar_handler_thread.join()
    lidar_scan.join()
    
    