class Batterie:
    def __init__(self, capteur_tension=False, capteur_courant=False, interrupteur=False):
        self.capteur_tension = capteur_tension
        self.capteur_courant = capteur_courant
        self.interrupteur = interrupteur
        self.tension = 0.0
        self.courant = 0.0
        self.puissance = 0.0
        self.energie = 0.0
        self.qualite = 100

    def recuperer_valeurs(self):
        if self.capteur_tension:
            # Code pour récupérer la tension de la batterie
            pass
        if self.capteur_courant:
            # Code pour récupérer le courant de la batterie
            pass

    def gerer_puissance(self):
        # Code pour gérer la puissance de la batterie
        pass

    def gerer_energie(self):
        # Code pour gérer l'énergie consommée par la batterie
        pass

    def gerer_qualite(self):
        # Code pour gérer la qualité de la batterie
        pass

    def afficher_info(self, info='tension'):
        if info == 'tension':
            return f"Tension: {self.tension} V"
        elif info == 'courant':
            return f"Courant: {self.courant} A"
        elif info == 'puissance':
            return f"Puissance: {self.puissance} W"
        elif info == 'energie':
            return f"Energie consommée: {self.energie} Wh"
        elif info == 'qualite':
            return f"Qualité de la batterie: {self.qualite}%"

    def gestion_totale(self):
        # Code pour gérer la page de gestion totale de la batterie
        pass
