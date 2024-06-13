import math
import time
import json

class Objet:
    def __init__(self, id, x, y, taille):
        self.id = id
        self.x = x
        self.y = y
        self.taille = taille
        self.positions_precedentes = [(x, y, time.time())]  # Ajout du temps actuel
        self.direction = 0
        self.vitesse = 0
        self.vitesse_ms = 0
        self.points = []
        self.last_seen = time.time()

    def update_position(self, x, y):
        # Mettre à jour la position de l'objet et ajouter la position précédente à la liste
        if self.x != x or self.y != y:
            self.positions_precedentes.append((self.x, self.y, time.time()))
            self.x = x
            self.y = y
            self.filtre_moyenne()

    def get_direction_speed(self):
        # Calculer le vecteur de déplacement entre la position actuelle et la position précédente
        dx = self.x - self.positions_precedentes[-1][0]
        dy = self.y - self.positions_precedentes[-1][1]

        # Calculer le temps écoulé entre la position actuelle et la position précédente
        dt = (time.time() - self.positions_precedentes[-1][2]) + 0.0000001 # Ajout de 0.000001 pour éviter la division par 0

        # La direction est l'angle du vecteur de déplacement
        self.direction = math.atan2(dy, dx)

        # La vitesse est la magnitude du vecteur de déplacement divisée par le temps écoulé
        self.vitesse = math.sqrt(dx**2 + dy**2) / dt

        # Convertir la vitesse en m/s
        self.vitesse_ms = self.vitesse /1000

        return self.direction, self.vitesse

    def simulate_movement(self, direction, vitesse, temps):
        # Convertir la direction en radians

        # Calculer le déplacement en x et y
        dx = vitesse * 10 * math.cos(direction) * temps
        dy = vitesse * 10 * math.sin(direction) * temps

        # Mettre à jour la position de l'objet
        self.x += dx
        self.y += dy

    def calculate_dx_dy(self, direction, vitesse, temps):
        # Assurez-vous que la direction est entre 0 et 2π
        direction = direction % (2 * math.pi)

        # Calculer le déplacement en x et y
        dx = vitesse  * math.cos(direction) * temps
        dy = vitesse  * math.sin(direction) * temps

        return dx, dy

    def filtre_moyenne(self, n=3):
        # Si ID est 0, on ne filtre pas la position
        if self.id == 0:
            return
        Tau = 0.03
        Te = 0.01
        A = 1/(Tau/Te + 1)
        B = Tau/Te

        # Filtre passe-bas pour lisser les positions toutes les 10ms
        if time.time() - self.last_seen > Te:
            self.x = A*(self.x + B*self.positions_precedentes[-1][0])
            self.y = A*(self.y + B*self.positions_precedentes[-1][1])
            self.last_seen = time.time()
    
    def is_not_moving(self):
        # Vérifier si l'objet n'est pas immobile depuis plus de 2 seconde
        if time.time() - self.positions_precedentes[-1][2] > 2:
            return True
        return False

    def __hash__(self):
        # Retourne un hash de l'objet
        return hash(self.id)

    def __eq__(self, other):
        # Vérifier si deux objets sont les mêmes
        if isinstance(other, Objet):
            return self.id == other.id
        return False
    
    def __str__(self):
        # Retourne une chaîne de caractères représentant l'objet sous format JSON
        #return f"{{\"id\": {self.id}, \"x\": {int(self.x)}, \"y\": {int(self.y)}, \"taille\": {int(self.taille)}}}"
        return json.dumps({"id": self.id, "x": int(self.x), "y": int(self.y), "taille": int(self.taille)})
    
    def __dict__(self):
        return {"id": self.id, "x": int(self.x), "y": int(self.y), "taille": int(self.taille)}