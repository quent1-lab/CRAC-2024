import pygame
from math import cos, sin, pi, floor
from rplidar import RPLidar

# Initialisation de Pygame et de l'affichage
pygame.init()
lcd = pygame.display.set_mode((320, 240))
pygame.mouse.set_visible(False)
lcd.fill((0, 0, 0))
pygame.display.update()

# Configuration du lidar
PORT_NAME = 'COM5'  # À modifier en fonction du port utilisé ; sur linux : /dev/ttyUSBx (x = 0, 1, 2, ...)
lidar = RPLidar(PORT_NAME)

# Utilisé pour mettre à l'échelle les données pour les afficher à l'écran
max_distance = 0

# Cette directive permet d'utiliser la variable globale max_distance
# pylint: disable=redefined-outer-name,global-statement

def process_data(data):
    global max_distance
    lcd.fill((0, 0, 0))
    for angle in range(360):
        distance = data[angle]
        if distance > 0:  # Ignorer les points de données initialement non collectés
            max_distance = max([min([5000, distance]), max_distance])
            radians = angle * pi / 180.0
            x = distance * cos(radians)
            y = distance * sin(radians)
            point = (160 + int(x / max_distance * 119), 120 + int(y / max_distance * 119))
            lcd.set_at(point, pygame.Color(255, 255, 255))
    pygame.display.update()

scan_data = [0] * 360

lidar.connect()
print(lidar.get_info())

try:
    for scan in lidar.iter_scans():
        for (_, angle, distance) in scan:
            scan_data[min([359, floor(angle)])] = distance
        process_data(scan_data)

        keys = pygame.key.get_pressed()
        quit = pygame.event.get(pygame.QUIT)              
        if quit or keys[pygame.K_ESCAPE] or keys[pygame.K_SPACE]:
            raise KeyboardInterrupt  # Simuler une interruption au clavier

except KeyboardInterrupt:
    print('Arrêt.')

finally:
    lidar.stop()
    lidar.disconnect()
