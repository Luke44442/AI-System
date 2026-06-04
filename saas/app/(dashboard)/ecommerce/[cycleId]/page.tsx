'use client';
import { useState, useEffect, use } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Loader2, Check, X, ChevronDown, ChevronUp, ShoppingBag,
  TrendingUp, Palette, FileText, Megaphone, AlertTriangle,
  CheckCircle, Copy, ExternalLink,
} from 'lucide-react';
import { cn, scoreColor } from '@/lib/utils';

interface CycleDetail {
  id: string;
  status: string;
  focusNiche: string | null;
  approvalStatus: string;
  errorMessage: string | null;
  opportunities: Opportunity[];
  storeBlueprint: StoreBlueprint | null;
  marketingPlan: MarketingPlan | null;
  approvalItems: ApprovalItem[];
  createdAt: string;
}

interface Opportunity {
  id: string;
  rank: number;
  name: string;
  description: string;
  category: string;
  productType: string;
  demandScore: number;
  competitionLevel: string;
  monetizationScore: number;
  overallScore: number;
  platforms: string[];
  targetBuyer: string;
  priceRange: string;
  whyNow: string;
  validationDecision: string | null;
  validationReason: string | null;
  suggestedPrice: string | null;
  differentiators: string[];
  isTopPick: boolean;
  listings: Listing[];
}

interface StoreBlueprint {
  storeName: string;
  storeNameAlts: string[];
  tagline: string;
  brandColors: string[];
  brandTone: string;
  niche: string;
  positioning: string;
  productCatalog: { name: string; type: string; price: string; description: string; is_hero: boolean }[];
  launchChecklist: { order: number; task: string; time_estimate: string; platform: string }[];
}

interface Listing {
  id: string;
  productName: string;
  title: string;
  description: string;
  tags: string[];
  price: string;
  bundleIdeas: string[];
}

interface MarketingPlan {
  tiktokIdeas: { hook: string; concept: string; format: string }[];
  hookScripts: string[];
  launchStrategy: string;
  postingSchedule: { day: string; time: string; platform: string; content_type: string }[];
}

