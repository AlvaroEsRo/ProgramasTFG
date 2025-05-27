from flask import Flask, render_template, request, redirect, jsonify, send_file
import urllib.parse
import requests
import zipfile
import os
import subprocess
import re
import tarfile
import threading
import time
import sys
from tkinter import Tk, filedialog

app = Flask(__name__)

log_file_path = os.path.join(os.path.dirname(__file__), "install_logs.txt")

# Asegúrate de que la carpeta existe
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    projects = ["cybert", "bogota", "scout", "paros", "cancuni", "bronco"]
    android_versions = ["14", "15"]

    if request.method == 'POST':
        project = request.form['project']
        android_version = request.form['android_version']
        sw_version = request.form['sw_version']
        build_type = request.form['build_type']

        # Build the folder URL according to build_type
        base_url = "https://artifacts.mot.com/artifactory"
        if build_type == "userdebug":
            url = f"{base_url}/{project}/{android_version}/{sw_version}/{project}_g_sys/{build_type}/intcfg_test-keys/"
        else:  # For "user" or other values
            url = f"{base_url}/{project}/{android_version}/{sw_version}/{project}_g_sys/{build_type}/release-keys_cid50/"

        # Make a request to get the folder index
        response = requests.get(url, auth=('olallaov', 'Paris2025'))
        if response.status_code != 200:
            return "Could not access the provided URL.", 404

        # Search for the file name with the pattern in hrefs
        pattern = re.compile(
            rf'href="(fastboot_{project}_g_sys_{build_type}_{android_version}_{sw_version}.*(release-keys|intcfg-test-keys).*\.tar\.gz)"'
        )
        match = pattern.search(response.text)
        if not match:
            return "No file matching the expected pattern was found.", 404

        file_name = match.group(1)
        file_url = urllib.parse.urljoin(url, file_name)
        print("URL to download:", file_url)

        # Redirect the user to the file URL so the browser handles the download
        return redirect(file_url)

    return render_template('sw_finder.html', projects=projects, android_versions=android_versions)

@app.route('/descargar', methods=['POST'])
def descargar():
    data = request.json  # Receive data as JSON
    project = data.get('project')
    android_version = data.get('android_version')
    sw_version = data.get('sw_version')
    build_type = data.get('build_type')

    if not project or not android_version or not sw_version or not build_type:
        return jsonify({"error": "Missing data in the request"}), 400

    # Build the folder URL
    base_url = "https://artifacts.mot.com/artifactory"
    url = f"{base_url}/{project}/{android_version}/{sw_version}/{project}_g_sys/{build_type}/release-keys_cid50/"

    # Make a request to get the folder index
    response = requests.get(url, auth=('olallaov', 'Paris2025'))
    if response.status_code != 200:
        return jsonify({"error": "Could not access the provided URL."}), 404

    # Search for the file name with the pattern in hrefs
    pattern = re.compile(
        rf'href="(fastboot_{project}_g_sys_{build_type}_{android_version}_{sw_version}.*release-keys.*\.tar\.gz)"'
    )
    match = pattern.search(response.text)
    if not match:
        return jsonify({"error": "No file matching the expected pattern was found."}), 404

    file_name = match.group(1)
    file_url = urllib.parse.urljoin(url, file_name)
    print("URL to download:", file_url)

    return jsonify({"message": "File found", "url": file_url})

@app.route('/install', methods=['GET', 'POST'])
def install():
    if request.method == 'POST':
        # Clear the log file at the start
        with open(log_file_path, "w") as log_file:
            log_file.write("")

        # Get the file path entered by the user
        raw_file_path = request.form.get('file_path', '').strip()

        # Extract only the content between quotes if any
        match = re.match(r'^"(.*)"$', raw_file_path)
        file_path = match.group(1) if match else raw_file_path

        carrier = request.form.get('carrier', 'default').strip()
        # Validate that the file path exists
        if not os.path.exists(file_path):
            return render_template('install.html', logs=["The file path does not exist."])

        if not file_path.endswith('.tar.gz'):
            return render_template('install.html', logs=["The selected file is not a valid .tar.gz file."])

        # Run the process in a separate thread
        thread = threading.Thread(target=run_installation, args=(file_path, carrier))
        thread.start()

    return render_template('install.html')

