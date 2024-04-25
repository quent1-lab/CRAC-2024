import pygame
import pygame_gui
from pygame_UI import *
from pygame_gui.core import ObjectID

class IHM_Command:
    def __init__(self, manager, desactive_callback=None, restart_callback=None, CAN_callback=None):    
        self.manager = manager
        self.size = (500, 400)

        self.desactive_callback = desactive_callback
        self.restart_callback = restart_callback
        self.CAN_callback = CAN_callback

        self.window = pygame_gui.elements.UIWindow(rect=pygame.Rect((100, 100), self.size),
                                                   manager=self.manager,
                                                   window_display_title="Command Manager")

        self.last_command_label = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((0, 5), (500, 30)),
                                                              text="Last command send: None",
                                                              manager=self.manager,
                                                              container=self.window)

        self.labels = []
        self.text_boxes = []
        self.tab_index = 0
        self.tab_line_index = 0

        self.command = None
        self.command_XYT_ = [None, None, None, None]
        self.command_CAN = [None,None,None,None]

        # Ajouter des zones de texte et des labels correspondants
        box_infos = [
            ("Command", (10, 50), (380, 30)),
            ("X", (10, 100), (80, 30)),
            ("Y", (110, 100), (80, 30)),
            ("T", (210, 100), (80, 30)),
            ("S", (310, 100), (80, 30)),
            ("CMD base10", (10, 180), (80, 30)),
            ("Byte1", (110, 180), (80, 30)),
            ("Byte2", (210, 180), (80, 30)),
            ("Byte3", (310, 180), (80, 30)),
        ]

        for label_text, box_position, box_size in box_infos:
            label = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((box_position[0], box_position[1] - 20), (box_size[0],box_size[1]-10) ),
                                                 text=label_text,
                                                 manager=self.manager,
                                                 container=self.window)
            self.labels.append(label)

            text_box = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((box_position, box_size)),
                                                            manager=self.manager,
                                                            container=self.window)
            self.text_boxes.append(text_box)

        self.last_command_CAN_label = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((10, 135), (100, 30)),
                                                        text="Commande CAN",
                                                        manager=self.manager,
                                                        container=self.window)

        self.send_button_command = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((390, 50), (70, 30)),
                                                        text='Send',
                                                        manager=self.manager,
                                                        container=self.window)
        
        self.send_button_XYT = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((390, 100), (70, 30)),
                                                    text='Send',
                                                    manager=self.manager,
                                                    container=self.window)

        self.send_button_CAN = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((390, 180), (70, 30)),
                                            text='Send',
                                            manager=self.manager,
                                            container=self.window)

        self.desactive_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, 230), (150, 30)),
                                                    text='Désactiver',
                                                    manager=self.manager,
                                                    container=self.window)
        
        self.restart_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((170, 230), (150, 30)),
                                                    text='RESTART',
                                                    manager=self.manager,
                                                    container=self.window)
        
        # Définir les zones de texte pour chaque ligne
        self.text_boxes_lines = [
            [self.text_boxes[0]],
            [self.text_boxes[1], self.text_boxes[2], self.text_boxes[3], self.text_boxes[4]],
            [self.text_boxes[5], self.text_boxes[6], self.text_boxes[7], self.text_boxes[8]],
        ]
        
    def process_events(self, event):
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.send_button_command:
                    self.send_command()
                elif event.ui_element == self.send_button_XYT:
                    self.send_command_XYT()
                elif event.ui_element == self.send_button_CAN:
                    self.send_command_CAN()
                elif event.ui_element == self.desactive_button:
                    if self.desactive_callback:
                        self.desactive_callback()
                elif event.ui_element == self.restart_button:
                    if self.restart_callback:
                        self.restart_callback()
        elif event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:

            # Find the text box that triggered the event
            for i, text_box in enumerate(self.text_boxes):
                if event.ui_element == text_box:
                    # Set the tab index to the index of the text box
                    self.tab_index = i
                    break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                # Déplacer le focus de la zone de texte suivante avec Tab
                self.tab_index = (self.tab_index + 1) % len(self.text_boxes)
                if self.tab_index == 0:
                    self.tab_line_index = 0
                elif self.tab_index >= 1 and self.tab_index <= 4:
                    self.tab_line_index = 1
                elif self.tab_index >= 5 and self.tab_index <= 8:
                    self.tab_line_index = 2

                self.manager.set_focus_set(self.text_boxes[self.tab_index])
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                # Envoyer la commande si toutes les zones de texte de la ligne actuelle sont remplies
                current_line_text_boxes = self.text_boxes_lines[self.tab_line_index]
                if all(box.get_text() for box in current_line_text_boxes):
                    if self.tab_index == 0:
                        self.send_command()
                    elif self.tab_index >= 1 and self.tab_index <= 4:
                        self.send_command_XYT()
                    elif self.tab_index >= 5 and self.tab_index <= 8:
                        self.send_command_CAN()

    def send_command(self):
        self.command = self.text_boxes[0].get_text()
        self.last_command_label.set_text(f"Last Command: {self.command}")
    
    def send_command_CAN(self):
        self.command_CAN[0] = self.text_boxes[5].get_text()
        self.command_CAN[1] = self.text_boxes[6].get_text()
        self.command_CAN[2] = self.text_boxes[7].get_text()
        self.command_CAN[3] = self.text_boxes[8].get_text()

        # Vérifie la validité des données
        for i in range(4):
            try:
                self.command_CAN[i] = int(self.command_CAN[i])
            except ValueError:
                self.command_CAN[i] = 0
                self.text_boxes[5+i].set_text("0")
        print(self.command_CAN)
        self.CAN_callback(self.command_CAN)

    def send_command_XYT(self):
        self.command_XYT_[0] = self.text_boxes[1].get_text()
        self.command_XYT_[1] = self.text_boxes[2].get_text()
        self.command_XYT_[2] = self.text_boxes[3].get_text()
        self.command_XYT_[3] = self.text_boxes[4].get_text()
        self.last_command_label.set_text(f"Last Command: {self.command_XYT_[0]} {self.command_XYT_[1]} {self.command_XYT_[2]} {self.command_XYT_[3]}")

    def restart(self):
        if self.restart_callback:
            self.restart_callback()
    
    def set_restart_callback(self, callback):
        self.restart_callback = callback
    
    def set_desactive_callback(self, callback):
        self.desactive_callback = callback

