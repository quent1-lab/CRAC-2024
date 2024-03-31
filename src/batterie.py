import pygame
import pygame_UI

class Batterie:
    def __init__(self, capteur_tension=False, capteur_courant=False, interrupteur=False, screen=None, position=(0, 0), nom='Batterie'):
        self.capteur_tension = capteur_tension
        self.capteur_courant = capteur_courant
        self.interrupteur = interrupteur
        
        self.connecter = False
        self.position = (0, 0)
        self.rect = pygame.Rect(self.position, (380, 190))
        
        self.etat_batterie = {
            'nom': nom,
            'tension': 0,
            'courant': 0,
            'puissance': 0,
            'energie': 0,
            'qualite': 0
        }
        
    def update_position(self, position):
        self.position = position

    def is_connected(self):
        if self.etat_batterie['tension'] > 0:
            self.connecter = True
        else:
            self.connecter = False
        return self.connecter
    
    def recuperer_valeurs(self, message):
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
    
    def draw(self):
        pygame.draw.rect(self.screen, (200, 200, 200), self.rect, 0, 10)
        pygame.draw.rect(self.screen, (0, 0, 0), self.rect, 2, 10)
    
    def draw_info(self):
        # Code pour dessiner l'affichage des informations de la batterie
        pass
    
    def draw_gestion_batterie(self):
        # Code pour dessiner l'affichage de la gestion de la batterie
        pass