interface ApprovalItem {
  id: string;
  step: string;
  title: string;
  description: string;
  riskLevel: string;
  instructions: string;
  status: string;
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-[9px] text-slate-500 mb-0.5">
        <span>{label}</span><span style={{ color }}>{value}</span>
      </div>
      <div className="h-1 bg-white/5 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value * 10}%` }}
          transition={{ duration: 0.6 }}
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function CopyBtn({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={async () => { await navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
      className="text-[10px] text-slate-500 hover:text-white flex items-center gap-1 px-2 py-0.5 rounded hover:bg-white/5 transition"
    >
      {copied ? <Check size={10} className="text-emerald-400" /> : <Copy size={10} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  );
}

function Section({ title, icon, children, defaultOpen = true }: {
  title: string; icon: React.ReactNode; children: React.ReactNode; defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="glass rounded-2xl overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between p-4 hover:bg-white/[0.02] transition"
      >
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          {icon}{title}
        </div>
        {open ? <ChevronUp size={14} className="text-slate-500" /> : <ChevronDown size={14} className="text-slate-500" />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden">
            <div className="p-4 pt-0">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function CycleDetailPage({ params }: { params: Promise<{ cycleId: string }> }) {
  const { cycleId } = use(params);
  const [cycle, setCycle] = useState<CycleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [approvingAll, setApprovingAll] = useState(false);
  const [approvingItem, setApprovingItem] = useState<string | null>(null);

  useEffect(() => {
    void fetchCycle();
    // Poll if running
    const interval = setInterval(async () => {
      const c = await fetchCycle(true);
      if (c?.status === 'complete' || c?.status === 'error') clearInterval(interval);
    }, 6000);
    return () => clearInterval(interval);
  }, [cycleId]);

  async function fetchCycle(silent = false) {
    if (!silent) setLoading(true);
    try {
      const res = await fetch(`/api/ecommerce/cycle?cycleId=${cycleId}`);
      if (res.ok) {
        const data = await res.json() as CycleDetail;
        setCycle(data);
        return data;
      }
    } finally {
      if (!silent) setLoading(false);
    }
  }

  async function approveItem(itemId: string, action: 'approve' | 'reject') {
    setApprovingItem(itemId);
    await fetch('/api/ecommerce/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ itemId, action }),
    });
    setApprovingItem(null);
    void fetchCycle(true);
  }

  async function approveAll() {
    setApprovingAll(true);
    await fetch('/api/ecommerce/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cycleId, action: 'approve_all' }),
    });
    setApprovingAll(false);
    void fetchCycle(true);
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 size={24} className="animate-spin text-violet-400" />
    </div>
  );

  if (!cycle) return <div className="text-slate-400 text-sm">Cycle not found.</div>;

  if (cycle.status === 'running') return (
    <div className="max-w-2xl mx-auto text-center py-20">
      <Loader2 size={32} className="animate-spin text-violet-400 mx-auto mb-4" />
      <h2 className="text-lg font-semibold text-white mb-2">7 agents working…</h2>
      <p className="text-slate-400 text-sm">Researching niches, validating ideas, building store, writing listings and marketing plan.</p>
      <p className="text-slate-500 text-xs mt-2">This takes 2–4 minutes. Page auto-refreshes.</p>
    </div>
  );

  if (cycle.status === 'error') return (
    <div className="max-w-2xl mx-auto glass p-6 rounded-2xl text-center">
      <AlertTriangle size={32} className="text-red-400 mx-auto mb-3" />
      <h2 className="text-lg font-semibold text-white mb-2">Cycle failed</h2>
      <p className="text-slate-400 text-sm">{cycle.errorMessage ?? 'Unknown error'}</p>
    </div>
  );

  const topOpp = cycle.opportunities.find(o => o.isTopPick) ?? cycle.opportunities[0];
  const store = cycle.storeBlueprint;

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">{store?.storeName ?? 'Cycle Results'}</h1>
          <p className="text-slate-400 text-xs mt-0.5">{store?.tagline}</p>
        </div>
        {cycle.approvalStatus !== 'approved' && (
          <button
            onClick={() => void approveAll()}
            disabled={approvingAll}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-xl transition"
          >
            {approvingAll ? <Loader2 size={13} className="animate-spin" /> : <CheckCircle size={13} />}
            Approve All & Launch
          </button>
        )}
        {cycle.approvalStatus === 'approved' && (
          <span className="flex items-center gap-1.5 text-emerald-400 text-sm font-medium">
            <CheckCircle size={16} /> All steps approved
          </span>
        )}
      </div>

      {/* Top opportunity summary */}
      {topOpp && (
        <div className="glass p-4 rounded-2xl grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Top Pick', value: topOpp.name, small: true },
            { label: 'Revenue Estimate', value: topOpp.suggestedPrice ?? topOpp.priceRange },
            { label: 'Competition', value: topOpp.competitionLevel },
            { label: 'Decision', value: topOpp.validationDecision ?? '—' },
          ].map(({ label, value, small }) => (
            <div key={label}>
              <p className="text-[10px] text-slate-500 mb-0.5 uppercase tracking-wider">{label}</p>
              <p className={cn('font-semibold text-white', small ? 'text-xs' : 'text-sm')}>{value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Opportunities */}
      <Section title={`15 Opportunities Discovered`} icon={<TrendingUp size={14} className="text-violet-400" />}>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {cycle.opportunities.slice(0, 15).map((opp, i) => (
            <div key={opp.id} className={cn(
              'p-3 rounded-xl border transition-colors',
              opp.isTopPick ? 'border-violet-500/40 bg-violet-500/5' : 'border-white/[0.06] bg-white/[0.02]',
            )}>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <span className={cn('text-lg font-bold tabular-nums', scoreColor(opp.overallScore))}>
                    {opp.overallScore.toFixed(0)}
                  </span>
                  <span className="text-[9px] text-slate-500 ml-1">/100</span>
                </div>
                <div className="flex items-center gap-1">
                  {opp.isTopPick && <span className="text-[9px] text-violet-400 bg-violet-400/10 px-1.5 py-0.5 rounded-full border border-violet-400/20">TOP PICK</span>}
                  {opp.validationDecision && (
                    <span className={cn('text-[9px] px-1.5 py-0.5 rounded-full border', {
                      'launch': 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
                      'test': 'text-amber-400 bg-amber-400/10 border-amber-400/20',
                      'reject': 'text-red-400 bg-red-400/10 border-red-400/20',
                    }[opp.validationDecision] ?? '')}>
                      {opp.validationDecision.toUpperCase()}
                    </span>
                  )}
                </div>
              </div>
              <h3 className="text-xs font-semibold text-white mb-1">{opp.name}</h3>
              <p className="text-[9px] text-slate-500 mb-2 line-clamp-2">{opp.description}</p>
              <div className="space-y-1">
                <ScoreBar label="Demand" value={opp.demandScore} color="#7c3aed" />
                <ScoreBar label="Monetization" value={opp.monetizationScore} color="#059669" />
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                <span className="text-[8px] text-slate-600 bg-white/[0.03] border border-white/[0.04] px-1.5 py-0.5 rounded">{opp.productType}</span>
                <span className="text-[8px] text-slate-600 bg-white/[0.03] border border-white/[0.04] px-1.5 py-0.5 rounded">{opp.priceRange}</span>
                <span className={cn('text-[8px] px-1.5 py-0.5 rounded border', {
                  low: 'text-emerald-600 bg-emerald-400/5 border-emerald-400/10',
                  medium: 'text-amber-600 bg-amber-400/5 border-amber-400/10',
                  high: 'text-red-600 bg-red-400/5 border-red-400/10',
                }[opp.competitionLevel] ?? '')}>
                  {opp.competitionLevel} comp
                </span>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* Store Blueprint */}
      {store && (
        <Section title="Store Blueprint" icon={<Palette size={14} className="text-sky-400" />}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div>
                <p className="text-[10px] text-slate-500 uppercase mb-1">Store Name</p>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-white">{store.storeName}</span>
                  <CopyBtn text={store.storeName} />
                </div>
                <p className="text-xs text-slate-500 mt-0.5">Alternatives: {store.storeNameAlts?.join(', ')}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 uppercase mb-1">Tagline</p>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-200">"{store.tagline}"</span>
                  <CopyBtn text={store.tagline} />
                </div>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 uppercase mb-1">Brand Colors</p>
                <div className="flex gap-2">
                  {store.brandColors?.map(c => (
                    <div key={c} className="flex items-center gap-1">
                      <div className="w-5 h-5 rounded border border-white/10" style={{ backgroundColor: c }} />
                      <span className="text-[9px] text-slate-500">{c}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 uppercase mb-1">Positioning</p>
                <p className="text-xs text-slate-400 leading-relaxed">{store.positioning}</p>
              </div>
            </div>

            <div>
              <p className="text-[10px] text-slate-500 uppercase mb-2">Product Catalog ({store.productCatalog?.length})</p>
              <div className="space-y-1">
                {store.productCatalog?.map((p, i) => (
                  <div key={i} className={cn(
                    'flex items-center justify-between p-2 rounded border text-xs',
                    p.is_hero ? 'border-violet-500/20 bg-violet-500/5' : 'border-white/[0.04] bg-white/[0.02]',
                  )}>
                    <div className="flex-1 min-w-0">
                      <span className="text-white font-medium truncate">{p.name}</span>
                      {p.is_hero && <span className="ml-1 text-[9px] text-violet-400">★ Hero</span>}
                    </div>
                    <span className="text-emerald-400 text-[10px] ml-2">{p.price}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Section>
      )}

      {/* Listings */}
      {topOpp?.listings?.length > 0 && (
        <Section title={`${topOpp.listings.length} Optimized Listings`} icon={<FileText size={14} className="text-emerald-400" />}>
          <div className="space-y-4">
            {topOpp.listings.map((listing, i) => (
              <div key={listing.id} className="border border-white/[0.06] rounded-xl p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <span className="text-[10px] text-slate-500">Listing {i + 1} · {listing.price}</span>
                    <h3 className="text-xs font-semibold text-white">{listing.productName}</h3>
                  </div>
                  <CopyBtn text={`TITLE:\n${listing.title}\n\nDESCRIPTION:\n${listing.description}\n\nTAGS:\n${listing.tags?.join(', ')}`} />
                </div>
                <p className="text-[10px] text-sky-400 font-medium mb-1">Title:</p>
                <p className="text-xs text-slate-300 mb-2">{listing.title}</p>
                <p className="text-[10px] text-slate-500 mb-1">Tags:</p>
                <div className="flex flex-wrap gap-1 mb-2">
                  {listing.tags?.map(t => (
                    <span key={t} className="text-[9px] bg-white/[0.04] border border-white/[0.05] px-1.5 py-0.5 rounded text-slate-400">{t}</span>
                  ))}
                </div>
                {listing.bundleIdeas?.length > 0 && (
                  <>
                    <p className="text-[10px] text-amber-400 mb-1">Bundle ideas:</p>
                    {listing.bundleIdeas.map((b, j) => (
                      <p key={j} className="text-[9px] text-slate-500">• {b}</p>
                    ))}
                  </>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Marketing */}
      {cycle.marketingPlan && (
        <Section title="Marketing Plan" icon={<Megaphone size={14} className="text-amber-400" />}>
          <div className="space-y-4">
            <div>
              <p className="text-xs font-medium text-white mb-2">TikTok Hook Scripts</p>
              <div className="space-y-1">
                {(cycle.marketingPlan.hookScripts as string[])?.slice(0, 10).map((hook, i) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-white/[0.02] border border-white/[0.04] rounded-lg">
                    <span className="text-xs text-slate-300">"{hook}"</span>
                    <CopyBtn text={hook} />
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs font-medium text-white mb-2">TikTok Video Ideas</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {(cycle.marketingPlan.tiktokIdeas as { hook: string; concept: string; format: string }[])?.slice(0, 4).map((idea, i) => (
                  <div key={i} className="p-3 bg-white/[0.02] border border-white/[0.04] rounded-xl">
                    <span className="text-[9px] text-violet-400 font-medium">{idea.format}</span>
                    <p className="text-xs text-white font-medium mt-0.5">"{idea.hook}"</p>
                    <p className="text-[9px] text-slate-500 mt-1">{idea.concept}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Section>
      )}

      {/* Approval Queue */}
      {cycle.approvalItems?.length > 0 && (
        <Section title="⚙️ Approval Queue — READY FOR YOUR REVIEW" icon={<CheckCircle size={14} className="text-emerald-400" />}>
          <div className="mb-3 p-3 bg-amber-500/5 border border-amber-500/20 rounded-xl text-xs text-amber-400">
            ⚠️ These actions require your manual execution. GrowthIQ will NEVER automatically create accounts, publish listings, or spend money on your behalf.
          </div>
          <div className="space-y-3">
            {cycle.approvalItems.map((item, i) => (
              <div key={item.id} className={cn(
                'rounded-xl border overflow-hidden',
                item.status === 'approved' ? 'border-emerald-500/20 bg-emerald-500/5'
                : item.status === 'rejected' ? 'border-red-500/20 bg-red-500/5'
                : 'border-white/[0.08] bg-white/[0.02]',
              )}>
                <div className="flex items-center justify-between p-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-500 tabular-nums w-4">{i + 1}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-white">{item.title}</span>
                        <span className={cn('text-[9px] px-1.5 py-0.5 rounded-full border', {
                          low: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
                          medium: 'text-amber-400 bg-amber-400/10 border-amber-400/20',
                          high: 'text-red-400 bg-red-400/10 border-red-400/20',
                        }[item.riskLevel] ?? '')}>
                          {item.riskLevel} risk
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-500">{item.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {item.status === 'approved' && <span className="text-emerald-400 text-xs flex items-center gap-1"><Check size={12} /> Approved</span>}
                    {item.status === 'rejected' && <span className="text-red-400 text-xs flex items-center gap-1"><X size={12} /> Rejected</span>}
                    {item.status === 'pending' && (
                      <>
                        <button
                          onClick={() => void approveItem(item.id, 'approve')}
                          disabled={approvingItem === item.id}
                          className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 bg-emerald-400/10 hover:bg-emerald-400/20 border border-emerald-400/20 px-3 py-1 rounded-lg transition"
                        >
                          {approvingItem === item.id ? <Loader2 size={10} className="animate-spin" /> : <Check size={10} />}
                          Approve
                        </button>
                        <button
                          onClick={() => void approveItem(item.id, 'reject')}
                          disabled={approvingItem === item.id}
                          className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 bg-red-400/10 border border-red-400/20 px-3 py-1 rounded-lg transition"
                        >
                          <X size={10} /> Skip
                        </button>
                      </>
                    )}
                  </div>
                </div>
                {item.status === 'approved' && (
                  <div className="border-t border-emerald-500/10 p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] text-slate-500">Step-by-step instructions:</span>
                      <CopyBtn text={item.instructions} />
                    </div>
                    <pre className="text-[9px] text-slate-300 whitespace-pre-wrap leading-relaxed font-mono overflow-x-auto">{item.instructions}</pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}
