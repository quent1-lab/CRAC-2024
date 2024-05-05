import  logging
from    rplidar import RPLidar, RPLidarException
import  math
import  serial.tools.list_ports
import  os
from    objet import Objet
from    client import *
import  logging
import  numpy as np
from    sklearn.cluster import DBSCAN

# Configuration du logger
logging.basicConfig(filename='lidar.log', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S', format='%(asctime)s - %(levelname)s - %(message)s')

class LidarScanner:
    def __init__(self, port=None):
        self.port = port
        self.lidar = None
        self.ROBOT_ANGLE = 0
        self.BORDER_DISTANCE = 200
        self.FIELD_SIZE = (3000, 2000)
        self.scanning = True
        self.perimetre_securite = 400 # rayon de sécurité en mm

        # Initialisation du robot virtuel
        self.ROBOT = Objet(0, 1500, 1000, 20)

        self.objets = []  # Liste pour stocker les objets détectés

        self.client_socket = Client('127.0.0.3', 22050, 3)

        logging.basicConfig(filename='lidar_scan.log', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S', format='%(asctime)s - %(levelname)s - %(message)s')

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
            new_angle = point[1] - self.ROBOT_ANGLE + 180
            
            x_robot = self.map_value(self.ROBOT.x, 0, self.FIELD_SIZE[0], self.FIELD_SIZE[0], 0)
            
            new_angle %= 360
            if new_angle < 0:
                new_angle += 360

            if distance != 0:
                x = distance * math.cos(math.radians(new_angle)) + x_robot
                y = distance * math.sin(math.radians(new_angle)) + self.ROBOT.y

                # Vérifier si le point est en dehors du terrain de jeu
                if self.BORDER_DISTANCE < x < self.FIELD_SIZE[0] - self.BORDER_DISTANCE and self.BORDER_DISTANCE < y < self.FIELD_SIZE[1] - self.BORDER_DISTANCE:
                    points.append((int(x), int(y), int(distance), int(new_angle)))
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

    def detect_objects(self, scan, eps=300, min_samples=3):

        # Regroupement des points avec DBSCAN
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

        return objets

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
                self.port = "/dev/" + [port.name for port in serial.tools.list_ports.comports() if port.serial_number and "0001" in port.serial_number][0]

            self.lidar = RPLidar(self.port, logger=logging.getLogger('rplidar'))
            self.lidar.connect()
        except RPLidarException as e:
            # Code pour gérer RPLidarException
            logging.error(f"Failed to connect to RPLidar, retrying: {e}")
            self.lidar.stop()
            self.connexion_lidar()
        except Exception as e:
            logging.error(f"Failed to create an instance of RPLidar: {e}")

            time.sleep(1)
            exit(0)

    def stop(self):
        self.scanning = False
        logging.info("Stopping LiDAR motor")
        print("LIDAR  : Arrêt du moteur")

    def generate_JSON_Objets(self, objets):
        # Générer une chaîne de caractères au format JSON des objets détectés en fonction des id
        json = "["
        for objet in objets:
            json += str(objet) + ","
        json = json[:-1] + "]"
        return json

    def generate_JSON_Points(self, points):
        # Générer une chaîne de caractères au format JSON des points en fonction des coordonnées (x, y)
        json = "["
        for point in points:
            json += f"{{\"x\": {point[0]}, \"y\": {point[1]}, \"dist\": {point[2]}, \"angle\": {point[3]}}},"
        json = json[:-1] + "]"
        return json

    def map_value(self,x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def receive_to_server(self, message):
        if message["cmd"] == "stop":
            self.client_socket.stop()
        else:
            if message["cmd"] == "coord":
                coord = message["data"]
                logging.info(f"Received new position: {coord}")
                self.ROBOT.update_position(coord["x"], coord["y"])
                self.ROBOT_ANGLE = coord["theta"]/10 # Angle en degrés * 10

    def run(self):
        
        self.connexion_lidar()
        print("LIDAR  : Connecté au LiDAR")
        logging.info("LiDAR connected")
        self.client_socket.set_callback(self.receive_to_server)
        self.client_socket.set_callback_stop(self.stop)
        self.client_socket.connect()

        while self.scanning:
            self.objets = []
            try:
                logging.info("Starting LiDAR scan")
                for scan in self.lidar.iter_scans():
                    if not self.scanning:
                        break
                    new_scan = self.transform_scan(scan)
                    self.client_socket.add_to_send_list(self.client_socket.create_message(10, "points", self.generate_JSON_Points(new_scan)))
                    
                    if len(new_scan) > 0:
                        new_objets = self.detect_objects(new_scan)
                        #self.suivre_objet(new_objets, 100)
                        
                        # Vérifier si l'objet rentre dans le périmètre de sécurité
                        for objet in new_objets:
                            distance_objet = math.sqrt((objet.x - self.ROBOT.x)**2 + (objet.y - self.ROBOT.y)**2)
                            #logging.info(f"Distance to object: {distance_objet}")
                            if distance_objet < self.perimetre_securite:
                                # Envoyer un message d'alerte
                                logging.info("Object detected in security perimeter")
                                self.client_socket.add_to_send_list(self.client_socket.create_message(0, "lidar", {"etat": "stop", "distance": distance_objet}))
                                
                                # Arrêter le robot
                                self.client_socket.add_to_send_list(self.client_socket.create_message(2, "CAN", {"id": 503, "byte1": 0}))
                                time.sleep(0.1)
                                self.client_socket.add_to_send_list(self.client_socket.create_message(2, "CAN", {"id": 503, "byte1": 1}))
                                break
                        
                        self.client_socket.add_to_send_list(self.client_socket.create_message(10, "objects", self.generate_JSON_Objets(new_objets)))
            except RPLidarException as e:
                # Code pour gérer RPLidarException
                print(f"LIDAR  : Une erreur RPLidarException s'est produite dans le run : {e}")
                self.lidar.stop()
                #self.lidar.disconnect()
                #self.connexion_lidar()
                time.sleep(2)
                
            except KeyboardInterrupt:
                self.stop()
                break
        self.lidar.stop()
        self.lidar.disconnect()
        exit(0)

if __name__ == '__main__':
    # Initialiser le client
    scanner = LidarScanner()
    try :
        print("LIDAR  : Démarrage du programme")
        logging.info("Starting LiDAR scanner")
        scanner.run()
    except KeyboardInterrupt:
        scanner.stop()
    except Exception as e:
            print(f"LIDAR  : Une erreur s'est produite : {e}")
            scanner.stop()
            time.sleep(2)
            #scanner.run()
    print("LIDAR  : Fin du programme")