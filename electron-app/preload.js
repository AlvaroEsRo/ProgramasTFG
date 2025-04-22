const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  runInstall: (filePath, carrier) => ipcRenderer.invoke('run-install', { filePath, carrier }),
  onLog: cb => ipcRenderer.on('install-log', (e, line) => cb(line))
});