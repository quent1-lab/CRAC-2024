import socket
import time
import threading

class Decodage:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stop_threads = False
        self.data = None
        self.task = []


    def connect(self):
        while not self.stop_threads:
            try:
                self.client_socket.connect((self.ip, self.port))
                break  # Si la connexion est réussie, sortir de la boucle
            except socket.error as e:
                time.sleep(2)  # Attendre 3 secondes avant de réessayer

    def new_task(self, data):
        # Créer une nouvelle tâche de traitement des données
        index = len(self.task)
        task = threading.Thread(target=self.decode_data, args=(data,index,))
        task.start()
        self.task.append([task,0])

    def decode_data(self, data,index):
        # Traiter les données reçues
        if data["cmd"] == "stop":
            self.stop_threads = True
        self.task[index][1] = 1

    def remove_task(self):
        # Supprimer une tâche de traitement des données
        for task in self.task:
            if task[1] == 1:
                task[0].join(timeout=0.2)  # Attendre le thread pendant 0.2 seconde
                if not task[0].is_alive():  # Si le thread est terminé, le retirer de la liste
                    self.task.remove(task)

    def close(self):
        self.client_socket.close()

    def __del__(self):
        self.client_socket.close()
    
    def run(self):
        self.connect()
        while not self.stop_threads:
            self.remove_task()

class Encodage:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen()
        self.connection, self.address = self.server_socket.accept()

    def send_data(self, message):
        self.connection.sendall(message.encode())

    def close(self):
        self.connection.close()
        self.server_socket.close()

if __name__ == "__main__":
    # Utilisation de la classe
    decodage = Decodage('127.0.0.1', 22050)
    decodage.run()  