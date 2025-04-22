const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

function createWindow() {
  const win = new BrowserWindow({
    width: 800, height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  });
  win.loadFile('index.html');
}

app.whenReady().then(createWindow);

ipcMain.handle('run-install', (event, { filePath, carrier }) => {
  return new Promise((resolve, reject) => {
    const isProd = process.env.NODE_ENV === 'production';
    const exePath = isProd
      ? path.join(__dirname, 'python', 'dist', 'sw_finder.exe')
      : 'python';
    const args = isProd
      ? ['--install', filePath, carrier]
      : [path.join(__dirname, 'python', 'sw_finder.py'), '--install', filePath, carrier];

    const child = spawn(exePath, args, { cwd: __dirname });
    child.stdout.on('data', data => event.sender.send('install-log', data.toString()));
    child.stderr.on('data', data => event.sender.send('install-log', `ERR> ${data}`));
    child.on('close', code => code === 0 ? resolve() : reject(new Error(`exit ${code}`)));
  });
});