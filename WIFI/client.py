import socket
import time

# Configuration du client
COMWIFI_IP = '192.168.22.100'  # Adresse IP de la Raspberry Pi
COMWIFI_PORT = 22050  # Port sur lequel le serveur ComWIFI écoute
i = 0
# Boucle d'envoi de données au serveur ComWIFI
print("Client ComWIFI démarré")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    print("Connexion au serveur ComWIFI...")
    client_socket.connect((COMWIFI_IP, COMWIFI_PORT))
    while True:
        message = "programme client 1: " + str(i)
        i += 1
        client_socket.sendall(message.encode())
        print("Données envoyées au serveur ComWIFI:", message)
        time.sleep(1)  # Attendre une seconde avant d'envoyer la prochaine donnée
