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
            ("CMD hexa", (10, 180), (80, 30)),
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
        for i in range(1,4):
            try:
                if self.command_CAN[i] == "":
                    self.command_CAN[i] = 0
                    self.text_boxes[5+i].set_text("0")
            except ValueError:
                pass
                
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
    def __init__(self, manager,_action_numero,_pos_actuelle, _callback_json=None, _callback_save=None, _callback_next=None, _callback_back=None,_id="", _config=None, _callback_delete=None, _angle = None):    
        self.manager = manager
        self.size = (610, 500)
        self.id = _id

        self.callback_json = _callback_json
        self.action_numero = _action_numero
        self.pos_actuelle = _pos_actuelle
        self.angle = 0
        self.distance = 0
        
        self.back_callback = _callback_back
        self.save_callback = _callback_save
        self.next_callback = _callback_next
        self.delete_callback = _callback_delete
        
        self.cote_actif = ""

        self.window = pygame_gui.elements.UIWindow(rect=pygame.Rect((100, 100), self.size),
                                                   manager=self.manager,
                                                   window_display_title="Action Auxiliaire Manager")

        self.labels = []
        self.texts = []
        self.buttons = []
        self.listes = []
        self.checkboxes = []
        self.panels = []
        self.button_delete = None
        
        # Charger la configuration des actions
        with open("data/config_ordre_to_can.json", "r") as file:
            self.config = json.load(file)
        
        self.name_action_Moteur = []
        self.name_action_Pince = []
        self.name_action_Peigne = []
        self.name_action_Bras = []
        self.name_action_Special = []
        self.name_recalage = []
        self.name_Vitesse = []
        
        # Récupérer les ordres des actions pour les listes
        for ordre in self.config["Moteur"]["ordre"]:
            self.name_action_Moteur.append(ordre)
        for ordre in self.config["HerkuleX"]["Pinces"]["gauche"]["ordre"]:
            self.name_action_Pince.append(ordre)
        for ordre in self.config["HerkuleX"]["Peigne"]["ordre"]:
            self.name_action_Peigne.append(ordre)
        for ordre in self.config["HerkuleX"]["Bras"]["ordre"]:
            self.name_action_Bras.append(ordre)
        for ordre in self.config["Action_special"]:
            self.name_action_Special.append(ordre)
        for ordre in self.config["Recalage"]["ordre"]:
            self.name_recalage.append(ordre)
        for ordre in self.config["Vitesse"]:
            self.name_Vitesse.append(ordre)
        

        # Ajouter des zones de texte et des labels correspondants
        box_infos = {
            "Numero_action": {"box1": {"type": "label", "position": (20, 5), "size": (150, 30), "text": f"Action numéro : {_action_numero}"}},
            "Cote_Actif": {"box1": {"type": "label", "position": (190, 5), "size": (200, 30), "text": f"Côté actif : Non défini"},},
            "Pos_actuelle":  {"box1": {"type": "label", "position": (370, 5), "size": (240, 30), "text": f"X: {_pos_actuelle[0]}  Y: {_pos_actuelle[1]}"}},
            
            "Deplacement": {"box1": {"type": "label", "position": (10, 50), "size": (90, 30), "text": "Déplacement"},
                            "box2": {"type": "checkbox", "position": (40, 80), "size": (35, 35), "text": "Deplac", "id":"#c_Deplac"}},
            
            "Ligne_droite": {"box1": {"type": "label", "position": (120, 50), "size": (150, 30), "text": "Ligne droite"},
                            "box2": {"type": "checkbox", "position": (120, 80), "size": (35, 35), "text": "Deplac", "id":"#c_Ligne_droite"},
                            "box3": {"type": "text", "position": (160, 80), "size": (110, 35), "id":"#t_Ligne_droite"}},            
            
            "Angle_arrive": {"box1": {"type": "label", "position": (300, 50), "size": (120, 30), "text": "Angle d'arrivé (°)"},
                              "box2": {"type": "checkbox", "position": (300, 80), "size": (35, 35), "text": "Deplac", "id":"#c_Angle_arrive"},
                              "box3": {"type": "text", "position": (340, 80), "size": (80, 35), "id":"#t_Angle_arrive"}},
            
            "Cote_a_controler": {"box1": {"type": "label", "position": (10, 120), "size": (230, 35), "text": "Côté à contrôler"},
                                "box2": {"type": "button", "position": (15, 150), "size": (105, 35), "text": "Avant"},
                                "box3": {"type": "button", "position": (125, 150), "size": (105, 35), "text": "Arrière"}},
            
            "Recalage": {"box1": {"type": "label", "position": (250, 120), "size": (100, 35), "text": "Recalage"},
                        "box2": {"type": "list", "position": (255, 150), "size": (100, 35), "text": self.name_recalage,"id":"#l_Recalage"}},
            
            "Action_special": {"box1": {"type": "label", "position": (400, 120), "size": (120, 30), "text": "Action spéciale"},
                               "box2": {"type": "list", "position": (380, 150), "size": (155, 35), "text": self.name_action_Special,"id":"#l_Action_special"}},
            
            "Moteur_pas_a_pas": {"box1": {"type": "label", "position": (0, 200), "size": (120, 30), "text": "Moteur p.à.p"},
                                "box2": {"type": "list", "position": (10, 230), "size": (100, 30), "text": self.name_action_Moteur, "id":"#l_Moteur"},
                                "box3": {"type": "label", "position": (10, 260), "size": (70, 35), "text": "Deplac"},
                                "box4": {"type": "checkbox", "position": (75, 260), "size": (35, 35), "text": "Moteur", "id":"#c_Moteur"}},
            
            "Peigne": {"box1": {"type": "label", "position": (110, 200), "size": (120, 30), "text": "Peigne"},
                    "box2": {"type": "list", "position": (120, 230), "size": (100, 30), "text": self.name_action_Peigne,"id":"#l_Peigne"},
                    "box3": {"type": "label", "position": (120, 260), "size": (70, 35), "text": "Deplac"},
                    "box4": {"type": "checkbox", "position": (185, 260), "size": (35, 35), "text": "Peigne", "id":"#c_Peigne"}},
            
            "Pinces": { "box1": {"type": "label", "position": (220, 200), "size": (220, 30), "text": "Pinces"},
                        "box2": {"type": "list", "position": (240, 230), "size": (190, 30), "text": self.name_action_Pince,"id":"#l_Pince_G"},
                        "box3": {"type": "list", "position": (1, 1), "size": (1, 1), "text": self.name_action_Pince,"id":"#l_Pince_D"},
                        "box4": {"type": "label", "position": (270, 260), "size": (70, 35), "text": "Deplac"},
                        "box5": {"type": "checkbox", "position": (335, 260), "size": (35, 35), "text": "Pince G", "id":"#c_Pinces"}},
            
            "Bras": {"box1": {"type": "label", "position": (450, 200), "size": (100, 30), "text": "Bras"},
                    "box2": {"type": "list", "position": (450, 230), "size": (100, 30), "text": self.name_action_Bras,"id":"#l_Bras"},
                    "box3": {"type": "label", "position": (450, 260), "size": (70, 35), "text": "Deplac"},
                    "box4": {"type": "checkbox", "position": (515, 260), "size": (35, 35), "text": "Bras", "id":"#c_Bras"}},            
            
            "New_coord": {"box1": {"type": "label", "position": (60, 310), "size": (270, 30), "text": "Nouvelle coordonnée (optionnel) :"},
                        "box2": {"type": "label", "position": (20, 335), "size": (130, 30), "text": "X"},
                        "box3": {"type": "text", "position": (20, 360), "size": (130, 30), "id":"#t_X"},
                        "box4": {"type": "label", "position": (160, 335), "size": (130, 30), "text": "Y"},
                        "box5": {"type": "text", "position": (160, 360), "size": (130, 30), "id":"#t_Y"},
                        "box6": {"type": "label", "position": (300, 335), "size": (130, 30), "text": "T"},
                        "box7": {"type": "text", "position": (300, 360), "size": (130, 30), "id":"#t_T"},
                        "box8": {"type": "label", "position": (440, 335), "size": (130, 30), "text": "S"},
                        "box9": {"type": "text", "position": (440, 360), "size": (130, 30), "id":"#t_S"},
                        "box10": {"type": "checkbox", "position": (20, 310), "size": (35, 35), "id":"#c_New_coord"}},
            
            "Vitesse": {"box1": {"type": "label", "position": (440, 50), "size": (80, 30), "text": "Vitesse"},
                        "box2": {"type": "list", "position": (440, 80), "size": (80, 35),"text": self.name_Vitesse, "id":"#l_Vitesse"}},
            
            "Back": {"box1": {"type": "button", "position": (20, 400), "size": (150, 30), "text": "Retour"}},
            "Save": {"box1": {"type": "button", "position": (180, 400), "size": (220, 30), "text": "Enregistrer"}},
            "Next": {"box1": {"type": "button", "position": (410, 400), "size": (150, 30), "text": "Suivant"}},
        }
        
        self.data = {
            "id_action": _action_numero,
            "Déplacement":{
                "Coord": {"X": _pos_actuelle[0], "Y": _pos_actuelle[1], "T": "", "S": "0"},
                "aknowledge": self.config["Coord"]["aknowledge"]
            },
            "Action" : {},
            "Special" :{},
            "Vitesse" : "Normal"
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
                    
                elif box_data["type"] == "checkbox":
                    checkbox = CheckBox(self.manager,self.window, box_data["position"], box_data["size"], box_data["id"])
                    
                    self.checkboxes.append(checkbox)
                
                elif box_data["type"] == "void":
                    pass
        
        if self.cote_actif == "":
            self.disable_listes()

        # Activer checkbox deplacement
        self.checkboxes[0].set_checked(True)
        
        # Désactiver les textes de la nouvelle coordonnée
        for i, text in enumerate(self.texts):
            if i != 1:
                text.disable()
        
        # Désactiver les boutons back et next
        self.buttons[-1].disable()
        self.buttons[-3].disable()
        
        # Mise a jour de l'angle
        if _angle:
            self.texts[1].set_text(str(_angle))
            self.data["Déplacement"]["Coord"]["T"] = _angle
            
        
        if _config:
            # Charger tous les paramètres
            self.load_data(_config)
        
        # Cacher la liste pince gauche
        self.listes[5].hide()

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
                        self.update_checkboxes()
                    
                    if changement:
                        self.update_listes()
                        self.update_checkboxes()
                        
                elif id == "#b_Arrière":
                    changement = True if self.cote_actif != "arriere" else False
                    self.cote_actif = "arriere"
                    # Mettre à jour le label
                    self.labels[1].set_text(f"Côté actif : {self.cote_actif.capitalize()}")
                    
                    # Activer les listes
                    if self.cote_actif != "":
                        self.enable_listes()
                        self.update_checkboxes()
                    
                    if changement:
                        self.update_listes()
                        self.update_checkboxes()
                        
                elif id == "#b_Retour":
                    if self.back_callback:
                        self.back_callback()
                elif id == "#b_Enregistrer":
                    self.save_data(self.data)
                elif id == "#b_Suivant":
                    if self.next_callback:
                        self.next_callback()
                
                elif id == "#b_Delete":
                    if self.delete_callback:
                        self.delete_callback(self.action_numero)
                
                # Gestion des checkbox
                elif id.split("_")[0] == "#c":
                    for checkbox in self.checkboxes:
                        if checkbox.get_id() == id:
                            checkbox.toggle()
                            
                            if id == "#c_Deplac":
                                # Activer ou non la checkbox et text ligne droite
                                if checkbox.get_checked():
                                    # Ajouter les données de coord
                                    self.data["Déplacement"] = {"Coord": {"X": self.pos_actuelle[0], "Y": self.pos_actuelle[1], "T": "", "S": "0"},
                                                                "aknowledge": self.config["Coord"]["aknowledge"]}
                                        
                                    # Activer Ligne droite
                                    self.checkboxes[1].enable()
                                    self.texts[0].set_text("")
                                    
                                    # Changer le texte de rotation
                                    self.labels[5].set_text("Angle d'arrivé (°)")
                                    self.texts[1].set_text("")
                                    
                                else:
                                    # Supprimer les données de coord
                                    self.data["Déplacement"] = {}
                                    self.texts[1].set_text("")
                                    
                                    # Désactiver Ligne droite
                                    self.checkboxes[1].set_checked(False)
                                    self.checkboxes[1].disable()
                                    self.texts[0].disable()
                                    self.texts[0].set_text("")
                                    
                                    # Active rotation
                                    self.checkboxes[2].enable()
                                    self.texts[1].enable()
                                    self.labels[5].set_text("Rotation (°)")
                                                               
                            elif id == "#c_Ligne_droite":
                                # Activer ou non la checkbox et text ligne droite
                                if checkbox.get_checked():
                                    # Désactiver rotation
                                    self.checkboxes[2].set_checked(False)
                                    self.checkboxes[2].disable()
                                    self.texts[1].disable()
                                    self.texts[1].set_text("")
                                    
                                    # Activer text ligne droite
                                    self.texts[0].enable()
                                    
                                    # Retirer les données de rotation et coord
                                    self.data["Déplacement"] = {}
                                else:
                                    # Activer rotation
                                    self.checkboxes[2].enable()
                                    self.texts[1].enable()
                                    
                                    # Désactiver text ligne droite
                                    self.texts[0].disable()
                                    self.texts[0].set_text("")
                                    
                                    # Ajouter les données de coord et supprimer les données de ligne droite
                                    self.data["Déplacement"] = {"Coord": {"X": self.pos_actuelle[0], "Y": self.pos_actuelle[1], "T": "", "S": "0"},
                                                                "aknowledge": self.config["Coord"]["aknowledge"]}
                                    
                            elif id == "#c_New_coord":
                                if checkbox.get_checked():
                                    for text in self.texts[2:]:
                                        text.enable()
                                else:
                                    for text in self.texts[2:]:
                                        text.disable()
                            
                            elif id == "#c_Moteur":
                                if "_M_"+self.cote_actif[:2] in self.data["Action"]:
                                    self.data["Action"]["_M_"+self.cote_actif[:2]]["en_mvt"] = checkbox.get_checked()
                                    
                            elif id == "#c_Peigne":
                                if "_P_"+self.cote_actif[:2] in self.data["Action"]:
                                    self.data["Action"]["_P_"+self.cote_actif[:2]]["en_mvt"] = checkbox.get_checked()
                            
                            elif id == "#c_Pinces":
                                if "_PG_"+self.cote_actif[:2] in self.data["Action"]:
                                    self.data["Action"]["_PG_"+self.cote_actif[:2]]["en_mvt"] = checkbox.get_checked()
                                if "_PD_"+self.cote_actif[:2] in self.data["Action"]:
                                    self.data["Action"]["_PD_"+self.cote_actif[:2]]["en_mvt"] = checkbox.get_checked()
                                    
                            elif id == "#c_Bras":
                                if "_B_" in self.data["Action"]:
                                    self.data["Action"]["_B_"]["en_mvt"] = checkbox.get_checked()

            elif event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED: # Si la liste change
                id = event.ui_element.get_object_ids()[1]
                texte = event.text
                if self.cote_actif != "":
                    if id == "#l_Moteur":
                        if texte == "-":
                            if "_M_av" in self.data["Action"] and self.cote_actif == "avant":
                                self.data["Action"].pop("_M_av")
                            elif "_M_ar" in self.data["Action"] and self.cote_actif == "arriere":
                                self.data["Action"].pop("_M_ar")
                        else:
                            self.data["Action"]["_M_"+self.cote_actif[:2]] = {
                                                                                "id": self.config["ID"][self.cote_actif],
                                                                                "en_mvt": self.checkboxes[3].get_checked(),
                                                                                "ordre": self.config["Moteur"]["ordre"][texte],
                                                                                "akn" : self.config["Moteur"]["aknowledge"][self.cote_actif],
                                                                                "str" : texte
                                                                            }
                            
                    elif id == "#l_Peigne":
                        if texte == "-":
                            if "_P_av" in self.data["Action"] and self.cote_actif == "avant":
                                self.data["Action"].pop("_P_av")
                            elif "_P_ar" in self.data["Action"] and self.cote_actif == "arriere":
                                self.data["Action"].pop("_P_ar")
                        else:
                            self.data["Action"]["_P_"+self.cote_actif[:2]] = {
                                                                                "id": self.config["ID"][self.cote_actif],
                                                                                "en_mvt": self.checkboxes[4].get_checked(),
                                                                                "ordre": self.config["HerkuleX"]["Peigne"]["ordre"][texte],
                                                                                "akn" : self.config["HerkuleX"]["Peigne"]["aknowledge"][self.cote_actif],
                                                                                "str" : texte
                                                                            }
                            
                    elif id == "#l_Pince_G":
                        if texte == "-":
                            if "_PG_av" in self.data["Action"] and self.cote_actif == "avant":
                                self.data["Action"].pop("_PG_av")
                            elif "_PG_ar" in self.data["Action"] and self.cote_actif == "arriere":
                                self.data["Action"].pop("_PG_ar")
                        else:
                            self.data["Action"]["_PG_"+self.cote_actif[:2]] = {
                                                                                "id": self.config["ID"][self.cote_actif],
                                                                                "en_mvt": self.checkboxes[5].get_checked(),
                                                                                "ordre": self.config["HerkuleX"]["Pinces"]["gauche"]["ordre"][texte],
                                                                                "akn" : self.config["HerkuleX"]["Pinces"]["gauche"]["aknowledge"][self.cote_actif],
                                                                                "str" : texte
                                                                            }
                            
                    elif id == "#l_Pince_D":
                        if texte == "-":
                            if "_PD_av" in self.data["Action"] and self.cote_actif == "avant":
                                self.data["Action"].pop("_PD_av")
                            elif "_PD_ar" in self.data["Action"] and self.cote_actif == "arriere":
                                self.data["Action"].pop("_PD_ar")
                        else:
                            self.data["Action"]["_PD_"+self.cote_actif[:2]] = {
                                                                                "id": self.config["ID"][self.cote_actif],
                                                                                "en_mvt": self.checkboxes[5].get_checked(),
                                                                                "ordre": self.config["HerkuleX"]["Pinces"]["droite"]["ordre"][texte],
                                                                                "akn" : self.config["HerkuleX"]["Pinces"]["droite"]["aknowledge"][self.cote_actif],
                                                                                "str" : texte
                                                                            }
                    
                    elif id == "#l_Action_special":
                        if texte == "-":
                            self.data["Special"] = {}
                        else:
                            self.data["Special"] = {
                                "id": self.config["ID"][self.cote_actif],
                                "ordre": texte,
                                "akn" : self.config["Action_special"][texte]["aknowledge"][self.cote_actif],
                                "str" : texte
                            }
                    
                if id == "#l_Bras":
                    if texte == "-":
                        if "_B_" in self.data["Action"]:
                            self.data["Action"].pop("_B_")
                    else:
                        self.data["Action"]["_B_"] = {
                                                        "id": self.config["ID"]["avant"],
                                                        "en_mvt": self.checkboxes[6].get_checked(),
                                                        "ordre": self.config["HerkuleX"]["Bras"]["ordre"][texte],
                                                        "akn" : self.config["HerkuleX"]["Bras"]["aknowledge"],
                                                        "str" : texte
                                                    }
                
                elif id == "#l_Recalage":
                    if texte == "-":
                        if "_R_" in self.data["Action"]:
                            self.data["Action"].pop("_R_")
                    else:
                        self.data["Action"]["_R_"] = {
                            "id": self.config["Recalage"]["id"],
                            "ordre": self.config["Recalage"]["ordre"][texte],
                            "akn" : self.config["Recalage"]["aknowledge"],
                            "str" : texte
                        }
                
                elif id == "#l_Vitesse":
                    self.data["Vitesse"] = texte
                                                        
            elif event.user_type == pygame_gui.UI_TEXT_ENTRY_CHANGED: # Si le texte change
                id = event.ui_element.get_object_ids()[1]
                try:
                    if id == "#t_Angle_arrive":
                        self.angle = int(event.text)
                        if not self.checkboxes[0].get_checked():
                            self.data["Déplacement"] = {"Rotation": self.angle * 10,
                                                        "aknowledge": self.config["Rotation"]["aknowledge"]}
                        else:
                            self.data["Déplacement"]["Coord"]["T"] = int(event.text)
                    elif id == "#t_Ligne_droite":
                        self.distance = int(event.text)
                        self.data["Déplacement"] = {"Ligne_Droite": self.distance,
                                                    "aknowledge": self.config["Ligne_Droite"]["aknowledge"]}
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
        for liste in self.listes[1:-1]:
            liste.disable()
    
    def enable_listes(self):
        for liste in self.listes:
            liste.enable()
    
    def update_listes(self):
        action = self.data.get("Action", {})
        moteur_ordre = action.get("_M_"+self.cote_actif[:2], {"str": "-"})
        herkulex_peigne_ordre = action.get("_P_"+self.cote_actif[:2], {"str": "-"})
        herkulex_pince_gauche = action.get("_PG_"+self.cote_actif[:2], {"str": "-"})
        herkulex_pince_droite = action.get("_PD_"+self.cote_actif[:2], {"str": "-"})
        herkulex_bras = action.get("_B_", {"str": "-"})
        action_special = self.data.get("Special", {"str": "-"})
        
        if "str" in action_special:        
            self.rebuild_liste(self.listes[1],action_special["str"])
        else:
            self.rebuild_liste(self.listes[1],"-")
        
        self.rebuild_liste(self.listes[2],moteur_ordre["str"])
        
        self.rebuild_liste(self.listes[3],herkulex_peigne_ordre["str"])
        
        self.rebuild_liste(self.listes[4],herkulex_pince_gauche["str"])
            
        self.rebuild_liste(self.listes[5],herkulex_pince_droite["str"])
        
        self.rebuild_liste(self.listes[6],herkulex_bras["str"])
            
    def update_checkboxes(self):
        action = self.data.get("Action", {})
        moteur_deplacement = action.get("_M_"+self.cote_actif[:2], {"en_mvt": False})
        herkulex_peigne_deplacement = action.get("_P_"+self.cote_actif[:2], {"en_mvt": False})
        herkulex_pince_gauche_deplacement = action.get("_PG_"+self.cote_actif[:2], {"en_mvt": False})
        herkulex_bras = action.get("_B_", {"en_mvt": False})
        
        self.checkboxes[3].set_checked(moteur_deplacement["en_mvt"])
        
        self.checkboxes[4].set_checked(herkulex_peigne_deplacement["en_mvt"])

        self.checkboxes[5].set_checked(herkulex_pince_gauche_deplacement["en_mvt"])
        
        self.checkboxes[6].set_checked(herkulex_bras["en_mvt"])
    
    def rebuild_liste(self,liste,option):
        liste.selected_option = option
        liste.menu_states['closed'].selected_option = option
        liste.menu_states['closed'].finish()
        liste.menu_states['closed'].start()
        liste.rebuild()
    
    def load_data(self,data):
        self.data = data
        self.data["id_action"] = self.action_numero
        for key in data["Action"]:
            if key[-2:] == "av":
                self.cote_actif = "avant"
                break
            elif key[-2:] == "ar":
                self.cote_actif = "arriere"
                break
            else:
                self.cote_actif = ""
        if "Coord" in data["Déplacement"]:
            self.pos_actuelle = [data["Déplacement"]["Coord"]["X"], data["Déplacement"]["Coord"]["Y"]]
            self.labels[2].set_text(f"X: {self.pos_actuelle[0]}  Y: {self.pos_actuelle[1]}")
            self.angle = data["Déplacement"]["Coord"]["T"]
        elif "Ligne_Droite" in data["Déplacement"]:
            self.distance = data["Déplacement"]["Ligne_Droite"]
            self.checkboxes[0].set_checked(False)
            self.checkboxes[1].set_checked(True)
            self.texts[0].set_text(str(self.distance))
            self.texts[0].enable()
            self.labels[5].set_text("Rotation (°)")
            self.texts[1].disable()
        elif "Rotation" in data["Déplacement"]:
            self.angle = data["Déplacement"]["Rotation"]
            self.checkboxes[0].set_checked(False)
            self.checkboxes[2].set_checked(True)
            self.texts[1].set_text(str(self.angle))
            self.texts[1].enable()
            self.labels[5].set_text("Rotation (°)")
            self.texts[0].disable()
            
        self.update_listes()
        self.enable_listes()
        self.update_checkboxes()
        
        if self.cote_actif == "":
            if self.cote_actif == "":
                self.disable_listes()

        self.button_delete = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((400, 5), (170, 30)),
                                                        text='Supprimer',
                                                        manager=self.manager,
                                                        container=self.window,
                                                        object_id=ObjectID(object_id="#b_Delete"))
        
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
