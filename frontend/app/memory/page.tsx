'use client';
import { useState } from 'react';
import { motion } from 'framer-motion';
import { MemoryCenter }  from '@/components/panels/MemoryCenter';
import { GlassCard, PanelHeader, NeonBadge, ScoreBar } from '@/components/ui';
import { useSystemStore } from '@/store/useSystemStore';
import { memoryApi }      from '@/lib/api';
import { Brain, Search, Database, Clock, Zap } from 'lucide-react';

export default function MemoryPage() {
  const { lessons, insights } = useSystemStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<unknown[]>([]);
  const [searching, setSearching] = useState(false);

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await memoryApi.query(searchQuery);
      setSearchResults(res.results);
    } finally {
      setSearching(false);
    }
  }

  const successLessons = lessons.filter(l => l.category === 'success').length;
  const failLessons    = lessons.filter(l => l.category === 'failure').length;
  const improvLessons  = lessons.filter(l => l.category === 'improvement').length;

  const STATS = [
    { label: 'Total Lessons',  value: lessons.length || '5', color: '#00c8ff', icon: '◈' },
    { label: 'Successes',      value: successLessons || '2',  color: '#00ff94', icon: '✓' },
    { label: 'Failures',       value: failLessons || '1',     color: '#ef4444', icon: '✗' },
    { label: 'Improvements',   value: improvLessons || '2',   color: '#9333ea', icon: '→' },
    { label: 'Insights',       value: insights.length || '3', color: '#f59e0b', icon: '★' },
  ];

  return (
    <div className="flex flex-col gap-3">
      <div className="font-orbitron text-base font-bold text-neon-blue">Memory Center</div>

      {/* Stats */}
      <div className="grid grid-cols-5 gap-3">
        {STATS.map(s => (
          <GlassCard key={s.label} className="flex items-center gap-3">
            <span className="text-xl opacity-70" style={{ color: s.color }}>{s.icon}</span>
            <div>
              <div className="font-orbitron font-bold text-lg" style={{ color: s.color }}>{s.value}</div>
              <div className="font-mono text-[8px] text-slate-500 uppercase tracking-wider">{s.label}</div>
            </div>
          </GlassCard>
        ))}
      </div>

      {/* Semantic search */}
      <GlassCard noPad>
        <PanelHeader title="Semantic Knowledge Search" icon={<Search size={12} />} badge="VECTOR" badgeColor="#9333ea" />
        <div className="p-4 space-y-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && void handleSearch()}
              placeholder="Search knowledge base semantically..."
              className="flex-1 px-3 py-2.5 bg-surface-mid/60 border border-[rgba(255,255,255,0.08)] rounded font-mono text-[11px] text-slate-200 placeholder-slate-600 focus:outline-none focus:border-neon-blue/40"
            />
            <button
              onClick={() => void handleSearch()}
              disabled={searching}
              className="px-5 py-2 border border-neon-blue/30 bg-neon-blue/10 text-neon-blue font-mono text-[10px] rounded transition-all hover:bg-neon-blue/20 disabled:opacity-50"
            >
              {searching ? 'SEARCHING...' : 'SEARCH'}
            </button>
          </div>
          {searchResults.length > 0 && (
            <div className="space-y-2">
              {(searchResults as Array<{ text?: string; id?: string; similarity?: number; metadata?: Record<string, unknown> }>).map((r, i) => (
                <motion.div
                  key={r.id ?? i}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="p-3 rounded border border-[rgba(147,51,234,0.2)] bg-[rgba(147,51,234,0.05)]"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-[8px] text-purple-400">{r.id}</span>
                    {r.similarity != null && (
                      <NeonBadge label={`${(r.similarity * 100).toFixed(0)}% match`} color="#9333ea" />
                    )}
                  </div>
                  <p className="font-mono text-[10px] text-slate-300 leading-relaxed">{r.text}</p>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </GlassCard>

      {/* Main memory panel */}
      <div className="grid grid-cols-[1fr_360px] gap-3" style={{ minHeight: 500 }}>
        <MemoryCenter />

        {/* System memory metrics */}
        <div className="flex flex-col gap-3">
          <GlassCard noPad>
            <PanelHeader title="Memory Systems" icon={<Database size={12} />} />
            <div className="p-4 space-y-3">
              {[
                { label: 'Short-term (Redis)',     used: 72, color: '#00c8ff', icon: <Zap size={11} /> },
                { label: 'Long-term (PostgreSQL)', used: 34, color: '#9333ea', icon: <Database size={11} /> },
                { label: 'Vector (ChromaDB)',       used: 18, color: '#ec4899', icon: <Brain size={11} /> },
                { label: 'Agent Inboxes (Queue)',   used: 8,  color: '#f59e0b', icon: <Clock size={11} /> },
              ].map(m => (
                <div key={m.label}>
                  <div className="flex items-center gap-1.5 mb-1">
                    <span style={{ color: m.color }}>{m.icon}</span>
                    <span className="font-mono text-[10px] text-slate-300">{m.label}</span>
                    <span className="ml-auto font-mono text-[9px]" style={{ color: m.color }}>{m.used}%</span>
                  </div>
                  <ScoreBar score={m.used} color={m.color} showValue={false} />
                </div>
              ))}
            </div>
          </GlassCard>

          <GlassCard noPad>
            <PanelHeader title="Memory Config" icon={<Brain size={12} />} />
            <div className="p-4 space-y-2">
              {[
                { key: 'Short-term TTL',  value: '1 hour' },
                { key: 'Long-term retain', value: '365 days' },
                { key: 'Vector results',   value: '10 max' },
                { key: 'Embedding model',  value: 'all-MiniLM-L6' },
              ].map(({ key, value }) => (
                <div key={key} className="flex justify-between items-center py-1 border-b border-[rgba(255,255,255,0.04)]">
                  <span className="font-mono text-[9px] text-slate-500">{key}</span>
                  <span className="font-mono text-[9px] text-neon-blue">{value}</span>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
