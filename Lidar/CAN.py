import can
import os
from client import Client

class ComCAN:
    def __init__(self, channel, bustype):
        self.channel = channel
        self.bustype = bustype
        self.can = None
        self.is_connected = False
        client = Client("127.0.0.2", 22050)
        client.connect()

    def connect(self):
        #Vérifie si le système d'exploitation est Linux
        #Si oui, on lance les commandes pour configurer le CAN
        try:
            if os.name == "posix":
                os.system('sudo ip link set can0 type can bitrate 1000000')
                os.system('sudo ifconfig can0 up')
                self.can = can.interface.Bus(channel = self.channel, bustype = self.bustype)
                self.is_connected = True
            else:
                print("Le système d'exploitation n'est pas compatible avec le CAN")
        except Exception as e:
            pass

    def disconnect(self):
        try:
            self.can.shutdown()
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

    def run(self):
        try:
            self.connect()
            while True:
                data = self.receive()
                print(data)
                
        except KeyboardInterrupt:
            self.disconnect()
            pass

if __name__ == "__main__":
    com = ComCAN('can0', 'socketcan')
    com.run()