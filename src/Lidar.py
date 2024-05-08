import  logging
from    rplidar import RPLidar, RPLidarException
import  math
import  serial.tools.list_ports
import  os
from    objet import Objet
from    client import *
import  numpy as np
from    sklearn.cluster import DBSCAN
import  threading

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
        self.perimetre_securite = 700 # rayon de sécurité en mm
        
        self.is_started = False # Si le programme est démarré
        self.en_mvt = False # Si le robot est en mouvement
        self.sens = "avant" # Sens de déplacement du robot

        # Initialisation du robot virtuel
        self.ROBOT = Objet(0, 1500, 1000, 20)

        self.objets = []  # Liste pour stocker les objets détectés
        self.new_scan = []  # Liste pour stocker les scans du LiDAR

        self.client_socket = Client('127.0.0.3', 22050, 3)
        
        self.client_socket.set_callback(self.receive_to_server)
        self.client_socket.set_callback_stop(self.stop)
        self.client_socket.connect()

        logging.basicConfig(filename='lidar_scan.log', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S', format='%(asctime)s - %(levelname)s - %(message)s')

    # ============================== Fin du constructeur ==============================

    def transform_scan(self, scan):
        """
        Transforme les données du scan en coordonnées cartésiennes.
        Retire les points en dehors du terrain de jeu.

        :param scan: Liste de tuples (quality, angle, distance)
        :return: Liste de tuples (x, y, distance)
        """
        points = []
        for i, point in enumerate(scan):
            
            distance = point[2]
            
            if distance > 600:
                continue
            
            # Filtre tous les points qui sont à moins de 200 mm du robot
            if distance <  250 :
                continue
            
            """if self.sens == "arriere":
                # On regarde derrière le robot
                if not (120 < point[1] < 240) :
                    continue
            elif self.sens == "avant":
                # On regarde devant le robot
                if not (point[1] > 300 or point[1] < 60) :
                    continue"""
            
            new_angle = point[1] - self.ROBOT_ANGLE
            
            #x_r = self.map_value(self.ROBOT.x, 0, 3000, 3000, 0)
            x_r = self.ROBOT.x

            new_angle %= 360

            if distance != 0:
                x = distance * math.cos(math.radians(new_angle)) + x_r
                y = distance * math.sin(math.radians(-new_angle)) + self.ROBOT.y

                # Vérifier si le point est en dehors du terrain de jeu
                if self.BORDER_DISTANCE < x < self.FIELD_SIZE[0] - self.BORDER_DISTANCE and self.BORDER_DISTANCE < y < self.FIELD_SIZE[1] - self.BORDER_DISTANCE:
                    points.append((int(x), int(y), int(distance), int(new_angle)))
        return points

    def detect_objects(self, scan, eps=150, min_samples=3):

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
            self.port = None
            self.connexion_lidar()
        except Exception as e:
            logging.error(f"Failed to create an instance of RPLidar: {e}")

            time.sleep(1)
            exit(0)

    def stop(self):
        self.scanning = False
        logging.info("Stopping LiDAR motor")

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
        elif message["cmd"] == "coord":
                coord = message["data"]
                self.ROBOT.update_position(coord["x"], coord["y"])
                self.ROBOT_ANGLE = coord["theta"]/10 # Angle en degrés * 10
        elif message["cmd"] == "jack":
            etat = message["data"]
            if etat["etat"] == "start":
                pass
        elif message["cmd"] == "move":
            etat = message["data"]
            self.en_mvt = etat["etat"]
        elif message["cmd"] == "sens":
            sens = message["data"]
            self.sens = sens["sens"]
        elif message["cmd"] == "start":
            self.is_started = True
                
    def clustering_process(self):
        while self.scanning:
            # Récupérer les scans de la file d'attente toutes les 200 ms
            try:
                if len(self.new_scan) > 0:
                    new_objets = self.detect_objects(self.new_scan)
                    
                    for objet in new_objets:
                            distance_objet = math.sqrt((objet.x - self.ROBOT.x)**2 + (objet.y - self.ROBOT.y)**2)
                            #logging.info(f"Objet détecté à {distance_objet} mm")
                            if self.is_started:
                                if distance_objet < self.perimetre_securite:
                                    if self.en_mvt:
                                        # Envoyer un message d'alerte
                                        self.client_socket.add_to_send_list(self.client_socket.create_message(0, "lidar", {"etat": "stop", "distance": distance_objet}))
                                        
                                        # Arrêter le robot
                                        self.client_socket.add_to_send_list(self.client_socket.create_message(2, "CAN", {"id": 503, "byte1": 0}))
                                        time.sleep(0.1)
                                        self.client_socket.add_to_send_list(self.client_socket.create_message(2, "CAN", {"id": 503, "byte1": 1}))
                                        break
                                elif distance_objet < self.perimetre_securite + 200:
                                    if not self.en_mvt:
                                        # Envoyer un message de reprise
                                        self.client_socket.add_to_send_list(self.client_socket.create_message(0, "lidar", {"etat": "start", "distance": distance_objet}))
                    
                    #self.client_socket.add_to_send_list(self.client_socket.create_message(10, "objects", self.generate_JSON_Objets(new_objets)))
                    
                    time.sleep(0.2)
            except Exception as e:
                logging.error(f"Error in clustering process: {e}")
            
    def run(self):  
        time.sleep(1)
        self.connexion_lidar()
        time.sleep(0.5)
        
        logging.info("LiDAR connected")
        
        self.en_mvt = False
        
        # Création d'un thread pour le clustering
        #clustering_thread = threading.Thread(target=self.clustering_process)
        #clustering_thread.start()
        try:
            logging.info(f"Status: {self.lidar.get_health()}")
        except Exception as e:
            logging.error(f"Error in getting LiDAR status: {e}")
        
        while self.scanning:
            self.objets = []
            try:
                logging.info("Scanning")
                for scan in self.lidar.iter_scans():
                    if not self.scanning:
                        break
                    self.new_scan = self.transform_scan(scan)
                    
                    if len(self.new_scan) > 0:
                        # Si 5 points consécutif sont détectés, on envoie une pause au serveur
                        new_objets = self.detect_objects(self.new_scan)
                        logging.info(f"New objects: {new_objets}")
                        if self.en_mvt and len(new_objets) > 0:
                            logging.info("Objet détecté")
                            self.client_socket.add_to_send_list(self.client_socket.create_message(4, "lidar", {"etat": "pause"}))
                            self.en_mvt = False
                        elif not self.en_mvt and len(new_objets) == 0:
                            logging.info("Aucun objet détecté")
                            self.client_socket.add_to_send_list(self.client_socket.create_message(4, "lidar", {"etat": "resume"}))
                    
                    #logging.info(f"New scan: {self.new_scan}")
                    #self.client_socket.add_to_send_list(self.client_socket.create_message(10, "points", self.generate_JSON_Points(self.new_scan)))
                        
            except RPLidarException as e:
                # Code pour gérer RPLidarException
                logging.error(f"An error occurred in the run: {e}")
                self.lidar.stop()
                time.sleep(3)
                
            except KeyboardInterrupt:
                self.stop()
                break
        
        self.client_socket.stop()
        self.lidar.stop()
        self.lidar.disconnect()
        exit(0)

if __name__ == '__main__':
    # Initialiser le client
    scanner = LidarScanner()
    time.sleep(2)
    try :
        logging.info("Starting LiDAR scanner")
        scanner.run()
    except KeyboardInterrupt:
        scanner.stop()
    except Exception as e:
            logging.error(f"An error occurred in the main: {e}")
            scanner.stop()
            time.sleep(2)
            """scanner = None
            scanner = LidarScanner()
            scanner.run()"""