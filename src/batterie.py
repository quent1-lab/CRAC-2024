import pygame
import pygame.font
from pygame_UI import *

class Batterie:
    def __init__(self, capteur=False, screen=None, position=(0, 0), nom='Batterie'):
        self.capteur= capteur
        self.interrupteur = False
        
        self.screen = screen
        self.connecter = False
        self.taille = self.taille_boite()
        self.position = position
        self.rect = pygame.Rect(self.position, self.taille)
        
        self.etat_batterie = {
            'nom': {'valeur': nom, 'unite': ''},
            'tension': {'valeur': 0, 'unite': 'V'},
            'courant': {'valeur': 0, 'unite': 'A'},
            'puissance': {'valeur': 0, 'unite': 'W'},
            'energie': {'valeur': 0, 'unite': 'Wh'},
            'qualite': {'valeur': 0, 'unite': '%'}
        }
        
    def update_position(self, position):
        self.position = position

    def is_connected(self):
        if self.etat_batterie['tension']['valeur'] > 0:
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

    def afficher_info(self, info=None, majuscule=False):
        if info:
            if majuscule:
                return str(info).capitalize() + ' : ' + str(self.etat_batterie[info]['valeur']) + ' ' + str(self.etat_batterie[info]['unite'])
            else:
                return str(info) + ' : ' + str(self.etat_batterie[info]['valeur']) + ' ' + str(self.etat_batterie[info]['unite'])
        else:
            return 'Erreur'
    
    def taille_boite(self):
        # Code pour déterminer la taille de la boite de l'interface en fonction des informations de la batterie à afficher
        # et de la taille de la police
        
        # Calculer la hauteur de la boite
        if not self.capteur:
            hauteur = 25 + 30 + 25
        else:
            hauteur = 50 + 30 + (25*5)
        
        # Calculer la largeur de la boite
        """largeur = 0
        for info in self.etat_batterie:
            largeur = max(largeur, len(self.afficher_info(info)))
        largeur = 10 + largeur * 20"""
        largeur = 190
        return (largeur, hauteur)
    
    def draw(self):
        self.draw_info()
        
    def draw_info(self):
        # Code pour dessiner l'encadrement des informations de la batterie
        color = (0,200,0) if self.is_connected() else (200,0,0)
        pygame.draw.rect(self.screen, color, self.rect, 0, 10)
        pygame.draw.rect(self.screen, (0, 0, 0), self.rect, 2, 10)
        
        # Code pour dessiner les informations de la batterie
        for i, info in enumerate(self.etat_batterie):
            if info == 'nom':
                # Dessiner le nom de la batterie centré et en gras
                font = pygame.font.Font(None, 30)
                text = font.render(self.etat_batterie['nom']['valeur'], False, (0, 0, 0))
                text_rect = text.get_rect(center=(self.position[0] + self.taille[0]/2, self.position[1] + 20))
                self.screen.blit(text, text_rect)
            
            else:
                if info == 'courant' and not self.capteur:
                    break
                # Dessiner les autres informations
                font = pygame.font.Font(None, 25)
                text = font.render(self.afficher_info(info,True), True, (0, 0, 0))
                self.screen.blit(text, (self.position[0] + 10, self.position[1] + 50 + (i-1) * 30))
    
    def draw_gestion_batterie(self):
        # Code pour dessiner l'affichage de la gestion de la batterie
        pass
    
if __name__ == '__main__':
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((800, 480))
    pygame.display.set_caption("Batterie")
    clock = pygame.time.Clock()
    
    batterie = Batterie(screen=screen, position=(10, 10), capteur=False, nom='Batterie 2')
    
    running = True
    while running:
        screen.fill((255, 255, 255))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                running = False
        
        batterie.draw()
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
