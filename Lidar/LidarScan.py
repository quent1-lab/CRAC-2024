import logging
from rplidar import RPLidar
import pygame
import math
import random
import time
import serial.tools.list_ports

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

    def run(self):
        try:
            self.connect()
            while True:
                self.send(b'1')
                print(self.receive())
                time.sleep(1)
        except KeyboardInterrupt:
            self.disconnect()
            pass

class LidarScanner:
    def __init__(self, port):
        self.port = port
        self.lidar = None
        self.lcd = None
        self.ROBOT_ANGLE = 0
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.FIELD_SIZE = (3000, 2000)
        self.WINDOW_SIZE = (900, 600)
        self.BORDER_DISTANCE = 100
        self.X_RATIO = self.WINDOW_SIZE[0] / self.FIELD_SIZE[0]
        self.Y_RATIO = self.WINDOW_SIZE[1] / self.FIELD_SIZE[1]
        self.X_ROBOT = self.FIELD_SIZE[0] / 2
        self.Y_ROBOT = self.FIELD_SIZE[1] / 2
        self.POINT_COLOR = (255, 0, 0)

        pygame.init()
        self.lcd = pygame.display.set_mode(self.WINDOW_SIZE)
        pygame.mouse.set_visible(True)
        pygame.display.set_caption('LiDAR Scan')
        self.lcd.fill(self.BLACK)
        pygame.display.update()

        logging.basicConfig(filename='lidar_scan.log', level=logging.INFO)

    def draw_robot(self, x, y, angle):
        pygame.draw.circle(self.lcd, pygame.Color(0, 0, 250), (x * self.X_RATIO, y * self.Y_RATIO), 10)
        pygame.draw.line(
            self.lcd, pygame.Color(0, 0, 250),
            (x * self.X_RATIO, y * self.Y_RATIO),
            ((x + 50 * math.cos(angle)) * self.X_RATIO, (y + 50 * math.sin(angle)) * self.Y_RATIO), 3
        )

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

        self.POINT_COLOR = (255, 0, 0)

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
            pygame.draw.circle(self.lcd, pygame.Color(self.POINT_COLOR), (x * self.X_RATIO, y * self.Y_RATIO), 2)
        except pygame.error as e:
            print("Failed to draw circle")
            logging.error(f"Failed to draw circle: {e}")

    def draw_object(self, objet):
        pygame.draw.circle(self.lcd, pygame.Color(255, 255, 0), (objet[0] * self.X_RATIO, objet[1] * self.Y_RATIO), 10)
        pygame.draw.circle(self.lcd, pygame.Color(50, 50, 200), (objet[0] * self.X_RATIO, objet[1] * self.Y_RATIO), int(objet[2] / 2 * self.X_RATIO), 3)

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

        return (x, y, taille)

    def tracking_object(self, zone_objet, zone_objet_precedente):
        if zone_objet > zone_objet_precedente:
            return "avance"
        elif zone_objet < zone_objet_precedente:
            return "recule"
        else:
            return "stable"
        
    def choix_du_port(self):
        ports = serial.tools.list_ports.comports()

        #Affichage des ports détectés
        for port in ports:
            print(port.device)
        
        #Si un seul port est détecté, on le retourne
        if len(ports) == 1:
            return ports[0].device
        
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
                        return port_.device
                raise ValueError
            except ValueError:
                print("Port invalide")
                continue
            except KeyboardInterrupt:
                exit(0)

    def valeur_de_test(self):
        scan = []
        for i in range(350):
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
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit(0)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        exit(0)

            scan = self.valeur_de_test()
            zone_objet = self.detect_object(scan)
            self.draw_field()
            self.draw_robot(self.X_ROBOT, self.Y_ROBOT, self.ROBOT_ANGLE)
            self.draw_object(zone_objet)
            for point in scan:
                self.draw_point(self.X_ROBOT, self.Y_ROBOT, point[1], point[2])

            pygame.display.update()
            self.lcd.fill(self.WHITE)
            self.ROBOT_ANGLE += 1
            time.sleep(0.1)
    
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


                    self.draw_robot(self.X_ROBOT, self.Y_ROBOT, self.ROBOT_ANGLE)
                    self.draw_field()
                    self.draw_object(self.detect_object(scan))
                    for (_, angle, distance) in scan:
                        self.draw_point(self.X_ROBOT, self.Y_ROBOT, angle, distance)
                    pygame.display.update()
                    self.lcd.fill(self.WHITE)

        except KeyboardInterrupt:
            self.stop()
            pass

if __name__ == '__main__':
    scanner = LidarScanner(LidarScanner.choix_du_port(self=0))
    scanner.run()
