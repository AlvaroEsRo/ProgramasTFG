const { app, BrowserWindow, ipcMain, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let mainWindow;
let flaskProcess;

app.on('ready', () => {
    if (!flaskProcess) {
        // Iniciar el servidor Flask
        flaskProcess = spawn('python', [path.join(__dirname, 'python', 'sw_finder.py')]);

        flaskProcess.stdout.on('data', (data) => {
            console.log(`Flask: ${data}`);
        });

        flaskProcess.stderr.on('data', (data) => {
            console.error(`Flask Error: ${data}`);
        });

        flaskProcess.on('close', (code) => {
            console.log(`Flask process exited with code ${code}`);
            flaskProcess = null;
        });
    }

    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
        },
    });

    mainWindow.loadURL('http://127.0.0.1:5000/');
});

// Manejar la solicitud para abrir un enlace en el navegador
ipcMain.handle('abrir-enlace', async (event, url) => {
    if (url) {
        shell.openExternal(url); // Abre el enlace en el navegador predeterminado
    } else {
        console.error('No se proporcionó un enlace válido.');
    }
});

// Detener el servidor Flask al cerrar la aplicación
app.on('window-all-closed', () => {
    if (flaskProcess) {
        flaskProcess.kill('SIGTERM');
    }
    app.quit();
});