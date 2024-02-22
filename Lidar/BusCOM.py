import socket
import threading
import keyboard
import json

# Message type : {"id_sender" : 1, "id_receiver" : 2, "cmd" : "init", "data" : None}
# ID : 0 = Broadcast, 1 = BusCOM, 2 = BusCAN, 3 = Lidar, 4 = Ordre Robot, 5 = Stratégie

# Configuration du serveur
HOST = '0.0.0.0'  # Adresse IP de la Raspberry Pi
PORT = 22050  # Port sur lequel le serveur écoute

# Liste pour stocker tous les threads clients
client_threads = []
client_adress = {
    0 : (None, None, "Broadcast"),
    1 : (None, None, "BusCOM"),
    2 : (None, None, "BusCAN"),
    3 : (None, None, "Lidar"),
    4 : (None, None, "Ordre Robot"),
    5 : (None, None, "Stratégie")
}

# Variable de contrôle pour arrêter les threads
stop_threads = False

# Fonction pour gérer chaque client
def handle_client(connection, address):
    global stop_threads, client_adress
    print('Connecté à', address)
    while not stop_threads:
        data = connection.recv(2048)  # Recevoir des données du client

        for message in load_json(data.decode()):
            if message["cmd"] == "stop":
                stop_threads = True
                break
            else:
                print(f"Message reçu : {message}")
                if message["cmd"] == "init":
                    client_adress[message["id_sender"]] = (connection, address, client_adress[message["id_sender"]][2])
                if message["cmd"] == "data":
                    if message["id_receiver"] == 1:
                        pass
                    else:
                        if client_adress[message["id_receiver"]][0] != None :
                            receveir = client_adress[message["id_receiver"]][0]
                            send(receveir,message)
            
    message = {"id_sender" : 1, "id_receiver" : 0, "cmd" : "stop", "data" : None}
    send(connection,message)
    connection.close()

def handle_connection():
    global stop_threads, client_threads
    while not stop_threads:
        try:
            connection, address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(connection, address))
            thread.start()
            client_threads.append(thread)
            print(f"Connexion active : {threading.activeCount()}")
        except socket.timeout:
            pass

def send(client_socket, message):
    messageJSON = json.dumps(message)
    client_socket.sendall(messageJSON.encode())

def load_json(data):
    # Vérifier s'il n'y qu'un seul message ou plusieurs
    if data.count('}{') > 0:
        data = data.split('}{')
        data[0] += '}'
        data[-1] = '{' + data[-1]
    else:
        data = [data]
    # Charger les données JSON
    messages = []
    for message in data:
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
        if keyboard.is_pressed('space'):  # Si la touche espace est enfoncée
            stop_threads = True  # Indiquer aux threads de s'arrêter
            break
    
    print("Arrêt des connexions...")
    for thread in client_threads:
        thread.join()
    connection_thread.join()
    print("Serveur ComWIFI arrêté")
    exit()