# ProgramasTFG

# Bug Tracker Excel - Herramienta de Análisis y Gestión

## Descripción

Bug Tracker Excel es una aplicación web desarrollada en Flask que permite analizar archivos Excel de seguimiento de bugs, identificar nuevos problemas, bugs cerrados, aún abiertos y generar reportes para plataformas como Jira. Especialmente diseñada para integrarse con los procesos de Motorola.

## Características Principales

- **Análisis de Excel**: Procesa archivos Excel con información de bugs desde la fila 11.
- **Detección inteligente de columnas**: Reconoce diferentes formatos de columnas en Excel.
- **Clasificación automática de bugs**: Categoriza bugs como nuevos, cerrados, aún abiertos o repetidos.
- **Base de datos persistente**: Almacena el historial de bugs para análisis comparativo.
- **Vista detallada de bugs**: Visualización completa de cada bug con toda su información.
- **Integración con Jira**: Generación de reportes formateados para Jira.

## Requisitos

- Python 3.6 o superior
- Flask
- pandas
- SQLite3

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/tuusuario/TFGProgramas.git
   cd TFGProgramas
   ```

2. Crea un entorno virtual:
   ```bash
   python -m venv venv
   ```

3. Activa el entorno virtual:
   - En Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - En macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. Asegúrate de que el entorno virtual esté activado:
   ```bash
   .\venv\Scripts\activate  # En Windows
   source venv/bin/activate  # En macOS/Linux
   ```

2. Ejecuta la aplicación:
   ```bash
   python .\ScriptArtifacts\sw_finder.py
   ```

3. Accede a la aplicación en tu navegador en [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Estructura del Proyecto

- `ScriptArtifacts/`: Contiene los scripts principales del proyecto.
- `templates/`: Archivos HTML para la interfaz de usuario.
- `static/`: Archivos estáticos como CSS, JavaScript e imágenes.
- `README.md`: Documentación del proyecto.

## Notas

- Asegúrate de que los archivos Excel que deseas analizar estén en el formato esperado (fila 11 como inicio de datos).
- Si necesitas agregar más dependencias, actualiza el archivo `requirements.txt` con:
  ```bash
  pip freeze > requirements.txt
  ```

## Contribuciones

Si deseas contribuir al proyecto, por favor abre un issue o envía un pull request en el repositorio.

## Licencia

Este proyecto está bajo la licencia [MIT](https://opensource.org/licenses/MIT).