import React, { useState } from 'react';
import { useAppStore, CycleMode } from '../store/appStore';

const MODES: { value: CycleMode; label: string; desc: string }[] = [
  { value: 'explore', label: 'EXPLORE',      desc: 'Research ideas only' },
  { value: 'build',   label: 'BUILD',        desc: 'Full store + brand' },
  { value: 'launch',  label: 'LAUNCH PREP',  desc: 'Everything + approval' },
];

export default function TopBar() {
  const { cycleRunning, stats, settingsOpen, setSettingsOpen, setCycleRunning, clearCenterBuffer } = useAppStore();
  const [mode, setMode] = useState<CycleMode>('launch');
  const [focusNiche, setFocusNiche] = useState('');
  const [showModes, setShowModes] = useState(false);

  function handleStart() {
    if (cycleRunning) {
      window.electronAPI.stopCycle();
      setCycleRunning(false);
    } else {
      clearCenterBuffer();
      window.electronAPI.startCycle({ mode, focusNiche: focusNiche.trim() || null });
      setCycleRunning(true);
    }
  }

  return (
    <div className="drag-region h-14 bg-surface border-b border-border flex items-center gap-3 px-4 select-none shrink-0">
      {/* Logo */}
      <div className="no-drag flex items-center gap-2 mr-2">
        <div className="w-7 h-7 rounded-lg bg-agents-orchestrator flex items-center justify-center text-xs font-black text-white">A</div>
        <span className="font-black text-sm tracking-widest text-white">ANDROOAGI</span>
      </div>

      {/* Stats pills */}
      <div className="no-drag flex items-center gap-2 text-xs">
        <Pill label="Cycles" value={stats.totalCycles} />
        <Pill label="Opps" value={stats.totalOppsFound} color="text-agents-scout" />
        <Pill label="Ready" value={stats.readyToLaunch} color="text-agents-store" />
      </div>

      <div className="flex-1" />

      {/* Niche input */}
      <input
        className="no-drag w-44 h-8 bg-surface-2 border border-border rounded-lg px-3 text-xs text-white placeholder:text-white/30 outline-none focus:border-agents-orchestrator/60 transition-colors"
        placeholder="Focus niche (optional)"
        value={focusNiche}
        onChange={(e) => setFocusNiche(e.target.value)}
        disabled={cycleRunning}
      />

      {/* Mode selector */}
      <div className="no-drag relative">
        <button
          className="h-8 px-3 bg-surface-2 border border-border rounded-lg text-xs text-white/70 hover:text-white hover:border-white/20 transition-colors"
          onClick={() => setShowModes(v => !v)}
          disabled={cycleRunning}
        >
          {MODES.find(m => m.value === mode)?.label} ▾
        </button>
        {showModes && (
          <div className="absolute right-0 top-10 w-52 bg-surface border border-border rounded-xl overflow-hidden shadow-2xl z-50 panel-slide-in">
            {MODES.map(m => (
              <button
                key={m.value}
                className={`w-full text-left px-4 py-3 text-xs hover:bg-surface-2 transition-colors ${mode === m.value ? 'text-agents-orchestrator' : 'text-white/70'}`}
                onClick={() => { setMode(m.value); setShowModes(false); }}
              >
                <div className="font-bold">{m.label}</div>
                <div className="text-white/40 mt-0.5">{m.desc}</div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Start / Stop */}
      <button
        className={`no-drag h-8 px-5 rounded-lg text-xs font-bold tracking-wider transition-all ${
          cycleRunning
            ? 'bg-red-900/50 border border-red-500/40 text-red-400 hover:bg-red-800/60'
            : 'bg-agents-orchestrator text-white hover:opacity-90 glow-orchestrator'
        }`}
        onClick={handleStart}
      >
        {cycleRunning ? '⬛ STOP' : '▶ START CYCLE'}
      </button>

      {/* Settings */}
      <button
        className="no-drag w-8 h-8 rounded-lg bg-surface-2 border border-border text-white/50 hover:text-white hover:border-white/20 text-sm transition-colors"
        onClick={() => setSettingsOpen(!settingsOpen)}
        title="Settings"
      >
        ⚙
      </button>

      {/* Window controls */}
      <div className="no-drag flex items-center gap-1 ml-1">
        <WinBtn color="bg-yellow-500" onClick={() => window.electronAPI.minimize()} />
        <WinBtn color="bg-green-500"  onClick={() => window.electronAPI.maximize()} />
        <WinBtn color="bg-red-500"    onClick={() => window.electronAPI.close()} />
      </div>
    </div>
  );
}

function Pill({ label, value, color = 'text-white/60' }: { label: string; value: number; color?: string }) {
  return (
    <div className="bg-surface-2 border border-border rounded-md px-2 py-0.5 flex items-center gap-1.5">
      <span className="text-white/30">{label}</span>
      <span className={`font-bold ${color}`}>{value}</span>
    </div>
  );
}

function WinBtn({ color, onClick }: { color: string; onClick: () => void }) {
  return (
    <button
      className={`w-3 h-3 rounded-full ${color} opacity-60 hover:opacity-100 transition-opacity`}
      onClick={onClick}
    />
  );
}