class IHM_Action_Aux:
    def __init__(self, manager,_action_numero,_pos_actuelle, _callback_json=None, _callback_save=None, _callback_next=None, _callback_back=None,_id=""):    
        self.manager = manager
        self.size = (610, 500)
        self.id = _id

        self.callback_json = _callback_json
        self.action_numero = _action_numero
        self.pos_actuelle = _pos_actuelle
        
        self.back_callback = _callback_back
        self.save_callback = _callback_save
        self.next_callback = _callback_next
        
        self.cote_actif = ""

        self.window = pygame_gui.elements.UIWindow(rect=pygame.Rect((100, 100), self.size),
                                                   manager=self.manager,
                                                   window_display_title="Action Auxiliaire Manager")

        self.labels = []
        self.texts = []
        self.buttons = []
        self.listes = []
        
        # Charger la configuration des actions
        with open("data/config_ordre_to_can.json", "r") as file:
            self.config = json.load(file)
        
        self.name_action_Moteur = []
        self.name_action_Pince = []
        self.name_action_Peigne = []
        self.name_action_Bras = []
        
        # Récupérer les ordres des actions pour les listes
        for ordre in self.config["Moteur"]["ordre"]["avant"]:
            self.name_action_Moteur.append(ordre)
        for ordre in self.config["HerkuleX"]["Pinces"]["gauche"]["ordre"]["avant"]:
            self.name_action_Pince.append(ordre)
        for ordre in self.config["HerkuleX"]["Peigne"]["ordre"]["avant"]:
            self.name_action_Peigne.append(ordre)
        for ordre in self.config["HerkuleX"]["Bras"]["ordre"]:
            self.name_action_Bras.append(ordre)
        

        # Ajouter des zones de texte et des labels correspondants
        box_infos = {
            "Numero_action": {"box1": {"type": "label", "position": (20, 5), "size": (150, 30), "text": f"Action numéro : {_action_numero}"}},
            "Cote_Actif": {"box1": {"type": "label", "position": (190, 5), "size": (200, 30), "text": f"Côté actif : Non défini"},},
            "Pos_actuelle":  {"box1": {"type": "label", "position": (370, 5), "size": (240, 30), "text": f"X: {_pos_actuelle[0]}  Y: {_pos_actuelle[1]}"}},
            "Angle_arrivee": {"box1": {"type": "label", "position": (60, 50), "size": (150, 30), "text": "Angle d'arrivée"},
                              "box2": {"type": "text", "position": (60, 80), "size": (155, 30), "id":"#t_Angle_arrivee"}},
            
            "Cote_a_controler": {"box1": {"type": "label", "position": (310, 50), "size": (230, 30), "text": "Côté à contrôler"},
                                "box2": {"type": "button", "position": (315, 80), "size": (105, 30), "text": "Avant"},
                                "box3": {"type": "button", "position": (425, 80), "size": (105, 30), "text": "Arrière"}},
            
            "Moteur_pas_a_pas": {"box1": {"type": "label", "position": (0, 130), "size": (120, 30), "text": "Moteur p.à.p"},
                                "box2": {"type": "list", "position": (10, 160), "size": (100, 30), "text": self.name_action_Moteur, "id":"#l_Moteur"}},
            
            "Peigne": {"box1": {"type": "label", "position": (110, 130), "size": (120, 30), "text": "Peigne"},
                    "box2": {"type": "list", "position": (120, 160), "size": (100, 30), "text": self.name_action_Peigne,"id":"#l_Peigne"},},
            
            "Pinces": { "box1": {"type": "label", "position": (220, 130), "size": (220, 30), "text": "Pinces (G/D)"},
                        "box2": {"type": "list", "position": (230, 160), "size": (100, 30), "text": self.name_action_Pince,"id":"#l_Pince_G"},
                        "box3": {"type": "list", "position": (340, 160), "size": (100, 30), "text": self.name_action_Pince,"id":"#l_Pince_D"}},
            
            "Bras": {"box1": {"type": "label", "position": (450, 130), "size": (100, 30), "text": "Bras"},
                    "box2": {"type": "list", "position": (450, 160), "size": (100, 30), "text": self.name_action_Bras,"id":"#l_Bras"},},
            
            
            "New_coord": {"box1": {"type": "label", "position": (20, 250), "size": (270, 30), "text": "Nouvelle coordonnée (optionnel) :"},
                        "box2": {"type": "label", "position": (20, 270), "size": (130, 30), "text": "X"},
                        "box3": {"type": "text", "position": (20, 300), "size": (130, 30), "id":"#t_X"},
                        "box4": {"type": "label", "position": (160, 270), "size": (130, 30), "text": "Y"},
                        "box5": {"type": "text", "position": (160, 300), "size": (130, 30), "id":"#t_Y"},
                        "box6": {"type": "label", "position": (300, 270), "size": (130, 30), "text": "T"},
                        "box7": {"type": "text", "position": (300, 300), "size": (130, 30), "id":"#t_T"},
                        "box8": {"type": "label", "position": (440, 270), "size": (130, 30), "text": "S"},
                        "box9": {"type": "text", "position": (440, 300), "size": (130, 30), "id":"#t_S"},},
            
            "Back": {"box1": {"type": "button", "position": (20, 370), "size": (150, 30), "text": "Retour"}},
            "Save": {"box1": {"type": "button", "position": (180, 370), "size": (220, 30), "text": "Enregistrer"}},
            "Next": {"box1": {"type": "button", "position": (410, 370), "size": (150, 30), "text": "Suivant"}},
        }
        
        self.data = {
            "Coord": {"X": _pos_actuelle[0], "Y": _pos_actuelle[1], "T": 0},
            "Action" : {
                
            }
        }

        for label_text, box_info in box_infos.items():
            for box_name, box_data in box_info.items():
                if box_data["type"] == "label":
                    label = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((box_data["position"][0], box_data["position"][1]), (box_data["size"][0],box_data["size"][1]) ),
                                                        text=box_data["text"],
                                                        manager=self.manager,
                                                        container=self.window,
                                                        object_id=ObjectID(object_id="#l_"+label_text))
                    self.labels.append(label)
                    
                elif box_data["type"] == "text":
                    text_box = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((box_data["position"], box_data["size"])),
                                                                manager=self.manager,
                                                                container=self.window,
                                                                object_id=ObjectID(object_id=box_data["id"]))
                    self.texts.append(text_box)
                    
                elif box_data["type"] == "button":
                    button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(box_data["position"], box_data["size"]),
                                                                                        text=box_data["text"],
                                                                                        manager=self.manager,
                                                                                        container=self.window,
                                                                                        object_id=ObjectID(object_id="#b_"+box_data["text"]))
                    self.buttons.append(button)
                elif box_data["type"] == "list":
                    liste = pygame_gui.elements.UIDropDownMenu(relative_rect=pygame.Rect(box_data["position"], box_data["size"]),
                                                                    options_list=box_data["text"],
                                                                    starting_option=box_data["text"][0],
                                                                    manager=self.manager,
                                                                    container=self.window,
                                                                    object_id=ObjectID(object_id=box_data["id"]))
                    self.listes.append(liste)
                
                elif box_data["type"] == "void":
                    pass
        
        if self.cote_actif == "":
            self.disable_listes()
        
    def process_events(self, event):
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED: # Si un bouton est pressé
                if len(event.ui_element.get_object_ids()) > 1:
                    id = event.ui_element.get_object_ids()[1]
                else:
                    id = ""
                if id == "#b_Avant":
                    changement = True if self.cote_actif != "avant" else False
                    self.cote_actif = "avant"
                    # Mettre à jour le label
                    self.labels[1].set_text(f"Côté actif : {self.cote_actif.capitalize()}")
                    
                    # Activer les listes
                    if self.cote_actif != "":
                        self.enable_listes()
                    
                    if changement:
                        self.update_listes()
                        
                elif id == "#b_Arrière":
                    changement = True if self.cote_actif != "arriere" else False
                    self.cote_actif = "arriere"
                    # Mettre à jour le label
                    self.labels[1].set_text(f"Côté actif : {self.cote_actif.capitalize()}")
                    
                    # Activer les listes
                    if self.cote_actif != "":
                        self.enable_listes()
                    
                    if changement:
                        self.update_listes()
                        
                elif id == "#b_Retour":
                    self.back_callback()
                elif id == "#b_Enregistrer":
                    self.save_data(self.data)
                elif id == "#b_Suivant":
                    self.next_callback()

            elif event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED: # Si la liste change
                id = event.ui_element.get_object_ids()[1]
                texte = event.text
                if self.cote_actif != "":
                    if id == "#l_Moteur":
                        try:
                            if texte == "-":
                                if self.cote_actif in self.data["Action"]["Moteur"]["ordre"]:
                                    if len(self.data["Action"]["Moteur"]["ordre"]) == 2:
                                        self.data["Action"]["Moteur"]["ordre"].pop(self.cote_actif)
                                    else:
                                        self.data["Action"].pop("Moteur")             
                            else:
                                self.data["Action"]["Moteur"]["ordre"][self.cote_actif] = texte
                        except KeyError:
                            self.data.setdefault("Action", {}).setdefault("Moteur", {}).setdefault("ordre", {})[self.cote_actif] = texte
                            
                    elif id == "#l_Peigne":
                        try:
                            if texte == "-":
                                if self.cote_actif in self.data["Action"]["HerkuleX"]["Peigne"]["ordre"]:
                                    if len(self.data["Action"]["HerkuleX"]["Peigne"]["ordre"]) == 2:
                                        self.data["Action"]["HerkuleX"]["Peigne"]["ordre"].pop(self.cote_actif)
                                    else:
                                        self.data["Action"]["HerkuleX"].pop("Peigne")
                            else:
                                self.data["Action"]["HerkuleX"]["Peigne"]["ordre"][self.cote_actif] = texte
                        except KeyError:
                            self.data.setdefault("Action", {}).setdefault("HerkuleX", {}).setdefault("Peigne", {}).setdefault("ordre", {})[self.cote_actif] = texte
                            
                    elif id == "#l_Pince_G":
                        try:
                            if texte == "-":
                                if self.cote_actif in self.data["Action"]["HerkuleX"]["Pinces"]["gauche"]["ordre"]:
                                    if len(self.data["Action"]["HerkuleX"]["Pinces"]["gauche"]["ordre"]) == 2:
                                        self.data["Action"]["HerkuleX"]["Pinces"]["gauche"]["ordre"].pop(self.cote_actif)
                                    else:
                                        self.data["Action"]["HerkuleX"]["Pinces"].pop("gauche")
                            else:
                                self.data["Action"]["HerkuleX"]["Pinces"]["gauche"]["ordre"][self.cote_actif] = texte
                        except KeyError:
                            self.data.setdefault("Action", {}).setdefault("HerkuleX", {}).setdefault("Pinces", {}).setdefault("gauche", {}).setdefault("ordre", {})[self.cote_actif] = texte
                            
                    elif id == "#l_Pince_D":
                        try:
                            if texte == "-":
                                if self.cote_actif in self.data["Action"]["HerkuleX"]["Pinces"]["droite"]["ordre"]:
                                    if len(self.data["Action"]["HerkuleX"]["Pinces"]["droite"]["ordre"]) == 2:
                                        self.data["Action"]["HerkuleX"]["Pinces"]["droite"]["ordre"].pop(self.cote_actif)
                                    else:
                                        self.data["Action"]["HerkuleX"]["Pinces"].pop("droite")
                            else:
                                self.data["Action"]["HerkuleX"]["Pinces"]["droite"]["ordre"][self.cote_actif] = texte
                        except KeyError:
                            self.data.setdefault("Action", {}).setdefault("HerkuleX", {}).setdefault("Pinces", {}).setdefault("droite", {}).setdefault("ordre", {})[self.cote_actif] = texte
                            
                    elif id == "#l_Bras":
                        try:
                            if texte == "-":
                                if self.cote_actif in self.data["Action"]["HerkuleX"]["Bras"]["ordre"]:
                                    if len(self.data["Action"]["HerkuleX"]["Bras"]["ordre"]) == 1:
                                        self.data["Action"]["HerkuleX"].pop("Bras")
                            else:
                                self.data["Action"]["HerkuleX"]["Bras"]["ordre"] = texte
                        except KeyError:
                            self.data.setdefault("Action", {}).setdefault("HerkuleX", {}).setdefault("Bras", {}).setdefault("ordre", {})["ordre"] = texte
                                                        
            elif event.user_type == pygame_gui.UI_TEXT_ENTRY_CHANGED: # Si le texte change
                id = event.ui_element.get_object_ids()[1]
                try:
                    if id == "#t_Angle_arrivee":
                        self.data["Coord"]["T"] = int(event.text)
                    elif id == "#t_X":
                        self.data["New_coord"]["X"] = int(event.text) 
                    elif id == "#t_Y":
                        self.data["New_coord"]["Y"] = int(event.text)
                    elif id == "#t_T":
                        self.data["New_coord"]["T"] = int(event.text)
                    elif id == "#t_S":
                        self.data["New_coord"]["S"] = int(event.text)
                except Exception as e:
                    print(e)
                            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                pass
    
    def set_callback_json(self, callback):
        self.desactive_callback = callback
    
    def save_data(self,data):
        if self.save_callback:
            self.save_callback(data)
        else:
            print(data)
        
    def get_id(self):
        return self.id
    
    def disable_listes(self):
        for liste in self.listes[:4]:
            liste.disable()
    
    def enable_listes(self):
        for liste in self.listes:
            liste.enable()
    
    def update_listes(self):
        action = self.data.get("Action", {})
        moteur_ordre = action.get("Moteur", {}).get("ordre", {})
        herkulex_peigne_ordre = action.get("HerkuleX", {}).get("Peigne", {}).get("ordre", {})
        herkulex_pince_gauche = action.get("HerkuleX", {}).get("Pinces", {}).get("gauche", {}).get("ordre", {})
        herkulex_pince_droite = action.get("HerkuleX", {}).get("Pinces", {}).get("droite", {}).get("ordre", {})
        herkulex_bras_ordre = action.get("HerkuleX", {}).get("Bras", {}).get("ordre", {})
        
        if self.cote_actif in moteur_ordre:
            self.rebuild_liste(self.listes[0],moteur_ordre[self.cote_actif])
        else:
            self.rebuild_liste(self.listes[0],"-")
        
        if self.cote_actif in herkulex_peigne_ordre:
            self.rebuild_liste(self.listes[1],herkulex_peigne_ordre[self.cote_actif])
        else:
            self.rebuild_liste(self.listes[1],"-")
        
        if self.cote_actif in herkulex_pince_gauche:
            self.rebuild_liste(self.listes[2],herkulex_pince_gauche[self.cote_actif])
        else:
            self.rebuild_liste(self.listes[2],"-")
            
        if self.cote_actif in herkulex_pince_droite:
            self.rebuild_liste(self.listes[3],herkulex_pince_droite[self.cote_actif])
        else:
            self.rebuild_liste(self.listes[3],"-")   
            
        if self.cote_actif in herkulex_bras_ordre:
            self.rebuild_liste(self.listes[4],herkulex_bras_ordre[self.cote_actif])
        else:
            self.rebuild_liste(self.listes[4],"-")    
    
    def rebuild_liste(self,liste,option):
        liste.selected_option = option
        liste.menu_states['closed'].selected_option = option
        liste.menu_states['closed'].finish()
        liste.menu_states['closed'].start()
        liste.rebuild()
    
    def close(self):
        self.window.kill()

class MainWindow:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.manager = pygame_gui.UIManager((800, 600), 'data/theme_button.json')

        self.button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((50, 50), (150, 50)),
                                                    text='Open Window',
                                                    manager=self.manager)

        self.new_window = None

    def run(self):
        clock = pygame.time.Clock()
        is_running = True
        while is_running:
            time_delta = clock.tick(60)/1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_running = False
                if event.type == pygame.USEREVENT:
                    if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                        if event.ui_element == self.button:
                            self.new_window = IHM_Action_Aux(self.manager,1,(3000,1500,360))
                self.manager.process_events(event)
                if self.new_window:
                    self.new_window.process_events(event)

            self.manager.update(time_delta)
            self.screen.fill((255, 255, 255))
            self.manager.draw_ui(self.screen)
            pygame.display.update()

if __name__ == "__main__":
    main_window = MainWindow()
    main_window.run()
