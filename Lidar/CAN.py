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
    
    def packed(self, id, data):
        # id : int, data : [(int, str)] -> [(data, format)]
        dataCan = None
        for i in range(len(data)):
            if dataCan is None:
                dataCan = struct.pack(data[i][1], data[i][0])
            else:
                dataCan += struct.pack(data[i][1], data[i])
        return can.Message(arbitration_id = id, data = dataCan, is_extended_id = False)
    
    def receive(self):
        try:
            messageCan = self.can.recv(10.0)
            if messageCan is not None:
                return messageCan.arbitration_id, messageCan.dlc, messageCan.data
            else:
                return None
        except Exception as e:
            pass
    
    def analyse_CAN(self, data):
        if data[0] == 0x28:
            # type data : bytearray(b'\x00\x00\x00\x00\x00\x00') -> 0-2 : (int)x, 2-4 : (int)y, 4-6 : (in)theta 
            x = struct.unpack('h', data[0:2])
            y = struct.unpack('h', data[2:4])
            theta = struct.unpack('h', data[4:6])
            print("BusCAN : x = ", x, "y = ", y, "theta = ", theta)
            self.client.add_to_send_list(self.client.create_message(0, "coord", {"x": x, "y": y, "theta": theta}))

    def receive_to_server(self, message):
        if message["cmd"] == "stop":
            self.client.stop()
        elif message["cmd"] == "data":
            messageCAN = message["data"]
            self.send(messageCAN)
        elif message["cmd"] == "clic":
            # type data à envoyer : short x, short y, short theta, char sens
            data = message["data"]
            dataCan = struct.pack('h', int(data["x"])) + struct.pack('h', int(data["y"])) + struct.pack('h', int(data["theta"])) + struct.pack('c', data["sens"].encode())
            messageCan = can.Message(arbitration_id = 0x28, data = dataCan, is_extended_id = False)
            self.send(messageCan)

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
            
            exit(0)
                
        except KeyboardInterrupt:
            self.client.send(self.client.create_message(0, "stop", {}))
            pass

if __name__ == "__main__":
    com = ComCAN('can0', 'socketcan')
    com.run()