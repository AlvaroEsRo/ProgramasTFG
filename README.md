# ProgramasTFG

## Overview

**ProgramasTFG** is a multi-tool project designed for Motorola software and bug management workflows. It includes:

- **Bug Tracker Excel**: A web application (Flask) for analyzing and reporting bugs from Excel files.
- **Firmware Installer**: A desktop application (Electron + Flask backend) for downloading, extracting, and flashing Motorola firmware images, with device detection and log export features.

---

## Features

### Bug Tracker Excel

- Analyze Excel bug tracking files (starting from row 11).
- Smart column detection for various Excel formats.
- Automatic bug classification: new, closed, open, or duplicate.
- Persistent database for historical bug analysis.
- Detailed bug views.
- Jira-formatted report generation.

### Firmware Installer

- Download Motorola firmware from Artifactory using project, Android version, and build type.
- Extract `.tar.gz` and `.tar` firmware packages using 7-Zip.
- Detect and flash devices via ADB and Fastboot.
- Run `flashall.bat` automatically after extraction.
- Export connected device info to Excel.
- Integrated logs for all operations.

---

## Requirements

- **Python 3.6+**
- **Node.js 16+** (for Electron app)
- **7-Zip** (installed at `C:\Program Files\7-Zip\7z.exe`)
- **pip** (Python package manager)
- **npm** (Node.js package manager)

**Python dependencies:**  
See `requirements.txt` (includes Flask, pandas, etc.)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/youruser/TFGProgramas.git
cd TFGProgramas
```

### 2. Set Up Python Environment

#### Windows

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

#### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set Up Electron Environment

```bash
npm install
```

---

## Usage

### Bug Tracker Excel

1. Activate the Python virtual environment:
   ```bash
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

2. Run the application:
   ```bash
   python .\ScriptArtifacts\sw_finder.py
   ```

3. Open your browser and go to [http://127.0.0.1:5000](http://127.0.0.1:5000).

### Firmware Installer

1. Build the Electron app:
   ```bash
   npm run build
   ```

2. Run the installer from the `dist` folder.

---

## Project Structure

- `ScriptArtifacts/`: Contains main project scripts.
- `templates/`: HTML files for the user interface.
- `static/`: Static files like CSS, JavaScript, and images.
- `README.md`: Project documentation.

---

## Notes

- Ensure Excel files are in the expected format (data starting from row 11).
- For additional dependencies, update `requirements.txt` with:
  ```bash
  pip freeze > requirements.txt
  ```

---

**Developed with ❤️ by Alvaro Estevez Rodriguez as part of my Final Degree Project (TFG).**

## Distribution as a Single Executable (Windows)

To distribute the application as a single executable file for Windows (without requiring Python installation), follow these steps:

1. **Package the Python backend:**
   - Install PyInstaller:
     ```bash
     pip install pyinstaller
     ```
   - From the `python` folder, run:
     ```bash
     pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" sw_finder.py
     ```
   - The executable will be generated in `python/dist/sw_finder.exe`.

2. **Configure Electron to launch the executable:**
   - In the Electron `main.js` file, change the line that launches Flask to:
     ```js
     flaskProcess = spawn(path.join(__dirname, 'python', 'dist', 'sw_finder.exe'));
     ```

3. **Package the Electron application:**
   - Install electron-builder:
     ```bash
     npm install --save-dev electron-builder
     ```
   - Add the appropriate configuration in `package.json` to include the executable.
   - Run the build:
     ```bash
     npm run build
     ```
   - The installer generated in the `dist/` folder will work on any Windows machine without requiring Python.

**Note:**  
Ensure that any external dependencies (like 7-Zip) are available on the target machine or included in the package.