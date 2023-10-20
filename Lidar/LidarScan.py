import logging
from rplidar import RPLidar
import pygame
import math
import random
import time

# Set up logging
logging.basicConfig(filename='lidar_scan.log', level=logging.INFO)

# Specify the serial port you are using for the LiDAR S1 (e.g. '/dev/ttyUSB0' on Linux)
port = 'COM8'  # Change this according to your configuration

# Initialize pygame
pygame.init()

# Create a window of 900x600 pixels
lcd = pygame.display.set_mode((900, 600))

# Hide the mouse cursor
pygame.mouse.set_visible(False)

# Fill the screen with black
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
lcd.fill(BLACK)

# Update the screen to display black
pygame.display.update()

# Define constants
FIELD_SIZE = (3000, 2000)  # Size of the field in mm
WINDOW_SIZE = (900, 600)  # Size of the pygame window in pixels
BORDER_DISTANCE = 100  # Distance between the robot and the edge of the field in mm
X_RATIO = WINDOW_SIZE[0] / FIELD_SIZE[0]  # Ratio between the size of the field and the size of the pygame window
Y_RATIO = WINDOW_SIZE[1] / FIELD_SIZE[1]  # Ratio between the size of the field and the size of the pygame window
X_ROBOT = FIELD_SIZE[0] / 2  # X coordinate of the robot in mm
Y_ROBOT = FIELD_SIZE[1] / 2  # Y coordinate of the robot in mm
ROBOT_ANGLE = 0
POINT_COLOR = (255, 0, 0)  # Define the color of the robot as a constant

def draw_robot(x, y, angle):
    """Draw a robot on the pygame window

    Args:
        x (int): X coordinate of the robot in mm
        y (int): Y coordinate of the robot in mm
        angle (int): Angle of the robot in degrees
    """
    pygame.draw.circle(lcd, pygame.Color(0,0,250), (x*(X_RATIO), y*(Y_RATIO)), 10)
    pygame.draw.line(lcd, pygame.Color(0,0,250), (x*(X_RATIO), y*(Y_RATIO)), ((x+50*math.cos(angle))*(X_RATIO), (y+50*math.sin(angle))*(Y_RATIO)), 3)

def draw_field():
    """Draw the field on the pygame window
    """
    pygame.draw.rect(lcd, pygame.Color(100,100,100), (BORDER_DISTANCE*(X_RATIO)-5, BORDER_DISTANCE*(Y_RATIO)-5, (FIELD_SIZE[0]-2*BORDER_DISTANCE)*(X_RATIO)+10, (FIELD_SIZE[1]-2*BORDER_DISTANCE)*(Y_RATIO)+10), 10)

def draw_point(x, y, angle, distance):
    global ROBOT_ANGLE
    """Draw a point on the pygame window

    Args:
        x (int): X coordinate of the point in mm
        y (int): Y coordinate of the point in mm
        angle (int): Angle of the point in degrees
        distance (int): Distance of the point in mm
    """
    new_angle = angle - ROBOT_ANGLE
    if new_angle < 0:
        new_angle = new_angle + 360
    x = X_ROBOT + int(distance * math.cos(new_angle * math.pi / 180)) #* 299 / 5000 
    y = Y_ROBOT + int(distance * math.sin(new_angle * math.pi / 180))

    POINT_COLOR = (255,0,0)

    #Saturé les valeurs de x et y pour qu'elles restent dans la fenêtre
    if x > FIELD_SIZE[0]-BORDER_DISTANCE:
        x= FIELD_SIZE[0]-BORDER_DISTANCE
        POINT_COLOR = (0,255,0)
    elif x < BORDER_DISTANCE:
        x = BORDER_DISTANCE
        POINT_COLOR = (0,255,0)

    if y > FIELD_SIZE[1]-BORDER_DISTANCE:
        y = FIELD_SIZE[1]-BORDER_DISTANCE
        POINT_COLOR = (0,255,0)
    elif y < BORDER_DISTANCE:
        y = BORDER_DISTANCE
        POINT_COLOR = (0,255,0)
    
    try:
        pygame.draw.circle(lcd, pygame.Color(POINT_COLOR), (x*(X_RATIO), y*(Y_RATIO)), 2)
    except pygame.error as e:
        print("Failed to draw circle")
        logging.error(f"Failed to draw circle: {e}")

def draw_object(object):
    """Draw an object on the pygame window
    Args:
        object (tuple): Tuple containing the x and y coordinates of the object in mm
    """
    pygame.draw.circle(lcd, pygame.Color(255,0,255), (object[0]*(X_RATIO), object[1]*(Y_RATIO)), object[2]*(X_RATIO))

