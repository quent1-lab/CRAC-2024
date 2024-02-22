import socket
import threading
import keyboard

# Message type : {"id_sender" : 1, "id_receiver" : 2, "cmd" : "init", "data" : None}

# Configuration du serveur
HOST = '0.0.0.0'  # Adresse IP de la Raspberry Pi
PORT = 22050  # Port sur lequel le serveur écoute

# Liste pour stocker tous les threads clients
client_threads = []
client_adress = {
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
        if not data:
            continue # Si les données sont vides, continuer
        else:
            if data["cmd"] == "init":
                if data["id"] in client_adress:
                    client_adress[data["id"]] = (connection, address, client_adress[data["id"]][2])
            print("Données reçues du client:", data.decode())
    message = {"id_sender" : 1, "id_receiver" : 0, "cmd" : "stop", "data" : None}
    connection.sendall(message.encode())  # Envoyer des données au client
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
            stop_threads = False  # Indiquer aux threads de s'arrêter
            break
    
    print("Arrêt des connexions...")
    for thread in client_threads:
        thread.join()
    connection_thread.join()
    print("Serveur ComWIFI arrêté")
    exit()