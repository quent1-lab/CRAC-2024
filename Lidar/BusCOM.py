import socket
import threading
import json

HOST = '0.0.0.0'
PORT = 22050

clients = []  # Liste pour stocker les informations sur les clients (socket, address, name)

stop_threads = False
lock = threading.Lock()

def handle_client(connection, address):
    global stop_threads, clients
    print('Connecté à', address)
    for data in receive_messages(connection):
        messages = load_json(data)
        with lock:
            for message in messages:
                handle_message(message, connection)

    print(f"Déconnexion de {address}")
    connection.close()
    with lock:
        clients = [client for client in clients if client[0] != connection]

def receive_messages(socket):
    buffer = ""
    while not stop_threads:
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

def handle_connection():
    global stop_threads, clients
    while not stop_threads:
        try:
            connection, address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(connection, address))
            thread.start()
            with lock:
                clients.append((connection, address, "Client"))
            print(f"Connexion active : {threading.active_count()}")
        except socket.timeout:
            pass

def send(client_socket, message):
    messageJSON = json.dumps(message) + "\n"
    try:
        client_socket.sendall(messageJSON.encode())
    except ConnectionResetError:
        print("Erreur de connexion")

def load_json(data):
    messages = []
    for message in data.split('\n'):
        if message:  # ignore empty lines
            messages.append(json.loads(message))
    return messages

def handle_message(message, connection):
    global clients
    if message["cmd"] == "stop":
        stop_threads = True
    elif message["cmd"] == "init":
        client_id = message["id_s"]
        clients.append((connection, None, f"Client {client_id}"))
        print(f"Client {client_id} connecté")
    elif message["cmd"] == "data":
        recipient_id = message["id_r"]
        recipient = next((client for client in clients if client[0] == connection and client[1] is not None and client[1][1] == recipient_id), None)
        if recipient is not None:
            send(recipient[0], message)
    elif message["cmd"] == "objects":
        recipient_id = message["id_r"]
        recipient = next((client for client in clients if client[0] == connection and client[1] is not None and client[1][1] == recipient_id), None)
        if recipient is not None:
            send(recipient[0], message)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    server_socket.settimeout(1)

    connection_thread = threading.Thread(target=handle_connection)
    connection_thread.start()

    while not stop_threads:
        pass

    print("Arrêt des connexions...")
    for client in clients:
        client[0].close()
    server_socket.close()
    print("Serveur arrêté")
    exit()
