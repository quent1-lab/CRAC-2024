import logging
from rplidar import RPLidar
import pygame
import math
import random
import time

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
        pygame.draw.circle(self.lcd, pygame.Color(255, 255, 0), (objet[0] * self.X_RATIO, objet[1] * self.Y_RATIO), int(objet[2] / 2 * self.X_RATIO), 3)

    def detect_object(self, scan):
        objet = min(scan, key=lambda x: x[2])
        angle_objet = objet[1]
        distance_objet = objet[2]
        points_autour_objet = []

        for point in scan:
            if angle_objet - 5 < point[1] < angle_objet + 5:
                if distance_objet - 100 < point[2] < distance_objet + 100:
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
        zone_objet_precedente = 0
        print("Programme de test")
        while True:
            scan = self.valeur_de_test()
            zone_objet = self.detect_object(scan)
            self.draw_field()
            self.draw_robot(self.X_ROBOT, self.Y_ROBOT, self.ROBOT_ANGLE)
            self.draw_object(zone_objet)
            for point in scan:
                self.draw_point(self.X_ROBOT, self.Y_ROBOT, point[1], point[2])
            zone_objet_precedente = zone_objet
            pygame.display.update()
            self.lcd.fill(self.WHITE)
            self.ROBOT_ANGLE += 1
            time.sleep(0.1)

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

            while True:
                for scan in self.lidar.iter_scans(8000):
                    self.draw_robot(self.X_ROBOT, self.Y_ROBOT, self.ROBOT_ANGLE)
                    self.draw_field()
                    self.draw_object(self.detect_object(scan))
                    for (_, angle, distance) in scan:
                        self.draw_point(self.X_ROBOT, self.Y_ROBOT, angle, distance)
                    pygame.display.update()
                    self.lcd.fill(self.WHITE)

        except KeyboardInterrupt:
            logging.info("Stopping LiDAR motor")
            self.lidar.stop()
            time.sleep(1)
            self.lidar.disconnect()

if __name__ == '__main__':
    scanner = LidarScanner('COM7')
    scanner.run()
