from    client  import  Client
import  logging
import  gpiozero
import  time
import  json
import  os

class Strategie:
    def __init__(self, _nom_start):
        self.nom_start = _nom_start
        self.strategie = None
        
        # Vérification de l'existence du fichier
        if os.path.exists(f"data/strategies/{self.nom_start}.json"):
            with open(f"data/strategies/{self.nom_start}.json", "r") as file:
                self.strategie = json.load(file)
        else:
            logging.error(f"La stratégie {self.nom_start} n'existe pas")
            return
        
        self.client = Client("127.0.0.4", 22050, 4, self.receive_to_server)
        
        self.is_running = False
        self.strategie_is_running = False
        self.robot_move = False
        
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
                
            elif message["cmd"] == "ARU":
                pass
        
        except Exception as e:
            print(f"Erreur lors de la réception du message : {str(e)}")
            
    def play(self):
        self.is_running = True
        self.client.start()
        
        while self.is_running:
            if self.strategie_is_running:
                self.run_strategie()
            else:
                self.run_start()
                
    def run_start(self):
        for action in self.strategie["start"]:
            if action["type"] == "attente":
                time.sleep(action["duree"])
                
            elif action["type"] == "envoi":
                self.client.send(action["message"])
                
            elif action["type"] == "strategie":
                self.strategie_is_running = True
                break
    
    def run_strategie(self):
        for action in self.strategie["strategie"]:
            if action["type"] == "attente":
                time.sleep(action["duree"])
                
            elif action["type"] == "envoi":
                self.client.send(action["message"])
                
            elif action["type"] == "strategie":
                self.strategie_is_running = False
                break
                
            elif action["type"] == "fonction":
                self.jouer(action["fonction"])

    def jouer(self, jeu):
        return self.fonction(jeu)