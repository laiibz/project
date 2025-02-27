from flask import Flask, render_template, request, jsonify
import socket
import os

app = Flask(__name__)

HEADER = 64
PORT = 5000
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "DISCONNECT!"
SERVER = "192.168.1.5"  # Replace with your server's IP address
ADDR = (SERVER, PORT)

def send_command(command):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    message = command.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    return client

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list-files', methods=['GET'])
def list_files():
    client = send_command("LIST")
    response = client.recv(1024).decode(FORMAT)
    client.close()
    files = response.split('\n')
    return jsonify(files)

@app.route('/download-file', methods=['POST'])
def download_file():
    filename = request.form.get('filename')
    client = send_command(f"DOWNLOAD {filename}")
    response = client.recv(HEADER).decode(FORMAT)
    
    if response.isdigit():  # If valid file size is received
        file_size = int(response)
        client.send("READY".encode(FORMAT))  # Acknowledge readiness

        # Absolute path to the 'downloads' folder
        CLIENT_FILES_DIR = os.path.join(os.path.dirname(__file__), 'downloads')
        if not os.path.exists(CLIENT_FILES_DIR):
            os.makedirs(CLIENT_FILES_DIR)
        
        filepath = os.path.join(CLIENT_FILES_DIR, filename)
        with open(filepath, "wb") as f:
            bytes_received = 0
            while bytes_received < file_size:
                data = client.recv(1024)
                if not data:  # Break the loop if no more data
                    break
                f.write(data)
                bytes_received += len(data)
        
        client.close()
        return jsonify({"message": f"File '{filename}' downloaded successfully!"})
    else:
        client.close()
        return jsonify({"message": response})

@app.route('/upload-file', methods=['POST'])
def upload_file():
    file = request.files['file']
    filename = file.filename
    filepath = os.path.join('uploads', filename)
    
    # Save file to 'uploads' folder
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    file.save(filepath)

    # Send upload command to server
    client = send_command(f"UPLOAD {filename}")
    
    # Send file size
    file_size = os.path.getsize(filepath)
    file_size_header = str(file_size).encode(FORMAT)
    file_size_header += b' ' * (HEADER - len(file_size_header))
    client.send(file_size_header)
    
    # Send file data
    with open(filepath, "rb") as f:
        while (data := f.read(1024)):
            client.send(data)
    
    response = client.recv(1024).decode(FORMAT)
    client.close()
    return jsonify({"message": response})

if __name__ == "__main__":
    app.run(debug=True)
