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
        
        self.client = Client("127.0.0.4", 22050, 4, self.receive_to_server)
        
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
                self.client.stop()
                
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
        self.client.set_callback(self.receive_to_server)
        self.client.set_callback_stop(self.stop)
        self.client.connect()
        
        while self.is_running:
            if self.strategie_is_running:
                self.start_jack()
                
                self.run_strategie()
    
    def start_jack(self):
        # Attend que le jack soit enclechée
        self.client.add_to_send_list(self.client.create_message(9, "jack", {"data": "wait_for_press"}))
        logging.info("STRAT : Attente du jack")
        self.JACK.wait_for_press()
        
        logging.info("STRAT : Jack enclenché")
        self.client.add_to_send_list(self.client.create_message(9, "jack", {"data": "wait_for_release"}))
        self.JACK.wait_for_release()
        
        logging.info("STRAT : Jack relaché")
        self.client.add_to_send_list(self.client.create_message(9, "jack", {"data": "start"}))
        
        # Reset la carte actionneur
        self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": 416, "byte1": 11}))
    
    def run_strategie(self):
                
        for key, item in self.strategie.items():
            deplacement = item["Déplacement"]
            action = item["Action"]
            special = item["Spécial"]
            
            if "Coord" in deplacement:
                self.move(deplacement)
                
            for key, act in action.items():
                self.client.add_to_send_list(self.client.create_message(2, "CAN", {"id": act["id"], "byte1": act["ordre"]}))
                
                """while act["akn"] not in self.liste_aknowledge and self.strategie_is_running:
                    time.sleep(0.1)"""
                
                time.sleep(3)
            
            if self.strategie_is_running == False:
                logging.info("Arrêt de la stratégie")
                break                  
    
    def move(self, deplacement):
        # Envoi de la commande de déplacement
        pos = (deplacement["Coord"]["X"], deplacement["Coord"]["Y"], int(deplacement["Coord"]["T"]), "0")
        logging.info(f"STRAT : Déplacement en {pos}")
        
        # Envoyez la position au CAN
        self.client.add_to_send_list(self.client.create_message(
            2, "clic", {"x": pos[0], "y": pos[1], "theta": pos[2], "sens": pos[3]}))
        
        # Attendre l'acquittement
        while deplacement["aknowledge"] not in self.liste_aknowledge and self.strategie_is_running:
            if self.strategie_is_running == False:
                break
            time.sleep(0.1)
        if deplacement["aknowledge"] in self.liste_aknowledge:
            self.liste_aknowledge.remove(deplacement["aknowledge"])
                
    def stop(self):
        self.is_running = False
        self.strategie_is_running = False