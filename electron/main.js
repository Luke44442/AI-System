'use strict';

const { app, BrowserWindow, ipcMain, shell, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');

// ── Config ──────────────────────────────────────────────────────────────────
const APP_PORT   = 3000;
const APP_URL    = `http://localhost:${APP_PORT}`;
const IS_DEV     = process.env.NODE_ENV === 'development' || !app.isPackaged;
const LOG_FILE   = path.join(app.getPath('userData'), 'growthiq.log');

let mainWindow   = null;
let splashWindow = null;
let nextProcess  = null;

// ── Logging ─────────────────────────────────────────────────────────────────
function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  process.stdout.write(line);
  fs.appendFileSync(LOG_FILE, line);
}

// ── Wait for port ────────────────────────────────────────────────────────────
function waitForPort(port, timeout = 60_000) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    function check() {
      http.get(`http://localhost:${port}`, res => {
        resolve();
      }).on('error', () => {
        if (Date.now() - start > timeout) {
          reject(new Error(`Timeout waiting for port ${port}`));
        } else {
          setTimeout(check, 1000);
        }
      });
    }
    check();
  });
}

// ── Spawn Next.js server ─────────────────────────────────────────────────────
function startNextServer() {
  const appDir = IS_DEV
    ? path.join(__dirname, '..', 'saas')
    : path.join(process.resourcesPath, 'app', 'saas');

  log(`Starting Next.js from: ${appDir}`);

  const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';

  nextProcess = spawn(npmCmd, ['start', '--', '-p', String(APP_PORT)], {
    cwd: appDir,
    env: {
      ...process.env,
      NODE_ENV: 'production',
      PORT: String(APP_PORT),
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  nextProcess.stdout.on('data', d => log(`[next] ${d.toString().trim()}`));
  nextProcess.stderr.on('data', d => log(`[next:err] ${d.toString().trim()}`));

  nextProcess.on('exit', (code, signal) => {
    log(`Next.js exited: code=${code} signal=${signal}`);
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('server-crashed');
    }
  });
}

// ── Splash window ─────────────────────────────────────────────────────────────
function createSplash() {
  splashWindow = new BrowserWindow({
    width: 420,
    height: 340,
    frame: false,
    resizable: false,
    center: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    backgroundColor: '#080c14',
    show: false,
  });

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
  splashWindow.once('ready-to-show', () => splashWindow.show());
}

// ── Main window ───────────────────────────────────────────────────────────────
function createMain() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 680,
    show: false,
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    backgroundColor: '#080c14',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  mainWindow.loadURL(APP_URL);

  mainWindow.once('ready-to-show', () => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.destroy();
    }
    mainWindow.show();
    if (IS_DEV) mainWindow.webContents.openDevTools();
  });

  mainWindow.on('closed', () => { mainWindow = null; });

  // Open external links in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) shell.openExternal(url);
    return { action: 'deny' };
  });
}

// ── App lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(async () => {
  createSplash();

  try {
    if (!IS_DEV) {
      // In production, start the bundled Next.js server
      startNextServer();
      log('Waiting for Next.js to be ready…');
    }

    // In dev mode, expect `npm run dev` to already be running
    await waitForPort(APP_PORT, IS_DEV ? 30_000 : 90_000);
    log('Server ready — launching main window');

    createMain();
  } catch (err) {
    log(`Boot error: ${err.message}`);
    dialog.showErrorBox(
      'GrowthIQ failed to start',
      `Could not connect to the application server.\n\nError: ${err.message}\n\nCheck the log at: ${LOG_FILE}`,
    );
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (!mainWindow) createMain();
});

app.on('before-quit', () => {
  if (nextProcess) {
    log('Shutting down Next.js server…');
    nextProcess.kill('SIGTERM');
  }
});

// ── IPC handlers ──────────────────────────────────────────────────────────────
ipcMain.handle('get-version', () => app.getVersion());

ipcMain.handle('open-external', (_e, url) => {
  if (url.startsWith('http')) shell.openExternal(url);
});

// Restart server if crashed
ipcMain.on('restart-server', () => {
  if (nextProcess) nextProcess.kill();
  startNextServer();
});
