import pygame
import pygame.font
from pygame_UI import *


class Batterie:
    def __init__(self, capteur=False, screen=None, position=(0, 0), nom='Batterie', _callback_desactiver_event=None, _callback_switch=None):
        self.capteur = capteur

        self.screen = screen
        self.is_running = True
        self.page_batterie = False
        self.taille = self.taille_boite()
        self.position = position
        self.rect = pygame.Rect(self.position, self.taille)
        
        self.callback_desactiver_event = _callback_desactiver_event
        self.callback_switch = _callback_switch

        self.etat_batterie = {
            'Nom': {'valeur': nom, 'unite': ''},
            'Tension': {'valeur': 0, 'unite': 'V'},
            'Courant': {'valeur': 0, 'unite': 'A'},
            'Switch' : {'valeur': 0, 'unite': ''},
            'Puissance': {'valeur': 0, 'unite': 'W'},
            'Energie': {'valeur': 0, 'unite': 'Wh'},
            'Qualite': {'valeur': 0, 'unite': '%'}
        }
        self.numero_batterie = nom.split(' ')[-1]

    def update_position(self, position):
        self.position = position
        self.rect = pygame.Rect(self.position, self.taille)

    def is_connected(self): # BUG : Si switch on,puis error 0x10 (donc switch off ?), puis alive et start -> switch reste off
        if self.etat_batterie['Tension']['valeur'] > 1:
            connecter = True
            if not self.etat_batterie['Switch']['valeur']:
                self.etat_batterie['Switch']['valeur'] = True
                self.callback_switch(True)
        else:
            connecter = False
            if self.etat_batterie['Switch']['valeur']:
                self.etat_batterie['Switch']['valeur'] = False
                self.callback_switch(False)
        return connecter

    def recuperer_valeurs(self, _json):
        if _json is None:
            return
        else:
            data = _json
            
        for key in data:
            if key == self.etat_batterie['Nom']['valeur']:
                for info in data[key]:
                    if info in self.etat_batterie:
                        self.etat_batterie[info]['valeur'] = data[key][info]
                        return True
            else:   
                continue
            
    def gerer_Puissance(self):
        # Code pour gérer la Puissance de la batterie
        pass

    def gerer_Energie(self):
        # Code pour gérer l'énergie consommée par la batterie
        pass

    def gerer_Qualite(self):
        # Code pour gérer la qualité de la batterie
        pass

    def afficher_info(self, info=None):
        if info:
            if info == 'Switch':
                valeur = 'ON' if self.etat_batterie[info]['valeur'] else 'OFF'
                return str(info) + ' : ' + valeur
            else:
                return str(info) + ' : ' + str(self.etat_batterie[info]['valeur']) + ' ' + self.etat_batterie[info]['unite']
        else:
            return 'Erreur'

    def taille_boite(self):
        # Code pour déterminer la taille de la boite de l'interface en fonction des informations de la batterie à afficher
        # et de la taille de la police

        # Calculer la hauteur de la boite
        if not self.capteur:
            hauteur = 30 + 26 + 20 # Marge + Nom + Tension
        else:
            hauteur = 30 + 26 + (20*4) # Marge + Nom + Tension + Courant + Switch

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
        color = (0, 200, 0) if self.etat_batterie['Switch']['valeur'] else (220, 0, 0)
        color = (200,200,200) if not self.capteur else color
        pygame.draw.rect(self.screen, color, self.rect, 0, 10)
        pygame.draw.rect(self.screen, (0, 0, 0), self.rect, 2, 10)

        # Code pour dessiner les informations de la batterie
        for i, info in enumerate(self.etat_batterie):
            if info == 'Nom':
                # Dessiner le Nom de la batterie centré et en gras
                font = pygame.font.SysFont("Arial", 26)
                text = font.render(
                    self.etat_batterie['Nom']['valeur'], False, (0, 0, 0))
                text_rect = text.get_rect(
                    center=(self.position[0] + self.taille[0]/2, self.position[1] + 20))
                self.screen.blit(text, text_rect)

            else:
                if (info == 'Courant' and not self.capteur) or info == 'Puissance':
                    break # Si capteur est faux on ne dessine pas les infos sur l'énegie de la batterie
                
                # Dessiner les autres informations
                font = pygame.font.SysFont("Arial", 20)
                text = font.render(self.afficher_info(
                    info),True, (0, 0, 0))
                self.screen.blit(
                    text, (self.position[0] + 10, self.position[1] + 45 + (i-1) * 30))

    def click(self, pos):
        if self.rect.collidepoint(pos) and self.capteur:
            #self.etat_batterie['Switch']['valeur'] = not self.etat_batterie['Switch']['valeur']
            #self.is_connected()
            self.draw_gestion_batterie()

    def draw_gestion_batterie(self):
        interrupteur = Interrupteur(self.screen, (325, 350), (150, 75), self.etat_batterie['Switch']['valeur']) 
        
        self.callback_desactiver_event(True)       
        
        def callback_ON():
            self.etat_batterie['Switch']['valeur'] = self.is_connected()
            
            if self.etat_batterie['Switch']['valeur'] == False:
                interrupteur.set_on_OFF()
        
        def callback_OFF():
            self.etat_batterie['Switch']['valeur'] = False
            if self.callback_switch:
                self.callback_switch(False)
        

        interrupteur.set_callback_OFF(callback_OFF)
        interrupteur.set_callback_ON(callback_ON)
        
        
        rect = pygame.Rect((50, 50), (700, 380))
        color = (200, 200, 200)
        
        rect_quit = pygame.Rect((700, 55), (45, 40))
        color_quit = (255, 0, 0)
        
        self.page_batterie = True
        while self.is_running and self.page_batterie:
            
            for event in pygame.event.get():
                interrupteur.handle_event(event)
                if event.type == pygame.QUIT:
                    self.stop()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if rect_quit.collidepoint(event.pos) or not rect.collidepoint(event.pos):
                        self.page_batterie = False
                        self.callback_desactiver_event(False)
                        break

            pygame.draw.rect(self.screen, color, rect, 0, 10)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 2, 10)
            
            pygame.draw.rect(self.screen, color_quit, rect_quit, 0, 10)
            
            # Dessiner les informations de la batterie
            for i, info in enumerate(self.etat_batterie):
                if info == 'Nom':
                    # Dessiner le Nom de la batterie centré et en gras
                    font = pygame.font.SysFont("Arial", 26)
                    text = font.render(
                        self.etat_batterie['Nom']['valeur'], False, (0, 0, 0))
                    text_rect = text.get_rect(
                        center=(50 + 700/2, 50 + 20))
                    self.screen.blit(text, text_rect)

                else:
                    if (info == 'Courant' and not self.capteur):
                        break
                    
                    # Dessiner les autres informations
                    font = pygame.font.SysFont("Arial", 20)
                    text = font.render(self.afficher_info(
                        info),True, (0, 0, 0))
                    self.screen.blit(
                        text, (50 + 10, 50 + 50 + (i-1) * 35))
                    
            # Dessiner le bouton de gestion de la batterie
            font = pygame.font.SysFont("Arial", 20)
            text = font.render('Gestion de la batterie', True, (0, 0, 0))
            marge = 10  # Définir la marge
            text_rect = text.get_rect(center=(50 + 700/2, 50 + 25 + (i+1) * 35))
            _rect = pygame.Rect(text_rect[0] - marge, text_rect[1] - marge, text_rect[2] + 2*marge, text_rect[3] + 2*marge)

            pygame.draw.rect(self.screen, (200, 200, 200), _rect, 0, 4)
            pygame.draw.rect(self.screen, (0, 0, 0), _rect, 2, 4)
            self.screen.blit(text, text_rect)
                        
            interrupteur.draw()
                    
                    
            
            pygame.display.flip()
    
    def mode_error(self):
        self.page_batterie = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.click(event.pos)
    
    def stop(self):
        self.is_running = False

