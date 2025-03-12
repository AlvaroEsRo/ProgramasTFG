import pandas as pd
import sqlite3
import os

def analizar_bugs_excel(ruta_excel):
    # 1. Leer el archivo Excel
    print(f"Leyendo archivo: {ruta_excel}")
    df = pd.read_excel(ruta_excel)
    
    # 2. Verificar las columnas disponibles y mapearlas correctamente
    # Las columnas que observo en la imagen son:
    # - ID (primera columna)
    # - Bug status
    # - Fixed in (CB?)
    # - Tested in (Data?)
    # - Fixed to get (priority/date)
    # - Priority for Change
    # - Name
    # - BUG DESCRIPTION
    # - Comments & corrective actions
    # - Defect ID
    
    # Verificar columnas obligatorias
    columnas_requeridas = ["Name", "BUG DESCRIPTION"]
    for col in columnas_requeridas:
        if col not in df.columns:
            print(f"Error: La columna '{col}' no existe en el Excel")
            return
    
    # 3. Conectar a la base de datos SQLite
    conn = sqlite3.connect("bugs_database.db")
    cursor = conn.cursor()
    
    # 4. Crear la tabla si no existe
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bugs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bug_id TEXT,
        bug_status TEXT,
        fixed_in TEXT,
        tested_in TEXT,
        priority TEXT,
        name TEXT,
        description TEXT,
        comments TEXT,
        defect_id TEXT,
        device TEXT,
        import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    
    # 5. Insertar registros en la base de datos
    registros_insertados = 0
    for index, row in df.iterrows():
        # Extraer valores, usando None si no existe la columna
        bug_id = row.get("Defect ID", None) if "Defect ID" in row else None
        bug_status = row.get("Bug status", None) if "Bug status" in row else None
        fixed_in = row.get("Fixed in (CB?)", None) if "Fixed in (CB?)" in row else None
        tested_in = row.get("Tested in (Data?)", None) if "Tested in (Data?)" in row else None
        priority = row.get("Priority for Change", None) if "Priority for Change" in row else None
        name = row.get("Name", None) 
        description = row.get("BUG DESCRIPTION", None)
        comments = row.get("Comments & corrective actions", None) if "Comments & corrective actions" in row else None
        
        # Si no hay un bug_id específico, usamos una combinación de name+description
        if not bug_id:
            bug_id = f"{str(name)[:20]}_{hash(str(description))}"
        
        cursor.execute("""
        INSERT INTO bugs 
        (bug_id, bug_status, fixed_in, tested_in, priority, name, description, comments, defect_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (bug_id, bug_status, fixed_in, tested_in, priority, name, description, comments, bug_id))
        registros_insertados += 1
    
    conn.commit()
    print(f"Se han insertado {registros_insertados} registros en la base de datos.")
    
    # 6. Analizar bugs para identificar duplicados
    cursor.execute("""
    SELECT name, description, COUNT(*) as total_count
    FROM bugs
    GROUP BY name, description
    HAVING COUNT(*) > 1
    ORDER BY total_count DESC
    """)
    
    duplicados = cursor.fetchall()
    
    print("\n=== REPORTE DE BUGS DUPLICADOS ===")
    if duplicados:
        for name, desc, count in duplicados:
            print(f"Bug: {name}")
            print(f"Descripción: {desc[:100]}..." if len(desc) > 100 else desc)
            print(f"Encontrado {count} veces en la base de datos")
            print("-" * 50)
    else:
        print("No se encontraron bugs duplicados.")
    
    # 7. Listar bugs nuevos (los que solo aparecen una vez)
    cursor.execute("""
    SELECT name, description
    FROM bugs
    GROUP BY name, description
    HAVING COUNT(*) = 1
    """)
    
    nuevos = cursor.fetchall()
    
    print("\n=== REPORTE DE BUGS NUEVOS ===")
    print(f"Se encontraron {len(nuevos)} bugs nuevos (no duplicados).")
    for i, (name, desc) in enumerate(nuevos[:5], 1):  # Mostrar solo los primeros 5 para no saturar
        print(f"{i}. {name}: {desc[:100]}..." if len(desc) > 100 else desc)
    
    if len(nuevos) > 5:
        print(f"... y {len(nuevos) - 5} más.")
    
    # Cerrar la conexión
    conn.close()

# Función principal para ejecutar el programa
if __name__ == "__main__":
    # Pedir la ruta del archivo Excel
    ruta_excel = input("Introduce la ruta del archivo Excel de bugs (o presiona Enter para usar 'bugs.xlsx'): ")
    if not ruta_excel:
        ruta_excel = "bugs.xlsx"
    
    # Verificar si el archivo existe
    if not os.path.exists(ruta_excel):
        print(f"Error: No se encuentra el archivo '{ruta_excel}'.")
    else:
        analizar_bugs_excel(ruta_excel)
