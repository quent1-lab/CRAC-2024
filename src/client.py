import socket
import time
import threading
import json
from queue import Queue, Empty
import logging

class ClientException(Exception):
    """Classe pour les exceptions du client"""

# Configuration du logger
#logging.basicConfig(filename='client.log', level=logging.INFO,datefmt='%d/%m/%Y %H:%M:%S', format='%(asctime)s - %(levelname)s - %(message)s')

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
        self.send_queue = Queue()
        self.lock = threading.Lock()  # Verrou pour la synchronisation des threads

        self.client_names = ["Broadcast", "Serveur", "BusCAN", "Lidar","","","","","","IHM_R","IHM"]
        if _id_client == 2205:
            self.client_name = "Erreur"
        else:
            self.client_name = self.client_names[_id_client]
    
    def create_message(self, _id_receiver, _cmd, _data):
        return {"id_s" : self.id_client, "id_r" : _id_receiver, "cmd" : _cmd, "data" : _data}

    def decode_stop(self, message):
        if message["cmd"] == "stop":
            self.stop()
    
    def receive_messages(self, socket):
        buffer = ""
        while not self.stop_threads:
            try:
                data = socket.recv(4096)
                if not data:
                    break
                buffer += data.decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    yield line
            except ConnectionResetError:
                break

    def receive_task(self):
        try:
            while not self.stop_threads:
                for _message in self.receive_messages(self.client_socket):
                    for message in self.load_json(_message):
                        self.callback(message)
        except Exception as e:
            logging.error(f"CLIENT : Une erreur est survenue lors de la réception des messages pour le client {self.client_name} : {str(e)}")

    def send_task(self):
        while not self.stop_threads:
            try:  
                message = self.send_queue.get(timeout=0.1)
                self.send(message)
            except Empty:
                pass
            except Exception as e:
                logging.error(f"CLIENT : Une erreur est survenue lors de l'envoi des messages pour le client {self.client_name} : {str(e)}")

    def add_to_send_list(self, message):
        self.send_queue.put(message)

    def stop(self):
        if self.callback_stop is not None:
            self.callback_stop()
        self.stop_threads = True
        logging.info(f"CLIENT : Arrêt de la queue pour le client {self.client_name}")
        # Vider la queue
        while not self.send_queue.empty():
            try:
                self.send_queue.get_nowait()
                self.send_queue.task_done()
            except Empty:
                break
        logging.info(f"CLIENT : Arrêt des threads pour le client {self.client_name}")
        close_thread = threading.Thread(target=self.close_connection)
        close_thread.start()
        close_thread.join()
        logging.info(f"CLIENT : Arrêt de la connexion pour le client {self.client_name}")

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
                logging.info(f"Données envoyées au serveur ComWIFI par le client {self.client_name}: {message}")
                time.sleep(0.5)
        except Exception as e:
            logging.error(f"CLIENT : Une erreur est survenue lors de l'envoi des données pour le client {self.client_name} : {str(e)}")
    
    def send(self, message):
        try:
            messageJSON = json.dumps(message) + "\n"
            with self.lock:
                self.client_socket.sendall(messageJSON.encode())
        except ConnectionResetError as e:
            logging.error(f"CLIENT : Erreur de connexion pour le client {self.client_name} : {str(e)}")
        except Exception as e:
            logging.error(f"CLIENT : Une erreur est survenue lors de l'envoi d'un message pour le client {self.client_name} : {str(e)}")
    
    def load_json(self, data):
        try:
            messages = []
            for message in data.split('\n'):
                if message:  # Ignore les lignes vides
                    messages.append(json.loads(message))
            return messages
        except json.JSONDecodeError as e:
            logging.error(f"CLIENT : Erreur de décodage JSON pour le client {self.client_name} : {str(e)}")
    
    def close_connection(self):
        try:
            self.tasks[1].join()
    
            self.client_socket.close()
            logging.info(f"CLIENT : Connexion fermée pour le client {self.client_name}")
        except Exception as e:
            logging.error(f"CLIENT : Une erreur est survenue lors de la fermeture de la connexion pour le client {self.client_name} : {str(e)}")
    
    def set_callback(self, _callback):
        self.callback = _callback

    def set_callback_stop(self, _callback):
        self.callback_stop = _callback
    
    def connect(self):
        try:
            logging.info(f"CLIENT : Connexion du client {self.client_name} au serveur")
            for i in range(3):
                try:
                    self.client_socket.connect((self.ip, self.port))
                    break  # Si la connexion est réussie, sortir de la boucle
                except socket.error as e:
                    logging.error(f"CLIENT : Erreur de connexion pour {self.client_name} au serveur : {str(e)}")
                    time.sleep(2)  # Attendre 2 secondes avant de réessayer
            else:
                logging.error(f"CLIENT : Nombre maximum de tentatives de connexion atteint pour le client {self.client_name}")
                raise ClientException(f"CLIENT : Nombre maximum de tentatives de connexion atteint pour le client {self.client_name}")

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
            logging.error(f"CLIENT : Une erreur est survenue lors de la connexion pour le client {self.client_name} : {str(e)}")

if __name__ == "__main__":
    try:
        # Utilisation de la classe
        client = Client('127.0.0.1', 22050, 1, None, True)
        client.connect()
    except ClientException as e:
        logging.error(f"CLIENT : {str(e)}")
