from flask import Flask, render_template, request, redirect
import urllib.parse
import requests
import zipfile
import os
import subprocess
import re

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Definir las opciones disponibles
    projects = [
        "cybert", 
        "bogota", 
        "scout", 
        "paros", 
        "cancuni", 
        "bronco",
    ]
    
    android_versions = ["14", "15"]
    
    if request.method == 'POST':
        project = request.form['project']
        android_version = request.form['android_version']
        sw_version = request.form['sw_version']
        build_type = request.form['build_type']
        
        # Construye la URL de artifacts sin project_variant
        base_url = "https://artifacts.mot.com/artifactory"
        url = f"{base_url}/{project}/{android_version}/{sw_version}/{project}_g_sys/{build_type}/release-keys_cid50/"
        
        # Codifica la URL para manejar caracteres especiales
        encoded_url = urllib.parse.quote(url, safe=':/')
        
        # Realiza una solicitud para obtener el índice de la carpeta
        response = requests.get(encoded_url, auth=('olallaov', 'Paris2025'))
        if response.status_code == 200:
            # Imprime el contenido de la respuesta para depuración
            print(response.text)

            # Ajusta el patrón para capturar solo el nombre del archivo
            pattern = re.compile(rf"fastboot_{project}_g_sys_{build_type}_{android_version}_{sw_version}.*release-keys.*\.tar\.gz")
            match = pattern.search(response.text)
            
            if match:
                # Limpia el nombre del archivo capturado
                file_name = match.group(0).strip()
                # Asegúrate de eliminar cualquier duplicado o caracteres adicionales
                file_name = file_name.split(">")[-1].replace('"', '').strip()
                print(f"Archivo encontrado: {file_name}")
                
                # Construye la URL completa del archivo
                file_url = f"{encoded_url}{file_name}"
                print(f"URL del archivo: {file_url}")
                
                # Descargar el archivo
                response = requests.get(file_url, stream=True)
                if response.status_code == 200:
                    zip_path = os.path.join("downloads", file_name)
                    os.makedirs("downloads", exist_ok=True)  # Crea la carpeta si no existe
                    with open(zip_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Descomprimir el archivo
                    extract_path = os.path.join("downloads", f"{project}_extracted")
                    os.makedirs(extract_path, exist_ok=True)
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)
                    
                    # Ejecutar un archivo dentro de la carpeta descomprimida (opcional)
                    script_to_run = os.path.join(extract_path, "script_to_run.py")
                    if os.path.exists(script_to_run):
                        subprocess.run(["python", script_to_run])
                    
                    # Elimina el archivo zip después de usarlo (opcional)
                    os.remove(zip_path)
                
                return redirect(file_url)
            else:
                return "No se encontró un archivo que coincida con el patrón esperado.", 404
        else:
            return "No se pudo acceder a la URL proporcionada.", 404
    
    return render_template('sw_finder.html', 
                          projects=projects, 
                          android_versions=android_versions)

if __name__ == '__main__':
    app.run(debug=True)