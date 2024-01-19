import socket
import threading
import pickle  # Pour sérialiser/désérialiser les objets Python
import time
import queue

def handle_client(client_socket, client_address):
    print(f"Connexion établie avec {client_address}")

    def receive_data():
        while True:
            data_received = client_socket.recv(4096)  # Choisissez une taille de tampon appropriée
            if not data_received:
                break  # Arrêter la boucle si la connexion est fermée par le client
            else:
                # Traitez les données reçues du client selon vos besoins
                objet_recu = pickle.loads(data_received)
                print(objet_recu)
                # ...

    def send_data():
        while True:
            # Envoie de données au client (exemple avec une chaîne)
            data_to_send = pickle.dumps("Hello, client!")
            client_socket.sendall(data_to_send)
            time.sleep(100)

    # Créer des threads pour la réception et l'envoi de données
    receive_thread = threading.Thread(target=receive_data)
    send_thread = threading.Thread(target=send_data)

    # Démarrer les threads
    receive_thread.start()
    send_thread.start()

    # Attendre la fin des threads (vous pouvez ajuster cela selon vos besoins)
    receive_thread.join()
    send_thread.join()

    # Fermer la connexion avec le client
    print(f"Connexion fermée avec {client_address}")
    client_socket.close()

# Initialiser le serveur
server_address = ('', 5000)  # Laissez l'adresse IP vide pour écouter sur toutes les interfaces
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(server_address)
server_socket.listen(5)  # Accepter jusqu'à 5 connexions simultanées

print("Serveur en attente de connexions...")

while True:
    # Attendre une connexion et créer un nouveau thread pour chaque client
    client_socket, client_address = server_socket.accept()
    client_handler_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_handler_thread.start()