def detect_object(scan):
    """
    détecte l'objet le plus proche du robot
    et détermine une zone moyenne de l'objet
    en fonction des points autour de l'objet
    """

    objet = min(scan, key=lambda x: x[2])
    angle_objet = objet[1]
    distance_objet = objet[2]

    #détermine les points autour de l'objet
    points_autour_objet = []
    for point in scan:
        if point[1] > angle_objet-5 and point[1] < angle_objet+5:
            #Il ne faut pas prendre les valeurs de distance trop éloigné de l'objet
            if point[2] < distance_objet + 100 and point[2] > distance_objet - 100:
                points_autour_objet.append(point)
    """
    Bloquer la detection au terrain
    """

    #détermine la zone moyenne de l'objet (x , y, taille)
    x = 0
    y = 0
    taille = 0
    for point in points_autour_objet:
        new_angle = point[1] - ROBOT_ANGLE
        if new_angle < 0:
            new_angle = new_angle + 360
        x += point[2] * math.cos(new_angle * math.pi / 180)
        y += point[2] * math.sin(new_angle * math.pi / 180)
        #Taille de l'objet en fonction de la distance et l'angle entre les points extrêmes
    angle_min = min(points_autour_objet, key=lambda x: x[1])
    angle_max = max(points_autour_objet, key=lambda x: x[1])
    distance_min = min(points_autour_objet, key=lambda x: x[2])
    distance_max = max(points_autour_objet, key=lambda x: x[2])
    taille = math.sqrt((distance_max[2] * math.cos(angle_max[1] * math.pi / 180) - distance_min[2] * math.cos(angle_min[1] * math.pi / 180))**2 + (distance_max[2] * math.sin(angle_max[1] * math.pi / 180) - distance_min[2] * math.sin(angle_min[1] * math.pi / 180))**2)

    """x = x / len(points_autour_objet)
    y = y / len(points_autour_objet)"""

    x = X_ROBOT + int(x / len(points_autour_objet))
    y = Y_ROBOT + int(y / len(points_autour_objet))

    return (x, y, taille)

def tracking_object(zone_objet,zone_objet_precedente):
    """
    Permet de tracker le robot pour connaitre sa trajectoire et sa vitesse
    Meme si une perte de detection à lieu
    """
    if zone_objet > zone_objet_precedente:
        return "avance"
    elif zone_objet < zone_objet_precedente:
        return "recule"
    else:
        return "stable"

def valeur_de_test():
    global ROBOT_ANGLE
    """
    Permet de tester le code sans avoir le lidar avec des valeurs de test aléatoire
    Les mesures en mm doivent être cohérentes avec les valeurs de FIELD_SIZE
    Il ne faut qu'un seul object sur le terrain
    """
    #Décaler l'angle des points en fonction de l'angle du robot en degrés et en saturant les valeurs à 360
    scan = []
    for i in range(350):
        angle = i + ROBOT_ANGLE
        if angle > 360:
            angle = angle - 360
        distance = 3000
        scan.append((0, angle, distance))
    for i in range(350, 360):
        angle = i + ROBOT_ANGLE
        if angle > 360:
            angle = angle - 360
        distance = random.randint(800,850)
        scan.append((0, angle, distance))

    return scan

def programme_test():
    global X_ROBOT, Y_ROBOT, ROBOT_ANGLE
    """
    Permet de tester le code sans avoir le lidar
    """
    print("Programme de test")
    zone_objet_precedente = 0
    while True:
        scan = valeur_de_test()
        zone_objet = detect_object(scan)
        draw_field()
        draw_robot(X_ROBOT, Y_ROBOT, ROBOT_ANGLE)
        draw_object(zone_objet)
        for point in scan:
            draw_point(X_ROBOT, Y_ROBOT, point[1], point[2])
        zone_objet_precedente = zone_objet
        
        #Déplacement du robot dans une zone de 500*500 mm du centre du terrain
        ROBOT_ANGLE += 1





def __main__():
    try:
        # Create an instance of the LiDAR S1
        lidar = RPLidar(port)
    except Exception as e:
        programme_test()
        logging.error(f"Failed to create an instance of RPLidar: {e}")
        raise
    try:
        # Commencez la collecte de données
        lidar.connect()
        logging.info("Starting LiDAR motor")
        print("Starting LiDAR motor")

        while True:
            for scan in lidar.iter_scans(200000):
                draw_robot(X_ROBOT, Y_ROBOT, ROBOT_ANGLE)
                draw_field()
                draw_object(detect_object(scan))
                for (_, angle, distance) in scan:
                    draw_point(X_ROBOT, Y_ROBOT, angle, distance)
                    #SI la touche q est pressée, le programme s'arrête
                    if pygame.key.get_pressed()[pygame.K_q]:
                        lidar.stop_motor()
                        lidar.disconnect()
                        pygame.quit()

                pygame.display.update()
                lcd.fill(WHITE)

    except KeyboardInterrupt:
        print("Stopping LiDAR motor")
        time.sleep(2)
        lidar.stop_motor()
        lidar.disconnect()
        pygame.quit()
        pass

if __name__ == '__main__':
    __main__()