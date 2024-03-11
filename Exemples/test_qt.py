import sys
import logging
import math
import os
import json
import numpy as np
from sklearn.cluster import DBSCAN
from objet import Objet
from client import Client
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor, QPixmap, QPainter, QFont,QPen
from PyQt5.QtCore import Qt, QRectF
from screeninfo import get_monitors



class MatchInfoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Informations sur le match")
        layout = QVBoxLayout()
        self.info_label = QLabel("Insérez vos informations sur le match ici")
        layout.addWidget(self.info_label)
        self.setLayout(layout)


class IHM(QMainWindow):
    def __init__(self, port=None):
        super().__init__()
        self.port = port
        self.lidar = None
        self.lcd = None
        self.BLACK = QColor(0, 0, 0)
        self.WHITE = QColor(255, 255, 255)
        self.LIGHT_GREY = QColor(200, 200, 200)
        self.GREEN = QColor(0, 255, 0)
        self.BLUE = QColor(0, 0, 255)
        self.RED = QColor(255, 0, 0)
        self.DARK_GREEN = QColor(0, 100, 0)
        self.FIELD_SIZE = (3000, 2000)
        self.BORDER_DISTANCE = 200
        self.POINT_COLOR = QColor(255, 0, 0)
        self.BACKGROUND_COLOR = self.LIGHT_GREY
        self.FONT_COLOR = self.BLACK

        # Initialize virtual robot
        self.ROBOT_Dimension = (264, 268)
        self.ROBOT = Objet(0, self.ROBOT_Dimension[0], self.ROBOT_Dimension[1], 20)
        self.ROBOT_ANGLE = 0

        self.path_picture = "src/Terrain_Jeu.png"
        self.id_compteur = 0
        self.objets = []
        self.new_scan = []
        self.scanning = True
        self.ETAT = 0
        self.EQUIPE = "Jaune"

        # Initialize Pygame and adjust window size
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.background = QLabel(self)
        self.init_ui()

        # Maximize the window
        self.WINDOW_SIZE = (self.width(), self.height())
        self.X_RATIO = self.WINDOW_SIZE[0] / self.FIELD_SIZE[0]
        self.Y_RATIO = self.WINDOW_SIZE[1] / self.FIELD_SIZE[1]
        print(self.WINDOW_SIZE)

    def init_ui(self):
        self.layout = QVBoxLayout()  # Initialize self.layout as a QVBoxLayout
        self.setWindowTitle("Application de Coupe de Robotique")

        monitor = get_monitors()[0]
        width = monitor.width - 100
        height = int(width * 2 / 3)  # Maintain 3:2 aspect ratio

        self.setGeometry(100, 100, width, height)

        self.create_top_left_widget()
        self.create_middle_widget()
        self.create_bottom_widget()

    def create_top_left_widget(self):
        top_left_layout = QVBoxLayout()

        self.position_label = QLabel("Position du robot : (0, 0)")
        top_left_layout.addWidget(self.position_label)

        self.layout.addLayout(top_left_layout)

    def create_middle_widget(self):
        self.game_area_label = QLabel()
        self.game_area_label.setAlignment(Qt.AlignCenter)

        self.scene.addWidget(self.game_area_label)
    
    def draw_field(self):
        field_rect = QRectF(self.BORDER_DISTANCE * self.X_RATIO - 5, self.BORDER_DISTANCE * self.Y_RATIO - 5,
                            (self.FIELD_SIZE[0] - 3 * self.BORDER_DISTANCE) * self.X_RATIO + 10,
                            (self.FIELD_SIZE[1] - 2 * self.BORDER_DISTANCE) * self.Y_RATIO + 10)
        field_pen = QPen(Qt.gray)
        field_pen.setWidth(10)
        self.scene.addRect(field_rect, field_pen)

    def create_bottom_widget(self):
        bottom_layout = QHBoxLayout()

        self.match_info_button = QPushButton("Afficher les informations sur le match")
        self.match_info_button.clicked.connect(self.show_match_info_window)
        bottom_layout.addWidget(self.match_info_button)

        self.layout.addLayout(bottom_layout)

    def show_match_info_window(self):
        match_info_window = MatchInfoWindow()
        match_info_window.exec_()

    def draw_robot(self):
        # Dessine le robot sur la scène
        rect = QRectF(self.ROBOT.x, self.ROBOT.y, self.ROBOT.largeur, self.ROBOT.longueur)
        rect.translate(-self.ROBOT.largeur / 2, -self.ROBOT.longueur / 2)
        self.scene.addRect(rect, pen=self.BLACK)

    def draw_text(self, text, x, y, color=(0, 0, 0)):
        # Dessine du texte sur la scène
        text_item = QGraphicsTextItem(text)
        text_item.setDefaultTextColor(QColor(*color))
        text_item.setPos(x, y)
        self.scene.addItem(text_item)

    def draw_data(self):
        # Dessine les données sur la scène
        pass  # À implémenter

    def draw_background(self):
        # Dessine le fond d'écran
        self.scene.clear()  # Efface la scène précédente
        self.draw_image(self.path_picture)
        self.draw_field()
        self.draw_data()

    def draw_image(self, path):
        pixmap = QPixmap(path)

        # Calculate the width and height as 60% of the window size
        width = int(self.width() * 0.6)
        height = int(width * 2 / 3)  # Maintain 3:2 aspect ratio

        # Scale the pixmap
        pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio)

        # Create a QGraphicsPixmapItem with the pixmap
        pixmap_item = QGraphicsPixmapItem(pixmap)

        # Add the pixmap_item to the scene
        self.scene.addItem(pixmap_item)

        # Center the view on the pixmap_item
        self.view.centerOn(pixmap_item)

    def draw_point(self, x, y):
        # Dessine un point sur la scène
        point_item = QGraphicsEllipseItem(x, y, 5, 5)
        point_item.setBrush(self.POINT_COLOR)
        self.scene.addItem(point_item)

    def draw_object(self, objet):
        # Dessine un objet sur la scène
        rect = QRectF(objet.x, objet.y, objet.largeur, objet.longueur)
        rect.translate(-objet.largeur / 2, -objet.longueur / 2)
        self.scene.addRect(rect, pen=self.BLACK)

    def draw_all_trajectoires(self, trajectoire_actuel, trajectoire_adverse, trajectoire_evitement):
        # Draw trajectories here
        pass

    def draw_trajectoire(self, trajectoire, color=(255, 255, 255)):
        # Draw trajectory here
        pass

    def transform_scan(self, scan, x_r, y_r, angle):
        # Transform scan here
        pass

    def detect_objects(self, scan, eps=150, min_samples=14):
        # Detect objects here
        pass

    def suivre_objet(self, objets, rayon_cercle=100):
        # Track objects here
        pass

    def stop(self):
        # Stop method here
        pass

    def load_json(self, json_string):
        # Load JSON here
        pass

    def receive_to_server(self, message):
        # Receive from server here
        pass

    def map_value(self,x, in_min, in_max, out_min, out_max):
        # Map value here
        pass

    def handle_mouse_click(self, event):
        # Handle mouse click here
        pass

    def is_within_game_area(self, pos):
        # Check if within game area here
        pass

    def init_match(self):
        # Initialize match here
        pass

    def run(self):
        self.show()
        self.draw_background()
        # Run loop here
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ihm = IHM()
    ihm.run()
    sys.exit(app.exec_())
