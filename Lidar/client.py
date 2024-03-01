import socket
import time
import threading
import json

class ClientException(Exception):
    '''Classe d'exception de base pour le client'''

class Client:
    def __init__(self, _ip, _port, _id_client=2205, _callback=None, _test=False):
        self.ip = _ip
        self.port = _port
        self.id_client = _id_client
        self.callback = _callback if _callback is not None else self.decode_stop
        self.callback_stop = None
        self.test = _test
        self.stop_threads = False
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tasks = []
        self.send_list = []
        self.lock = threading.Lock()  # Verrou pour la synchronisation des threads
    
    def create_message(self, _id_receiver, _cmd, _data):
        return {"id_s" : self.id_client, "id_r" : _id_receiver, "cmd" : _cmd, "data" : _data}

    def decode_stop(self, message):
        if message["cmd"] == "stop":
            self.stop()
    
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

    def receive_task(self):
        try:
            while True:
                with self.lock:
                    if self.stop_threads:
                        break
                for _message in self.receive_messages(self.client_socket):
                    for message in self.load_json(_message):
                        self.callback(message)
        except Exception as e:
            raise ClientException(f"Erreur lors de la réception des messages : {e}")

    def send_data(self):
        try:
            i = 0
            while True:
                with self.lock:
                    if self.stop_threads:
                        break
                message = self.create_message(1, "data", i)
                i += 1
                self.add_to_send_list(message)
                print("Données envoyées au serveur ComWIFI:", message)
                while True:
                    with self.lock:
                        if len(self.send_list) > 0 and not self.stop_threads:
                            break
                    time.sleep(0.5)
        except Exception as e:
            raise ClientException(f"Erreur lors de l'envoi des données : {e}")
    
    def send(self, message):
        try:
            messageJSON = json.dumps(message) + "\n"
            with self.lock:
                self.client_socket.sendall(messageJSON.encode())
        except Exception as e:
            raise ClientException(f"Erreur lors de l'envoi du message : {e}")
    
    def send_task(self):
        try:
            while True:
                with self.lock:
                    if self.stop_threads:
                        break
                for message in self.send_list:
                    self.send(message)
                    self.send_list.remove(message)
                    time.sleep(0.01)
        except Exception as e:
            raise ClientException(f"Erreur lors de l'envoi des tâches : {e}")
    
    def add_to_send_list(self, message):
        with self.lock:
            self.send_list.append(message)

    def load_json(self, data):
        try:
            messages = []
            for message in data.split('\n'):
                if message:  # Ignore les lignes vides
                    messages.append(json.loads(message))
            return messages
        except Exception as e:
            raise ClientException(f"Erreur lors du chargement du JSON : {e}")

    def stop(self):
        try:
            if self.callback_stop is not None:
                self.callback_stop()
            self.stop_threads = True
            close_trhead = threading.Thread(target=self.close_connection)
            close_trhead.start()
            print("Arrêt de la connexion pour le client", {self.id_client})
        except Exception as e:
            raise ClientException(f"Erreur lors de l'arrêt du client : {e}")
    
    def close_connection(self):
        try:
            for task in self.tasks:
                task.join()
            self.client_socket.close()
            print("Connexion fermée pour le client", {self.id_client})
        except Exception as e:
            raise ClientException(f"Erreur lors de la fermeture de la connexion : {e}")
    
    def set_callback(self, _callback):
        self.callback = _callback

    def set_callback_stop(self, _callback):
        self.callback_stop = _callback
    
    def connect(self):
        try:
            print("Connexion du client", self.id_client, "au serveur ComWIFI")
            i = 0
            while True:
                i += 1
                try:
                    self.client_socket.connect((self.ip, self.port))
                    break  # Si la connexion est réussie, sortir de la boucle
                except socket.error as e:
                    print("Erreur de connexion pour le client", self.id_client, "au serveur ComWIFI")
                    print("Réessai de la connexion dans 2 secondes")
                    if i >= 3:
                        print("Nombre maximum de tentatives de connexion atteint")
                        raise e
                    time.sleep(3)  # Attendre 3 secondes avant de réessayer

            if self.id_client is None:
                self.id_client = 2205
            message = self.create_message(1, "init", None)
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
        except Exception as e:
            raise ClientException(f"Erreur lors de la connexion du client : {e}")

if __name__ == "__main__":
    # Utilisation de la classe
    try:
        client = Client('127.0.0.1', 22050)
        client.connect()
    except ClientException as e:
        print(f"Erreur lors de l'utilisation du client : {e}")
