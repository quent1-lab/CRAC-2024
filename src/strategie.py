from    client  import  Client
import  threading
import  gpiozero
import  logging
import  time
import  math
import  json
import  os

# configuration du logger
logging.basicConfig(filename='strat.log', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S', format='%(asctime)s - %(levelname)s - %(message)s')

class Strategie:
    def __init__(self, _path = None):
        self.path_strat = _path
        self.strategie = None
        self.temps_pause = 0
        self.coord_prec = [0,0]
        self.lidar_stop = False
        
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
        self.type_mvt = "immobile"
        self.action = 0
        self.ancienne_vit = ""
        
        self.ETAT = 0
        self.EQUIPE = "jaune"
        self.state_lidar = ""
        self.state_strat = 0
        self.TIMER = 0
        self.temps_de_jeu = 100
        
        self.ROBOT_coord = [0, 0, 0]
        
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
            
            elif message["cmd"] == "coord":
                coord = message["data"]
                self.ROBOT_coord = [coord["x"], coord["y"], int(coord["theta"]/10)]

            elif message["cmd"] == "lidar":
                self.state_lidar = message["data"]["etat"]
                
                if self.state_lidar == "pause":      
                    lidar_stop = True        
                    if self.type_mvt == "XYT" or self.type_mvt == "ligne":
                        logging.info("STRAT : Pause du robot en mvt")
                        # Arrêter le robot
                        #self.client_strat.add_to_send_list(self.client_strat.create_message(2, "CAN", {"id": 1, "byte1": 0}))
                        
                        self.state_strat = "arret_urg"
                        self.type_mvt = "immobile"
                    else:
                        logging.info("STRAT : Pause du robot")

            
            elif message["cmd"] == "strategie":
                strat_path = message["data"]["strategie"]
                # Charger la stratégie
                if os.path.exists(strat_path):
                    try :
                        with open(strat_path, "r") as file:
                            self.strategie = json.load(file)  
                            
                        self.strategie_is_running = True
                        self.state_strat = "wait_jack"
                        logging.info(f"STRAT : stratégie {strat_path} chargé")   
                            
                    except Exception as e:
                        logging.error(f"STRAT : Erreur lors du chargement de la stratégie : {str(e)}")
                        self.client_strat.add_to_send_list(self.client_strat.create_message(9, "strat", {"data": "erreur_charg"}))
                else:
                    logging.error(f"STRAT : La stratégie {strat_path} n'existe pas")
                
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
        
        logging.info("STRAT : Attente du début de la partie")
        
        while self.JACK.value == 0:
            time.sleep(0.1)
        
        logging.info("STRAT : Démarrage de la stratégie")
        
        self.TIMER = time.time()
        self.stop_with_timer()
        
        self.state_strat = "idle"
        self.client_strat.add_to_send_list(self.client_strat.create_message(0, "start", None))  
    
    def stop_with_timer(self):
        
        def timer():
            while time.time() - self.TIMER < self.temps_de_jeu and self.strategie_is_running:
                time.sleep(1)
            self.strategie_is_running = False
            self.client_strat.add_to_send_list(self.client_strat.create_message(0, "end", None))
        
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

            # Vérification de l'état du robot. Si le robot est à l'arrêt plus de 6 secondes, on relance l'action précédente
            # En fonction des coordonnées du robot
            if (time.time() - self.temps_pause) > 4:
                
                if self.coord_prec != [0,0]:
                    # Si le robot n'a pas bougé d'un rayon de 3cm depuis 6 secondes, on relance l'action précédente
                    distance_ = int(math.sqrt((self.coord_prec[0] - self.ROBOT_coord[0])**2 + (self.coord_prec[1] - self.ROBOT_coord[1])**2))
                    logging.info(f"STRAT : Distance parcourue en 6s : {distance_}")
                    if distance_ == 0:
                        
                        if self.state_strat == "wait_aknowledge_apres_mvt" or self.state_strat == "action_apres_mvt":
                            continue
                        else:
                            self.liste_aknowledge = []
                            wait_aknowlodege = []
                            self.state_strat = "deplac"
                            self.state_lidar = "resume"
                            logging.info("STRAT : Relance de la pause")
                        self.lidar_stop = False
                        
                self.temps_pause = time.time()
                self.coord_prec = self.ROBOT_coord[:2]

            
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
                
                if self.state_lidar == "pause":
                    self.state_strat = "pause"
                    continue
                
                # Chargement de la vitesse
                if "Vitesse" in item:
                    if item["Vitesse"] != self.ancienne_vit:
                        self.ancienne_vit = item["Vitesse"]
                        logging.info(f"STRAT : Changement de vitesse : {item['Vitesse']}")
                        if item["Vitesse"] == "Rapide":
                            self.client_strat.add_to_send_list(self.client_strat.create_message(2, "set_vit",{ "vitesse": 1200}))
                        elif item["Vitesse"] == "Lent":
                            self.client_strat.add_to_send_list(self.client_strat.create_message(2, "set_vit",{ "vitesse": 10}))
                        elif item["Vitesse"] == "Normal":
                            self.client_strat.add_to_send_list(self.client_strat.create_message(2, "set_vit",{ "vitesse": 600}))
                    time.sleep(0.02)
                
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
                
                self.state_strat = "wait_aknowledge_en_mvt"
                
                logging.info(f"STRAT : Attente de l'acquittement des actions en mouvement : {wait_aknowlodege}")
            
            elif self.state_strat == "wait_aknowledge_en_mvt":
                # Etat d'attente de l'acquittement des actions et du déplacement
                self.action_actuelle["state"] = "wait_aknowledge_en_mvt"

                for akn in wait_aknowlodege:
                    if akn in self.liste_aknowledge:
                        self.liste_aknowledge.remove(akn)
                        wait_aknowlodege.remove(akn)

                if len(wait_aknowlodege) == 0:
                   self.client_strat.add_to_send_list(self.client_strat.create_message(2, "move", {"etat": False})) 
                   self.state_strat = "action_apres_mvt"
                   self.liste_aknowledge = []
                   logging.info("STRAT : Fin de l'attente des acquittements des actions en mouvement")
                   self.type_mvt = "immobile"
            
            elif self.state_strat == "action_apres_mvt":
                # Etat d'attente de l'acquittement des actions après le mouvement
                action_apres_mvt = []
                
                self.action_actuelle["state"] = "action_apres_mvt"
                action = item["Action"]
                
                try:
                    for key, act in action.items():
                        logging.info(f"STRAT : Action : {act}")
                        if act["id"] == "0x24":
                            # Recalage
                            ordre = act["ordre"]
                            sens = -1 if ordre % 2 == 0 else 1
                            mode = 0

                            # Déterminer la valeur de recalage en fonction des coordonnées du robot
                            if ordre % 2 == 0:
                                # Recalage en Y
                                mode = 2
                                if self.ROBOT_coord[1] <= 1000:
                                    recal = 134
                                else:
                                    recal = 1866
                            else:
                                # Recalage en X
                                mode = 1
                                if self.ROBOT_coord[0] <= 1500:
                                    recal = 134
                                else:
                                    recal = 2866

                            logging.info(f"STRAT : Recalage en cours : sens = {sens}, mode = {mode}, recal = {recal}")
                            self.client_strat.add_to_send_list(self.client_strat.create_message(2, "recalage", {"distance": 300 * sens, "mode": mode, "recalage": recal}))
                            self.wait_for_aknowledge(act["akn"])
                            logging.info("STRAT : Fin du recalage")

                        elif act["en_mvt"] == False:
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
                    if self.action == len(self.strategie):
                        self.state_strat = "end"
                        self.strategie_is_running = False
                        self.client_strat.add_to_send_list(self.client_strat.create_message(0, "end", None))
                        break
            
            elif self.state_strat == "pause":
                if self.state_lidar == "resume":
                    self.state_strat = "deplac"
            
            elif self.state_strat == "arret_urg":
                self.client_strat.add_to_send_list(self.client_strat.create_message(2, "CAN", {"id": 503, "byte1": 0})) 
                time.sleep(0.02)
                self.client_strat.add_to_send_list(self.client_strat.create_message(2, "CAN", {"id": 503, "byte1": 1}))
                time.sleep(1)
                self.state_strat = "pause_en_mvt"
            
            elif self.state_strat == "pause_en_mvt":
                if self.state_lidar == "resume":
                    # Réactiver l'asservissement
                    #self.client_strat.add_to_send_list(self.client_strat.create_message(2, "desa", False)) 
                    logging.info("STRAT : Reprise de la stratégie")
                    deplac = item["Déplacement"]
                    wait_aknowlodege = []
                    self.liste_aknowledge = []
                    
                    if "Coord" in deplac:
                        logging.info("STRAT : Reprise du déplacement")
                        self.move(deplac,wait_aknowlodege)
                        
                    elif "Ligne_Droite" in deplac:
                        logging.info("STRAT : Reprise du déplacement en ligne droite")
                        distance = deplac["Ligne_Droite"]
                        x = int(self.ROBOT_coord[0] + distance * math.cos(math.radians(self.ROBOT_coord[2])))
                        y = int(self.ROBOT_coord[1] + distance * math.sin(math.radians(self.ROBOT_coord[2])))
                        # Calcul de l'angle du robot à la fin du déplacement
                        theta = int(math.atan2(y - self.ROBOT_coord[1], x - self.ROBOT_coord[0]))
                        self.move({"Coord": {"X": x, "Y": y, "T": theta, "S": "0"}, "aknowledge": 276},wait_aknowlodege)
                        
                    self.state_strat = "action_en_mvt"
                    logging.info("STRAT : Fin de la pause en mvt")

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
            
            self.client_strat.add_to_send_list(self.client_strat.create_message(0, "move", {"etat": True}))
            self.client_strat.add_to_send_list(self.client_strat.create_message(3, "sens", {"sens": "avant"}))
            
            logging.info(f"STRAT : Position envoyée {self.EQUIPE} : {pos}")
            
            # Envoyez la position au CAN
            self.client_strat.add_to_send_list(self.client_strat.create_message(
                2, "clic", {"x": pos[0], "y": pos[1], "theta": pos[2], "sens": pos[3]}))
            
            akn.append(deplacement["aknowledge"])
            self.type_mvt = "XYT"
            
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi de la position move : {str(e)}")
    
    def rotate(self, deplacement, akn):
        # Envoi de la commande de rotation
        angle = deplacement["Rotation"]
        
        if self.EQUIPE == "bleu":
            angle = (angle + 180) % 360
        
        akn.append(deplacement["aknowledge"])
        logging.info(f"STRAT : Envoi de la commande de rotation : {angle}")
        # Envoyez la position au CAN
        self.client_strat.add_to_send_list(self.client_strat.create_message(2, "rotation", {"angle": angle}))
        
        self.type_mvt = "rotate"
    
    def ligne_droite(self, deplacement, akn):
        # Envoi de la commande de rotation
        distance = deplacement["Ligne_Droite"]
        
        akn.append(deplacement["aknowledge"])
        logging.info(f"STRAT : Envoi de la commande de déplacement en ligne droite : {distance}")
        self.client_strat.add_to_send_list(self.client_strat.create_message(3, "move", {"etat": True}))
        
        if distance < 0:
            # Envoyez la position au CAN
            self.client_strat.add_to_send_list(self.client_strat.create_message(3, "sens", {"sens": "arriere"}))
        else :
            self.client_strat.add_to_send_list(self.client_strat.create_message(3, "sens", {"sens": "avant"}))
        
        # Envoyez la position au CAN
        self.client_strat.add_to_send_list(self.client_strat.create_message(2, "deplacement", {"distance": distance}))
        
        self.type_mvt = "ligne"
    
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
            time.sleep(0.8)
            #akn.append(action["akn"])
            #self.wait_for_aknowledge(action["akn"])
    
    def stop(self):
        self.is_running = False
        self.strategie_is_running = False
        
if __name__ == "__main__":
    try:
        strat = Strategie()
        strat.play()
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de la stratégie : {str(e)}")