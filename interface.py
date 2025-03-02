from flask import Flask, render_template, send_from_directory, redirect, url_for, request, jsonify
import os
from datetime import datetime
import mimetypes

app = Flask(__name__)

FILES_DIR = "server_files"  # Directory for shared files
LOG_FILE = r"C:\Users\user 2\OS project\server_logs.txt"
USERS_FILE = r"C:\Users\user 2\OS project\active_users.txt"

# Ensure directories exist
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)
if not os.path.exists(LOG_FILE):
    open(LOG_FILE, 'a').close()
if not os.path.exists(USERS_FILE):
    open(USERS_FILE, 'a').close()

# Function to get list of files with upload time
def get_file_list():
    files = os.listdir(FILES_DIR)
    file_info = []
    for file in files:
        file_path = os.path.join(FILES_DIR, file)
        upload_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
        file_info.append({"filename": file, "upload_time": upload_time})
    return file_info
# Function to log server activities
# Function to log server activities with timestamp
def log_message(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")  # Get current date and time
    log_entry = f"{timestamp} {message}"
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(log_entry + "\n")

# Function to log active users and activities
def log_user_activity(ip, activity):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"{timestamp} | {ip} | {activity}"
    log_message(message)
    with open(USERS_FILE, 'a') as user_file:
        user_file.write(message + "\n")

# Route: Dashboard Overview
@app.route('/')
def dashboard():
    files = get_file_list()
    with open(LOG_FILE, 'r') as log_file:
        logs = log_file.readlines()
    with open(USERS_FILE, 'r') as user_file:
        user_logs = user_file.readlines()
    return render_template('dash.html', files=files, logs=logs, user_logs=user_logs)

# Route: Download File
@app.route('/download-file/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(FILES_DIR, filename, as_attachment=True)

# Route: Delete File
@app.route('/delete/<filename>')
def delete_file(filename):
    file_path = os.path.join(FILES_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        log_message(f"File deleted: {filename}")
    return redirect(url_for('dashboard'))

# Route: View File Content
@app.route('/view-file/<filename>', methods=['GET'])
def view_file(filename):
    filepath = os.path.join(FILES_DIR, filename)
    if os.path.exists(filepath):
        return send_from_directory(directory=FILES_DIR, path=filename)
    else:
        return jsonify({"message": "File not found"}), 404
# Route: Upload File
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('dashboard'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('dashboard'))
    file_path = os.path.join(FILES_DIR, file.filename)
    file.save(file_path)
    client_ip = request.remote_addr
    log_user_activity(client_ip, f"Uploaded file: {file.filename}")
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
