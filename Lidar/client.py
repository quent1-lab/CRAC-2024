import socket
import time
import threading
import json

class Client:
    def __init__(self, _ip, _port, _id_client=2205, _callback=None, _test=False):
        self.ip = _ip
        self.port = _port
        self.id_client = _id_client
        self.callback = _callback if _callback is not None else self.decode_stop
        self.test = _test
        self.stop_threads = False
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tasks = []
        self.send_list = []
    
    def decode_stop(self, message):
        if message["cmd"] == "stop":
            self.stop()

    def receive_task(self):
        while not self.stop_threads:
            data_received = self.client_socket.recv(2048)
            for message in self.load_json(data_received.decode()):
                self.callback(message)

    def send_data(self):
        i = 0
        while not self.stop_threads:
            message = {"id_sender" : self.id_client, "id_receiver" : 3, "cmd" : "data", "data" : i}
            i += 1
            self.send(message)
            print("Données envoyées au serveur ComWIFI:", message)
            time.sleep(5)  # Attendre une seconde avant d'envoyer la prochaine donnée
    
    def send(self, message):
        messageJSON = json.dumps(message)
        try :
            self.client_socket.sendall(messageJSON.encode())
        except ConnectionResetError:
            print("Erreur de connexion pour le client", self.id_client)
            self.stop_threads = True

    def send_task(self):
        while not self.stop_threads:
            for message in self.send_list:
                self.send(message)
    
    def add_to_send_list(self, message):
        self.send_list.append(message)

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

    def stop(self):
        self.stop_threads = True
        close_trhead = threading.Thread(target=self.close_connection)
        close_trhead.start()
        print("Arrêt de la connexion pour le client", {self.id_client})
    
    def close_connection(self):
        for task in self.tasks:
            task.join()
        self.client_socket.close()
        print("Connexion fermée pour le client", {self.id_client})
    
    def set_callback(self, _callback):
        self.callback = _callback

    def connect(self):
        print("Connexion du client", self.id_client, "au serveur ComWIFI")
        while True:
            try:
                self.client_socket.connect((self.ip, self.port))
                break  # Si la connexion est réussie, sortir de la boucle
            except socket.error as e:
                print("Erreur de connexion pour le client", self.id_client, "au serveur ComWIFI")
                print("Réessai de la connexion dans 2 secondes")
                time.sleep(2)  # Attendre 3 secondes avant de réessayer

        if self.id_client is None:
            self.id_client = 2205
        message = {"id_sender" : self.id_client, "id_receiver" : 1, "cmd" : "init", "data" : None}
        self.send(message)

        receive_thread = threading.Thread(target=self.receive_task)
        receive_thread.start()

        if self.test:
            send_thread = threading.Thread(target=self.send_data)
            send_thread.start()
        else:
            send_thread = threading.Thread(target=self.send_task)
            send_thread.start()
        
        self.tasks.append(receive_thread)
        self.tasks.append(send_thread)

if __name__ == "__main__":
    # Utilisation de la classe
    client = Client('127.0.0.1', 22050)
    client.connect()