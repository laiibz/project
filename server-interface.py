from flask import Flask, render_template, send_from_directory, redirect, url_for
import os
import threading
import socket

app = Flask(__name__)

FILES_DIR = "server_files"  # Directory for shared files
LOG_FILE = r"C:\Users\user 2\OS project\server_logs.txt"

# Ensure directories exist
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

# Function to get list of files
def get_file_list():
    return os.listdir(FILES_DIR)

# Route: Dashboard Overview
@app.route('/')
def dashboard():
    files = get_file_list()
    with open(LOG_FILE, 'r') as log_file:
        logs = log_file.readlines()
    return render_template('dashboard.html', files=files, logs=logs)

# Route: Download File
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(FILES_DIR, filename, as_attachment=True)

# Route: Delete File
@app.route('/delete/<filename>')
def delete_file(filename):
    file_path = os.path.join(FILES_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for('dashboard'))

# Function to log server activities
def log_message(message):
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(message + "\n")

if __name__ == "__main__":
    app.run(port=5001, debug=True)
