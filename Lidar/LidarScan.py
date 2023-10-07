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
X_ROBOT = 1500
Y_ROBOT = 1000
ROBOT_ANGLE = 0
POINT_COLOR = (255, 0, 0)  # Define the color of the robot as a constant

try:
    # Commencez la collecte de données
    lidar.connect()
    logging.info("Starting LiDAR motor")


    while True:
        for scan in lidar.iter_scans(200000):
            for (_, angle, distance) in scan:
                new_angle = angle + ROBOT_ANGLE
                if new_angle > 360:
                    new_angle = new_angle - 360
                #Affichez les données du scan sur la fenêtre pygame en utilisant des cercles
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

            #Mettez à jour l'écran pour afficher les cercles toutes les 1 secondes.
            try:
                pygame.display.update()
            except pygame.error as e:
                print("Failed to update display")
                logging.error(f"Failed to update display: {e}")
            lcd.fill(BLACK)

                

except KeyboardInterrupt:
    lidar.disconnect()
    pass

finally:
    # Arrêtez la rotation et déconnectez le LiDAR
    lidar.stop_motor()
    lidar.disconnect()