if __name__ == '__main__':
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((800, 480))
    pygame.display.set_caption("Batterie")
    clock = pygame.time.Clock()

    batteries = [
        Batterie(screen=screen, position=(10, 10),capteur=False, nom='Batterie 1'),
        Batterie(screen=screen, position=(10, 10),capteur=True,  nom='Batterie 2'),
        Batterie(screen=screen, position=(10, 10),capteur=True, nom='Batterie 3'),
        Batterie(screen=screen, position=(10, 10),capteur=True, nom='Batterie 4')
    ]
    
    nb_batteries_colonne = 0
    somme_taille = 60
    
    while nb_batteries_colonne < len(batteries):
        if somme_taille + batteries[nb_batteries_colonne].taille[1] + 10 > screen.get_height():
            break
        somme_taille += batteries[nb_batteries_colonne].taille[1] + 10
        nb_batteries_colonne += 1
        
    somme_taille = 0
    for i, batterie in enumerate(batteries):
        if i % nb_batteries_colonne == 0 and i != 0:
            somme_taille = 0
        batterie.update_position((10 + (i//nb_batteries_colonne) * (batterie.taille[0]+10), 65 + somme_taille))
        
        somme_taille += batterie.taille[1] + 10

        
    
        
    running = True
    while running:
        screen.fill((255, 255, 255))

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                running = False
            for batterie in batteries:
                batterie.handle_event(event)

        for batterie in batteries:
            batterie.draw()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
