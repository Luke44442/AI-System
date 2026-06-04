'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Sparkles } from 'lucide-react';

const SUGGESTIONS = [
  'AI tools for small businesses',
  'Faceless YouTube channel ideas',
  'Digital products under $50',
  'Freelance niches with high demand in 2025',
];

export function QuickResearch() {
  const router = useRouter();
  const [topic, setTopic] = useState('');

  function go(t?: string) {
    const q = (t ?? topic).trim();
    if (!q) return;
    router.push(`/research?q=${encodeURIComponent(q)}`);
  }

  return (
    <div className="glass p-5 rounded-2xl">
      <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
        <Sparkles size={14} className="text-violet-400" />
        Quick Research
      </h2>
      <div className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={topic}
            onChange={e => setTopic(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && go()}
            placeholder="Enter a topic or niche…"
            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl pl-9 pr-4 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-violet-500/40 transition"
          />
        </div>
        <button
          onClick={() => go()}
          disabled={!topic.trim()}
          className="bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition"
        >
          Go
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map(s => (
          <button
            key={s}
            onClick={() => go(s)}
            className="text-xs text-slate-400 hover:text-violet-400 bg-white/[0.03] hover:bg-violet-500/10 border border-white/[0.05] px-2.5 py-1 rounded-full transition"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
