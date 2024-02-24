import socket
import threading
import json

# Message type : {"id_s" : 1, "id_r" : 2, "cmd" : "init", "data" : None}
# ID : 0 = Broadcast, 1 = BusCOM, 2 = BusCAN, 3 = Lidar, 4 = Ordre Robot, 5 = Stratégie

# Configuration du serveur
HOST = '0.0.0.0'  # Adresse IP de la Raspberry Pi
PORT = 22050  # Port sur lequel le serveur écoute

# Liste pour stocker tous les threads clients
client_threads = []
client_adress = { # id : (socket, adress, name)
    0 : (None, None, "Broadcast"),
    1 : (None, None, "BusCOM"),
    2 : (None, None, "BusCAN"),
    3 : (None, None, "Lidar"),
    4 : (None, None, "Ordre Robot"),
    5 : (None, None, "Stratégie"),
    10 : (None, None, "IHM"),
    2205 : (None, None, "Erreur (2205) client init non reconnu"),
}

# Variable de contrôle pour arrêter les threads
stop_threads = False

# Verrou pour synchroniser l'accès aux données partagées entre les threads
lock = threading.Lock()

# Fonction pour gérer chaque client
def handle_client(connection, address):
    global stop_threads, client_adress
    print('Connecté à', address)
    for data in receive_messages(connection):
        for message in load_json(data):
            #print(f"Message reçu : {message}")
            if message["cmd"] == "stop":
                stop_threads = True
                break
            else:
                if message["cmd"] == "init":
                    client_adress[message["id_s"]] = (connection, address, client_adress[message["id_s"]][2])
                    if message["id_s"] == 2205:
                        print(f"Erreur (2205) client init non reconnu")
                    else:
                        print(f"Client {client_adress[message['id_s']][2]} connecté")
                if message["cmd"] == "data":
                    if message["id_r"] == 1:
                        pass
                    else:
                        if client_adress[message["id_r"]][0] is not None:
                            receveir = client_adress[message["id_r"]][0]
                            send(receveir, message)
                if message["cmd"] == "objects":
                    if client_adress[message["id_r"]][0] is not None:
                        receveir = client_adress[message["id_r"]][0]
                        send(receveir, message)
    
    message = {"id_s" : 1, "id_r" : 0, "cmd" : "stop", "data" : None}
    send(connection, message)

def receive_messages(socket):
    buffer = ""
    while not stop_threads:
        data = socket.recv(4096)
        if not data:
            break
        buffer += data.decode()
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            yield line

def handle_connection():
    global stop_threads, client_threads
    while not stop_threads:
        try:
            connection, address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(connection, address))
            thread.start()
            with lock:
                client_threads.append(thread)
            print(f"Connexion active : {threading.active_count()}")
        except socket.timeout:
            pass

def send(client_socket, message):
    messageJSON = json.dumps(message) + "\n"
    try :
        client_socket.sendall(messageJSON.encode())
    except ConnectionResetError:
        print("Erreur de connexion")
        pass

def load_json(data):
    messages = []
    for message in data.split('\n'):
        if message:  # ignore empty lines
            messages.append(json.loads(message))
    return messages


# Création du socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    # Liaison du socket au port
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    server_socket.settimeout(1)  # Définir un délai d'attente de 1 seconde
    print("ComWIFI en attente de connexions...")

    # Démarrer le thread pour arrêter les threads clients
    connection_thread = threading.Thread(target=handle_connection)
    connection_thread.start()

    # Boucle d'acceptation des connexions entrantes
    while not stop_threads:
        pass  # Pour garder le programme en cours d'exécution indéfiniment jusqu'à ce que stop_threads soit True
    
    print("Arrêt des connexions...")
    for thread in client_threads:
        thread.join()
    connection_thread.join()
    for client in client_adress:
        if client_adress[client][0] is not None:
            client_adress[client][0].close()
    server_socket.close()
    print("Serveur ComWIFI arrêté")
    exit()
