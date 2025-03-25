from flask import Flask, render_template, request, redirect
import urllib.parse

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
    
    android_versions = ["14.0", "15.0"]
    
    if request.method == 'POST':
        project = request.form['project']
        android_version = request.form['android_version']
        sw_version = request.form['sw_version']
        build_type = request.form['build_type']
        
        # Construye la URL de artifacts sin project_variant
        base_url = "https://artifacts.mot.com/artifactory"
        url = f"{base_url}/{project}/{android_version}/{sw_version}/{build_type}"
        
        # Codifica la URL para manejar caracteres especiales
        encoded_url = urllib.parse.quote(url, safe=':/')
        
        return redirect(encoded_url)
    
    return render_template('sw_finder.html', 
                          projects=projects, 
                          android_versions=android_versions)

if __name__ == '__main__':
    app.run(debug=True)