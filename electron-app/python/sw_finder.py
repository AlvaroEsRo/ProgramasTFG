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

        # Construir la URL de la carpeta según el build_type
        base_url = "https://artifacts.mot.com/artifactory"
        if build_type == "userdebug":
            url = f"{base_url}/{project}/{android_version}/{sw_version}/{project}_g_sys/{build_type}/intcfg_test-keys/"
        else:  # Para "user" u otros valores
            url = f"{base_url}/{project}/{android_version}/{sw_version}/{project}_g_sys/{build_type}/release-keys_cid50/"

        # Realizar una solicitud para obtener el índice de la carpeta
        response = requests.get(url, auth=('olallaov', 'Paris2025'))
        if response.status_code != 200:
            return "No se pudo acceder a la URL proporcionada.", 404

        # Buscar el nombre del archivo con el patrón en los href
        pattern = re.compile(
            rf'href="(fastboot_{project}_g_sys_{build_type}_{android_version}_{sw_version}.*(release-keys|intcfg-test-keys).*\.tar\.gz)"'
        )
        match = pattern.search(response.text)
        if not match:
            return "No se encontró un archivo que coincida con el patrón esperado.", 404

        file_name = match.group(1)
        file_url = urllib.parse.urljoin(url, file_name)
        print("URL para descargar:", file_url)

        # Redirigir al usuario a la URL del archivo para que el navegador maneje la descarga
        return redirect(file_url)

    return render_template('sw_finder.html', projects=projects, android_versions=android_versions)

@app.route('/descargar', methods=['POST'])
def descargar():
    data = request.json  # Recibir datos como JSON
    project = data.get('project')
    android_version = data.get('android_version')
    sw_version = data.get('sw_version')
    build_type = data.get('build_type')

    if not project or not android_version or not sw_version or not build_type:
        return jsonify({"error": "Faltan datos en la solicitud"}), 400

    # Construir la URL de la carpeta
    base_url = "https://artifacts.mot.com/artifactory"
    url = f"{base_url}/{project}/{android_version}/{sw_version}/{project}_g_sys/{build_type}/release-keys_cid50/"

    # Realizar una solicitud para obtener el índice de la carpeta
    response = requests.get(url, auth=('olallaov', 'Paris2025'))
    if response.status_code != 200:
        return jsonify({"error": "No se pudo acceder a la URL proporcionada."}), 404

    # Buscar el nombre del archivo con el patrón en los href
    pattern = re.compile(
        rf'href="(fastboot_{project}_g_sys_{build_type}_{android_version}_{sw_version}.*release-keys.*\.tar\.gz)"'
    )
    match = pattern.search(response.text)
    if not match:
        return jsonify({"error": "No se encontró un archivo que coincida con el patrón esperado."}), 404

    file_name = match.group(1)
    file_url = urllib.parse.urljoin(url, file_name)
    print("URL para descargar:", file_url)

    return jsonify({"message": "Archivo encontrado", "url": file_url})

@app.route('/install', methods=['GET', 'POST'])
def install():
    if request.method == 'POST':
        # Limpiar el archivo de logs al inicio
        with open(log_file_path, "w") as log_file:
            log_file.write("")

        # Obtener la ruta del archivo ingresada por el usuario
        raw_file_path = request.form.get('file_path', '').strip()

        # Extraer solo el contenido entre comillas si las hay
        match = re.match(r'^"(.*)"$', raw_file_path)
        file_path = match.group(1) if match else raw_file_path

        carrier = request.form.get('carrier', 'default').strip()
        # Validar que la ruta del archivo exista
        if not os.path.exists(file_path):
            return render_template('install.html', logs=["La ruta del archivo no existe."])

        if not file_path.endswith('.tar.gz'):
            return render_template('install.html', logs=["El archivo seleccionado no es un archivo .tar.gz válido."])

        # Ejecutar el proceso en un hilo separado
        thread = threading.Thread(target=run_installation, args=(file_path, carrier))
        thread.start()

    return render_template('install.html')

def run_installation(file_path, carrier):
    try:
        extract_path = os.path.dirname(file_path)
        log_message(f"Descomprimiendo el archivo en: {extract_path}")

        seven_zip_path = r"C:\Program Files\7-Zip\7z.exe"
        run_command([seven_zip_path, "x", file_path, f"-o{extract_path}", "-bso1", "-bsp1"], log_file_path)
        log_message(f"Primera descompresión completada en: {extract_path}")

        extracted_files = os.listdir(extract_path)
        for extracted_file in extracted_files:
            extracted_file_path = os.path.join(extract_path, extracted_file)
            if extracted_file_path.endswith(('.tar', '.zip')):
                log_message(f"Encontrado archivo comprimido adicional: {extracted_file_path}")
                if wait_for_file_ready(extracted_file_path):
                    run_command([seven_zip_path, "x", extracted_file_path, f"-o{extract_path}", "-bso1", "-bsp1"], log_file_path)
                    log_message(f"Segunda descompresión completada en: {extract_path}")
                else:
                    log_message(f"Error: El archivo {extracted_file_path} no está listo para descomprimir.")
                break

        # Ejecutar fastboot oem config carrier <canal>
        log_message(f"Ejecutando: fastboot oem config carrier {carrier}")
        run_command(["fastboot", "oem", "config", "carrier", carrier], log_file_path, cwd=extract_path)

        # Ejecutar fastboot -w
        log_message("Ejecutando: fastboot -w")
        run_command(["fastboot", "-w"], log_file_path, cwd=extract_path)

        # Ejecutar flashall.bat en primer plano
        flashall_path = os.path.join(extract_path, "flashall.bat")
        if os.path.exists(flashall_path):
            log_message(f"Ejecutando: {flashall_path}")
            # Ejecutar en primer plano y mostrar logs
            run_command([flashall_path], log_file_path, cwd=extract_path)
            log_message("Archivo 'flashall.bat' ejecutado con éxito.")
        else:
            log_message("El archivo 'flashall.bat' no se encontró en la carpeta descomprimida.")

        log_message("Instalación completada con éxito.")
    except Exception as e:
        log_message(f"Error durante la instalación: {e}")

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
            log_file.write(f"Error al ejecutar el comando: {e}\n")
        print(f"Error al ejecutar el comando: {e}")

def log_message(message):
    """Escribe un mensaje en el archivo de logs y lo muestra en la terminal."""
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
        return jsonify({"logs": f"Error leyendo logs: {e}"})

import time

def wait_for_file_ready(filepath, timeout=60):
    """Espera a que el archivo exista y su tamaño deje de cambiar."""
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

if __name__ == '__main__':
    app.run(debug=True)