import socket
import time
import threading

# Configuration du client
COMWIFI_IP = '192.168.22.100'  # Adresse IP de la Raspberry Pi
COMWIFI_PORT = 22050  # Port sur lequel le serveur ComWIFI écoute

stop_threads = True

def receive_data(client_socket):
    global stop_threads
    while stop_threads:
        data_received = client_socket.recv(1024)
        print("Données reçues du serveur ComWIFI:", data_received.decode())
        if data_received == b"stop":
            stop_threads = False
            break
    
def send_data(client_socket):
    global stop_threads
    i = 0
    while stop_threads:
        message = "programme client 1: " + str(i)
        i += 1
        client_socket.sendall(message.encode())
        print("Données envoyées au serveur ComWIFI:", message)
        time.sleep(1)  # Attendre une seconde avant d'envoyer la prochaine donnée

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((COMWIFI_IP, COMWIFI_PORT))

    receive_thread = threading.Thread(target=receive_data, args=(client_socket,))
    send_thread = threading.Thread(target=send_data, args=(client_socket,))

    receive_thread.start()
    send_thread.start()

    while True:
        if not stop_threads:
            receive_thread.join()
            send_thread.join()
            break

