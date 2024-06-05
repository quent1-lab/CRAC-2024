import socket
import threading
import json
import errno
import logging
import time

# Configuration du logger
logging.basicConfig(filename='buscom.log', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S', format='%(asctime)s - %(levelname)s - %(message)s')

class ServeurException(Exception):
    """Classe pour les exceptions du serveur"""

class Serveur:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.authenticated_clients = []  # Liste pour les clients authentifiés
        self.pending_clients = []  # Liste pour les clients non authentifiés
        self.client_names = ["Broadcast", "Serveur", "BusCAN", "Lidar","Strategie","","","","PAMI","IHM_R","IHM"]

        self.tasks = []
        self.stop_threads = False
        self.lock = threading.Lock()

    def handle_client(self, connection, address):
        logging.info(f'BusCOM : Connecté à {address}')
        print(f'BusCOM : Connecté à {address}')
        while not self.stop_threads:
            try:
                for data in self.receive_messages(connection):
                    messages = self.load_json(data)
                    with self.lock:
                        for message in messages:
                            self.handle_message(message, connection)
            except Exception as e:
                logging.error(f"Erreur lors de la manipulation du client : {str(e)}")
                break
            time.sleep(0.01)
        if not self.stop_threads:
            try:
                self.deconnect_client(connection, address)
            except:
                pass
            print(f"BusCOM : Déconnecté de ({address})")
            logging.info(f"BusCOM : Déconnecté de ({address})")

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
                time.sleep(0.01)
            except ConnectionResetError:
                logging.error("BusCOM : Erreur de connexion", exc_info=True)
                break
            except Exception as e:
                logging.error(f"BusCOM : Erreur de réception : {str(e)}")
                break

    def handle_connection(self):
        while not self.stop_threads:
            try:
                connection, address = self.server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(connection, address))
                thread.start()
                with self.lock:
                    self.pending_clients.append([connection, address,0])
                    self.tasks.append(thread)
            except socket.timeout:
                pass
            except OSError as e:
                if e.errno == errno.EBADF:
                    logging.info("BusCOM : Arrêt des connexions, erreur de socket")
                    break
                else:
                    logging.error("BusCOM : Erreur de connexion", exc_info=True)
            time.sleep(0.01)

    def send(self, client_socket, message):
        messageJSON = json.dumps(message) + "\n"
        try:
            client_socket.sendall(messageJSON.encode())
        except (ConnectionResetError, BrokenPipeError):
            logging.error("BusCOM : Erreur de connexion", exc_info=True)
            raise ServeurException("BusCOM : Erreur de connexion")
        except Exception as e:
            logging.error("BusCOM : Erreur d'envoi", exc_info=True)
            raise ServeurException("BusCOM : Erreur d'envoi")
    
    def send_stop(self):
        message = {"id_s" : 0, "id_r" : 0, "cmd" : "stop", "data" : ""}
        for client in self.authenticated_clients:
            try:
                self.send(client[0], message)
            except:
                pass
    
    def deconnection(self):
        self.stop_threads = True
        self.send_stop()
        for task in self.tasks:
            try:
                if task.is_alive():
                    task.join()
            except:
                pass
        for client in self.authenticated_clients + self.pending_clients:
            try:
                if client[0].fileno() != -1:
                    client[0].close()
            except:
                pass
            
        if self.server_socket.fileno() != -1:
            self.server_socket.close()
        logging.info("BusCOM : Serveur arrêté")
        print("BusCOM : Serveur arrêté")
    
    def deconnect_client(self, connection, address):
        logging.info(f"BusCOM : Déconnexion de {address}")
        with self.lock:
            self.authenticated_clients = [client for client in self.authenticated_clients if client[0] != connection]
            self.pending_clients = [client for client in self.pending_clients if client[0] != connection]
        try:
            connection.close()
        except Exception as e:
            logging.error(f"BusCOM : Erreur lors de la déconnexion de {address} : {str(e)}")
        
    def load_json(self, data):
        messages = []
        for message in data.split('\n'):
            if message:
                try:
                    messages.append(json.loads(message))
                except json.JSONDecodeError:
                    logging.error("BusCOM : Erreur de décodage JSON", exc_info=True)
        return messages

    def init_connection(self, connection, id):
        for client in self.pending_clients:
            if client[0] == connection:
                client[2] = id
                self.authenticated_clients.append(client)
                self.pending_clients.remove(client)
                logging.info(f"BusCOM : Connexion authentifiée : {self.client_names[id]}")
                break

    def handle_message(self, message, connection):
        if message["cmd"] == "stop":
            self.stop_threads = True
        elif message["cmd"] == "init":
            client_id = message["id_s"]
            self.init_connection(connection, client_id)
        else:
            if message["id_r"] == 0:
                for client in self.authenticated_clients:
                    if client[0] != connection:
                        self.send(client[0], message)
            else:
                for client in self.authenticated_clients:
                    if client[2] == message["id_r"]:
                        self.send(client[0], message)

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.server_socket:
            logging.info("BusCOM : Démarrage du serveur...")
            print("BusCOM : Démarrage du serveur...")
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            self.server_socket.settimeout(1)

            connection_thread = threading.Thread(target=self.handle_connection)
            connection_thread.start()

            self.tasks.append(connection_thread)

            while not self.stop_threads:
                pass

            logging.info("BusCOM : Arrêt des connexions...")
            print("BusCOM : Arrêt des connexions...")
            self.deconnection()

if __name__ == "__main__":
    serveur = Serveur("0.0.0.0", 22050)
    try:
        serveur.start()
    except KeyboardInterrupt:
        serveur.stop_threads = True
    except ServeurException as e:
        logging.error(str(e), exc_info=True)
        serveur.deconnection()
