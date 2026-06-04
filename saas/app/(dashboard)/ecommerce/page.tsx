'use client';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShoppingBag, Loader2, Sparkles, TrendingUp, Clock,
  CheckCircle, XCircle, AlertCircle, ChevronRight, Play,
} from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

interface CycleSummary {
  id: string;
  status: 'running' | 'complete' | 'error';
  focusNiche: string | null;
  approvalStatus: string;
  createdAt: string;
  storeBlueprint: { storeName: string } | null;
  _count: { opportunities: number };
}

function StatusBadge({ status }: { status: string }) {
  const map = {
    running: { icon: <Loader2 size={10} className="animate-spin" />, label: 'Running', cls: 'text-amber-400 bg-amber-400/10 border-amber-400/20' },
    complete: { icon: <CheckCircle size={10} />, label: 'Complete', cls: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20' },
    error: { icon: <XCircle size={10} />, label: 'Error', cls: 'text-red-400 bg-red-400/10 border-red-400/20' },
  }[status] ?? { icon: <Clock size={10} />, label: status, cls: 'text-slate-400 bg-slate-400/10 border-slate-400/20' };

  return (
    <span className={cn('flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border', map.cls)}>
      {map.icon} {map.label}
    </span>
  );
}

const STEPS = [
  { label: 'Market Research', desc: 'Scanning 15 niches', icon: '🧭' },
  { label: 'Validation', desc: 'Filtering top 3 ideas', icon: '🧪' },
  { label: 'Store Builder', desc: 'Designing storefront', icon: '🏗️' },
  { label: 'Listings & SEO', desc: 'Writing 5 listings', icon: '✍️' },
  { label: 'Product Specs', desc: 'Creating product files', icon: '🎨' },
  { label: 'Marketing Plan', desc: 'Building content strategy', icon: '📈' },
  { label: 'Approval Package', desc: 'Packaging for review', icon: '⚙️' },
];

export default function EcommerceDashboard() {
  const [cycles, setCycles] = useState<CycleSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [launching, setLaunching] = useState(false);
  const [focusNiche, setFocusNiche] = useState('');
  const [activeStep, setActiveStep] = useState(0);
  const [pollingId, setPollingId] = useState<string | null>(null);

  useEffect(() => {
    void fetchCycles();
  }, []);

  // Poll running cycles
  useEffect(() => {
    if (!pollingId) return;
    const interval = setInterval(async () => {
      const res = await fetch(`/api/ecommerce/cycle?cycleId=${pollingId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'complete' || data.status === 'error') {
          setPollingId(null);
          setLaunching(false);
          void fetchCycles();
        } else {
          // Advance step indicator
          const oppCount = data.opportunities?.length ?? 0;
          const hasStore = !!data.storeBlueprint;
          const hasListings = data.opportunities?.some((o: { listings?: unknown[] }) => o.listings?.length) ?? false;
          const hasMarketing = !!data.marketingPlan;
          const hasApproval = data.approvalItems?.length > 0;
          setActiveStep(
            hasApproval ? 6
            : hasMarketing ? 5
            : hasListings ? 4
            : hasStore ? 3
            : oppCount > 0 && oppCount <= 3 ? 2
            : oppCount > 3 ? 1
            : 0,
          );
        }
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [pollingId]);

  async function fetchCycles() {
    setLoading(true);
    try {
      const res = await fetch('/api/ecommerce/cycle');
      if (res.ok) setCycles(await res.json());
    } finally {
      setLoading(false);
    }
  }

  async function launchCycle() {
    setLaunching(true);
    setActiveStep(0);
    try {
      const res = await fetch('/api/ecommerce/cycle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ focusNiche: focusNiche.trim() || undefined }),
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.error ?? 'Failed to start cycle');
        setLaunching(false);
        return;
      }
      setPollingId(data.cycleId);
      void fetchCycles();
    } catch {
      setLaunching(false);
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <ShoppingBag size={22} className="text-violet-400" />
          E-Commerce OS
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          7-agent system that discovers profitable niches, builds store concepts, writes listings, and plans marketing — automatically.
        </p>
      </div>

      {/* Launch panel */}
      <div className="glass p-5 rounded-2xl">
        <h2 className="text-sm font-semibold text-white mb-3">Run Research Cycle</h2>
        <div className="flex gap-3 mb-4">
          <input
            type="text"
            value={focusNiche}
            onChange={e => setFocusNiche(e.target.value)}
            placeholder="Optional: focus niche (e.g. 'wedding templates', 'fitness planners')"
            disabled={launching}
            className="flex-1 bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-violet-500/40 disabled:opacity-50 transition"
          />
          <button
            onClick={() => void launchCycle()}
            disabled={launching}
            className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-medium px-5 py-2.5 rounded-xl text-sm transition"
          >
            {launching ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            {launching ? 'Running…' : 'Launch Cycle'}
          </button>
        </div>

        {/* Step progress — shown while running */}
        <AnimatePresence>
          {launching && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
              <div className="grid grid-cols-4 sm:grid-cols-7 gap-2 mt-2">
                {STEPS.map((step, i) => (
                  <div key={step.label} className={cn(
                    'text-center p-2 rounded-lg transition-all',
                    i < activeStep ? 'bg-emerald-500/10 border border-emerald-500/20'
                    : i === activeStep ? 'bg-violet-500/15 border border-violet-500/30 animate-pulse'
                    : 'bg-white/[0.02] border border-white/[0.04]',
                  )}>
                    <div className="text-lg">{step.icon}</div>
                    <div className="text-[9px] font-medium text-white mt-0.5">{step.label}</div>
                    <div className="text-[8px] text-slate-600">{step.desc}</div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-500 mt-3 text-center">
                Running 7 AI agents… this takes 2–4 minutes. You can leave this page.
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Cycles list */}
      <div>
        <h2 className="text-sm font-medium text-slate-400 mb-3">Research Cycles</h2>
        {loading ? (
          <div className="glass rounded-xl p-8 text-center">
            <Loader2 size={20} className="animate-spin text-violet-400 mx-auto" />
          </div>
        ) : cycles.length === 0 ? (
          <div className="glass rounded-xl p-12 text-center">
            <ShoppingBag size={32} className="text-slate-700 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">No cycles yet. Launch your first research run above.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {cycles.map(cycle => (
              <Link key={cycle.id} href={`/ecommerce/${cycle.id}`}>
                <motion.div
                  whileHover={{ x: 2 }}
                  className="glass p-4 rounded-xl flex items-center gap-4 hover:border-violet-500/20 transition-colors cursor-pointer"
                >
                  <div className="w-10 h-10 bg-violet-500/10 border border-violet-500/20 rounded-xl flex items-center justify-center text-lg shrink-0">
                    🏪
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-sm font-medium text-white">
                        {cycle.storeBlueprint?.storeName ?? (cycle.focusNiche ? `"${cycle.focusNiche}"` : 'Auto-discovery cycle')}
                      </span>
                      <StatusBadge status={cycle.status} />
                    </div>
                    <p className="text-xs text-slate-500">
                      {cycle._count.opportunities} opportunities found
                      {cycle.focusNiche ? ` · Focus: ${cycle.focusNiche}` : ' · All niches'}
                      {' · '}{new Date(cycle.createdAt).toLocaleDateString()}
                    </p>
                  </div>
                  {cycle.status === 'complete' && (
                    <div className="flex items-center gap-1.5">
                      {cycle.approvalStatus === 'approved' ? (
                        <span className="text-[10px] text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2 py-0.5 rounded-full">
                          Approved
                        </span>
                      ) : (
                        <span className="text-[10px] text-amber-400 bg-amber-400/10 border border-amber-400/20 px-2 py-0.5 rounded-full">
                          Needs Review
                        </span>
                      )}
                    </div>
                  )}
                  <ChevronRight size={14} className="text-slate-700 shrink-0" />
                </motion.div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
