import React, { useEffect, useState } from 'react';
import { useAppStore } from '../store/appStore';

export default function SettingsModal() {
  const { settingsOpen, setSettingsOpen } = useAppStore();
  const [apiKey, setApiKey] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (settingsOpen) {
      window.electronAPI.getSettings().then((s: any) => {
        setApiKey(s.apiKey ?? '');
      });
    }
  }, [settingsOpen]);

  if (!settingsOpen) return null;

  async function handleSave() {
    setSaving(true);
    await window.electronAPI.saveSettings({ apiKey: apiKey.trim() });
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  function handleClear() {
    if (window.confirm('Clear all cycle history? This cannot be undone.')) {
      window.electronAPI.clearCycles();
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-surface border border-border rounded-2xl w-full max-w-md p-6 shadow-2xl panel-slide-in">
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-bold text-white">Settings</h2>
          <button
            className="text-white/40 hover:text-white transition-colors text-lg"
            onClick={() => setSettingsOpen(false)}
          >
            ✕
          </button>
        </div>

        <div className="space-y-5">
          {/* API Key */}
          <div>
            <label className="block text-xs text-white/50 mb-2 uppercase tracking-widest">
              Anthropic API Key
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              placeholder="sk-ant-api..."
              className="w-full bg-surface-2 border border-border rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/20 outline-none focus:border-agents-orchestrator/60 transition-colors"
            />
            <p className="text-[10px] text-white/30 mt-2">
              Get yours at{' '}
              <button
                className="text-agents-scout underline"
                onClick={() => window.electronAPI.openExternal('https://console.anthropic.com')}
              >
                console.anthropic.com
              </button>
              . Stored locally — never uploaded.
            </p>
          </div>

          {/* Save button */}
          <button
            className={`w-full h-10 rounded-xl font-bold text-sm transition-all ${
              saved
                ? 'bg-agents-store/20 text-agents-store border border-agents-store/30'
                : 'bg-agents-orchestrator text-white hover:opacity-90'
            }`}
            onClick={handleSave}
            disabled={saving}
          >
            {saved ? '✓ Saved!' : saving ? 'Saving...' : 'Save Settings'}
          </button>

          {/* Danger zone */}
          <div className="border-t border-border pt-4">
            <div className="text-[10px] text-white/30 uppercase tracking-widest mb-3">Danger Zone</div>
            <button
              className="w-full h-9 rounded-xl border border-red-500/20 text-red-400/60 text-xs hover:bg-red-500/10 hover:text-red-400 transition-colors"
              onClick={handleClear}
            >
              Clear All Cycle History
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
