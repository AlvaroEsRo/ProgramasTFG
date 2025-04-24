const { app, BrowserWindow, ipcMain, shell } = require('electron');
const { spawn, exec } = require('child_process');
const path = require('path');

let mainWindow;
let flaskProcess;

app.on('ready', () => {
    if (!flaskProcess) {
        // Iniciar el servidor Flask solo si no está ya iniciado
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
            nodeIntegration: true, // Habilitar Node.js en el frontend
            contextIsolation: false, // Deshabilitar el aislamiento de contexto
        },
    });

    mainWindow.loadURL('http://127.0.0.1:5000/');
});

// Manejar la solicitud de credenciales desde el frontend
ipcMain.handle('solicitar-credenciales', async () => {
    const usuario = await dialog.showInputBox({
        title: 'Usuario',
        label: 'Introduce tu usuario:',
    });

    if (!usuario) return null;

    const contraseña = await dialog.showInputBox({
        title: 'Contraseña',
        label: 'Introduce tu contraseña:',
        inputType: 'password',
    });

    if (!contraseña) return null;

    return { usuario, contraseña };
});

// Manejar la solicitud para abrir un enlace en el navegador
ipcMain.handle('abrir-enlace', async (event, url) => {
    if (url) {
        shell.openExternal(url); // Abre el enlace en el navegador predeterminado
    } else {
        console.error('No se proporcionó un enlace válido.');
    }
});

// Detener todos los procesos al cerrar la aplicación
app.on('window-all-closed', () => {
    if (flaskProcess) {
        flaskProcess.kill('SIGTERM'); // Envía una señal para terminar el proceso Flask
        flaskProcess = null;
    }

    // Detener cualquier otro proceso relacionado con Python
    exec('taskkill /F /IM python.exe', (err, stdout, stderr) => {
        if (err) {
            console.error(`Error al detener procesos Python: ${err.message}`);
        } else {
            console.log('Procesos Python detenidos:', stdout);
        }
    });

    app.quit();
});