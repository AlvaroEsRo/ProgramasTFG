from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return "No se subió ningún archivo"
        
        file = request.files["file"]
        if file.filename == "":
            return "No se seleccionó ningún archivo"
        
        if file:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)
            return redirect(url_for("results", filename=file.filename))
    
    return render_template("index.html")

@app.route("/results/<filename>")
def results(filename):
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    
    try:
        df = pd.read_excel(filepath)
        print(df)  # Para verificar que el archivo se lee correctamente
    except Exception as e:
        return f"Error al procesar el archivo: {e}"
    
    conn = sqlite3.connect("bugs_database.db")
    cursor = conn.cursor()

    # Modificar la estructura de la tabla para incluir el nombre del archivo
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bugs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bug_id TEXT,
        bug_status TEXT,
        fixed_in TEXT,
        tested_by TEXT,
        priority TEXT,
        name TEXT,
        description TEXT,
        comments TEXT,
        defect_id TEXT,
        file_name TEXT,
        import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    
    nuevos_bugs = []
    bugs_repetidos = []
    
    for index, row in df.iterrows():
        name = row.get("Name")
        description = row.get("BUG DESCRIPTION")

        # Verificar si el bug existe en cualquier archivo anterior
        cursor.execute("""
        SELECT file_name FROM bugs WHERE name = ? AND description = ?
        """, (name, description))
        
        existing_file = cursor.fetchone()
        
        if existing_file is None:
            nuevos_bugs.append((name, description))
            cursor.execute("""
            INSERT INTO bugs (bug_id, bug_status, fixed_in, tested_by, priority, name, description, comments, defect_id, file_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (row.get("ID"), row.get("Bug status"), row.get("Fixed in (CB?)"), row.get("Tested_by"), 
                  row.get("Priority"), name, description, row.get("Comments & corrective actions"), row.get("Defect ID"), filename))
        else:
            bugs_repetidos.append((name, description, existing_file[0]))

    conn.commit()
    conn.close()
    
    return render_template(
        "results.html",
        nuevos_bugs_count=len(nuevos_bugs),
        repetidos_bugs_count=len(bugs_repetidos),
        nuevos_bugs=nuevos_bugs,
        bugs_repetidos=bugs_repetidos,
        filename=filename
    )

if __name__ == "__main__":
    app.run(debug=True)
