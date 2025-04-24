const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let mainWindow;

app.on('ready', () => {
    // Iniciar el servidor Flask
    const flaskProcess = spawn(path.join(__dirname, 'python', 'dist', 'sw_finder.exe'));

    flaskProcess.stdout.on('data', (data) => {
        console.log(`Flask: ${data}`);
    });

    flaskProcess.stderr.on('data', (data) => {
        console.error(`Flask Error: ${data}`);
    });

    // Crear la ventana de Electron
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: false, // No se necesita Node.js en el frontend
        },
    });

    // Cargar la página principal desde Flask
    mainWindow.loadURL('http://127.0.0.1:5000/');
});

app.on('window-all-closed', () => {
    app.quit();
});