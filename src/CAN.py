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
            time.sleep(0.001)
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
                
            elif data[0] in self.liste_ack or data[0] == 0x114 or data[0] == 0x115 or data[0] == 0x116 or data[0] == 0x117:
                # Message d'acquittement
                self.client.add_to_send_list(self.client.create_message(0, "akn", {"id": data[0]}))
                
                """elif data[0] == 0x114:
                # Fin d'instruction de positionnement
                self.client.add_to_send_list(self.client.create_message(0, "akn_m", None))"""
            
            elif data[0] == 0x1A0 or data[0] == 0x1A1:
                id_action = dataX[0]
                logging.info(f"BusCAN : ID action : {id_action}")
                if id_action == 5:
                    #self.client.add_to_send_list(self.client.create_message(9, "get_pos", {"id_herk": dataX[1], "pos": struct.unpack('h', dataX[1:3])}))
                    pass
        
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
                
            elif data[0] == 0x207:
                # Arret d'urgence
                etat = dataX[0]
                self.client.add_to_send_list(self.client.create_message(0, "ARU", {"etat": etat}))

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

            elif message["cmd"] == "recalage":
                data = message["data"]
                # Format des données : distance (short), mode (entier non signé 1 octet), recalage (short)
                dataCan = struct.pack('h', data["distance"]) + struct.pack('B', data["mode"]) + struct.pack('h', data["recalage"]) + struct.pack('Bbb', 0, 0, 0)
                messageCan = can.Message(arbitration_id=0x24, data=dataCan, is_extended_id=False)
                self.send(messageCan)
            
            elif message["cmd"] == "rotation":
                data = message["data"]
                # Format des données : angle (short)
                dataCan = struct.pack('h', data["angle"])
                messageCan = can.Message(arbitration_id=0x23, data=dataCan, is_extended_id=False)
                self.send(messageCan)
            
            elif message["cmd"] == "deplacement":
                data = message["data"]
                # Format des données : distance (short), mode (entier non signé 1 octet)
                dataCan = struct.pack('h', data["distance"]) + struct.pack('B', 0) + struct.pack('hBbb', 0, 0, 0, 0)
                messageCan = can.Message(arbitration_id=0x24, data=dataCan, is_extended_id=False)
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
                
                if type(commande) == str:
                    if commande[:2] != "0x":
                        commande = "0x" + commande
                    commande = int(commande, 16)
                
                if commande == 0x1FC or commande == 0x1FD:
                    # Format des données : data 8 octets
                    byte = data["byte1"]
                    dataCan = struct.pack('d', byte)
                    messageCan = can.Message(arbitration_id=commande, data=dataCan, is_extended_id=False)
                elif commande == 0x030:
                    id = data["byte1"]
                    # Format des données : id (B), x (short), y (short), theta (short)
                else:
                    # byte correspond à la liste des données à envoyer
                    byte = list(data.items())[1:]  # Convertir le dictionnaire en liste et supprimer la première valeur
                    byte_values = [b[1] for b in byte]  # Extraire les valeurs de la liste
                    messageCAN = can.Message(arbitration_id=commande, data=byte_values, is_extended_id=False)
                
                self.send(messageCAN)
            elif message["cmd"] == "resta":
                data = message["data"]
                # Format des données : restart (char)
                if data:
                    messageCan = can.Message(arbitration_id=0x34, data=[1], is_extended_id=False)
                self.send(messageCan)
                #print("BusCAN : Message de restart envoyé")
            
            elif message["cmd"] == "set_odo":
                x_y_t = message["data"]
                # Format des données : x (short), y (short), theta (short)
                logging.info(f"BusCAN : x_y_t : {x_y_t}")
                dataCan = struct.pack('h', x_y_t["x"]) + struct.pack('h', x_y_t["y"]) + struct.pack('h', x_y_t["theta"])
                messageCan = can.Message(arbitration_id=0x30, data=dataCan, is_extended_id=False)
                self.send(messageCan)
            
            elif message["cmd"] == "set_vit":
                data = message["data"]
                # Format des données : vitesse (short)
                dataCan = struct.pack('h', data["vitesse"])
                messageCan = can.Message(arbitration_id=0x29, data=dataCan, is_extended_id=False)
                self.send(messageCan)

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