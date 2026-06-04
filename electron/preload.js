'use strict';
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  onBootStatus: (cb) => ipcRenderer.on('boot-status', (_e, msg) => cb(msg)),
  onBootDone:   (cb) => ipcRenderer.once('boot-done', (_e, url) => cb(url)),
  getVersion:   ()   => ipcRenderer.invoke('get-version'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
});
