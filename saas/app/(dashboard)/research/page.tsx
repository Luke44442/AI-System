'use client';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Loader2, TrendingUp, Bookmark, ChevronRight, Sparkles } from 'lucide-react';
import { cn, scoreColor, scoreGrade, platformIcon } from '@/lib/utils';

interface Opportunity {
  title: string;
  description: string;
  niche: string;
  platforms: string[];
  virality_score: number;
  monetization_score: number;
  competition_score: number;
  ease_score: number;
  overall_score: number;
  keywords: string[];
  content_angle: string;
  why_now: string;
}

const EXAMPLE_TOPICS = [
  'AI productivity tools for freelancers',
  'Solo travel in Southeast Asia',
  'Budget home gym setup',
  'Passive income with digital products',
  'Mental health for entrepreneurs',
];

function OpportunityCard({ opp, index }: { opp: Opportunity; index: number }) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await fetch('/api/opportunities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectId: 'default', // TODO: project selector
          title: opp.title,
          description: opp.description,
          niche: opp.niche,
          platforms: opp.platforms,
          overallScore: opp.overall_score,
          viralityScore: opp.virality_score,
          monetizationScore: opp.monetization_score,
          competitionScore: opp.competition_score,
          easeScore: opp.ease_score,
          contentAngle: opp.content_angle,
          whyNow: opp.why_now,
          keywords: opp.keywords,
        }),
      });
      setSaved(true);
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="glass p-4 rounded-xl hover:border-violet-500/20 transition-colors group"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn('text-2xl font-bold tabular-nums', scoreColor(opp.overall_score))}>
              {opp.overall_score}
            </span>
            <span className="text-xs text-slate-500 font-medium">
              {scoreGrade(opp.overall_score)} score
            </span>
          </div>
          <h3 className="font-semibold text-white text-sm leading-snug">{opp.title}</h3>
          <p className="text-xs text-slate-500 mt-0.5">{opp.niche}</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving || saved}
          className={cn(
            'shrink-0 p-1.5 rounded-lg transition-colors',
            saved
              ? 'text-emerald-400 bg-emerald-400/10'
              : 'text-slate-600 hover:text-violet-400 hover:bg-violet-400/10',
          )}
        >
          {saving ? <Loader2 size={14} className="animate-spin" /> : <Bookmark size={14} />}
        </button>
      </div>

      <p className="text-xs text-slate-400 leading-relaxed mb-3">{opp.description}</p>

      {/* Scores */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 mb-3">
        {[
          { label: 'Virality', value: opp.virality_score },
          { label: 'Monetization', value: opp.monetization_score },
          { label: 'Low Competition', value: 100 - opp.competition_score },
          { label: 'Ease', value: opp.ease_score },
        ].map(({ label, value }) => (
          <div key={label}>
            <div className="flex justify-between text-[10px] text-slate-500 mb-0.5">
              <span>{label}</span>
              <span className={scoreColor(value)}>{value}</span>
            </div>
            <div className="h-1 bg-white/5 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${value}%` }}
                transition={{ delay: index * 0.04 + 0.2, duration: 0.5 }}
                className={cn('h-full rounded-full', value >= 70 ? 'bg-emerald-500' : value >= 50 ? 'bg-sky-500' : 'bg-amber-500')}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Platforms + angle */}
      <div className="flex items-center gap-1.5 flex-wrap mb-2">
        {opp.platforms.map(p => (
          <span key={p} className="text-[10px] bg-white/5 border border-white/[0.06] px-1.5 py-0.5 rounded text-slate-400">
            {platformIcon(p)} {p}
          </span>
        ))}
      </div>

      <div className="text-[10px] text-slate-500 border-t border-white/[0.04] pt-2 mt-2">
        <span className="text-violet-400 font-medium">Angle: </span>
        {opp.content_angle}
      </div>
    </motion.div>
  );
}

export default function ResearchPage() {
  const [topic, setTopic] = useState('');
  const [results, setResults] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [runTopic, setRunTopic] = useState('');

  async function runResearch(t?: string) {
    const q = (t ?? topic).trim();
    if (!q) return;
    setLoading(true);
    setError('');
    setResults([]);
    setRunTopic(q);

    try {
      const res = await fetch('/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: q }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? 'Research failed');
        return;
      }
      setResults(data.results);
    } catch {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <TrendingUp size={22} className="text-violet-400" />
          Research Engine
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Enter any topic or niche to discover the top 10 ranked opportunities right now.
        </p>
      </div>

      {/* Search bar */}
      <div className="glass p-4 rounded-2xl">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={topic}
              onChange={e => setTopic(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && void runResearch()}
              placeholder="e.g. AI tools for content creators, sustainable fashion..."
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl pl-9 pr-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-violet-500/40 transition"
            />
          </div>
          <button
            onClick={() => void runResearch()}
            disabled={loading || !topic.trim()}
            className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium px-5 py-3 rounded-xl text-sm transition"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
            {loading ? 'Researching…' : 'Research'}
          </button>
        </div>

        {/* Example topics */}
        <div className="flex items-center gap-2 mt-3 flex-wrap">
          <span className="text-[10px] text-slate-600">Try:</span>
          {EXAMPLE_TOPICS.map(t => (
            <button
              key={t}
              onClick={() => { setTopic(t); void runResearch(t); }}
              className="text-[10px] text-slate-400 hover:text-violet-400 bg-white/[0.03] hover:bg-violet-500/10 border border-white/[0.05] px-2 py-1 rounded-full transition"
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-2">
          <p className="text-sm text-slate-400 flex items-center gap-2">
            <Loader2 size={14} className="animate-spin text-violet-400" />
            Analyzing &ldquo;{runTopic}&rdquo; — this takes 10–20 seconds…
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="glass p-4 rounded-xl animate-pulse h-52 bg-white/[0.02]" />
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      <AnimatePresence>
        {results.length > 0 && !loading && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-medium text-slate-300">
                {results.length} opportunities for &ldquo;{runTopic}&rdquo;
              </h2>
              <span className="text-[10px] text-slate-500">Sorted by overall score</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
              {results.map((opp, i) => (
                <OpportunityCard key={opp.title + i} opp={opp} index={i} />
              ))}
            </div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
