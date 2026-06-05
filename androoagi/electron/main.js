'use strict';

const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const Store = require('electron-store');
const { runCycle, stopCycle } = require('./workflow/cycle');

// ── Config store ──────────────────────────────────────────────────────────────
const store = new Store({
  name: 'androoagi',
  defaults: {
    apiKey: '',
    cycles: [],
    totalOppsFound: 0,
    totalCycles: 0,
  },
});

const IS_DEV = process.env.NODE_ENV === 'development' || process.argv.includes('--dev');
let mainWindow = null;
let cycleRunning = false;

// ── Emit helper ───────────────────────────────────────────────────────────────
function emit(channel, data) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send(channel, data);
  }
}

// ── Window ────────────────────────────────────────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    frame: false,
    titleBarStyle: 'hidden',
    backgroundColor: '#0a0a0f',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  if (IS_DEV) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }

  mainWindow.on('closed', () => { mainWindow = null; });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) shell.openExternal(url);
    return { action: 'deny' };
  });
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
app.on('activate', () => { if (!mainWindow) createWindow(); });

// ── IPC: Window controls ──────────────────────────────────────────────────────
ipcMain.on('window:minimize', () => mainWindow?.minimize());
ipcMain.on('window:maximize', () => {
  if (mainWindow?.isMaximized()) mainWindow.unmaximize();
  else mainWindow?.maximize();
});
ipcMain.on('window:close', () => mainWindow?.close());

// ── IPC: Settings ─────────────────────────────────────────────────────────────
ipcMain.handle('settings:get', () => ({
  apiKey: store.get('apiKey') || '',
}));

ipcMain.handle('settings:save', (_e, { apiKey }) => {
  store.set('apiKey', apiKey);
  return { ok: true };
});

// ── IPC: Cycles ───────────────────────────────────────────────────────────────
ipcMain.handle('cycles:list', () => {
  return store.get('cycles', []);
});

ipcMain.handle('cycles:get', (_e, cycleId) => {
  const cycles = store.get('cycles', []);
  return cycles.find(c => c.id === cycleId) ?? null;
});

ipcMain.handle('cycles:clear', () => {
  store.set('cycles', []);
  return { ok: true };
});

ipcMain.handle('stats:get', () => ({
  totalOppsFound: store.get('totalOppsFound', 0),
  totalCycles: store.get('totalCycles', 0),
  readyToLaunch: (() => {
    const cycles = store.get('cycles', []);
    return cycles.filter(c => c.status === 'complete' && c.approvalStatus !== 'all_approved').length;
  })(),
}));

// ── IPC: Cycle control ────────────────────────────────────────────────────────
ipcMain.on('cycle:start', async (_e, opts) => {
  if (cycleRunning) return;
  const apiKey = store.get('apiKey');
  if (!apiKey) {
    emit('cycle:error', { message: 'API key not configured. Open Settings to add your Anthropic API key.' });
    return;
  }

  cycleRunning = true;
  emit('cycle:started', { mode: opts.mode ?? 'build', focusNiche: opts.focusNiche });

  try {
    const cycle = await runCycle({ emit, apiKey, opts });

    // Save to store
    const cycles = store.get('cycles', []);
    cycles.unshift(cycle);
    if (cycles.length > 50) cycles.pop(); // keep last 50
    store.set('cycles', cycles);
    store.set('totalCycles', (store.get('totalCycles', 0)) + 1);
    store.set('totalOppsFound', (store.get('totalOppsFound', 0)) + (cycle.opportunities?.length ?? 0));

    emit('cycle:complete', cycle);
  } catch (err) {
    console.error('[cycle error]', err);
    emit('cycle:error', { message: err.message });
  } finally {
    cycleRunning = false;
  }
});

ipcMain.on('cycle:stop', () => {
  stopCycle();
  cycleRunning = false;
  emit('cycle:stopped', {});
});

// ── IPC: Approvals ────────────────────────────────────────────────────────────
ipcMain.handle('approval:update', (_e, { cycleId, itemId, action }) => {
  const cycles = store.get('cycles', []);
  const cycle = cycles.find(c => c.id === cycleId);
  if (!cycle) return { ok: false };

  if (itemId === 'all') {
    cycle.approvalItems = cycle.approvalItems.map(i => ({ ...i, status: action }));
    cycle.approvalStatus = action === 'approved' ? 'all_approved' : 'all_rejected';
  } else {
    const item = cycle.approvalItems.find(i => i.id === itemId);
    if (item) item.status = action;
    const allApproved = cycle.approvalItems.every(i => i.status === 'approved');
    cycle.approvalStatus = allApproved ? 'all_approved' : 'partial';
  }

  store.set('cycles', cycles);
  return { ok: true, cycle };
});

ipcMain.on('shell:open', (_e, url) => {
  if (url.startsWith('http')) shell.openExternal(url);
});
