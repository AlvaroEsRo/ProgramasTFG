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

# Inicializar la base de datos solo si no existe
def init_db():
    conn = sqlite3.connect('bugs_database.db')
    cursor = conn.cursor()
    
    # En lugar de eliminar la tabla, solo la creamos si no existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bugs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bug_number TEXT,
        discovery_date TEXT,
        raised_in TEXT,
        bug_status TEXT,
        fixed_in TEXT,
        fixed_by TEXT,
        tested_by TEXT,
        technology TEXT,
        priority TEXT,
        name TEXT,
        description TEXT,
        comments TEXT,
        defect_id TEXT
    )
    ''')
    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente.")

def init_cr_db():
    conn = sqlite3.connect('bugs_database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS change_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bug_number TEXT,
        project TEXT,
        issue_type TEXT,
        summary TEXT,
        affects_version TEXT,
        team_found TEXT,
        region_code TEXT,
        country TEXT,
        carrier TEXT,
        components TEXT,
        severity TEXT,
        description TEXT,
        created_at TEXT,
        FOREIGN KEY (bug_number) REFERENCES bugs(bug_number)
    )
    ''')
    conn.commit()
    conn.close()
    print("Tabla de CRs inicializada correctamente.")

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            return redirect(url_for('analyze_bugs', filename=file.filename))
    return render_template('upload.html')

