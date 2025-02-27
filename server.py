import socket
import threading
import os
import shutil

HEADER = 64
PORT = 5000
SERVER = "192.168.1.5"
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "DISCONNECT!"
ROOT_DIR = "server_root"
FILES_DIR = "server_files"  # Directory for shared files

# Ensure directories exist
if not os.path.exists(ROOT_DIR):
    os.makedirs(ROOT_DIR)
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

def move_files_to_server_files():
    """Move any new files from ROOT_DIR to FILES_DIR."""
    for file in os.listdir(ROOT_DIR):
        src = os.path.join(ROOT_DIR, file)
        dest = os.path.join(FILES_DIR, file)
        if os.path.isfile(src):
            shutil.move(src, dest)
            print(f"[FILE MOVED] {file} moved to {FILES_DIR}")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    connected = True
    while connected:
        try:
            move_files_to_server_files()  # Ensure all root files are in server_files
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length.strip())
                command = conn.recv(msg_length).decode(FORMAT)
                print(f"[{addr}] Command received: {command}")
                
                if command == DISCONNECT_MESSAGE:
                    connected = False
                elif command == "LIST":
                    files = os.listdir(FILES_DIR)
                    response = "\n".join(files) if files else "No files available."
                    conn.send(response.encode(FORMAT))
                elif command.startswith("UPLOAD"):
                    filename = command.split(" ")[1]
                    filepath = os.path.join(FILES_DIR, filename)
                    file_size_data = conn.recv(HEADER).decode(FORMAT)
                    file_size = int(file_size_data.strip())
                    with open(filepath, "wb") as f:
                        bytes_received = 0
                        while bytes_received < file_size:
                            data = conn.recv(1024)
                            f.write(data)
                            bytes_received += len(data)
                    conn.send(f"File {filename} uploaded successfully.".encode(FORMAT))
                elif command.startswith("DOWNLOAD"):
                    filename = command.split(" ")[1]
                    filepath = os.path.join(FILES_DIR, filename)
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath)
                        conn.send(str(file_size).encode(FORMAT))
                        conn.recv(HEADER)  # Acknowledge readiness
                        with open(filepath, "rb") as f:
                            while (data := f.read(1024)):
                                conn.send(data)
                        conn.send(f"File {filename} downloaded successfully.".encode(FORMAT))
                    else:
                        conn.send("File not found.".encode(FORMAT))
        except Exception as e:
            print(f"[ERROR] {e}")
            connected = False
    conn.close()

def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

print("[STARTING] Server is starting...")
start()



