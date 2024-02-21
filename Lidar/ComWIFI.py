import socket

# Configuration du serveur
HOST = '0.0.0.0'  # Adresse IP de la Raspberry Pi
PORT = 22050  # Port sur lequel le serveur écoute

# Création du socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    # Liaison du socket au port
    server_socket.bind((HOST, PORT))
    # Écoute de nouvelles connexions
    server_socket.listen()
    print("ComWIFI en attente de connexions...")

    # Acceptation de la connexion entrante
    connection, address = server_socket.accept()
    with connection:
        print('Connecté à', address)

        # Boucle de réception et d'envoi des données
        while True:
            data = connection.recv(1024)  # Recevoir des données du client
            if not data:
                break  # Si les données sont vides, sortir de la boucle
