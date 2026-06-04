'use client';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, Copy, Check, Sparkles, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

const CONTENT_TYPES = [
  { value: 'tiktok_script',      label: 'TikTok Script',       emoji: '🎵', desc: '30-60 sec viral script' },
  { value: 'youtube_idea',       label: 'YouTube Video',        emoji: '▶️', desc: '8-15 min outline + script' },
  { value: 'instagram_caption',  label: 'Instagram Caption',    emoji: '📸', desc: 'Caption + 25 hashtags' },
  { value: 'twitter_thread',     label: 'Twitter Thread',       emoji: '🐦', desc: '8-12 tweet thread' },
  { value: 'ad_copy',            label: 'Ad Copy',              emoji: '📣', desc: 'Facebook/Instagram ads' },
  { value: 'email_sequence',     label: 'Email Sequence',       emoji: '📧', desc: '5-email welcome series' },
  { value: 'landing_page',       label: 'Landing Page',         emoji: '🌐', desc: 'Full page copy' },
] as const;

type ContentType = (typeof CONTENT_TYPES)[number]['value'];

interface GeneratedContent {
  type: string;
  platform: string;
  title: string;
  content: string;
  hook?: string;
  cta?: string;
  hashtags?: string[];
  estimated_reach?: string;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }
  return (
    <button onClick={copy} className="flex items-center gap-1 text-xs text-slate-400 hover:text-white transition px-2 py-1 rounded hover:bg-white/5">
      {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
      {copied ? 'Copied!' : 'Copy'}
    </button>
  );
}

export default function ContentPage() {
  const [type, setType] = useState<ContentType>('tiktok_script');
  const [topic, setTopic] = useState('');
  const [audience, setAudience] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GeneratedContent | null>(null);
  const [error, setError] = useState('');

  async function generate() {
    if (!topic.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await fetch('/api/content', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, topic: topic.trim(), audience: audience.trim() || undefined }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? 'Generation failed');
        return;
      }
      setResult(data);
    } catch {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <FileText size={22} className="text-sky-400" />
          Content Generator
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Generate platform-optimized content from any topic or opportunity.
        </p>
      </div>

      <div className="glass p-5 rounded-2xl space-y-5">
        {/* Content type selector */}
        <div>
          <label className="text-xs font-medium text-slate-400 mb-2 block">Content type</label>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
            {CONTENT_TYPES.map(ct => (
              <button
                key={ct.value}
                onClick={() => setType(ct.value)}
                className={cn(
                  'flex flex-col items-start p-3 rounded-xl border text-left transition-all',
                  type === ct.value
                    ? 'border-violet-500/40 bg-violet-500/10 text-white'
                    : 'border-white/[0.06] bg-white/[0.02] text-slate-400 hover:border-white/10 hover:text-slate-300',
                )}
              >
                <span className="text-lg mb-1">{ct.emoji}</span>
                <span className="text-xs font-medium">{ct.label}</span>
                <span className="text-[10px] text-slate-600">{ct.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Topic input */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Topic / opportunity</label>
            <input
              type="text"
              value={topic}
              onChange={e => setTopic(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && void generate()}
              placeholder="e.g. 5 AI tools that save 10 hours/week"
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-violet-500/40 transition"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">
              Target audience <span className="text-slate-600">(optional)</span>
            </label>
            <input
              type="text"
              value={audience}
              onChange={e => setAudience(e.target.value)}
              placeholder="e.g. freelance designers, age 25-35"
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-violet-500/40 transition"
            />
          </div>
        </div>

        <button
          onClick={() => void generate()}
          disabled={loading || !topic.trim()}
          className="flex items-center gap-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium px-5 py-2.5 rounded-xl text-sm transition"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
          {loading ? 'Generating…' : 'Generate content'}
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      <AnimatePresence>
        {result && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-white">{result.title}</h2>
              <span className="text-xs text-slate-500 bg-white/[0.04] px-2 py-1 rounded-full">{result.platform}</span>
            </div>

            {result.hook && (
              <div className="glass p-4 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-sky-400">Hook</span>
                  <CopyButton text={result.hook} />
                </div>
                <p className="text-sm text-white leading-relaxed whitespace-pre-wrap">{result.hook}</p>
              </div>
            )}

            <div className="glass p-4 rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-violet-400">Content</span>
                <CopyButton text={result.content} />
              </div>
              <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">{result.content}</p>
            </div>

            {result.cta && (
              <div className="glass p-4 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-emerald-400">Call to Action</span>
                  <CopyButton text={result.cta} />
                </div>
                <p className="text-sm text-white">{result.cta}</p>
              </div>
            )}

            {result.hashtags && result.hashtags.length > 0 && (
              <div className="glass p-4 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-amber-400">Hashtags</span>
                  <CopyButton text={result.hashtags.join(' ')} />
                </div>
                <div className="flex flex-wrap gap-1">
                  {result.hashtags.map(h => (
                    <span key={h} className="text-xs text-sky-400 bg-sky-400/10 px-2 py-0.5 rounded-full">{h}</span>
                  ))}
                </div>
              </div>
            )}

            {result.estimated_reach && (
              <p className="text-xs text-slate-500">📊 Estimated reach: {result.estimated_reach}</p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
