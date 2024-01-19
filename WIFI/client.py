import socket
import threading
import pickle
import queue
import time

class Client:
    def __init__(self):
        self.objet_lidar = None
        self.objet_lidar_lock = threading.Lock()  # Verrou pour assurer une lecture/écriture sécurisée
        self.lidar_queue = queue.Queue()

    def receive_data(self, client_socket):
        while True:
            data_received = client_socket.recv(4096)
            if not data_received:
                break
            else:
                
                message = pickle.loads(data_received)
                print(message)

    def send_data(self, client_socket):
        while True:
            with self.objet_lidar_lock:
                # Accéder à self.objet_lidar en toute sécurité
                objet_lidar_local = self.objet_lidar

            # Faire quelque chose avec objet_lidar_local et l'envoyer au serveur
            message_to_send = pickle.dumps(objet_lidar_local)
            client_socket.sendall(message_to_send)
            time.sleep(0.1)

    def handle_lidar_data(self):
        while True:
            with self.objet_lidar_lock:
                # Accéder à self.objet_lidar en toute sécurité
                self.objet_lidar = self.lidar_queue.get()  # Attendre que des données soient disponibles
                # Faire quelque chose avec objet_lidar_local
                print("Objet reçu côté client:", self.objet_lidar)

# Initialiser le client
client = Client()
server_address = ('192.168.36.63', 5000)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(server_address)

# Démarrer les threads de communication
receive_thread = threading.Thread(target=client.receive_data, args=(client_socket,))
send_thread = threading.Thread(target=client.send_data, args=(client_socket,))
lidar_handler_thread = threading.Thread(target=client.handle_lidar_data)

receive_thread.start()
send_thread.start()
lidar_handler_thread.start()

receive_thread.join()
send_thread.join()
lidar_handler_thread.join()

# Fermer la connexion client
client_socket.close()