def run_installation(file_path, carrier):
    try:
        extract_path = os.path.dirname(file_path)
        log_message(f"Extracting the file to: {extract_path}")

        seven_zip_path = r"C:\Program Files\7-Zip\7z.exe"
        run_command([seven_zip_path, "x", file_path, f"-o{extract_path}", "-bso1", "-bsp1"], log_file_path)
        log_message(f"First extraction completed in: {extract_path}")

        extracted_files = os.listdir(extract_path)
        for extracted_file in extracted_files:
            extracted_file_path = os.path.join(extract_path, extracted_file)
            if extracted_file_path.endswith(('.tar', '.zip')):
                log_message(f"Found additional compressed file: {extracted_file_path}")
                if wait_for_file_ready(extracted_file_path):
                    run_command([seven_zip_path, "x", extracted_file_path, f"-o{extract_path}", "-bso1", "-bsp1"], log_file_path)
                    log_message(f"Second extraction completed in: {extract_path}")
                else:
                    log_message(f"Error: The file {extracted_file_path} is not ready to extract.")
                break

        # Execute fastboot oem config carrier <carrier>
        log_message(f"Running: fastboot oem config carrier {carrier}")
        if not run_fastboot_command(["fastboot", "oem", "config", "carrier", carrier], log_file_path, cwd=extract_path):
            log_message("No device connected. Aborting installation.")
            return

        log_message("Running: fastboot -w")
        if not run_fastboot_command(["fastboot", "-w"], log_file_path, cwd=extract_path):
            log_message("No device connected. Aborting installation.")
            return

        # Execute flashall.bat in the foreground
        flashall_path = os.path.join(extract_path, "flashall.bat")
        if os.path.exists(flashall_path):
            log_message(f"Running: {flashall_path}")
            run_command([flashall_path], log_file_path, cwd=extract_path)
            log_message("File 'flashall.bat' executed successfully.")
        else:
            log_message("The file 'flashall.bat' was not found in the extracted folder.")

        log_message("Installation completed successfully.")
    except Exception as e:
        log_message(f"Error during installation: {e}")

def run_command(command, log_file_path, cwd=None):
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            bufsize=1
        )
        with open(log_file_path, "a", buffering=1, encoding="utf-8") as log_file:
            for line in process.stdout:
                log_file.write(line)
                log_file.flush()
                print(line, end="")
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)
    except Exception as e:
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"Error running command: {e}\n")
        print(f"Error running command: {e}")

def log_message(message):
    """Writes a message to the log file and prints it to the terminal."""
    with open(log_file_path, "a") as log_file:
        log_file.write(message + "\n")
    print(message)

@app.route('/logs')
def get_logs():
    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return jsonify({"logs": content})
    except UnicodeDecodeError:
        with open(log_file_path, "r", encoding="latin1") as f:
            content = f.read()
        return jsonify({"logs": content})
    except Exception as e:
        return jsonify({"logs": f"Error reading logs: {e}"})

def wait_for_file_ready(filepath, timeout=60):
    """Waits for the file to exist and its size to stop changing."""
    start = time.time()
    last_size = -1
    while time.time() - start < timeout:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size == last_size:
                return True
            last_size = size
        time.sleep(1)
    return False

def kill_process_by_name(process_name):
    """Terminates all processes with the given name (Windows)."""
    try:
        subprocess.run(["taskkill", "/f", "/im", process_name], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log_message(f"Terminated all processes named: {process_name}")
    except Exception as e:
        log_message(f"Error terminating process {process_name}: {e}")

def run_fastboot_command(command, log_file_path, cwd=None, timeout=30):
    """
    Runs a fastboot command with a timeout. If 'waiting for any device' is detected,
    kills the process and logs an error.
    """
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            bufsize=1
        )
        waiting = False
        with open(log_file_path, "a", buffering=1, encoding="utf-8") as log_file:
            start_time = time.time()
            for line in iter(process.stdout.readline, ''):
                log_file.write(line)
                log_file.flush()
                print(line, end="")
                if "waiting for any device" in line.lower():
                    waiting = True
                    break
                # Timeout check
                if time.time() - start_time > timeout:
                    waiting = True
                    break
            if waiting:
                process.terminate()
                log_file.write("No device connected. Aborting operation.\n")
                log_file.flush()
                print("No device connected. Aborting operation.")
                return False
            # Continue reading remaining output if not waiting
            for line in process.stdout:
                log_file.write(line)
                log_file.flush()
                print(line, end="")
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)
        return True
    except Exception as e:
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"Error running command: {e}\n")
        print(f"Error running command: {e}")
        return False

if __name__ == '__main__':
    app.run(debug=True)