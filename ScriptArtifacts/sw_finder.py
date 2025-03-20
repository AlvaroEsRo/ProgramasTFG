from flask import Flask, render_template, request, redirect
import urllib.parse

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        project = request.form['project']
        android_version = request.form['android_version']
        sw_version = request.form['sw_version']
        project_variant = request.form['project_variant']
        build_type = request.form['build_type']
        
        # Construye la URL de artifacts
        base_url = "https://artifacts.mot.com/artifactory"
        url = f"{base_url}/{project}/{android_version}/{sw_version}/{project_variant}/{build_type}"
        
        # Codifica la URL para manejar caracteres especiales
        encoded_url = urllib.parse.quote(url, safe=':/')
        
        return redirect(encoded_url)
    
    return render_template('sw_finder.html')

if __name__ == '__main__':
    app.run(debug=True)
