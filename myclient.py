from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
import socket
import os
from datetime import datetime

app = Flask(__name__)

HEADER = 64
PORT = 5000
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "DISCONNECT!"
SERVER = "192.168.1.5"  
ADDR = (SERVER, PORT)
LOG_FILE = "server_logs.txt"
CLIENT_FILES_DIR = os.path.join(os.path.dirname(__file__), 'downloads')
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'server_files')


if not os.path.exists(CLIENT_FILES_DIR):
    os.makedirs(CLIENT_FILES_DIR)
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


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
    return render_template('myclient.html')

# Route to list files with date and time of upload
@app.route('/list-files', methods=['GET'])
def list_files():
    try:
        # Send LIST command to the server
        client = send_command("LIST")
        files = client.recv(4096).decode(FORMAT).split("\n")
        client.close()
        
        file_info_list = []
        for file in files:
            if file:
                upload_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                file_info_list.append({
                    'filename': file,
                    'upload_time': upload_time
                })
        
        return jsonify(file_info_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to download a file by its filename
@app.route('/download-file/<filename>', methods=['GET'])
def download_file(filename):
    try:
        # Send DOWNLOAD command to the server
        client = send_command(f"DOWNLOAD {filename}")
        
        file_size = int(client.recv(HEADER).decode(FORMAT).strip())
        client.send("READY".encode(FORMAT))  # Send acknowledgment
        
        file_path = os.path.join(CLIENT_FILES_DIR, filename)
        with open(file_path, "wb") as f:
            bytes_received = 0
            while bytes_received < file_size:
                data = client.recv(1024)
                f.write(data)
                bytes_received += len(data)
        
        client.close()
        return send_from_directory(directory=CLIENT_FILES_DIR, path=filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to view a file in the browser
@app.route('/view-file/<filename>', methods=['GET'])
def view_file(filename):
    filepath = os.path.join(CLIENT_FILES_DIR, filename)
    if os.path.exists(filepath):
        return send_from_directory(directory=CLIENT_FILES_DIR, path=filename)
    else:
        return jsonify({"message": "File not found"}), 404

# Route to handle file upload
@app.route('/upload-file', methods=['POST'])
def upload_file():
    file = request.files['file']
    filename = file.filename
    file_path = os.path.join(CLIENT_FILES_DIR, filename)
    file.save(file_path)

    # Send UPLOAD command to the server
    try:
        client = send_command(f"UPLOAD {filename}")
        
        # Send file size first with proper padding
        file_size = os.path.getsize(file_path)
        file_size_message = str(file_size).encode(FORMAT)
        file_size_message += b' ' * (HEADER - len(file_size_message))
        client.send(file_size_message)
        
        # Read and send the file in chunks
        with open(file_path, "rb") as f:
            while (data := f.read(1024)):
                client.send(data)
        
        # Close the connection after sending the file
        client.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True,port=5001)