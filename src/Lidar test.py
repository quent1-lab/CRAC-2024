import pygame
from    rplidar import RPLidar, RPLidarException
import  serial.tools.list_ports
import  time
import  math
import  numpy as np
from    sklearn.cluster import DBSCAN

# Configuration du logger

class LidarScanner:
    def __init__(self, port=None):
        self.port = port
        self.lidar = None
        self.ROBOT_ANGLE = 0
        self.BORDER_DISTANCE = 200
        self.FIELD_SIZE = (3000, 2000)
        self.scanning = True
        self.perimetre_securite = 600 # rayon de sécurité en mm
        
        self.is_started = False # Si le programme est démarré
        self.en_mvt = False # Si le robot est en mouvement
        self.sens = "avant" # Sens de déplacement du robot

        self.objets = []  # Liste pour stocker les objets détectés
        self.new_scan = []  # Liste pour stocker les scans du LiDAR
        
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
            
            
            if distance > 1000:
                continue
            
            # Filtre tous les points qui sont à moins de 200 mm du robot
            if distance <  250 :
                continue
            
            new_angle = point[1] - self.ROBOT_ANGLE

            new_angle %= 360

            if distance != 0:
                x = distance * math.cos(math.radians(new_angle)) + 1500
                y = distance * math.sin(math.radians(-new_angle)) + 1000

            if self.BORDER_DISTANCE < x < self.FIELD_SIZE[0] - self.BORDER_DISTANCE and self.BORDER_DISTANCE < y < self.FIELD_SIZE[1] - self.BORDER_DISTANCE:
                    points.append((int(x), int(y), int(distance), int(new_angle)))
        return points

    def detect_objects(self, scan, eps=100, min_samples=4):

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
            
            nouvel_objet = (int(x_moyen), int(y_moyen))

            objets.append(nouvel_objet)

        return objets

    
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

    
    def connexion_lidar(self):
        # Connexion au lidar
        try:
            if self.port == None:
                self.port = "/dev/" + [port.name for port in serial.tools.list_ports.comports() if port.serial_number and "0001" in port.serial_number][0]
            self.lidar = RPLidar(self.port)
            self.lidar.connect()
        except RPLidarException as e:
            # Code pour gérer RPLidarException
            self.lidar.stop()
            self.port = None
            self.connexion_lidar()
        except Exception as e:

            time.sleep(1)
            exit(0)

    def stop(self):
        self.scanning = False

    def map_value(self,x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
            
    def run(self):
        
        self.connexion_lidar()
        print("LIDAR  : Connecté au LiDAR")
        
        self.en_mvt = False
        
        while self.scanning:
            self.objets = []
            try:
                for scan in self.lidar.iter_scans():
                    if not self.scanning:
                        break
                    self.new_scan = self.transform_scan(scan)
                    
                    self.lcd.fill((0, 0, 0))
                    for point in self.new_scan:
                        self.draw_point(point[0], point[1])
                    if len(self.new_scan) > 0:
                        self.objets = self.detect_objects(self.new_scan)
                        for objet in self.objets:
                            pygame.draw.circle(self.lcd, pygame.Color(
                                (255, 0, 0)), (objet[0] * self.X_RATIO, objet[1] * self.Y_RATIO), 20, 1)
                    
                    pygame.display.update()
                        
            except RPLidarException as e:
                # Code pour gérer RPLidarException
                print(f"LIDAR  : Une erreur RPLidarException s'est produite dans le run : {e}")
                self.lidar.stop()
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
        scanner.run()
    except KeyboardInterrupt:
        scanner.stop()
    except Exception as e:
            print(f"LIDAR  : Une erreur s'est produite : {e}")
            scanner.stop()
            time.sleep(2)
            #scanner.run()
    print("LIDAR  : Fin du programme")