@app.route('/analyze/<filename>')
def analyze_bugs(filename):
    # Aseguramos que la base de datos existe pero NO la reiniciamos
    init_db()
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Leer el Excel desde la fila 11 (índice 10)
    df = pd.read_excel(filepath, header=10)
    
    # Imprime los nombres de las columnas para diagnóstico
    print("Columnas disponibles:", df.columns.tolist())
    
    conn = sqlite3.connect('bugs_database.db')
    cursor = conn.cursor()

    new_bugs = []
    closed_bugs = []
    still_open_bugs = []
    repeated_bugs = []

    # Mapeo flexible de nombres de columnas
    column_mapping = {
        'bug_number': ['Bug number', 'bug number', 'BUG NUMBER', 'Bug Number'],
        'bug_status': ['Bug status', 'bug status', 'BUG STATUS', 'Bug Status'],
        'name': ['Name', 'name', 'NAME'],
        'description': ['BUG DESCRIPTION', 'Bug Description', 'bug description', 'Description'],
        'discovery_date': ['discovery date', 'Discovery date', 'DISCOVERY DATE', 'Discovery Date'],
        'raised_in': ['Raised in\n(Soft. Vers.)', 'raised in', 'Raised in'],
        'fixed_in': ['Fixed in\n(Soft. Vers.)', 'fixed in', 'Fixed in'],
        'fixed_by': ['Fixed by QA or on prototype (prototype by default)', 'Fixed by'],
        'tested_by': ['Tested by  MCO', 'Tested by', 'tested by'],
        'technology': ['Technology', 'technology', 'TECHNOLOGY'],
        'priority': ['Priority', 'priority', 'PRIORITY'],
        'comments': ['Comments & corrective actions', 'Comments', 'comments'],
        'defect_id': ['Defect ID QC', 'defect id', 'Defect ID']
    }
    
    # Función para encontrar la columna correcta
    def find_column(possible_names):
        for name in possible_names:
            if name in df.columns:
                return name
        return None
    
    # Verificar si tenemos todas las columnas necesarias
    missing_columns = []
    columns = {}
    for key, possible_names in column_mapping.items():
        col_name = find_column(possible_names)
        if col_name:
            columns[key] = col_name
        else:
            missing_columns.append(key)
    
    if missing_columns:
        return f"Error: Columnas no encontradas: {', '.join(missing_columns)}"
    
    # Imprimir la asignación para depuración
    print("Asignación de columnas:", columns)
    
    # Definir función safe_get_value fuera del bucle
    def safe_get_value(row, key):
        try:
            value = row[columns[key]]
            return None if pd.isna(value) else value
        except Exception as e:
            print(f"Error al acceder a {key}: {e}")
            return None
    
    # Primero, determinar qué bugs ya existen en la base de datos
    existing_bug_numbers = {}  # Guardaremos bug_number -> bug_status
    try:
        cursor.execute("SELECT bug_number, bug_status FROM bugs")
        for row in cursor.fetchall():
            if row[0]:
                existing_bug_numbers[str(row[0]).strip()] = row[1]
    except Exception as e:
        print(f"Error al consultar bugs existentes: {e}")
    
    print(f"Bugs existentes en la base de datos: {existing_bug_numbers}")
    
    # Procesar cada fila del Excel
    for _, row in df.iterrows():
        try:
            # Acceder a los valores usando los nombres reales de columnas
            bug_number = str(row[columns['bug_number']]).strip()
            bug_status = row[columns['bug_status']]
            name = row[columns['name']]
            description = row[columns['description']]
            
            # Si alguna de las columnas principales es nula, saltamos la fila
            if pd.isna(bug_number) or pd.isna(bug_status) or pd.isna(name):
                print(f"Fila con valores nulos importantes, saltando...")
                continue
            
            print(f"Procesando bug: {bug_number}, estado: {bug_status}")
            
            # Convertir la fecha a string si no es nula
            discovery_date = safe_get_value(row, 'discovery_date')
            if pd.notnull(discovery_date):
                if isinstance(discovery_date, datetime):
                    discovery_date = discovery_date.strftime('%Y-%m-%d')
                else:
                    discovery_date = str(discovery_date)
            
            # Clasificar el bug
            bug_exists = bug_number in existing_bug_numbers
            
            if bug_exists:
                print(f"Bug {bug_number} existe en la base de datos")
                repeated_bugs.append((bug_number, name))
                
                # Obtener el estado anterior del bug
                previous_status = existing_bug_numbers.get(bug_number, '')
                
                if bug_status == 'CLOSED' and previous_status != 'CLOSED':
                    closed_bugs.append((bug_number, name))
                    print(f"Bug {bug_number} marcado como cerrado")
                elif bug_status == 'OPEN':
                    still_open_bugs.append((bug_number, name))
                    print(f"Bug {bug_number} sigue abierto")
                
                # Actualizar el bug existente
                try:
                    cursor.execute('''
                    UPDATE bugs SET 
                        bug_status = ?,
                        fixed_in = ?,
                        comments = ?
                    WHERE bug_number = ?
                    ''', (
                        bug_status, 
                        safe_get_value(row, 'fixed_in'), 
                        safe_get_value(row, 'comments'), 
                        bug_number
                    ))
                    print(f"Bug actualizado: {bug_number}")
                except Exception as e:
                    print(f"Error al actualizar bug {bug_number}: {e}")
            else:
                print(f"Bug {bug_number} es nuevo")
                new_bugs.append((bug_number, name))
                
                # Insertar el nuevo bug
                try:
                    cursor.execute('''
                    INSERT INTO bugs (
                        bug_number, discovery_date, raised_in, bug_status, fixed_in, 
                        fixed_by, tested_by, technology, priority, name, description, 
                        comments, defect_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        bug_number,
                        discovery_date,
                        safe_get_value(row, 'raised_in'),
                        bug_status,
                        safe_get_value(row, 'fixed_in'),
                        safe_get_value(row, 'fixed_by'),
                        safe_get_value(row, 'tested_by'),
                        safe_get_value(row, 'technology'),
                        safe_get_value(row, 'priority'),
                        name,
                        description,
                        safe_get_value(row, 'comments'),
                        safe_get_value(row, 'defect_id')
                    ))
                    print(f"Bug insertado: {bug_number}")
                except Exception as e:
                    print(f"Error al insertar bug {bug_number}: {e}")
        except Exception as e:
            print(f"Error procesando fila: {e}")
            continue
    
    # Imprimir resumen
    print(f"Nuevos bugs: {len(new_bugs)}")
    print(f"Bugs cerrados: {len(closed_bugs)}")
    print(f"Bugs aún abiertos: {len(still_open_bugs)}")
    print(f"Bugs repetidos: {len(repeated_bugs)}")
    
    conn.commit()
    conn.close()
    
    # Asegurarse de que las listas contienen datos reales para depuración
    print("Nuevos bugs:", new_bugs)
    print("Bugs cerrados:", closed_bugs)
    print("Bugs aún abiertos:", still_open_bugs)
    
    return render_template('results.html', 
                          new_bugs=new_bugs, 
                          closed_bugs=closed_bugs, 
                          still_open_bugs=still_open_bugs, 
                          repeated_bugs=repeated_bugs,
                          filename=filename)
@app.route('/bug/<bug_number>/<filename>')
def view_bug(bug_number, filename):
    conn = sqlite3.connect('bugs_database.db')
    cursor = conn.cursor()
    
    # Obtener los detalles del bug
    cursor.execute("""
    SELECT bug_number, discovery_date, raised_in, bug_status, fixed_in, 
           fixed_by, tested_by, technology, priority, name, description, 
           comments, defect_id
    FROM bugs WHERE bug_number = ?
    """, (bug_number,))
    
    bug_details = cursor.fetchone()
    conn.close()
    
    if not bug_details:
        return "Bug no encontrado", 404
    
    # Convertir a diccionario para facilitar el acceso en la plantilla
    bug_info = {
        'bug_number': bug_details[0],
        'discovery_date': bug_details[1],
        'raised_in': bug_details[2],
        'bug_status': bug_details[3],
        'fixed_in': bug_details[4],
        'fixed_by': bug_details[5],
        'tested_by': bug_details[6],
        'technology': bug_details[7],
        'priority': bug_details[8],
        'name': bug_details[9],
        'description': bug_details[10],
        'comments': bug_details[11],
        'defect_id': bug_details[12]
    }
    
    return render_template('bug_details.html', bug=bug_info, filename=filename)
# Añadir esta nueva ruta antes del if __name__ == '__main__':

@app.route('/jira_report/<bug_number>', methods=['GET', 'POST'])
def jira_report(bug_number):
    conn = sqlite3.connect('bugs_database.db')
    cursor = conn.cursor()
    
    # Obtener los detalles del bug
    cursor.execute("""
    SELECT bug_number, discovery_date, raised_in, bug_status, fixed_in, 
           fixed_by, tested_by, technology, priority, name, description, 
           comments, defect_id
    FROM bugs WHERE bug_number = ?
    """, (bug_number,))
    
    bug_details = cursor.fetchone()
    
    if not bug_details:
        conn.close()
        return "Bug no encontrado", 404
    
    # Convertir a diccionario para facilitar el acceso en la plantilla
    bug_info = {
        'bug_number': bug_details[0],
        'discovery_date': bug_details[1],
        'raised_in': bug_details[2],
        'bug_status': bug_details[3],
        'fixed_in': bug_details[4],
        'fixed_by': bug_details[5],
        'tested_by': bug_details[6],
        'technology': bug_details[7],
        'priority': bug_details[8],
        'name': bug_details[9],
        'description': bug_details[10],
        'comments': bug_details[11],
        'defect_id': bug_details[12]
    }
    
    # Manejar envío del formulario
    if request.method == 'POST':
        cr_data = {
            'bug_number': bug_number,
            'project': request.form.get('project'),
            'issue_type': request.form.get('issueType'),
            'summary': request.form.get('summary'),
            'affects_version': request.form.get('affectsVersion'),
            'team_found': request.form.get('teamFound'),
            'region_code': request.form.get('regionCode'),
            'country': request.form.get('country'),
            'carrier': request.form.get('carrier'),
            'components': request.form.get('components'),
            'severity': request.form.get('severity'),
            'description': request.form.get('description'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Guardar CR en la base de datos
        cursor.execute('''
        INSERT INTO change_requests (
            bug_number, project, issue_type, summary, affects_version,
            team_found, region_code, country, carrier, components,
            severity, description, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            cr_data['bug_number'],
            cr_data['project'],
            cr_data['issue_type'],
            cr_data['summary'],
            cr_data['affects_version'],
            cr_data['team_found'],
            cr_data['region_code'],
            cr_data['country'],
            cr_data['carrier'],
            cr_data['components'],
            cr_data['severity'],
            cr_data['description'],
            cr_data['created_at']
        ))
        conn.commit()
        
        # Obtener el ID del CR recién insertado
        cr_id = cursor.lastrowid
        conn.close()
        
        # Redirigir a la página de visualización del CR
        return redirect(url_for('view_cr', cr_id=cr_id))
    
    conn.close()
    return render_template('jira_report.html', bug=bug_info)

