import  can
import  os
import  struct
import  logging
import  struct
import  json
import  time

from    client  import  Client

# Configuration du logger
logging.basicConfig(filename='buscan.log', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S', format='%(asctime)s - %(levelname)s - %(message)s')

class ComCAN:
    def __init__(self, channel, bustype):
        self.channel = channel
        self.bustype = bustype
        self.can = None
        self.is_connected = False
        self.client = Client("127.0.0.2", 22050, 2, self.disconnect)
        
        self.liste_ack = {}
        with open("data/config_ordre_to_can.json","r",encoding="utf-8") as file:
            config_json = json.load(file)
        
        # Recherche des messages d'acquittement
        def find_aknowledge(d, path, result):
            try:
                for key, value in d.items():
                    new_path = path + [key]
                    if key == "aknowledge":
                        if isinstance(value, dict):
                            for key, value in value.items():
                                result[value] = ".".join(new_path + [key])
                        else:
                            result[value] = ".".join(new_path)
                    elif key == "ordre":
                        continue
                    elif isinstance(value, dict):
                        find_aknowledge(value, new_path, result)
            except Exception as e:
                logging.error(f"BusCAN : Erreur lors de la recherche des messages d'acquittement : {str(e)}")
        
        find_aknowledge(config_json, [], self.liste_ack)
        logging.info(f"BusCAN : Liste des messages d'acquittement : {self.liste_ack}")
        

    def connect(self):
        try:
            if os.name == "posix":
                os.system('sudo ip link set can0 type can bitrate 1000000')
                os.system('sudo ifconfig can0 up')
                self.can = can.interface.Bus(channel=self.channel, bustype=self.bustype)
                #self.can.state = can.BusState.ACTIVE
                self.is_connected = True
                logging.info("BusCAN : Connexion établie")
            else:
                logging.error("BusCAN : Le système d'exploitation n'est pas compatible avec le CAN")
        except Exception as e:
            logging.error(f"BusCAN : Erreur lors de la connexion : {str(e)}")

    def disconnect(self):
        try:
            self.can.shutdown()
            os.system('sudo ifconfig can0 down')
            self.is_connected = False
            logging.info("BusCAN : Connexion fermée")
        except Exception as e:
            logging.error(f"BusCAN : Erreur lors de la déconnexion : {str(e)}")

    def send(self, data):
        try:
            self.can.send(data)
            #logging.info("Message envoyé sur le bus CAN")
        except Exception as e:
            logging.error(f"BusCAN : Erreur lors de l'envoi du message : {str(e)}")
    
    def packed(self, id, data):
        dataCan = None
        try:
            for i in range(len(data)):
                if dataCan is None:
                    dataCan = struct.pack(data[i][1], data[i][0])
                else:
                    dataCan += struct.pack(data[i][1], data[i])
        except Exception as e:
            logging.error(f"BusCAN : Erreur lors de l'emballage des données : {str(e)}")
        return can.Message(arbitration_id=id, data=dataCan, is_extended_id=False)
    
    def receive(self):
        try:
            messageCan = self.can.recv(10.0)
            if messageCan is not None:
                #logging.info(f"BusCAN : Message reçu : {messageCan}")
                return messageCan.arbitration_id, messageCan.dlc, messageCan.data
            else:
                return None
        except Exception as e:
            time.sleep(0.001)
            logging.error(f"BusCan : Erreur lors de la réception du message : {str(e)}")
    
    def analyse_CAN(self, data):
        try:
            dataX = data[2]
            if data[0] == 0x28:
                x = struct.unpack('h', dataX[0:2])
                y = struct.unpack('h', dataX[2:4])
                theta = struct.unpack('h', dataX[4:6])
                self.client.add_to_send_list(self.client.create_message(0, "coord", {"x": x[0], "y": y[0], "theta": theta[0]}))
            elif data[0] == 0x203:
                # V_Batterie : ID batterie (short), V_Batterie (short)
                id_bat = dataX[0]
                v_bat = dataX[1] /10

                if id_bat == 1:
                    self.client.add_to_send_list(self.client.create_message(0, "energie", {"Batterie Main": {"Tension" : v_bat}}))
                    print(f"V_Batterie_Main : {v_bat}")
                else:
                    self.client.add_to_send_list(self.client.create_message(0, "energie", {f"Batterie {id_bat-1}": {"Tension" : v_bat}}))
                    print(f"V_Batterie_{id_bat-1} : {v_bat}")
            elif data[0] == 0x204:
                # I_Batterie : ID batterie (short), I_Batterie (short)
                id_bat = dataX[0]
                i_bat = dataX[1] /100
                self.client.add_to_send_list(self.client.create_message(0, "energie", {f"Batterie {id_bat}": {"Courant" : i_bat}}))
                print(f"I_Batterie_{id_bat} : {i_bat}")
            elif data[0] == 0x205:
                # Switch_Batterie : ID batterie (short), Switch_Batterie (short)
                id_bat = dataX[0]
                s_bat = dataX[1]
                self.client.add_to_send_list(self.client.create_message(0, "energie", {f"Batterie {id_bat}": {"Switch" : s_bat}}))
                print(f"Switch_Batterie_{id_bat} : {s_bat}")
            elif data[0] == 0x114:
                # Fin d'instruction de positionnement
                self.client.add_to_send_list(self.client.create_message(0, "akn_m", None))
            elif data[0] == 0x115:
                # Fin d'instruction de déplacement
                self.client.add_to_send_list(self.client.create_message(0, "akn_d", None))
            elif data[0] in self.liste_ack:
                # Message d'acquittement
                self.client.add_to_send_list(self.client.create_message(0, "akn", {"id": data[0], "name": self.liste_ack[data[0]]}))
            else:
                logging.info(f"BusCAN : ID inconnu -> data : {data}")
                #print(f"ID inconnu ; data : {data}")
        except Exception as e:
            logging.info(f"BusCAN : ID inconnu -> data : {data}")
            logging.error(f"BusCAN : Erreur lors de l'analyse du message CAN : {str(e)}")

    def receive_to_server(self, message):
        try:
            if message["cmd"] == "stop":
                self.client.stop()

            elif message["cmd"] == "clic":
                data = message["data"]
                # Format des données : x (short), y (short), theta (short), sens(char)
                dataCan = struct.pack('h', data["x"]) + struct.pack('h', data["y"]) + struct.pack('h', data["theta"]) + struct.pack('c', data["sens"].encode())
                messageCan = can.Message(arbitration_id=0x20, data=dataCan, is_extended_id=False)
                self.send(messageCan)
                logging.info(f"BusCAN : Message de clic envoyé : {messageCan}")

            elif message["cmd"] == "recalage":
                data = message["data"]
                # Format des données : distance (short), mode (char), recalage (short)
                dataCan = struct.pack('h', data["distance"]) + struct.pack('c', str(data["mode"]).encode()) + struct.pack('h', data["recalage"])
                
                messageCan = can.Message(arbitration_id=0x24, data=dataCan, is_extended_id=False)
                self.send(messageCan)
            
            elif message["cmd"] == "rotation":
                data = message["data"]
                # Format des données : angle (short)
                dataCan = struct.pack('h', data["angle"])
                messageCan = can.Message(arbitration_id=0x25, data=dataCan, is_extended_id=False)
                self.send(messageCan)
                
            elif message["cmd"] == "desa":
                data = message["data"]
                # Format des données : desa (char)
                if data:
                    messageCan = can.Message(arbitration_id=0x1F7, data=[0], is_extended_id=False)
                else:
                    messageCan = can.Message(arbitration_id=0x1F7, data=[1], is_extended_id=False)
                self.send(messageCan)

            elif message["cmd"] == "CAN":
                data = message["data"]
                commande = data["id"]
                byte = data[1:]
                messageCAN = can.Message(arbitration_id=commande, data=byte, is_extended_id=False)
                
                self.send(messageCAN)
            elif message["cmd"] == "resta":
                data = message["data"]
                # Format des données : restart (char)
                if data:
                    messageCan = can.Message(arbitration_id=0x34, data=[1], is_extended_id=False)
                self.send(messageCan)
                #print("BusCAN : Message de restart envoyé")
        except Exception as e:
            logging.error(f"Erreur lors du traitement du message serveur : {str(e)}")


    def run(self):
        print("BusCAN : Lancement du programme")
        logging.info("BusCAN : Lancement du programme")
        try:
            self.client.set_callback_stop(self.disconnect)
            self.client.set_callback(self.receive_to_server)
            self.client.connect()
            self.connect()
            print("BusCAN : Connecté au serveur")
            while self.is_connected:
                data = self.receive()
                if data is not None:
                    self.analyse_CAN(data)
            exit(0)
        except KeyboardInterrupt:
            self.client.send(self.client.create_message(0, "stop", {}))
            pass

if __name__ == "__main__":
    com = ComCAN('can0', 'socketcan')
    com.run()