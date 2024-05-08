from    client  import  Client
import  threading
import  gpiozero
import  logging
import  time
import  json
import  os

# configuration du logger
logging.basicConfig(filename='strat.log', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S', format='%(asctime)s - %(levelname)s - %(message)s')

class Strategie:
    def __init__(self, _path = None):
        self.path_strat = _path
        self.strategie = None
        
        # Vérification de l'existence du fichier
        if self.path_strat:
            if os.path.exists(self.path_strat):
                with open(self.path_strat, "r") as file:
                    self.strategie = json.load(file)
            else:
                logging.error(f"STRAT : La stratégie {self.path_strat} n'existe pas")
                return
        
        self.client_strat = Client("127.0.0.4", 22050, 4, self.receive_to_server)
        
        self.JACK = gpiozero.Button(16, pull_up=True)
        
        self.is_running = False
        self.strategie_is_running = False
        self.action_actuelle = {"Item": None,
                                "state": "idle",}
        self.action = 0
        
        self.ETAT = 0
        self.EQUIPE = "jaune"
        self.state_lidar = ""
        self.state_strat = 0
        self.TIMER = 0
        self.temps_de_jeu = 100
        
        self.liste_aknowledge = []
    
    # ============================== Fin du constructeur ==============================
    
    def receive_to_server(self, message):
        try:
            if message["cmd"] == "stop":
                self.client_strat.stop()
                
            elif message["cmd"] == "config":
                data = message["data"]
                self.ETAT = data["etat"]    
                self.EQUIPE = data["equipe"]
                logging.info(f"STRAT : Configuration reçue : {data}")
                
            elif message["cmd"] == "akn_m":
                self.robot_move = False
                
            elif message["cmd"] == "akn":
                data = message["data"]
                if self.strategie_is_running:
                    self.liste_aknowledge.append(data["id"])
                    logging.info(f"STRAT : Acquittement reçu : {data['id']}")
                
            elif message["cmd"] == "ARU":
                self.strategie_is_running = False

            elif message["cmd"] == "lidar":
                self.state_lidar = message["etat"]
                """if self.state_lidar == "stop":
                    self.state_strat = "pause"
                    
                elif self.state_lidar == "resume":
                    self.state_strat = "resume"""
            
            elif message["cmd"] == "strategie":
                strat_path = message["data"]["strategie"]
                # Charger la stratégie
                if os.path.exists(strat_path):
                    with open(strat_path, "r") as file:
                        self.strategie = json.load(file)
                    logging.info(f"STRAT : Chargement de la stratégie {strat_path}")
                else:
                    logging.error(f"STRAT : La stratégie {strat_path} n'existe pas")
                
                self.strategie_is_running = True
                self.state_strat = "wait_jack"
        
        except Exception as e:
            logging.error(f"STRAT : Erreur lors de la réception du message : {str(e)}")

    def map_value(self,x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    
    def play(self):
        self.is_running = True
        self.client_strat.set_callback(self.receive_to_server)
        self.client_strat.set_callback_stop(self.stop)
        self.client_strat.connect()
        
        while self.is_running:
            if self.strategie_is_running:
                self.start_jack()
                
                self.run_strategie_3()
            time.sleep(0.1)
    
    def start_jack(self):

        self.client_strat.add_to_send_list(self.client_strat.create_message(9, "jack", {"data": "input_jack"}))
        self.JACK.wait_for_release() # Attend que le jack soit enclenché
        
        # Reset la carte actionneur
        self.client_strat.add_to_send_list(self.client_strat.create_message(2, "CAN", {"id": 416, "byte1": 11}))
        self.client_strat.add_to_send_list(self.client_strat.create_message(2, "CAN", {"id": 417, "byte1": 11}))
        
        self.client_strat.add_to_send_list(self.client_strat.create_message(9, "jack", {"data": "wait_start"}))
        self.JACK.wait_for_press() # Attend que le jack soit relaché
        self.TIMER = time.time()

        self.state_strat = "idle"
        self.client_strat.add_to_send_list(self.client_strat.create_message(0, "start", None))  
    
    def stop_with_timer(self):
        
        def timer():
            while time.time() - self.TIMER < self.temps_de_jeu and self.strategie_is_running:
                time.sleep(1)
            self.strategie_is_running = False
        
        t = threading.Thread(target=timer)
        t.start()           
    
    def run_strategie_2(self):
        # Excecute la stratégie de façon non bloquante
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
                self.move(deplacement)
            elif "Rotation" in deplacement:
                self.rotate(deplacement)
            elif "Ligne_Droite" in deplacement:
                self.ligne_droite(deplacement)
            
            # Envoi des actions en mouvement
            self.send_actions(action_en_mvt)
            
            if self.strategie_is_running == False:
                break
            
            # Attend l'acquittement du mouvement
            self.wait_for_aknowledge(deplacement["aknowledge"])
            
            if self.strategie_is_running == False:
                break
            
            # Envoi des actions après le mouvement
            self.send_actions(action_apres_mvt)
            
            if self.strategie_is_running == False:
                logging.info("Arrêt de la stratégie")
                break
    
    def run_strategie_3(self):
        # Excecute la stratégie de façon non bloquante
        
        while self.strategie_is_running:
            if self.action > len(self.strategie):
                self.state_strat = "end"
                self.strategie_is_running = False
                self.client_strat.add_to_send_list(self.client_strat.create_message(0, "end", None))
                break
            
            if self.state_strat == "idle":
                # Etat d'attente et de récupération de la nouvelle action
                self.action += 1
                try:
                    self.action_actuelle["Item"] = self.strategie[str(self.action)]
                    self.action_actuelle["state"] = "idle"
                except Exception as e:
                    logging.error(f"Erreur lors de la lecture de l'action : {str(e)}")

                self.state_strat = "deplac"
                
                if self.strategie_is_running == False:
                    break
                
                item = self.strategie[str(self.action)]
                wait_aknowlodege = []
                
            elif self.state_strat == "deplac":
                # Etat de déplacement
                deplacement = item["Déplacement"]
                self.action_actuelle["state"] = "deplac"
                
                if self.state_lidar == "stop":
                    self.state_strat = "pause"
                    continue
                
                if "Coord" in deplacement:
                    self.move(deplacement,wait_aknowlodege)
                elif "Rotation" in deplacement:
                    self.rotate(deplacement,wait_aknowlodege)
                elif "Ligne_Droite" in deplacement:
                    self.ligne_droite(deplacement,wait_aknowlodege)
                
                self.state_strat = "action_en_mvt"
                
            elif self.state_strat == "action_en_mvt":
                # Etat d'attente de l'acquittement des actions en mouvement
                action = item["Action"]
                action_en_mvt = []
                
                self.action_actuelle["state"] = "action_en_mvt"
                
                try:
                    for key, act in action.items():
                        if act["en_mvt"] == True:
                            action_en_mvt.append(action[key])
                except Exception as e:
                    logging.error(f"Erreur lors de la lecture des actions : {str(e)}")
                
                # Envoi des actions en mouvement
                self.send_actions(action_en_mvt,wait_aknowlodege)
                
                self.state_strat = "wait_aknowledge"
                
                logging.info(f"STRAT : Attente de l'acquittement des actions en mouvement : {wait_aknowlodege}")
            
            elif self.state_strat == "wait_aknowledge_en_mvt":
                # Etat d'attente de l'acquittement des actions et du déplacement
                self.action_actuelle["state"] = "wait_aknowledge_en_mvt"
                
                for akn in wait_aknowlodege:
                    if akn in self.liste_aknowledge:
                        self.liste_aknowledge.remove(akn)
                        wait_aknowlodege.remove(akn)
                
                if len(wait_aknowlodege) == 0:
                   self.state_strat = "action_apres_mvt"
                   self.liste_aknowledge = []
                   logging.info("STRAT : Fin de l'attente des acquittements des actions en mouvement")
            
            elif self.state_strat == "action_apres_mvt":
                # Etat d'attente de l'acquittement des actions après le mouvement
                action_apres_mvt = []
                
                self.action_actuelle["state"] = "action_apres_mvt"
                action = item["Action"]
                
                try:
                    for key, act in action.items():
                        if act["en_mvt"] == False:
                            action_apres_mvt.append(action[key])
                except Exception as e:
                    logging.error(f"Erreur lors de la lecture des actions : {str(e)}")
                
                # Envoi des actions après le mouvement
                self.send_actions(action_apres_mvt,wait_aknowlodege)
                
                self.state_strat = "wait_aknowledge_apres_mvt"
                logging.info(f"STRAT : Attente de l'acquittement des actions après le mouvement : {wait_aknowlodege}")
                
            elif self.state_strat == "wait_aknowledge_apres_mvt":
                # Etat d'attente de l'acquittement des actions après le mouvement
                self.action_actuelle["state"] = "wait_aknowledge_apres_mvt"
                
                for akn in wait_aknowlodege:
                    if akn in self.liste_aknowledge:
                        self.liste_aknowledge.remove(akn)
                        wait_aknowlodege.remove(akn)
                
                if len(wait_aknowlodege) == 0:
                    self.state_strat = "idle"
                    self.liste_aknowledge = []
                    logging.info("STRAT : Fin de l'attente des acquittements des actions après le mouvement")
            
            elif self.state_strat == "pause":
                if self.state_lidar == "resume":
                    self.state_strat = "resume"
            
            elif self.state_strat == "resume":
                self.state_strat = self.action_actuelle["state"]
            
            
    def move(self, deplacement, akn):
        try:
            pos = [0, 0, 0, 0]
            if self.EQUIPE == "bleu":
                pos[0] = int(self.map_value(deplacement["Coord"]["X"], 0, 3000, 3000, 0))
                pos[1] = deplacement["Coord"]["Y"]
                pos[2] = int((1800 - deplacement["Coord"]["T"]) % 3600)
                pos[3] = deplacement["Coord"]["S"]
            elif self.EQUIPE == "jaune":
                # Envoi de la commande de déplacement
                pos = [deplacement["Coord"]["X"], deplacement["Coord"]["Y"], int(deplacement["Coord"]["T"]), deplacement["Coord"]["S"]]                
            
            logging.info(f"STRAT : Position envoyée {self.EQUIPE} : {pos}")
            # Envoyez la position au CAN
            self.client_strat.add_to_send_list(self.client_strat.create_message(
                2, "clic", {"x": pos[0], "y": pos[1], "theta": pos[2], "sens": pos[3]}))
            
            akn.append(deplacement["aknowledge"])
            
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi de la position move : {str(e)}")
    
    def rotate(self, deplacement, akn):
        # Envoi de la commande de rotation
        angle = deplacement["Rotation"]
        
        if self.EQUIPE == "bleu":
            angle = (angle + 180) % 360
        
        akn.append(deplacement["aknowledge"])
        
        # Envoyez la position au CAN
        self.client_strat.add_to_send_list(self.client_strat.create_message(2, "rotation", {"angle": angle}))
    
    def ligne_droite(self, deplacement, akn):
        # Envoi de la commande de rotation
        distance = deplacement["Ligne_Droite"]
        
        akn.append(deplacement["aknowledge"])
        
        # Envoyez la position au CAN
        self.client_strat.add_to_send_list(self.client_strat.create_message(2, "deplacement", {"distance": distance}))
    
    def wait_for_aknowledge(self, id):
        while id not in self.liste_aknowledge and self.strategie_is_running:
            time.sleep(0.1)
        if id in self.liste_aknowledge:
            self.liste_aknowledge.remove(id)
            
    def wait_for_list_aknowledge(self, ids):
        # Attend que tous les acquittements soient reçus
        while len(ids) > 0 and self.strategie_is_running:
            for id in ids:
                if id in self.liste_aknowledge:
                    self.liste_aknowledge.remove(id)
    
    def send_actions(self, actions, akn):
        for action in actions:
            self.client_strat.add_to_send_list(self.client_strat.create_message(2, "CAN", {"id": action["id"], "byte1": action["ordre"]}))
            time.sleep(1.2)
            #akn.append(action["akn"])
            #self.wait_for_aknowledge(action["aknowledge"])
    
    def stop(self):
        self.is_running = False
        self.strategie_is_running = False
        
if __name__ == "__main__":
    try:
        strat = Strategie()
        strat.play()
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de la stratégie : {str(e)}")