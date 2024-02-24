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
        self.callback_stop = None
        self.test = _test
        self.stop_threads = False
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tasks = []
        self.send_list = []
        self.lock = threading.Lock()  # Verrou pour la synchronisation des threads
    
    def generate_message(self, _id_receiver, _cmd, _data):
        return {"id_s" : self.id_client, "id_r" : _id_receiver, "cmd" : _cmd, "data" : _data}

    def decode_stop(self, message):
        if message["cmd"] == "stop":
            self.stop()

    def receive_task(self):
        for _message in self.receive_messages(self.client_socket):
            for message in self.load_json(_message):
                self.callback(message)
    
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

    def send_data(self):
        i = 0
        while not self.stop_threads:
            message = self.generate_message(1, "data", i)
            i += 1
            self.add_to_send_list(message)
            print("Données envoyées au serveur ComWIFI:", message)
            while len(self.send_list) > 0 and not self.stop_threads:
                time.sleep(0.5)
    
    def send(self, message):
        messageJSON = json.dumps(message) + "\n"
        try :
            self.client_socket.sendall(messageJSON.encode())
        except ConnectionResetError:
            print("Erreur de connexion pour le client", self.id_client)
            self.stop_threads = True

    def send_task(self):
        while not self.stop_threads:
            for message in self.send_list:
                if self.stop_threads:
                    break
                self.send(message)
                self.send_list.remove(message)
    
    def add_to_send_list(self, message):
        with self.lock:
            self.send_list.append(message)

    def load_json(self, data):
        messages = []
        for message in data.split('\n'):
            if message:  # Ignore les lignes vides
                messages.append(json.loads(message))
        return messages

    def stop(self):
        if self.callback_stop is not None:
            self.callback_stop()
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

    def set_callback_stop(self, _callback):
        self.callback_stop = _callback
    
    def connect(self):
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
        message = self.generate_message(1, "init", None)
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
