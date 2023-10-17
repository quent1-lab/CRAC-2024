import logging
from rplidar import RPLidar
import pygame
import math

# Set up logging
logging.basicConfig(filename='lidar_scan.log', level=logging.INFO)

# Specify the serial port you are using for the LiDAR S1 (e.g. '/dev/ttyUSB0' on Linux)
port = 'COM8'  # Change this according to your configuration

try:
    # Create an instance of the LiDAR S1
    lidar = RPLidar(port)
except Exception as e:
    logging.error(f"Failed to create an instance of RPLidar: {e}")
    raise

# Initialize pygame
pygame.init()

# Create a window of 900x600 pixels
lcd = pygame.display.set_mode((900, 600))

# Hide the mouse cursor
pygame.mouse.set_visible(False)

# Fill the screen with black
BLACK = (0, 0, 0)
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
    pygame.draw.circle(lcd, pygame.Color(POINT_COLOR), (x*(X_RATIO), y*(Y_RATIO)), 10)
    pygame.draw.line(lcd, pygame.Color(POINT_COLOR), (x*(X_RATIO), y*(Y_RATIO)), ((x+50*math.cos(angle))*(X_RATIO), (y+50*math.sin(angle))*(Y_RATIO)), 2)

def draw_field():
    """Draw the field on the pygame window
    """
    pygame.draw.rect(lcd, pygame.Color(POINT_COLOR), (BORDER_DISTANCE*(X_RATIO), BORDER_DISTANCE*(Y_RATIO), (FIELD_SIZE[0]-2*BORDER_DISTANCE)*(X_RATIO), (FIELD_SIZE[1]-2*BORDER_DISTANCE)*(Y_RATIO)), 2)

def draw_point(x, y, angle, distance):
    """Draw a point on the pygame window

    Args:
        x (int): X coordinate of the point in mm
        y (int): Y coordinate of the point in mm
        angle (int): Angle of the point in degrees
        distance (int): Distance of the point in mm
    """
    new_angle = angle + ROBOT_ANGLE
    if new_angle > 360:
        new_angle = new_angle - 360
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

    pygame.display.update()
    lcd.fill(BLACK)

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
            points_autour_objet.append(point)

    #détermine la zone moyenne de l'objet
    zone_objet = 0
    for point in points_autour_objet:
        zone_objet += point[2]
    zone_objet = zone_objet/len(points_autour_objet)

    return zone_objet



try:
    # Commencez la collecte de données
    lidar.connect()
    logging.info("Starting LiDAR motor")

    while True:
        for scan in lidar.iter_scans(200000):
            for (_, angle, distance) in scan:
                draw_robot(X_ROBOT, Y_ROBOT, ROBOT_ANGLE)
                draw_field()
                draw_point(X_ROBOT, Y_ROBOT, angle, distance)

except KeyboardInterrupt:
    lidar.disconnect()
    pass