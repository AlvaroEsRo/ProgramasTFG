from flask import Flask, render_template, request, redirect, jsonify
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

log_file_path = r"C:\ProgramasTFG\install_logs.txt"  # Archivo temporal para almacenar los logs

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
    project = request.form['project']
    android_version = request.form['android_version']
    sw_version = request.form['sw_version']
    build_type = request.form['build_type']

    # Construir la URL de la carpeta
    base_url = "https://artifacts.mot.com/artifactory"
    url = f"{base_url}/{project}/{android_version}/{sw_version}/{project}_g_sys/{build_type}/release-keys_cid50/"

    # Realizar una solicitud para obtener el índice de la carpeta
    response = requests.get(url, auth=('olallaov', 'Paris2025'))
    if response.status_code != 200:
        return "No se pudo acceder a la URL proporcionada.", 404

    # Buscar el nombre del archivo con el patrón en los href
    pattern = re.compile(
        rf'href="(fastboot_{project}_g_sys_{build_type}_{android_version}_{sw_version}.*release-keys.*\.tar\.gz)"'
    )
    match = pattern.search(response.text)
    if not match:
        return "No se encontró un archivo que coincida con el patrón esperado.", 404

    file_name = match.group(1)
    file_url = urllib.parse.urljoin(url, file_name)
    print("URL para descargar:", file_url)

    # Abrir diálogo para seleccionar carpeta de destino
    root = Tk()
    root.withdraw()  # Oculta la ventana principal de Tkinter
    carpeta = filedialog.askdirectory(title="Selecciona la carpeta de destino para la descarga")
    root.destroy()
    if not carpeta:
        return "No se seleccionó ninguna carpeta.", 400

    file_path = os.path.join(carpeta, file_name)

    # Descargar el archivo
    descarga = requests.get(file_url, stream=True, auth=('olallaov', 'Paris2025'))
    if descarga.status_code == 200:
        with open(file_path, "wb") as f:
            for chunk in descarga.iter_content(chunk_size=8192):
                f.write(chunk)
        return f"Archivo descargado en: {file_path}"
    else:
        return f"Error al descargar el archivo. Código de estado: {descarga.status_code}", 500

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
        # Obtener el directorio del archivo seleccionado
        extract_path = os.path.dirname(file_path)
        log_message(f"Descomprimiendo el archivo en: {extract_path}")

        # Descomprimir el archivo utilizando 7-Zip (primera descompresión)
        seven_zip_path = r"C:\Program Files\7-Zip\7z.exe"  # Ruta al ejecutable de 7-Zip
        run_command([seven_zip_path, "x", file_path, f"-o{extract_path}"], log_file_path)
        log_message(f"Primera descompresión completada en: {extract_path}")

        # Buscar el archivo descomprimido (por ejemplo, un .tar o .zip)
        extracted_files = os.listdir(extract_path)
        for extracted_file in extracted_files:
            extracted_file_path = os.path.join(extract_path, extracted_file)
            if extracted_file_path.endswith(('.tar', '.zip')):
                log_message(f"Encontrado archivo comprimido adicional: {extracted_file_path}")

                # Descomprimir el archivo adicional (segunda descompresión)
                run_command([seven_zip_path, "x", extracted_file_path, f"-o{extract_path}"], log_file_path)
                log_message(f"Segunda descompresión completada en: {extract_path}")
                break

        # Ejecutar el archivo flashall.bat
        flashall_path = os.path.join(extract_path, "flashall.bat")
        if os.path.exists(flashall_path):
            log_message(f"Ejecutando: {flashall_path}")
            try:
                # Abrir una nueva ventana de terminal y ejecutar flashall.bat
                subprocess.Popen(
                    ["cmd.exe", "/c", "start", "cmd.exe", "/k", "flashall.bat"],
                    cwd=extract_path,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                log_message("Archivo 'flashall.bat' ejecutado con éxito en una nueva ventana.")
            except Exception as e:
                log_message(f"Error al ejecutar 'flashall.bat': {e}")
        else:
            log_message("El archivo 'flashall.bat' no se encontró en la carpeta descomprimida.")

        log_message("Instalación completada con éxito.")
    except Exception as e:
        log_message(f"Error durante la instalación: {e}")

def run_command(command, log_file_path, cwd=None):
    """Ejecuta un comando y captura su salida en tiempo real, incluyendo porcentajes."""
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd)
        with open(log_file_path, "a") as log_file:
            for line in process.stdout:
                # Escribir cada línea en el archivo de logs
                log_file.write(line)
                log_file.flush()

                # Mostrar la línea en la terminal
                print(line, end="")

                # Extraer y mostrar el porcentaje de progreso si está presente
                match = re.search(r'(\d+)%', line)
                if match:
                    percentage = match.group(1)
                    print(f"Progreso de descompresión: {percentage}%")
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)
    except Exception as e:
        with open(log_file_path, "a") as log_file:
            log_file.write(f"Error al ejecutar el comando: {e}\n")
        print(f"Error al ejecutar el comando: {e}")

def log_message(message):
    """Escribe un mensaje en el archivo de logs y lo muestra en la terminal."""
    with open(log_file_path, "a") as log_file:
        log_file.write(message + "\n")
    print(message)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)