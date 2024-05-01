from client import Client

class Strategie:
    def __init__(self, nom, fonction):
        self.nom = nom
        self.fonction = fonction
        
        self.client = Client("127.0.0.5", 22050,4)

    def __str__(self):
        return self.nom

    def jouer(self, jeu):
        return self.fonction(jeu)