import can
import os
from client import Client
import struct
import logging
import struct

class ComCAN:
    def __init__(self, channel, bustype):
        self.channel = channel
        self.bustype = bustype
        self.can = None
        self.is_connected = False
        self.client = Client("127.0.0.2", 22050, 2, self.disconnect)
        # Configuration du logger
        logging.basicConfig(filename='buscan.log', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S', format='%(asctime)s - %(levelname)s - %(message)s')

    def connect(self):
        try:
            if os.name == "posix":
                os.system('sudo ip link set can0 type can bitrate 1000000')
                os.system('sudo ifconfig can0 up')
                self.can = can.interface.Bus(channel=self.channel, bustype=self.bustype)
                self.is_connected = True
                logging.info("BusCAN : Connexion établie")
            else:
                logging.error("BusCAN : Le système d'exploitation n'est pas compatible avec le CAN")
        except Exception as e:
            logging.error(f"Erreur lors de la connexion : {str(e)}")

    def disconnect(self):
        try:
            self.can.shutdown()
            os.system('sudo ifconfig can0 down')
            self.is_connected = False
            logging.info("BusCAN : Connexion fermée")
        except Exception as e:
            logging.error(f"Erreur lors de la déconnexion : {str(e)}")

    def send(self, data):
        try:
            self.can.send(data)
            logging.info("Message envoyé sur le bus CAN")
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi du message : {str(e)}")
    
    def packed(self, id, data):
        dataCan = None
        try:
            for i in range(len(data)):
                if dataCan is None:
                    dataCan = struct.pack(data[i][1], data[i][0])
                else:
                    dataCan += struct.pack(data[i][1], data[i])
        except Exception as e:
            logging.error(f"Erreur lors de l'emballage des données : {str(e)}")
        return can.Message(arbitration_id=id, data=dataCan, is_extended_id=False)
    
    def receive(self):
        try:
            messageCan = self.can.recv(10.0)
            if messageCan is not None:
                return messageCan.arbitration_id, messageCan.dlc, messageCan.data
            else:
                return None
        except Exception as e:
            logging.error(f"Erreur lors de la réception du message : {str(e)}")
    
    def analyse_CAN(self, data):
        try:
            dataX = data[2]
            if data[0] == 0x28:
                x = struct.unpack('h', dataX[0:2])
                y = struct.unpack('h', dataX[2:4])
                theta = struct.unpack('h', dataX[4:6])
                self.client.add_to_send_list(self.client.create_message(0, "coord", {"x": x[0], "y": y[0], "theta": theta[0]}))
            elif data[0] == 0x203:
                print("message recu", dataX)
                # V_Batterie : ID batterie (char), V_Batterie (short)
                v_bat = struct.unpack('h', dataX[1:3])
                id_bat = struct.unpack('c', dataX[0:1])
                print("v_bat", v_bat, "id_bat", id_bat)
                if id_bat == 1:
                    self.client.add_to_send_list(self.client.create_message(0, "energie", {"Tension": {"Main" : v_bat}}))
                    print(f"V_Main : {v_bat}")
                elif id_bat == 2:
                    self.client.add_to_send_list(self.client.create_message(0, "energie", {"Tension": {"Bat1" : v_bat}}))
                    print(f"V_Batterie_1 : {v_bat}")
                elif id_bat == 3:
                    self.client.add_to_send_list(self.client.create_message(0, "energie", {"Tension": {"Bat2" : v_bat}}))
                    print(f"V_Batterie_2 : {v_bat}")
                elif id_bat == 4:
                    self.client.add_to_send_list(self.client.create_message(0, "energie", {"Tension": {"Bat3" : v_bat}}))
                    print(f"V_Batterie_3 : {v_bat}")
            elif data[0] == 0x204:
                # I_Batterie : ID batterie (char), I_Batterie (short)
                i_bat = struct.unpack('h', dataX[1:3])
                id_bat = struct.unpack('c', dataX[0:1])
                if id_bat == 1:
                    self.client.add_to_send_list(self.client.create_message(0, "energie", {"Courant": {"Bat1" : i_bat}}))
                    print(f"I_Batterie_1 : {i_bat}")
                elif id_bat == 2:
                    self.client.add_to_send_list(self.client.create_message(0, "energie", {"Courant": {"Bat2" : i_bat}}))
                    print(f"I_Batterie_2 : {i_bat}")
                elif id_bat == 3:
                    self.client.add_to_send_list(self.client.create_message(0, "energie", {"Courant": {"Bat3" : i_bat}}))
                    print(f"I_Batterie_3 : {i_bat}")
            elif data[0] == 0x205:
                # Switch_Batterie : ID batterie (char), Switch_Batterie (short)
                s_bat = struct.unpack('h', dataX[1:3])
                id_bat = struct.unpack('c', dataX[0:1])
                if id_bat == 1:
                    self.client.add_to_send_list(self.client.create_message(0, "energie", {"Switch": {"Bat1" : s_bat}}))
                    print(f"Switch_Batterie_1 : {s_bat}")
                elif id_bat == 2:
                    self.client.add_to_send_list(self.client.create_message(0, "energie", {"Switch": {"Bat2" : s_bat}}))
                    print(f"Switch_Batterie_2 : {s_bat}")
                elif id_bat == 3:
                    self.client.add_to_send_list(self.client.create_message(0, "energie", {"Switch": {"Bat3" : s_bat}}))
                    print(f"Switch_Batterie_3 : {s_bat}")
            else:
                logging.error(f"ID inconnu ; data : {data}")
                print(f"ID inconnu ; data : {data}")
        except Exception as e:
            logging.error(f"Erreur lors de l'analyse du message CAN : {str(e)}")

    def receive_to_server(self, message):
        try:
            if message["cmd"] == "stop":
                self.client.stop()
            elif message["cmd"] == "data":
                messageCAN = message["data"]
                self.send(messageCAN)
            elif message["cmd"] == "clic":
                data = message["data"]
                # Format des données : x (short), y (short), theta (short), sens(char)
                dataCan = struct.pack('h', data["x"]) + struct.pack('h', data["y"]) + struct.pack('h', data["theta"]) + struct.pack('c', data["sens"].encode())
                messageCan = can.Message(arbitration_id=0x20, data=dataCan, is_extended_id=False)
                self.send(messageCan)
                print("BusCAN : Message de clic envoyé", messageCan)
            elif message["cmd"] == "recal":
                data = message["data"]
                # Format des données : zone (char)
                dataCan = struct.pack('c', data["zone"])
                messageCan = can.Message(arbitration_id=0x24, data=dataCan, is_extended_id=False)
                #self.send(messageCan)
                print("BusCAN : Message de recalage envoyé")
            elif message["cmd"] == "desa":
                data = message["data"]
                # Format des données : desa (char)
                if data:
                    messageCan = can.Message(arbitration_id=0x1F7, data=[0], is_extended_id=False)
                    print("CAN : moteur désactivé")
                else:
                    messageCan = can.Message(arbitration_id=0x1F7, data=[1], is_extended_id=False)
                    print("CAN : moteur activé")
                self.send(messageCan)
            elif message["cmd"] == "CAN":
                data = message["data"]
                commande = data["id"]
                b1 = data["byte1"]
                b2 = data["byte2"]
                b3 = data["byte3"]
                messageCAN = can.Message(arbitration_id=commande, data=[b1,b2,b3], is_extended_id=False)
                
                self.send(messageCAN)
                print("Envoie demande energie", messageCAN)
            elif message["cmd"] == "resta":
                data = message["data"]
                # Format des données : restart (char)
                if data:
                    messageCan = can.Message(arbitration_id=0x34, data=[1], is_extended_id=False)
                self.send(messageCan)
                print("BusCAN : Message de restart envoyé")
        except Exception as e:
            logging.error(f"Erreur lors du traitement du message serveur : {str(e)}")


    def run(self):
        print("BusCAN : Lancement du programme")
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