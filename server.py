import socket
from datetime import datetime
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
FILES_DIR = "server_files"  
LOG_FILE = "server_logs.txt"

def log_message(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")  
    log_entry = f"{timestamp} {message}"
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(log_entry + "\n")
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
    log_message(f"[NEW CONNECTION] {addr} connected.")
    connected = True
    while connected:
        try:
            move_files_to_server_files()  # Ensure all root files are in server_files
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length.strip())
                command = conn.recv(msg_length).decode(FORMAT)
                print(f"[{addr}] Command received: {command}")
                log_message(f"[{addr}] Command received: {command}")
                if command == DISCONNECT_MESSAGE:
                    connected = False
                elif command == "LIST":
                    files = os.listdir(FILES_DIR)
                    response = "\n".join(files) if files else "No files available."
                    conn.send(response.encode(FORMAT))
                elif command.startswith("UPLOAD"):
                    filename = command.split(" ")[1]
                    filepath = os.path.join(FILES_DIR, filename)
                    
                    # Receive and decode the file size
                    file_size_data = conn.recv(HEADER).decode(FORMAT)
                    file_size = int(file_size_data.strip())
                    
                    # Receive and save the file
                    with open(filepath, "wb") as f:
                        bytes_received = 0
                        while bytes_received < file_size:
                            data = conn.recv(1024)
                            if not data:
                                break
                            f.write(data)
                            bytes_received += len(data)
                    
                    if bytes_received == file_size:
                        response_message = f"File '{filename}' uploaded successfully."
                    else:
                        response_message = "File upload failed."
                    
                    conn.send(response_message.encode(FORMAT))
                    log_message(f"[{addr}] {response_message}")




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
                        log_message(f"File {filename} downloaded successfully.".encode(FORMAT))
                    else:
                        conn.send("File not found.".encode(FORMAT))
                        log_message(f"File not found.".encode(FORMAT))
        except Exception as e:
            print(f"[ERROR] {e}")
            connected = False
    conn.close()

def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    log_message(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
log_message("[STARTING] Server is starting...")
print("[STARTING] Server is starting...")
start()



