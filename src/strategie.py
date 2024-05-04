from    client  import  Client
import  logging
import  gpiozero
import  time
import  json
import  os

class Strategie:
    def __init__(self, _nom_strat):
        self.nom_strat = _nom_strat
        self.strategie = None
        
        # Vérification de l'existence du fichier
        if os.path.exists(f"data/strategies/{self.nom_strat}"):
            with open(f"data/strategies/{self.nom_strat}", "r") as file:
                self.strategie = json.load(file)
        else:
            logging.error(f"La stratégie {self.nom_strat} n'existe pas")
            return
        
        self.client_strat = Client("127.0.0.4", 22050, 4, self.receive_to_server)
        
        self.JACK = gpiozero.Button(16, pull_up=True)
        
        self.is_running = False
        self.strategie_is_running = False
        
        self.ETAT = 0
        self.EQUIPE = "jaune"
        
        self.liste_aknowledge = []
        

    def __str__(self):
        return self.nom
    
    def receive_to_server(self, message):
        try:
            if message["cmd"] == "stop":
                self.client_strat.stop()
                
            elif message["cmd"] == "config":
                data = message["data"]
                self.ETAT = data["etat"]    
                self.EQUIPE = data["equipe"]
                
            elif message["cmd"] == "akn_m":
                self.robot_move = False
                
            elif message["cmd"] == "akn":
                data = message["data"]
                if self.strategie_is_running:
                    self.liste_aknowledge.append(data["id"])
                    logging.info(f"STRAT : Acquittement reçu : {data['id']}")
                
            elif message["cmd"] == "ARU":
                self.strategie_is_running = False
        
        except Exception as e:
            print(f"Erreur lors de la réception du message : {str(e)}")
            
    def play(self):
        self.is_running = True
        self.strategie_is_running = True
        self.client_strat.set_callback(self.receive_to_server)
        self.client_strat.set_callback_stop(self.stop)
        self.client_strat.connect()
        
        while self.is_running:
            if self.strategie_is_running:
                self.start_jack()
                
                self.run_strategie()
    
    def start_jack(self):

        self.client_strat.add_to_send_list(self.client_strat.create_message(9, "jack", {"data": "input_jack"}))
        self.JACK.wait_for_release() # Attend que le jack soit enclenché
        
        self.client_strat.add_to_send_list(self.client_strat.create_message(9, "jack", {"data": "wait_start"}))
        self.JACK.wait_for_press() # Attend que le jack soit relaché

        self.client_strat.add_to_send_list(self.client_strat.create_message(9, "jack", {"data": "start"}))
        
        # Reset la carte actionneur
        self.client_strat.add_to_send_list(self.client_strat.create_message(2, "CAN", {"id": 416, "byte1": 11}))
    
    def run_strategie(self):
                
        for key, item in self.strategie.items():
            if self.strategie_is_running == False:
                break
            
            logging.info(f"STRAT : {key} , {item}")
            
            deplacement = item["Déplacement"]
            action = item["Action"]
            special = item["Special"]
            
            action_en_mvt = []
            action_apres_mvt = []
            
            try:
                for key, act in action.items():
                    if act["en_mvt"] == True:
                        action_en_mvt.append(action[key])
                    else:
                        action_apres_mvt.append(action[key])
            except Exception as e:
                logging.error(f"Erreur lors de la lecture des actions : {str(e)}")
            
            if "Coord" in deplacement:
                logging.info(f"STRAT : Déplacement en {deplacement['Coord']}")
                self.move(deplacement)
            elif "Rotation" in deplacement:
                self.rotate(deplacement)
            elif "Ligne_Droite" in deplacement:
                self.ligne_droite(deplacement)
            
            self.send_actions(action_apres_mvt)
            
            if self.strategie_is_running == False:
                logging.info("Arrêt de la stratégie")
                break                  
    
    def move(self, deplacement):
        try:
            # Envoi de la commande de déplacement
            pos = (deplacement["Coord"]["X"], deplacement["Coord"]["Y"], int(deplacement["Coord"]["T"]), "0")
            logging.info(f"STRAT : Déplacement en {pos}")
            
            # Envoyez la position au CAN
            self.client_strat.add_to_send_list(self.client_strat.create_message(
                2, "clic", {"x": pos[0], "y": pos[1], "theta": pos[2], "sens": pos[3]}))
            
            logging.info(f"STRAT : Envoi de la position")
            # Attendre l'acquittement
            self.wait_for_aknowledge(deplacement["aknowledge"])
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi de la position move : {str(e)}")
    
    def rotate(self, deplacement):
        # Envoi de la commande de rotation
        angle = deplacement["Rotation"]
        
        # Envoyez la position au CAN
        self.client_strat.add_to_send_list(self.client_strat.create_message(2, "rotation", {"angle": angle}))

        # Attendre l'acquittement
        self.wait_for_aknowledge(deplacement["aknowledge"])
    
    def ligne_droite(self, deplacement):
        # Envoi de la commande de rotation
        distance = deplacement["Ligne_Droite"]
        
        # Envoyez la position au CAN
        self.client_strat.add_to_send_list(self.client_strat.create_message(2, "deplacement", {"distance": distance}))

        # Attendre l'acquittement
        self.wait_for_aknowledge(deplacement["aknowledge"])
    
    def wait_for_aknowledge(self, id):
        while id not in self.liste_aknowledge and self.strategie_is_running:
            time.sleep(0.1)
        if id in self.liste_aknowledge:
            self.liste_aknowledge.remove(id)
    
    def send_actions(self, actions):
        for action in actions:
            self.client_strat.add_to_send_list(self.client_strat.create_message(2, "CAN", {"id": action["id"], "byte1": action["ordre"]}))
            #self.wait_for_aknowledge(action["aknowledge"])
            time.sleep(2)
    
    def stop(self):
        self.is_running = False
        self.strategie_is_running = False