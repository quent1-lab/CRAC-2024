"""import socket
import time
import threading
import json

class Client:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.stop_threads = False
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data = None

    def receive_data(self):
        while not self.stop_threads:
            data_received = self.client_socket.recv(2048)
            for message in self.load_json(data_received.decode()):
                if message["cmd"] == "stop":
                    self.stop_threads = True
                    print("Arrêt de la connexion")
                    break
                if message["cmd"] == "data":
                    print("Données reçues de", message["id_sender"],":", message["data"])

    def send_data(self):
        i = 0
        message = {"id_sender" : 3, "id_receiver" : 1, "cmd" : "init", "data" : None}
        self.send(message)
        while not self.stop_threads:
            message = {"id_sender" : 3, "id_receiver" : 2, "cmd" : "data", "data" : i}
            i += 1
            self.send(message)
            print("Données envoyées au serveur ComWIFI:", message)
            time.sleep(5)  # Attendre une seconde avant d'envoyer la prochaine donnée
    
    def send(self, message):
        messageJSON = json.dumps(message)
        try :
            self.client_socket.sendall(messageJSON.encode())
        except ConnectionResetError:
            print("Erreur de connexion")
            self.stop_threads = True
    
    def load_json(self, data):
        messages = []
        if data:  # Vérifier que les données ne sont pas vides
            if data.count('}{') > 0:
                data = data.split('}{')
                for i in range(1, len(data) - 1):
                    data[i] = '{' + data[i] + '}'
                data[0] += '}'
                data[-1] = '{' + data[-1]
            else:
                data = [data]
            for message in data:
                messages.append(json.loads(message))
        return messages

    def connect(self):
        while True:
            try:
                self.client_socket.connect((self.ip, self.port))
                break  # Si la connexion est réussie, sortir de la boucle
            except socket.error as e:
                time.sleep(2)  # Attendre 3 secondes avant de réessayer

        receive_thread = threading.Thread(target=self.receive_data)
        send_thread = threading.Thread(target=self.send_data)

        receive_thread.start()
        send_thread.start()

        while not self.stop_threads:
            pass

        receive_thread.join()
        send_thread.join()
        self.client_socket.close()
        print("Connexion terminée")
                

    def get_data(self):
        return self.data

# Utilisation de la classe
client = Client('127.0.0.1', 22050)
client.connect()"""

from client import *

def decode_client1(message):
    if message["cmd"] == "stop":
        client1.stop()
    else:
        if message["data"] != None:
            print("Données reçues de", message["id_sender"],":", message["data"])

def decode_client2(message):
    if message["cmd"] == "stop":
        client2.stop()
    else:
        if message["data"] != None:
            print("Données reçues de", message["id_sender"],":", message["data"])

# Utilisation de la classe
client1 = Client('127.0.0.1', 22050,2, decode_client1, True)
client2 = Client('127.0.0.2', 22050,3, decode_client2, True)

client1_thread = threading.Thread(target=client1.connect)
client2_thread = threading.Thread(target=client2.connect)

client1_thread.start()
client2_thread.start()

client1_thread.join()
client2_thread.join()
print("Programme terminé")