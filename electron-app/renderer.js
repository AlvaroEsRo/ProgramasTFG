window.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('install-form');
  const logBox = document.getElementById('log-box');

  window.api.onLog(line => {
    logBox.textContent += line;
    logBox.scrollTop = logBox.scrollHeight;
  });

  form.addEventListener('submit', async e => {
    e.preventDefault();
    logBox.textContent = '';
    const filePath = document.getElementById('file-path').value;
    const carrier = document.getElementById('carrier').value;
    try {
      await window.api.runInstall(filePath, carrier);
      logBox.textContent += '\n=== Instalación completada ===\n';
    } catch(err) {
      logBox.textContent += `\n*** ERROR: ${err.message}\n`;
    }
  });
});