'use strict';

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Window controls
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close:    () => ipcRenderer.send('window:close'),

  // Settings
  getSettings: ()       => ipcRenderer.invoke('settings:get'),
  saveSettings: (data)  => ipcRenderer.invoke('settings:save', data),

  // Cycles
  listCycles:  ()      => ipcRenderer.invoke('cycles:list'),
  getCycle:    (id)    => ipcRenderer.invoke('cycles:get', id),
  clearCycles: ()      => ipcRenderer.invoke('cycles:clear'),

  // Stats
  getStats: () => ipcRenderer.invoke('stats:get'),

  // Cycle control
  startCycle: (opts) => ipcRenderer.send('cycle:start', opts),
  stopCycle:  ()     => ipcRenderer.send('cycle:stop'),

  // Approvals
  updateApproval: (payload) => ipcRenderer.invoke('approval:update', payload),

  // External links
  openExternal: (url) => ipcRenderer.send('shell:open', url),

  // Event listeners (renderer subscribes to main-process events)
  on: (channel, fn) => {
    const allowed = [
      'cycle:started', 'cycle:complete', 'cycle:error', 'cycle:stopped',
      'agent:status', 'agent:chunk', 'agent:complete',
    ];
    if (allowed.includes(channel)) {
      const sub = (_e, ...args) => fn(...args);
      ipcRenderer.on(channel, sub);
      return () => ipcRenderer.removeListener(channel, sub);
    }
  },

  once: (channel, fn) => {
    ipcRenderer.once(channel, (_e, ...args) => fn(...args));
  },
});
