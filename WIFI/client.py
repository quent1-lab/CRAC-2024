import socket
import time
import threading

class Client:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.stop_threads = True
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.client_socket.settimeout(1)  # Définir un délai d'attente de 1 seconde
        self.data = None

    def receive_data(self):
        while self.stop_threads:
            data_received = self.client_socket.recv(2048)
            data = data_received.decode()
            if data["cmd"] == "stop":
                self.stop_threads = False
                break

    def send_data(self):
        i = 0
        while self.stop_threads:
            message = "programme client 1: " + str(i)
            i += 1
            self.client_socket.sendall(message.encode())
            print("Données envoyées au serveur ComWIFI:", message)
            time.sleep(1)  # Attendre une seconde avant d'envoyer la prochaine donnée

    def connect(self):
        while True:
            try:
                self.client_socket.connect((self.ip, self.port))
                break  # Si la connexion est réussie, sortir de la boucle
            except socket.error as e:
                time.sleep(3)  # Attendre 3 secondes avant de réessayer

        receive_thread = threading.Thread(target=self.receive_data)
        send_thread = threading.Thread(target=self.send_data)

        receive_thread.start()
        send_thread.start()

        while self.stop_threads:
            if not self.stop_threads:
                self.client_socket.close()
                receive_thread.join()
                send_thread.join()
                break
        exit()

    def get_data(self):
        return self.data

# Utilisation de la classe
client = Client('192.168.22.100', 22050)
client.connect()