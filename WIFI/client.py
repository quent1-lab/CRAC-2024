import socket
import threading
import pickle  # Pour sérialiser/désérialiser les objets Python

def receive_data(sock):
    while True:
        data_received = sock.recv(4096)  # Choisissez une taille de tampon appropriée
        if not data_received:
            break  # Arrêter la boucle si la connexion est fermée par le serveur
        else:
            # Traitez les données reçues du serveur selon vos besoins
            objet_recu = pickle.loads(data_received)
            # ...

def send_data(sock):
    while True:
        # Envoie de données au serveur (exemple avec une chaîne)
        data_to_send = pickle.dumps("Hello, serveur!")
        client_socket.sendall(data_to_send)

# Initialiser le client
server_address = ('192.168.36.63', 5000)  # Remplacez par l'adresse IP et le port du serveur
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(server_address)

# Créer des threads pour la réception et l'envoi de données
receive_thread = threading.Thread(target=receive_data, args=(client_socket,))
send_thread = threading.Thread(target=send_data, args=(client_socket,))

# Démarrer les threads
receive_thread.start()
send_thread.start()

# Attendre la fin des threads (vous pouvez ajuster cela selon vos besoins)
receive_thread.join()
send_thread.join()

# Fermer la socket
client_socket.close()
