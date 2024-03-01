import socket
import threading
import json

class ServeurException(Exception):
    """Classe pour les exceptions du serveur"""

class Serveur:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []  # Liste pour stocker les informations sur les clients (socket, address, ID)
        self.tasks = []
        self.stop_threads = False
        self.lock = threading.Lock()

    def handle_client(self, connection, address):
        print(f'BusCOM : Connecté à {address}')
        while not self.stop_threads:
            try:
                for data in self.receive_messages(connection):
                    messages = self.load_json(data)
                    with self.lock:
                        for message in messages:
                            self.handle_message(message, connection)
            except ConnectionResetError:
                break

        """print(f"BusCOM : Déconnexion de {address}")
        connection.close()
        with self.lock:
            self.clients = [client for client in self.clients if client[0] != connection]"""

    def receive_messages(self, socket):
        buffer = ""
        while not self.stop_threads:
            data = socket.recv(4096)
            if not data:
                break
            buffer += data.decode()
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                yield line

    def handle_connection(self):
        while not self.stop_threads:
            try:
                connection, address = self.server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(connection, address))
                thread.start()
                with self.lock:
                    self.clients.append([connection, address, None])
                    self.tasks.append(thread)
                print(f"BusCOM : Connexion active : {threading.active_count()}")
            except socket.timeout:
                pass

    def send(self, client_socket, message):
        messageJSON = json.dumps(message) + "\n"
        try:
            client_socket.sendall(messageJSON.encode())
        except ConnectionResetError:
            raise ServeurException("BusCOM : Erreur de connexion")
    
    def send_stop(self):
        message = {"id_s" : 0, "id_r" : 0, "cmd" : "stop", "data" : ""}
        for client in self.clients:
            self.send(client[0], message)
    
    def deconnection(self):
        self.stop_threads = True
        self.send_stop()
        for task in self.tasks:
            if task.is_alive():  # Check if the thread is alive before joining
                task.join()
        for client in self.clients:
            if client[0].fileno() != -1:  # Check if the socket is open before closing
                client[0].close()
        if self.server_socket.fileno() != -1:  # Check if the server socket is open before closing
            self.server_socket.close()


    def load_json(self, data):
        messages = []
        for message in data.split('\n'):
            if message:  # ignore empty lines
                try:
                    messages.append(json.loads(message))
                except json.JSONDecodeError:
                    print("BusCOM : Erreur de décodage JSON")
        return messages

    def handle_message(self, message, connection):
        if message["cmd"] == "stop":
            self.stop_threads = True
        elif message["cmd"] == "init":
            client_id = message["id_s"]
            for client in self.clients:
                if client[0] == connection:
                    client[2] = client_id
                    break
        else:
            if message["id_r"] == 0:
                # Envoie les coordonnées à tous les clients
                for client in self.clients:
                    if client[0] != connection:
                        self.send(client[0], message)
            else:
                # Envoie les coordonnées à un client spécifique
                for client in self.clients:
                    if client[2] == message["id_r"]:
                        self.send(client[0], message)

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.server_socket:
            print("BusCOM : Démarrage du serveur...")
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Permet de réutiliser le port après un arrêt brutal
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            self.server_socket.settimeout(1)

            connection_thread = threading.Thread(target=self.handle_connection)
            connection_thread.start()

            while not self.stop_threads:
                pass

            print("BusCOM : Arrêt des connexions...")
            self.deconnection()
            print("BusCOM : Serveur arrêté")

if __name__ == "__main__":
    serveur = Serveur("0.0.0.0",22050)
    try:
        serveur.start()
    except KeyboardInterrupt:
        serveur.stop_threads = True
    except ServeurException as e:
        print(e)
        serveur.deconnection()
