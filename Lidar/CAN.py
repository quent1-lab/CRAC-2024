import can
import os
from client import Client
import struct

class ComCAN:
    def __init__(self, channel, bustype):
        self.channel = channel
        self.bustype = bustype
        self.can = None
        self.is_connected = False
        self.client = Client("127.0.0.2", 22050, 2, self.disconnect)

    def connect(self):
        #Vérifie si le système d'exploitation est Linux
        #Si oui, on lance les commandes pour configurer le CAN
        try:
            if os.name == "posix":
                os.system('sudo ip link set can0 type can bitrate 1000000')
                os.system('sudo ifconfig can0 up')
                self.can = can.interface.Bus(channel = self.channel, bustype = self.bustype)
                self.is_connected = True
                print("BusCAN : Connexion établie")
            else:
                print("BusCAN : Le système d'exploitation n'est pas compatible avec le CAN")
        except Exception as e:
            pass

    def disconnect(self):
        try:
            self.can.shutdown()
            self.is_connected = False
        except Exception as e:
            pass

    def send(self, data):
        try:
            self.can.send(data)
        except Exception as e:
            pass

    def receive(self):
        try:
            return self.can.recv(10.0)
        except Exception as e:
            pass
    
    def analyse_CAN(self, data):
        # Les données du message CAN
        data = bytes([0x00, 0x00, 0x00, 0x00, 0xfe, 0xff])

        # Décoder les 4 premiers bytes en un entier non signé
        value1 = struct.unpack('>I', data[:4])[0]

        # Décoder les 2 derniers bytes en un court entier non signé
        value2 = struct.unpack('>H', data[4:])[0]
        print(value1, value2)
        """if data[0] == hex(28):
            x = int(data[1:3], 16)
            y = int(data[3:5], 16)
            theta = int(data[5:7], 16)
            print("BusCAN : x = ", x, "y = ", y, "theta = ", theta)
            #self.client.add_to_send_list(self.client.create_message(0, "coord", {"x": x, "y": y, "theta": theta}))"""

    def receive_to_server(self, message):
        if message["cmd"] == "stop":
            self.client_socket.stop()
        elif message["cmd"] == "data":
            messageCAN = message["data"]
            self.send(messageCAN)

    def run(self):
        self.client.set_callback_stop(self.disconnect)
        self.client.set_callback(self.receive_to_server)
        try:
            self.client.connect()
            self.connect()
            while self.is_connected:
                data = self.receive()
                if data is not None:
                    self.analyse_CAN(data)
                    #print("BusCAN :",data)
                
        except KeyboardInterrupt:
            self.disconnect()
            pass

if __name__ == "__main__":
    com = ComCAN('can0', 'socketcan')
    com.run()