@app.route('/view_cr/<int:cr_id>')
def view_cr(cr_id):
    conn = sqlite3.connect('bugs_database.db')
    cursor = conn.cursor()
    
    # Obtener los detalles del CR
    cursor.execute("""
    SELECT id, bug_number, project, issue_type, summary, affects_version,
           team_found, region_code, country, carrier, components,
           severity, description, created_at
    FROM change_requests WHERE id = ?
    """, (cr_id,))
    
    cr_details = cursor.fetchone()
    
    if not cr_details:
        conn.close()
        return "CR no encontrado", 404
    
    # Convertir a diccionario
    cr_info = {
        'id': cr_details[0],
        'bug_number': cr_details[1],
        'project': cr_details[2],
        'issue_type': cr_details[3],
        'summary': cr_details[4],
        'affects_version': cr_details[5],
        'team_found': cr_details[6],
        'region_code': cr_details[7],
        'country': cr_details[8],
        'carrier': cr_details[9],
        'components': cr_details[10],
        'severity': cr_details[11],
        'description': cr_details[12],
        'created_at': cr_details[13]
    }
    
    # Obtener información del bug relacionado
    cursor.execute("SELECT name FROM bugs WHERE bug_number = ?", (cr_info['bug_number'],))
    bug_name = cursor.fetchone()
    if bug_name:
        cr_info['bug_name'] = bug_name[0]
    
    conn.close()
    return render_template('view_cr.html', cr=cr_info)

@app.route('/saved_crs')
def saved_crs():
    conn = sqlite3.connect('bugs_database.db')
    cursor = conn.cursor()
    
    # Obtener todos los CRs guardados
    cursor.execute("""
    SELECT cr.id, cr.bug_number, cr.summary, cr.created_at, cr.severity, b.name
    FROM change_requests cr
    LEFT JOIN bugs b ON cr.bug_number = b.bug_number
    ORDER BY cr.created_at DESC
    """)
    
    crs = cursor.fetchall()
    conn.close()
    
    return render_template('saved_crs.html', crs=crs)

if __name__ == '__main__':
    init_db()  # Inicializar la tabla de bugs
    init_cr_db()  # Inicializar la tabla de CRs
    app.run(debug=True)