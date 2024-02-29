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
            messageCan = self.can.recv(10.0)
            return messageCan.arbitration_id, messageCan.dlc, messageCan.data
        except Exception as e:
            pass
    
    def analyse_CAN(self, data):
        # Les données du message CAN
        # Décoder les 4 premiers bytes en un entier non signé
        if data[0] == 0x28:
            # type data : bytearray(b'\x00\x00\x00\x00\x00\x00') -> 0-2 : (int)x, 2-4 : (int)y, 4-6 : (in)theta 
            x = struct.unpack('h', data[0:2])
            y = struct.unpack('h', data[2:4])
            theta = struct.unpack('h', data[4:6])
            print("BusCAN : x = ", x, "y = ", y, "theta = ", theta)
            self.client.add_to_send_list(self.client.create_message(0, "coord", {"x": x, "y": y, "theta": theta}))

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
                
        except KeyboardInterrupt:
            self.client_socket.send(self.client.create_message(0, "stop", {}))
            pass

if __name__ == "__main__":
    com = ComCAN('can0', 'socketcan')
    com.run()